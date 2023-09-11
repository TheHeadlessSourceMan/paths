"""
Indicates a file with location (or start/end location)

myfile.txt:1 # get line 1 from the file
myfile.txt:1:2 # get the entire line1 starting at character2 to the end of line
myfile.txt:1-2 # get lines 1 and 2
myfile.txt:1:2-2:3 # get an oddly specific range
"""
import typing
import re
import paths
import urllib.parse


class LocationWithinFile:
    """
    A location without a filename.

    Broken into its own object so multifile locations can have one
    url, but many locations
    """

    def __init__(self,
        fromRow:typing.Optional[int]=None,fromColumn:typing.Optional[int]=None,
        toRow:typing.Optional[int]=None,toColumn:typing.Optional[int]=None):
        self._fromLine:typing.Optional[int]=fromRow
        self._fromColumn:typing.Optional[int]=fromColumn
        self._toLine:typing.Optional[int]=toRow
        self._toColumn:typing.Optional[int]=toColumn

    def __eq__(self, __o: object)->bool:
        """
        Compare to another location
        """
        if isinstance(__o,LocationWithinFile):
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
            return self==FileLocation(__o)
        return False
    
    def openEditor(self,editor:typing.Optional[str]=None):
        """
        shortcut to call the openEditor tool
        """
        import openEditor
        openEditor.openEditor(editor=editor)

    def contains(self,other:'LocationWithinFile')->bool:
        """
        Does this entirely contain another location?
        """
        if other.fromLine<=self.toLine:
            if other.fromColumn<=self.toColumn:
                if other.toLine>=self.fromLine:
                    if other.toColumn>=self.toColumn:
                        return True
        return False

    def containedBy(self,other:'LocationWithinFile')->bool:
        """
        Is this entirely contained by another location?
        """
        return other.contains(self)

    def overlaps(self,other:'LocationWithinFile')->bool:
        """
        Does this contain or overlap another location?
        """
        # if either point in the other item is within the range of this item, return True
        if other.fromLine<=self.toLine and other.fromColumn<=self.toColumn and \
            other.fromLine>=self.fromLine and other.fromColumn>=self.fromColumn:
                return True
        if other.toLine<=self.toLine and other.toColumn<=self.toColumn and \
            other.toLine>=self.fromLine and other.toColumn>=self.fromColumn:
                return True
        # or if other completely contains this
        return other.contains(self)

    @property
    def fromLine(self):
        """
        same as fromRow
        """
        return self._fromLine
    @fromLine.setter
    def fromLine(self,fromLine:typing.Optional[int]):
        self._fromLine=fromLine
    @property
    def line(self):
        """
        same as fromRow
        """
        return self._fromLine
    @line.setter
    def line(self,fromLine:typing.Optional[int]):
        self._fromLine=fromLine
        
    @property
    def fromRow(self):
        """
        same as fromRow
        """
        return self._fromLine
    @fromRow.setter
    def fromRow(self,fromLine:typing.Optional[int]):
        self._fromLine=fromLine
    @property
    def row(self):
        """
        same as fromRow
        """
        return self._fromLine
    @row.setter
    def row(self,fromLine:typing.Optional[int]):
        self._fromLine=fromLine

    @property
    def toLine(self):
        """
        same as toRow
        """
        return self._toLine
    @toLine.setter
    def toLine(self,toLine:typing.Optional[int]):
        self._toLine=toLine
    @property
    def toRow(self):
        """
        same as toRow
        """
        return self.toLine
    @toRow.setter
    def toRow(self,toRow:typing.Optional[int]):
        self.toLine=toRow

    @property
    def fromColumn(self):
        """
        starting column/character for the given row in the file
        """
        return self._fromColumn
    @fromColumn.setter
    def fromColumn(self,fromColumn:typing.Optional[int]):
        if fromColumn is None:
            fromColumn=0
        self._fromColumn=fromColumn
    @property
    def col(self):
        """
        starting column/character for the given row in the file
        """
        return self.fromColumn
    @col.setter
    def col(self,fromColumn:typing.Optional[int]):
        self.fromColumn=fromColumn

    @property
    def toColumn(self):
        """
        ending column/character for the given row in the file
        """
        return self._toColumn
    @toColumn.setter
    def toColumn(self,toColumn:typing.Optional[int]):
        if toColumn is None:
            toColumn=-1
        self._toColumn=toColumn

    def __repr__(self)->str:
        """
        string representation of this object
        """
        ret=[]
        if self.line is not None:
            ret.append('%d'%self.line)
            if self.fromColumn is not None:
                ret.append(':%d'%self.fromColumn)
            if self.toLine is not None:
                ret.append('-%d'%self.toLine)
                if self.toColumn is not None:
                    ret.append(':%d'%self.toColumn)
        return ''.join(ret)


