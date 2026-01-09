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
from urlTyping import isUrlCompatible


class FileLocationSinglePoint:
    """
    A single index point within a file.

    Basically just a row and column, but this
    makes them easily comparable.
    """

    def __init__(self,row:int,column:int):
        self.row=row
        self.column=column

    def copy(self)->'FileLocationSinglePoint':
        """
        Create a copy of this point
        """
        return FileLocationSinglePoint(self.row,self.column)

    def max(self,
        other:typing.Union[
            'FileLocationSinglePoint',
            typing.Iterable['FileLocationSinglePoint']]
        )->'FileLocationSinglePoint':
        """
        Returns the maximum of this and one or more other points
        """
        if hasattr(other,'__iter__'):
            mmax=self
            for item in other: # type: ignore
                if item>mmax:
                    mmax=item
            return mmax
        if other>self: # type: ignore
            return other # type: ignore
        return self

    def min(self,
        other:typing.Union[
            'FileLocationSinglePoint',
            typing.Iterable['FileLocationSinglePoint']]
        )->'FileLocationSinglePoint':
        """
        Returns the maximminimum of this and one or more other points
        """
        if hasattr(other,'__iter__'):
            mmax=self
            for item in other: # type: ignore
                if item<mmax:
                    mmax=item
            return mmax
        if other<self: # type: ignore
            return other # type: ignore
        return self

    def __cmp__(self,other:'FileLocationSinglePoint')->int:
        """
        Like the old __cmp__ dunder, but
        respects array-style negative numbers
        Returns
            -1: a<b
             0: a=b
             1: a>b

        NOTE: Since this has no knowledge of the length of the
        thing being indexed, handling negatives is a little tricky.
        Therefore, negatives are always preferred.  That is, 999999<-2
        will always return True, even if the document is 1 byte long.
        """
        def _cmpVal(a:int,b:int)->int:
            if a<0:
                if b<0:
                    if a>b:
                        return -1
                    return a<b
                return a
            if b<0:
                return b
            if a<b:
                return -1
            return a>b
        rowCmp=_cmpVal(self.row,other.row)
        if rowCmp==0:
            return _cmpVal(self.column,other.column)
        return rowCmp

    def __lt__(self,other:'FileLocationSinglePoint')->bool:
        return self.__cmp__(other)<0

    def __le__(self,other:'FileLocationSinglePoint')->bool:
        return self.__cmp__(other)<=0

    def __gt__(self,other:'FileLocationSinglePoint')->bool:
        return self.__cmp__(other)>0

    def __ge__(self,other:'FileLocationSinglePoint')->bool:
        return self.__cmp__(other)>=0

    def __eq__(self, # type: ignore
        other:'FileLocationSinglePoint')->bool:
        return self.__cmp__(other)==0


