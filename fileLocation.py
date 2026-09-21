"""
Indicates a file with location (or start/end location)

myfile.txt:1 # get line 1 from the file
myfile.txt:1:2 # get the entire line1 starting at character2 to the end of line
myfile.txt:1-2 # get lines 1 and 2
myfile.txt:1:2-2:3 # get an oddly specific range
"""
import typing
import re
import urllib.parse
import paths
from paths._url import Url,URLCompatible
from paths.urlTyping import isUrlCompatible
from .textLocation import TextLocation,TextLocationSinglePoint


class UrlWithFileLocation(TextLocation):
    """
    Indicates a url to a file with location (or start/end location)

    myfile.txt:1 # get line 1 from the file
    myfile.txt:1:2 # get the entire line1 from character2 to the end of line
    myfile.txt:1-2 # get lines 1 and 2
    myfile.txt:1:2-2:3 # get an oddly specific range

    TODO:
    * could we also do
        myfile.txt:1,3,5 to pick out specific lines?
    * how does this work with proper urls?
    * should slicing [] notation also be a valid url notation?
        myfile.txt[1:-1]

    NOTE: behind the scenes this is also a URL of the form
    specified in RFC-5147
    https://datatracker.ietf.org/doc/html/rfc5147
    """
    _URL_BASE_CLASSES = {}

    FILE_LOCATION_REGEX=re.compile(
        r"""(?P<filename>(.*[/\\])?[^:(]*)([:(](?P<row>\d*)(\s*[:,]\s*(?P<col>\d*))?\)?)""") # noqa: E501 # pylint: disable=line-too-lo

    def __init__(self,
        url:"UrlWithLocationCompatible"="",
        fromRow:typing.Union[None,int,
            'FileLocationCompatible',TextLocationSinglePoint,TextLocation]=None,
        fromColumn:typing.Optional[int]=None,
        toRow:typing.Union[None,int,TextLocationSinglePoint]=None,
        toColumn:typing.Optional[int]=None,
        relativeTo:typing.Optional[paths.URLCompatible]=None,
        maxParentLevels:typing.Optional[int]=None,
        maxChildLevels:typing.Optional[int]=None,
        location:typing.Union[None,'FileLocationCompatible','TextLocation']=None):
        """
        :fromRow: can be used as location to make ordered-parameters easier
        :maxParentLevels: the maximum number of parent levels to allow
            in a relative path - for security, recommend setting this to 0
        :maxChildLevels: the maximum number of child levels to allow
            in a relative path
        :location: fill in any missing to/from row/column with this location
        """
        self.url:Url
        TextLocation.__init__(self)
        UrlWithFileLocation.assign(self,url,
            fromRow,fromColumn,toRow,toColumn,
            relativeTo,maxParentLevels,maxChildLevels,location)

    def __hash__(self)->int:
        return hash(str(self))

    def asOffsetIntoText(self,text:typing.Optional[str]=None)->typing.Tuple[int,int]:
        """
        Convert this point into an offset in the given text.
        You can leave the text blank and it will auto-read from file.

        NOTE: this has to look up carriage returns every time,
        so if you do a lot of this, it may be better to use a
        stored index table, eg, generated from rowOffsets().
        """
        if text is None:
            text=self.url.readString()
        return TextLocation.asOffsetIntoText(self,text)

    def rowOffsets(self,text:typing.Optional[str]=None)->typing.List[int]:
        """
        Generate a table of row offsets
        You can leave the text blank and it will auto-read from file.
        """
        if text is None:
            text=self.url.readString()
        return TextLocation.rowOffsets(self,text)

    def copy(self)->"UrlWithFileLocation":
        """
        Copy this url with location
        """
        return UrlWithFileLocation(self.url,
            self.fromRow,self.fromColumn,self.toRow,self.toColumn)

    def __eq__(self, # type: ignore
        __o:typing.Union["UrlWithFileLocation",URLCompatible]
        )->bool:
        """
        Compare to a filename, location, or url
        """
        if isinstance(__o,UrlWithFileLocation):
            if __o.url!=self.url:
                return False
            if __o.fromRow>1 and self.fromRow>1:
                if __o.fromRow!=self.fromRow:
                    return False
                if __o.fromColumn>1 and self.fromColumn>1:
                    if __o.fromColumn!=self.fromColumn:
                        return False
                    if __o.toRow>1 and self.toRow>1:
                        if __o.toRow!=self.toRow:
                            return False
                        if __o.toColumn>1 and self.toColumn>1:
                            if __o.toColumn!=self.toColumn:
                                return False
            return True
        elif hasattr(__o,'location'):
            return self==getattr(__o,'location')
        elif isinstance(__o,str):
            return self==UrlWithFileLocation(__o)
        elif isinstance(__o,paths.URL)\
            or hasattr(__o,'url')\
            or hasattr(__o,'filename'):
            return self.url==paths.asURL(typing.cast(paths.URLCompatible,__o))
        return False

    def __cmp__(self,other:'UrlWithLocationCompatible')->int:
        """
        Oldschool compare
        """
        other=asUrlWithFileLocation(other)
        result=self.url.__cmp__(other.url)
        if result==0:
            result=self.fromPoint.__cmp__(other.fromPoint)
            if result==0:
                result=self.toPoint.__cmp__(other.toPoint)
        return result

    # Implementing the new dunder methods using __cmp__
    def __lt__(self,other):
        return self.__cmp__(other)<0
    def __le__(self,other):
        return self.__cmp__(other)<=0
    def __ne__(self,other):
        return self.__cmp__(other)!=0
    def __gt__(self, other):
        return self.__cmp__(other)>0
    def __ge__(self,other):
        return self.__cmp__(other)>=0

    def contains(self,other:TextLocation)->bool: # type: ignore
        """
        Does this entirely contain another location?
        """
        if isinstance(other,UrlWithFileLocation) and other.url!=self.url:
            return False
        return TextLocation.contains(self,other)

    def overlaps(self,other:TextLocation)->bool:
        """
        Does this contain or overlap another location?
        """
        if isinstance(other,UrlWithFileLocation) and other.url!=self.url:
            return False
        return TextLocation.overlaps(self,other)

    def union(self,
        other:'TextLocation',fillGaps:bool=True
        )->'UrlWithFileLocation':
        """
        Return a new location that is a combination of this location
        and another location.

        :fillGaps: if it is file.txt:100-110 and file.txt:200-210, should
            we return file.txt:100-210, or raise a ValueError exception?
        """
        if isinstance(other,UrlWithFileLocation) and other.url!=self.url:
            raise ValueError('Cannot combine line ranges across two different files')
        location=TextLocation.union(self,other)
        return UrlWithFileLocation(self.url,location)
    def __add__(self, # type: ignore
        other:'TextLocation'
        )->typing.Optional['FileLocation']:
        """
        Implement addition operator same as union() function
        """
        return self.union(other)

    def difference(self,
        other:'TextLocation'
        )->typing.Union[None,
            'UrlWithFileLocation',
            typing.Tuple['UrlWithFileLocation','UrlWithFileLocation']]:
        """
        Return a new location that is a this location
        with another location removed from it.

        returns None if this causes the location to completely disappear
        NOTE: this could result in this being split into two, eg. 
            file.txt:100..400 - file.txt:200..300 = (file.txt:100..200, file.txt:300-400)
        """
        if isinstance(other,UrlWithFileLocation) and other.url!=self.url:
            raise ValueError('Cannot subtract line ranges across two different files')
        location=TextLocation.difference(self,other)
        if location is None:
            return None
        if isinstance(location,tuple):
            return (
                UrlWithFileLocation(self.url,location[0]),
                UrlWithFileLocation(self.url,location[1]))
        return UrlWithFileLocation(self.url,location)
    def __sub__(self,
        other:'TextLocation'
        )->typing.Union[None,
            'UrlWithFileLocation',
            typing.Tuple['UrlWithFileLocation','UrlWithFileLocation']]:
        """
        Implement subtraction operator same as difference() function
        """
        return self.difference(other)

    def intersection(self,
        other:'TextLocation'
        )->typing.Optional['UrlWithFileLocation']:
        """
        Return a new location that is a combination of the parts of this location
        and of another location that overlap.

        returns None if there are no parts in common causing the
        location to completely disappear
        """
        if isinstance(other,UrlWithFileLocation) and other.url!=self.url:
            # raise ValueError('Cannot intersect line ranges across two different files')
            return None # probably ok to say that there is no intersection?
        location=TextLocation.intersection(self,other)
        if location is None:
            return None
        return UrlWithFileLocation(self.url,location)

    def read(self)->str:
        """
        read the data at the specified location
        """
        def v2a(n,default=0):
            if n is None:
                return default
            if n<1:
                return 0
            return n-1
        data=self.url.read()
        if self.fromLine is None:
            return data
        lines=data.replace('\r','').split('\n')
        lines=lines[v2a(self.fromLine):v2a(self.toLine,-1)]
        lines[0]=lines[0][v2a(self.fromColumn):]
        lines[-1]=lines[-1][0:v2a(self.toColumn,-1)]
        return '\n'.join(lines)
    @property
    def text(self)->str:
        """
        Text at this location
        """
        return self.read()

    def assign(self, # type: ignore # pylint: disable=arguments-renamed
        url:"UrlWithLocationCompatible"="",
        fromRow:typing.Union[None,int,
            'FileLocationCompatible',TextLocationSinglePoint,TextLocation]=None,
        fromColumn:typing.Optional[int]=None,
        toRow:typing.Union[None,int,TextLocationSinglePoint]=None,
        toColumn:typing.Optional[int]=None,
        relativeTo:typing.Optional[paths.URLCompatible]=None,
        maxParentLevels:typing.Optional[int]=None,
        maxChildLevels:typing.Optional[int]=None,
        location:typing.Union[None,'FileLocationCompatible','TextLocation']=None
        )->None:
        """
        assign the value of this file location

        If the given filename ends with : indices, then it attempts
        to extract file locations. eg.
            main.c:100
            main.c:100:4
            main.c:100,4
            main.c:100,4 101,10
            ... and similar

        :fromRow: can be used as location to make ordered-parameters easier
        :maxParentLevels: the maximum number of parent levels to allow
            in a relative path - for security, recommend setting this to 0
        :maxChildLevels: the maximum number of child levels to allow
            in a relative path
        :location: fill in any missing to/from row/column with this location
        """
        if isinstance(url,UrlWithFileLocation):
            if fromRow is None:
                fromRow=url.fromRow
            if fromColumn is None:
                fromColumn=url.fromColumn
            if toRow is None:
                toRow=url.toRow
            if toColumn is None:
                toColumn=url.toColumn
            url=url.url
        self.url=Url(url,relativeTo,maxParentLevels,maxChildLevels)
        fragments=self.url.fragments
        if fragments:
            rowfrag=Url.fragValueToRange(fragments.get('line',fragments.get('row','')))
            colfrag=Url.fragValueToRange(fragments.get('char',fragments.get('col','')))
            if fromRow is None and rowfrag[0]:
                fromRow=int(rowfrag[0])
            if fromColumn is None and colfrag[0]:
                fromColumn=int(colfrag[0])
            if toRow is None and len(rowfrag)>1 and rowfrag[1]:
                toRow=int(rowfrag[1])
            if toColumn is None and len(colfrag)>1 and colfrag[1]:
                toColumn=int(colfrag[1])
        TextLocation.assign(self,fromRow,fromColumn,toRow,toColumn,location)

    @property
    def fromRow(self)->int:
        """
        starting row of this file location
        """
        return Url.fragValueToRange(
            self.url.fragments.get('line',self.url.fragments.get('row','')))[0]
    @fromRow.setter
    def fromRow(self,fromRow:typing.Optional[int]=None):
        if fromRow is None:
            fromRow=0
        parts=list(self.url.fragments.get('line','0').split(','))
        parts[0]=str(fromRow)
        self.url.fragments['line']=','.join(parts)
    @property
    def toRow(self)->int:
        """
        ending row of this file location
        """
        return Url.fragValueToRange(
            self.url.fragments.get('line',self.url.fragments.get('row','')))[1]
    @toRow.setter
    def toRow(self,toRow:typing.Optional[int]=None):
        if toRow is None:
            toRow=0
        parts=list(self.url.fragments.get('line','0').split(','))
        if len(parts)>1:
            parts[1]=str(toRow)
        else:
            parts.append(str(toRow))
        self.url.fragments['line']=','.join(parts)

    @property
    def fromColumn(self)->int:
        """
        starting Column of this file location
        """
        return Url.fragValueToRange(
            self.url.fragments.get('char',self.url.fragments.get('col','')))[0]
    @fromColumn.setter
    def fromColumn(self,fromColumn:typing.Optional[int]=None):
        if fromColumn is None:
            fromColumn=0
        parts=list(self.url.fragments.get('char','0').split(','))
        parts[0]=str(fromColumn)
        self.url.fragments['char']=','.join(parts)
    @property
    def toColumn(self)->int:
        """
        ending Column of this file location
        """
        return Url.fragValueToRange(
            self.url.fragments.get('char',self.url.fragments.get('col','')))[1]
    @toColumn.setter
    def toColumn(self,toColumn:typing.Optional[int]=None):
        if toColumn is None:
            toColumn=0
        parts=list(self.url.fragments.get('char','0').split(','))
        if len(parts)>1:
            parts[1]=str(toColumn)
        else:
            parts.append(str(toColumn))
        self.url.fragments['char']=','.join(parts)

    @property
    def filename(self # type: ignore
        )->typing.Optional[str]:
        """
        returns the url as a filename
        """
        return self.url.filePath

    def html(self, # pylint: disable=invalid-overridden-method # type: ignore
        hrefFormat:str='',
        title:typing.Optional[str]=None
        )->str:
        """
        Get this as an html tag.

        hrefFormat is a string with replacements, see help for formatted()

        :property title: title of the thing to click on.
            If None, uses the filename as the title
        """
        if title is None:
            title=self.filename
        href=self.formatted(hrefFormat)
        urllib.parse.quote(href)
        return f'<a href="{href}">{title}</a>'

    def formatted(self,
        fmt,
        otherReplacements:typing.Optional[typing.Dict[str,typing.Any]]=None
        )->str:
        """
        fmt is a string with the optional replacement values
            {filename}
            {row}
            {col}
            {row?then this}
            {col?then this}
        otherReplacements more stuff to replace
            just like {filename}, etc(without brackets)
            These will be replaced first, and in order so you can do
            many interesting stunts.
        """
        # first do all of the simple replacements
        if otherReplacements is not None:
            for k,v in otherReplacements.items():
                fmt=fmt.replace('{%s}'%k,str(v))
        replacements={
            'filename':self.url.fullPath,
            'row':self.row,
            'col':self.col}
        for k,v in replacements.items():
            fmt=fmt.replace('{%s}'%k,str(v))
        # now solve all conditionals
        truths={}
        for k,v in replacements.items():
            if (isinstance(v,int) and v>1) or v:
                truths[k]=True
        conditionalResults:typing.List[str]=[]
        for section in fmt.split('{'):
            if not conditionalResults:
                # first is what it is
                conditionalResults.append(section)
            else:
                section=section.rsplit('}')
                cond=section[0].split('?',1)
                if cond[0] in truths:
                    conditionalResults.append(cond[1])
                if len(section)>1:
                    conditionalResults.append(section[-1])
        return ''.join(conditionalResults)

    def __repr__(self)->str:
        return self.formatted('{filename}{row?:{row}{col?:{col}}}')