class FileLocation(LocationWithinFile):
    """
    Indicates a file with location (or start/end location)

    myfile.txt:1 # get line 1 from the file
    myfile.txt:1:2 # get the entire line1 starting at character2 to the end of line
    myfile.txt:1-2 # get lines 1 and 2
    myfile.txt:1:2-2:3 # get an oddly specific range

    TODO:
    * could we also do
        myfile.txt:1,3,5 to pick out specific lines?
    * how does this work with proper urls?
    * should slicing [] notation also be a valid url notation?
        myfile.txt[1:-1]
    """

    FILE_LOCATION_REGEX=re.compile(r"""(?P<filename>(.*[/\\])?[^:(]*)([:(](?P<row>\d*)(\s*[:,]\s*(?P<col>\d*))?\)?)""")

    def __init__(self,
        url:paths.URLCompatible,
        fromRow:typing.Optional[int]=None,
        fromColumn:typing.Optional[int]=None,
        toLine:typing.Optional[int]=None,
        toColumn:typing.Optional[int]=None,
        smartDecodeUrl=True):
        """ """
        LocationWithinFile.__init__(self,fromRow,fromColumn,toLine,toColumn)
        self.smartDecodeUrl=smartDecodeUrl
        self._url:paths.URLCompatible=url
        if isinstance(url,str):
            self.assign(url,fromRow,fromColumn)
        
    def __eq__(self, __o: object)->bool:
        """
        Compare to a filename, location, or url
        """
        if isinstance(__o,FileLocation):
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
            return self==FileLocation(__o)
        elif isinstance(__o,paths.URL) or hasattr(__o,'url') or hasattr(__o,'filename'):
            return self.url==paths.asURL(typing.cast(paths.URLCompatible,__o))
        return False

    def contains(self,other:LocationWithinFile)->bool:
        """
        Does this entirely contain another location?
        """
        if isinstance(other,FileLocation) and other.url!=self.url:
            return False
        return LocationWithinFile.contains(self,other)

    def overlaps(self,other:LocationWithinFile)->bool:
        """
        Does this contain or overlap another location?
        """
        if isinstance(other,FileLocation) and other.url!=self.url:
            return False
        return LocationWithinFile.overlaps(self,other)

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
        lines=lines[v2a(self.fromLine):v2a(self.toLine,None)]
        lines[0]=lines[0][v2a(self.fromColumn):]
        lines[-1]=lines[-1][0:v2a(self.toColumn,None)]
        return '\n'.join(lines)

    def assign(self,fileLocation:str,row:typing.Optional[int]=0,col:typing.Optional[int]=0)->None:
        """
        assign the value of this file location
        """
        fileLocationParts=fileLocation.replace('\\','/').split('/')
        fileRowCol=fileLocationParts[-1].split(':')
        if row is None:
            row=0
        if len(fileRowCol)>1:
            if row==0:
                row=int(fileRowCol[1])
            if len(fileRowCol)>2 and col==0:
                col=int(fileRowCol[2])
            fileLocationParts[-1]=fileRowCol[0]
            fileLocation='/'.join(fileLocationParts)
        self._url=fileLocation
        self.row=row
        self.fromColumn=col

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
    def filename(self)->typing.Optional[str]:
        return self.url.filePath
    
    def html(self,hrefFormat,title=None):
        """
        Get this as an html tag.
        
        hrefFormat is a string with replacements, see help for the formatted() function
        
        :property title: title of the thing to click on.  If None, uses the filename as the title
        """
        if title is None:
            title=self.filename
        href=self.formatted(hrefFormat)
        urllib.parse.quote(href)
        return f'<a href="{href}">{title}</a>'
 
    def formatted(self,fmt,otherReplacements:typing.Optional[typing.Dict[str,typing.Any]]=None):
        """
        fmt is a string with the optional replacement values
            {filename}
            {row}
            {col}
            {row?then this}
            {col?then this}
        otherReplacements more stuff to replace just like {filename}, etc (without brackets)
            These will be replaced first, and in order so you can do many interesting stunts.
        """
        # first do all of the simple replacements
        if otherReplacements is not None:
            for k,v in otherReplacements.items():
                fmt=fmt.replace('{%s}'%k,str(v))
        replacements={'filename':self.filename,'row':self.row,'col':self.col}
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
    
    def __old_repr__(self)->str:
        r"""
        Get this location as a string.  Eg:
            /home/tjones/file.txt:3

        If there is no associated file/url then will simply say
            Line 3
        """
        ret:typing.List[str]=[]
        try:
            url=self.url
            if url is None:
                if self.line is not None:
                    ret.append('Line ')
                elif url.protocol=='file' and url.filePath is not None:
                    ret.append(url.filePath)
                    ret.append(':')
                else:
                    ret.append(str(url))
                    ret.append(':')
        except paths.MalformedURL:
            # if there's an error, print what we've got so we can at least debug stuff
            ret.append(str(self._url))
            ret.append(':')
        ret.append(LocationWithinFile.__repr__(self))
        return ''.join(ret)