class LocationWithinFile:
    """
    A location without a filename.

    Broken into its own object so multifile locations can have one
    url, but many locations
    """

    @typing.overload
    def __init__(self,
        fromRow:FileLocationSinglePoint,
        fromColumn:None=None,
        toRow:typing.Optional[FileLocationSinglePoint]=None,
        toColumn:None=None,
        location:None=None):
        """
        :fromRow: can be used as location to make ordered-parameters easier
        :location: fill in any missing to/from row/column with this location
        """

    @typing.overload
    def __init__(self,
        fromRow:typing.Optional[int]=None,
        fromColumn:typing.Optional[int]=None,
        toRow:typing.Optional[int]=None,
        toColumn:typing.Optional[int]=None,
        location:typing.Optional['FileLocationCompatible']=None):
        """
        :fromRow: can be used as location to make ordered-parameters easier
        :location: fill in any missing to/from row/column with this location
        """

    @typing.overload
    def __init__(self,
        fromRow:'FileLocationCompatible'):
        """
        :fromRow: can be used as location to make ordered-parameters easier
        """

    def __init__(self,
        fromRow:typing.Union[None,int,'FileLocationCompatible',FileLocationSinglePoint]=None,
        fromColumn:typing.Optional[int]=None,
        toRow:typing.Union[None,int,FileLocationSinglePoint]=None,
        toColumn:typing.Optional[int]=None,
        location:typing.Optional['FileLocationCompatible']=None):
        """
        :fromRow: can be used as location to make ordered-parameters easier
        :location: fill in any missing to/from row/column with this location
        """
        self.fromPoint=FileLocationSinglePoint(0,0)
        self.toPoint=FileLocationSinglePoint(-1,-1)
        self.assign(fromRow,fromColumn,toRow,toColumn,location)

    def assign(self,
        fromRow:typing.Union[None,int,
            'FileLocationCompatible',FileLocationSinglePoint,'LocationWithinFile']=None,
        fromColumn:typing.Optional[int]=None,
        toRow:typing.Union[None,int,FileLocationSinglePoint]=None,
        toColumn:typing.Optional[int]=None,
        location:typing.Union[None,'FileLocationCompatible','LocationWithinFile']=None)->None:
        """
        :fromRow: can be used as location to make ordered-parameters easier
        :location: fill in any missing to/from row/column with this location
        """
        if not fromRow is None:
            if isinstance(fromRow,FileLocationSinglePoint):
                self.fromPoint=fromRow.copy()
                fromRow=None
            elif not isinstance(fromRow,int):
                location=fromRow
                fromRow=None
        if not toRow is None:
            if isinstance(toRow,FileLocationSinglePoint):
                self.toPoint=toRow.copy()
                toRow=None
        if location is not None:
            if not isinstance(location,LocationWithinFile):
                location=asFileLocation(location)
            if fromRow is None:
                fromRow=location.fromRow
            if fromColumn is None:
                fromColumn=location.fromColumn
            if toRow is None:
                toRow=location.toRow
            if toColumn is None:
                toColumn=location.toColumn
        if fromRow is not None:
            self.fromPoint.row=fromRow
        if fromColumn is not None:
            self.fromPoint.column=fromColumn
        if toRow is not None:
            self.toPoint.row=toRow
        if toColumn is not None:
            self.toPoint.column=toColumn

    def copy(self)->"LocationWithinFile":
        """
        Create a copy of this location within file
        """
        return LocationWithinFile(
            self.fromPoint.row,self.fromPoint.column,self.toPoint.row,self.toPoint.column)

    def __eq__(self,__o: object)->bool:
        """
        Compare to another location
        """
        if isinstance(__o,LocationWithinFile):
            return self.fromPoint==__o.fromPoint and self.toPoint==__o.toPoint
        elif hasattr(__o,'location'):
            return self==getattr(__o,'location')
        elif isinstance(__o,str):
            return self==UrlWithFileLocation(__o)
        return False

    def openEditor(self,editor:typing.Optional[str]=None):
        """
        shortcut to call the openEditor tool
        """
        import openEditor
        openEditor.openEditor(self,editor=editor) # type: ignore

    def contains(self,other:'LocationWithinFile')->bool:
        """
        Does this entirely contain another location?
        """
        return other.fromPoint<=self.fromPoint and other.toPoint>=self.toPoint

    def containedBy(self,other:'LocationWithinFile')->bool:
        """
        Is this entirely contained by another location?
        """
        return other.contains(self)

    def overlaps(self,other:'LocationWithinFile')->bool:
        """
        Does this contain or overlap another location?
        """
        # if either point in the other item is within
        # the range of this item, return True
        if other.fromPoint<=self.toPoint\
            and other.fromPoint>=self.fromPoint:
            return True
        if other.toPoint<=self.toPoint\
            and other.toPoint>=self.fromPoint:
            return True
        # or if other completely contains this
        return other.contains(self)

    def union(self,
        other:'LocationWithinFile',fillGaps:bool=True
        )->'LocationWithinFile':
        """
        Return a new location that is a combination of this location
        and another location.

        :fillGaps: if it is file.txt:100-110 and file.txt:200-210, should
            we return file.txt:100-210, or raise a ValueError exception?
        """
        if not fillGaps and not self.overlaps(other):
            raise ValueError(f'Regions {self} and {other} are discontigious')
        fromPoint=self.fromPoint.min(other.fromPoint)
        toPoint=self.fromPoint.max(other.toPoint)
        return LocationWithinFile(fromPoint,None,toPoint)

    def difference(self,
        other:'LocationWithinFile'
        )->typing.Union[None,
            'LocationWithinFile',
            typing.Tuple['LocationWithinFile','LocationWithinFile']]:
        """
        Return a new location that is a this location
        with another location removed from it.

        returns None if this causes the location to completely disappear
        NOTE: this could result in this being split into two, eg. 
            file.txt:100..400 - file.txt:200..300 = (file.txt:100..200, file.txt:300-400)
        """
        if not self.overlaps(other):
            # nothing will be removed
            return self.copy()
        if other.contains(self):
            # the entire thing will be removed
            return None
        if self.fromPoint<other.fromPoint:
            if self.toPoint>other.toPoint:
                # this splits us in half!
                return (
                    LocationWithinFile(self.fromPoint,None,other.fromPoint),
                    LocationWithinFile(other.toPoint,None,self.toPoint))
            fromPoint=other.fromPoint
            toPoint=self.toPoint
        else:
            fromPoint=self.fromPoint
            toPoint=other.toPoint
        return LocationWithinFile(fromPoint,None,toPoint)

    def intersection(self,
        other:'LocationWithinFile'
        )->typing.Optional['LocationWithinFile']:
        """
        Return a new location that is a combination of the parts of this location
        and of another location that overlap.

        returns None if there are no parts in common causing the
        location to completely disappear
        """
        if not self.overlaps(other):
            # they do not overlap, so intersection is empty
            return None
        fromPoint=self.fromPoint.max(other.fromPoint)
        toPoint=self.toPoint.min(other.toPoint)
        return LocationWithinFile(fromPoint,None,toPoint)

    @property
    def fromRow(self)->int:
        """
        same as fromRow
        """
        return self._fromRow
    @fromRow.setter
    def fromRow(self,fromRow:typing.Optional[int]=None):
        self._fromRow=0 if fromRow is None else fromRow
    @property
    def fromLine(self)->int:
        """
        same as fromRow
        """
        return self._fromRow
    @fromLine.setter
    def fromLine(self,fromLine:typing.Optional[int]=None):
        self._fromRow=0 if fromLine is None else fromLine
    @property
    def line(self)->int:
        """
        same as fromRow
        """
        return self._fromRow
    @line.setter
    def line(self,fromLine:typing.Optional[int]=None):
        self._fromRow=0 if fromLine is None else fromLine
    @property
    def row(self)->int:
        """
        same as fromRow
        """
        return self._fromRow
    @row.setter
    def row(self,row:typing.Optional[int]=None):
        self._fromRow=0 if row is None else row

    @property
    def toRow(self)->int:
        """
        same as toRow
        """
        return self._toRow
    @toRow.setter
    def toRow(self,toRow:typing.Optional[int]=None):
        self._toRow=-1 if toRow is None else toRow
    @property
    def toLine(self)->int:
        """
        same as toRow
        """
        return self._toRow
    @toLine.setter
    def toLine(self,toLine:typing.Optional[int]=None):
        self._toRow=-1 if toLine is None else toLine

    @property
    def numRows(self)->int:
        """
        numnber of rows
        """
        return self._toRow-self._fromRow+1
    @numRows.setter
    def numRows(self,numRows:typing.Optional[int]=None):
        if numRows is None or numRows<=0:
            numRows=1
        self.toRow=self._fromRow+numRows-1
    @property
    def numLines(self)->int:
        """
        same as numRows
        """
        return self.numRows
    @numLines.setter
    def numLines(self,numLines:typing.Optional[int]):
        self.numRows=numLines

    @property
    def fromColumn(self)->int:
        """
        starting column/character for the given row in the file
        """
        return self._fromColumn
    @fromColumn.setter
    def fromColumn(self,fromColumn:typing.Optional[int]=None):
        self._fromColumn=0 if fromColumn is None else fromColumn
    @property
    def fromCol(self)->int:
        """
        starting column/character for the given row in the file
        """
        return self._fromColumn
    @fromCol.setter
    def fromCol(self,fromCol:typing.Optional[int]=None):
        self._fromColumn=0 if fromCol is None else fromCol
    @property
    def col(self)->int:
        """
        starting column/character for the given row in the file
        """
        return self._fromColumn
    @col.setter
    def col(self,fromColumn:typing.Optional[int]=None):
        self._fromColumn=0 if fromColumn is None else fromColumn
    @property
    def column(self)->int:
        """
        starting column/character for the given row in the file
        """
        return self._fromColumn
    @column.setter
    def column(self,column:typing.Optional[int]=None):
        self._fromColumn=0 if column is None else column

    @property
    def toColumn(self)->int:
        """
        ending column/character for the given row in the file
        """
        return self._toColumn
    @toColumn.setter
    def toColumn(self,toColumn:typing.Optional[int]=None):
        self._toColumn=0 if toColumn is None else toColumn
    @property
    def toCol(self)->int:
        """
        ending column/character for the given row in the file
        """
        return self._toColumn
    @toCol.setter
    def toCol(self,toCol:typing.Optional[int]=None):
        self._toColumn=0 if toCol is None else toCol

    def __repr__(self)->str:
        """
        string representation of this object
        """
        ret=[]
        if self.line is not None:
            ret.append('%d'%self.line)
            if self._fromColumn!=-1:
                ret.append(':%d'%self._fromColumn)
            if self._toRow!=-1:
                ret.append('-%d'%self._toRow)
                if self._toColumn!=-1:
                    ret.append(':%d'%self._toColumn)
        return ''.join(ret)