FileLocationRange=UrlWithFileLocation
FileLocation=UrlWithFileLocation
UrlLocation=UrlWithFileLocation
UrlWithLocation=UrlWithFileLocation

UrlWithLocationCompatible=typing.Union[UrlWithFileLocation,paths.URLCompatible]
UrlLocationCompatible=UrlWithLocationCompatible
FileLocationCompatible=UrlLocationCompatible
def asUrlWithFileLocation(location:UrlLocationCompatible)->UrlWithFileLocation:
    """
    Always return a UrlWithFileLocation, either
    by creating one or by returning the
    value passed in
    """
    if isinstance(location,UrlWithFileLocation):
        return location
    return UrlWithFileLocation(location)
asFileLocation=asUrlWithFileLocation
asUrlWithLocation=asUrlWithFileLocation
asUrlLocation=asUrlWithFileLocation

def isFileLocationCompatible(something:typing.Any)->bool:
    """
    Check to see if something is compatible with FileLocation
    """
    if isinstance(something,UrlWithFileLocation):
        return True
    if isUrlCompatible(something):
        return True
    return False

class UrlWithFileLocations(UrlWithFileLocation):
    """
    A UrlWithFileLocation that occurs in more than one spot.

    For instance a "Find All" list

    NOTE: fromRow,fromCol - toRow,ToCol become the overall range
        that all contained locations exist within.
    """
    def __init__(self,url:paths.URLCompatible,
        fileLocations:typing.Iterable[TextLocation]):
        """ """
        UrlWithFileLocation.__init__(self,url)
        self.locations:typing.List[TextLocation]=list(fileLocations)

    @property
    def urlFileLocations(self
        )->typing.Generator[UrlWithFileLocation,None,None]:
        """
        similar to self.locations, but returns full,
        standalone FileLocation objects (with url)
        """
        for fl in self.locations:
            yield UrlWithFileLocation(self.url,
                fl.fromRow,fl.fromColumn,fl.toRow,fl.toColumn)

    @property
    def fromRow(self)->int:
        """
        the starting row/line in the file

        NOTE: there is no setter, because that doesn't make sense
        """
        r=0
        for loc in self.locations:
            if r is None or loc.fromRow<r:
                r=loc.fromRow
        return r
    @fromRow.setter
    def fromRow(self,fromRow:typing.Optional[int]=None):
        _=fromRow
        raise IndexError("Cannot manually set size of the file")
    row=fromRow # type: ignore
    line=fromRow # type: ignore
    fromLine=fromRow # type: ignore

    @property
    def toRow(self)->int:
        """
        ending row/line in the file

        NOTE: there is no setter, because that doesn't make sense
        """
        r=-1
        for loc in self.locations:
            if r is None or loc.toRow>r:
                r=loc.toRow
        return r
    @toRow.setter
    def toRow(self,toRow:typing.Optional[int]=None):
        _=toRow
        raise IndexError("Cannot manually set size of the file")
    toLine=toRow # type: ignore

    @property
    def fromColumn(self)->int:
        """
        starting column/character for the given row in the file

        NOTE: there is no setter, because that doesn't make sense
        """
        r=None
        c=0
        for loc in self.locations:
            if r is None or loc.fromRow<r:
                r=loc.fromRow
                c=loc.fromColumn
            elif r==loc.fromRow and loc.fromColumn<c:
                c=loc.fromColumn
        return c
    @fromColumn.setter
    def fromColumn(self,fromColumn:typing.Optional[int]=None):
        _=fromColumn
        raise IndexError("Cannot manually set size of the file")

    @property
    def toColumn(self)->int:
        """
        ending column/character for the given row in the file

        NOTE: there is no setter, because that doesn't make sense
        """
        r=None
        c=-1
        for loc in self.locations:
            if r is None or loc.toRow>r:
                r=loc.toRow
                c=loc.toColumn
            elif r==loc.toRow and loc.toColumn>c:
                c=loc.toColumn
        return c
    @toColumn.setter
    def toColumn(self,toColumn:typing.Optional[int]=None):
        _=toColumn
        raise IndexError("Cannot manually set size of the file")

    def __repr__(self)->str:
        r"""
        Get this location as a string.  Eg:
            /home/tjones/file.txt:3,5,7

        If there is no associated file/url then will simply say
            Line 3,5,7
        """
        ret:typing.List[str]=[]
        if self.url is None:
            if self.line is not None:
                ret.append('Line ')
        elif self.url.protocol=='file':
            fp=self.url.filePath
            if not fp:
                fp='[unknown]'
            ret.append(fp)
            ret.append(':')
        else:
            ret.append(str(self.url))
            ret.append(':')
        ret2=[]
        for loc in self.locations:
            ret2.append(str(loc))
        ret.append(','.join(ret2))
        return ''.join(ret)


class MessageLocation:
    """
    Common base class for a message that is tied to a particular
    location in a file.

    For instance, a spellchecker that higlights a specific word
    """
    def __init__(self,msg:str,location:typing.Optional[UrlWithFileLocation]):
        self.location=location
        self.msg=msg

    def __repr__(self):
        if self.location is None:
            return f'[[UNKNOWN]] {self.msg}'
        return f'[{self.location}] {self.msg}'


class FileLocationError(MessageLocation,Exception):
    """
    Common base class for any error that is tied to a location in a file
    (for instance, compiler errors)

    This is simply a MessageLocation object turned into an Exception
    """
    def __init__(self,msg:str,location:typing.Optional[UrlWithFileLocation]):
        MessageLocation.__init__(self,msg,location)
        Exception.__init__(self,str(self))