FileLocationRange=FileLocation

FileLocationCompatible=typing.Union[FileLocation,paths.URLCompatible]
def asFileLocation(location:FileLocationCompatible)->FileLocation:
    if isinstance(location,FileLocation):
        return location
    return FileLocation(location)

class MultiFileLocation(FileLocation):
    """
    A FileLocation that occours in more than one spot.

    For instance a "Find All" list

    NOTE: fromRow,fromCol - toRow,ToCol become the overall range
        that all contained locations exist within.
    """
    def __init__(self,url:paths.URLCompatible,
        fileLocations:typing.Iterable[LocationWithinFile],
        smartDecodeUrl:bool=True):
        """ """
        FileLocation.__init__(self,url,smartDecodeUrl=smartDecodeUrl)
        self.locations:typing.List[LocationWithinFile]=list(fileLocations)

    @property
    def fileLocations(self)->typing.Generator[FileLocation,None,None]:
        """
        similar to self.locations, but returns full, standalone FileLocation objects (with url)
        """
        for fl in self.locations:
            yield FileLocation(self.url,
                fl.fromRow,fl.fromColumn,
                fl.toRow,fl.toColumn,
                self.smartDecodeUrl)

    @property # type: ignore
    def fromRow(self)->typing.Optional[int]:
        """
        the starting row/line in the file

        NOTE: there is no setter, because that doesn't make sense
        """
        r=None
        for loc in self.locations:
            if r is None or loc.fromRow<r:
                r=loc.fromRow
        return r
    row=fromRow
    line=fromRow
    fromLine=fromRow

    @property # type: ignore
    def toRow(self)->typing.Optional[int]:
        """
        ending row/line in the file

        NOTE: there is no setter, because that doesn't make sense
        """
        r=None
        for loc in self.locations:
            if r is None or loc.toRow>r:
                r=loc.toRow
        return r
    toLine=toRow

    @property # type: ignore
    def fromColumn(self)->typing.Optional[int]:
        """
        starting column/character for the given row in the file

        NOTE: there is no setter, because that doesn't make sense
        """
        r=None
        c=None
        for loc in self.locations:
            if r is None or loc.fromRow<r:
                r=loc.fromRow
                c=loc.fromColumn
            elif r==loc.fromRow and loc.fromColumn<c:
                c=loc.fromColumn
        return c

    @property # type: ignore
    def toColumn(self)->typing.Optional[int]:
        """
        ending column/character for the given row in the file

        NOTE: there is no setter, because that doesn't make sense
        """
        r=None
        c=None
        for loc in self.locations:
            if r is None or loc.toRow>r:
                r=loc.toRow
                c=loc.toColumn
            elif r==loc.toRow and loc.toColumn>c:
                c=loc.toColumn
        return c

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
    location in a file.  (For instance, a spellchecker that higlights a specific word)
    """
    def __init__(self,msg:str,location:FileLocation):
        self.location:FileLocation=location
        self.msg:str=msg

    def __repr__(self):
        return f'[{self.location}] {self.msg}'


class FileLocationError(MessageLocation,Exception):
    """
    Common base class for any error that is tied to a location in a file
    (for instance, compiler errors)

    This is simply a MessageLocation object turned into an Exception
    """
    def __init__(self,msg:str,location:FileLocation):
        MessageLocation.__init__(self,msg,location)
        Exception.__init__(self,str(self))