class UrlWithFileLocation(LocationWithinFile,Url):
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

    FILE_LOCATION_REGEX=re.compile(
        r"""(?P<filename>(.*[/\\])?[^:(]*)([:(](?P<row>\d*)(\s*[:,]\s*(?P<col>\d*))?\)?)""") # noqa: E501 # pylint: disable=line-too-long

    def __new__(cls,
        url:paths.URLCompatible,
        fromRow:typing.Union[None,int,
            'FileLocationCompatible',FileLocationSinglePoint,LocationWithinFile]=None,
        fromColumn:typing.Optional[int]=None,
        toRow:typing.Union[None,int,FileLocationSinglePoint]=None,
        toColumn:typing.Optional[int]=None,
        smartDecodeUrl:bool=True,
        relativeTo:typing.Optional[paths.URLCompatible]=None,
        maxParentLevels:typing.Optional[int]=None,
        maxChildLevels:typing.Optional[int]=None,
        location:typing.Union[None,'FileLocationCompatible','LocationWithinFile']=None):
        """
        :fromRow: can be used as location to make ordered-parameters easier
        :maxParentLevels: the maximum number of parent levels to allow
            in a relative path - for security, recommend setting this to 0
        :maxChildLevels: the maximum number of child levels to allow
            in a relative path
        :location: fill in any missing to/from row/column with this location
        """
        return super(UrlWithFileLocation,cls).__new__(cls) # pylint: disable=no-value-for-parameter # type: ignore

    def __init__(self,
        url:paths.URLCompatible,
        fromRow:typing.Union[None,int,
            'FileLocationCompatible',FileLocationSinglePoint,LocationWithinFile]=None,
        fromColumn:typing.Optional[int]=None,
        toRow:typing.Union[None,int,FileLocationSinglePoint]=None,
        toColumn:typing.Optional[int]=None,
        smartDecodeUrl:bool=True,
        relativeTo:typing.Optional[paths.URLCompatible]=None,
        maxParentLevels:typing.Optional[int]=None,
        maxChildLevels:typing.Optional[int]=None,
        location:typing.Union[None,'FileLocationCompatible','LocationWithinFile']=None):
        """
        :fromRow: can be used as location to make ordered-parameters easier
        :maxParentLevels: the maximum number of parent levels to allow
            in a relative path - for security, recommend setting this to 0
        :maxChildLevels: the maximum number of child levels to allow
            in a relative path
        :location: fill in any missing to/from row/column with this location
        """
        self.smartDecodeUrl:bool=smartDecodeUrl
        Url.__init__(self,'')
        LocationWithinFile.__init__(self)
        self.assign(url,
            fromRow,fromColumn,toRow,toColumn,
            smartDecodeUrl,relativeTo,maxParentLevels,maxChildLevels,location)

    def copy(self)->"UrlWithFileLocation":
        """
        Copy this url with location
        """
        return UrlWithFileLocation(self.url,
            self.fromRow,self.fromColumn,self.toRow,self.toColumn,
            self.smartDecodeUrl)

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

    def contains(self,other:LocationWithinFile)->bool: # type: ignore
        """
        Does this entirely contain another location?
        """
        if isinstance(other,UrlWithFileLocation) and other.url!=self.url:
            return False
        return LocationWithinFile.contains(self,other)

    def overlaps(self,other:LocationWithinFile)->bool:
        """
        Does this contain or overlap another location?
        """
        if isinstance(other,UrlWithFileLocation) and other.url!=self.url:
            return False
        return LocationWithinFile.overlaps(self,other)

    def union(self,
        other:'LocationWithinFile',fillGaps:bool=True
        )->'UrlWithFileLocation':
        """
        Return a new location that is a combination of this location
        and another location.

        :fillGaps: if it is file.txt:100-110 and file.txt:200-210, should
            we return file.txt:100-210, or raise a ValueError exception?
        """
        if isinstance(other,UrlWithFileLocation) and other.url!=self.url:
            raise ValueError('Cannot combine line ranges across two different files')
        location=LocationWithinFile.union(self,other)
        return UrlWithFileLocation(self.url,location)
    def __add__(self, # type: ignore
        other:'LocationWithinFile'
        )->typing.Optional['FileLocation']:
        """
        Implement addition operator same as union() function
        """
        return self.union(other)

    def difference(self,
        other:'LocationWithinFile'
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
        location=LocationWithinFile.difference(self,other)
        if location is None:
            return None
        if isinstance(location,tuple):
            return (
                UrlWithFileLocation(self.url,location[0]),
                UrlWithFileLocation(self.url,location[1]))
        return UrlWithFileLocation(self.url,location)
    def __sub__(self,
        other:'LocationWithinFile'
        )->typing.Union[None,
            'UrlWithFileLocation',
            typing.Tuple['UrlWithFileLocation','UrlWithFileLocation']]:
        """
        Implement subtraction operator same as difference() function
        """
        return self.difference(other)

    def intersection(self,
        other:'LocationWithinFile'
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
        location=LocationWithinFile.intersection(self,other)
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

    def assign(self, # type: ignore # pylint: disable=arguments-renamed
        url:paths.URLCompatible,
        fromRow:typing.Union[None,int,
            'FileLocationCompatible',FileLocationSinglePoint,LocationWithinFile]=None,
        fromColumn:typing.Optional[int]=None,
        toRow:typing.Union[None,int,FileLocationSinglePoint]=None,
        toColumn:typing.Optional[int]=None,
        smartDecodeUrl=True,
        relativeTo:typing.Optional[paths.URLCompatible]=None,
        maxParentLevels:typing.Optional[int]=None,
        maxChildLevels:typing.Optional[int]=None,
        location:typing.Union[None,'FileLocationCompatible','LocationWithinFile']=None
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
        self.smartDecodeUrl=smartDecodeUrl
        Url.assign(self,url,relativeTo,maxParentLevels,maxChildLevels)
        LocationWithinFile.assign(self,fromRow,fromColumn,toRow,toColumn,location)

    @property
    def fromRow(self)->int:
        """
        starting row of this file location
        """
        parts=self.fragments.get('line','0').split(',')
        return int(parts[0])
    @fromRow.setter
    def fromRow(self,fromRow:typing.Optional[int]=None):
        if fromRow is None:
            fromRow=0
        parts=list(self.fragments.get('line','0').split(','))
        parts[0]=str(fromRow)
        self.fragments['line']=','.join(parts)
    @property
    def toRow(self)->int:
        """
        ending row of this file location
        """
        parts=self.fragments.get('line','0').split(',')
        return int(parts[-1])
    @toRow.setter
    def toRow(self,toRow:typing.Optional[int]=None):
        if toRow is None:
            toRow=0
        parts=list(self.fragments.get('line','0').split(','))
        if len(parts)>1:
            parts[1]=str(toRow)
        else:
            parts.append(str(toRow))
        self.fragments['line']=','.join(parts)

    @property
    def fromColumn(self)->int:
        """
        starting Column of this file location
        """
        parts=self.fragments.get('char','0').split(',')
        return int(parts[0])
    @fromColumn.setter
    def fromColumn(self,fromColumn:typing.Optional[int]=None):
        if fromColumn is None:
            fromColumn=0
        parts=list(self.fragments.get('char','0').split(','))
        parts[0]=str(fromColumn)
        self.fragments['char']=','.join(parts)
    @property
    def toColumn(self)->int:
        """
        ending Column of this file location
        """
        parts=self.fragments.get('char','0').split(',')
        return int(parts[-1])
    @toColumn.setter
    def toColumn(self,toColumn:typing.Optional[int]=None):
        if toColumn is None:
            toColumn=0
        parts=list(self.fragments.get('char','0').split(','))
        if len(parts)>1:
            parts[1]=str(toColumn)
        else:
            parts.append(str(toColumn))
        self.fragments['char']=','.join(parts)

    @property
    def url(self)->paths.URL:
        """
        The file to whom we are referring
        """
        return typing.cast(paths.URL,paths.asURL(self._url))
    @url.setter
    def url(self,url:paths.URLCompatible):
        self._url=url

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
            'filename':self.fullPath,
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

UrlLocationCompatible=typing.Union[UrlWithFileLocation,paths.URLCompatible]
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
        fileLocations:typing.Iterable[LocationWithinFile],
        smartDecodeUrl:bool=True):
        """ """
        UrlWithFileLocation.__init__(self,url,smartDecodeUrl=smartDecodeUrl)
        self.locations:typing.List[LocationWithinFile]=list(fileLocations)

    @property
    def urlFileLocations(self
        )->typing.Generator[UrlWithFileLocation,None,None]:
        """
        similar to self.locations, but returns full,
        standalone FileLocation objects (with url)
        """
        for fl in self.locations:
            yield UrlWithFileLocation(self.url,
                fl.fromRow,fl.fromColumn,fl.toRow,fl.toColumn,self.smartDecodeUrl)

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
