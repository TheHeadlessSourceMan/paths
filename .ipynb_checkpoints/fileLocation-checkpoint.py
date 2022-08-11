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

    @property
    def fromLine(self):
        """
        same as fromRow
        """
        return self._fromLine
    @fromLine.setter
    def fromLine(self,fromLine:typing.Optional[int]):
        self._fromLine=fromLine
    fromRow=fromLine
    _fromRow=fromLine
    line=fromLine
    row=fromLine

    @property
    def toLine(self):
        """
        same as toRow
        """
        return self._toLine
    @toLine.setter
    def toLine(self,toLine:typing.Optional[int]):
        self._toLine=toLine
    toRow=toLine
    _toRow=toLine

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
    col=fromColumn

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

    FILE_LOCATION_REGEX=re.compile(r"""(?P<filename>(.*[/\\])?[^:(]*)([:(](?P<row>[0-9])(\s*[:,]\s*(?P<col>[0-9]*))?[)]?)""")

    def __init__(self,url:paths.URLCompatible,
        fromRow:typing.Optional[int]=None,
        fromColumn:typing.Optional[int]=None,
        toLine:typing.Optional[int]=None,
        toColumn:typing.Optional[int]=None,
        smartDecodeUrl=True):
        """ """
        LocationWithinFile.__init__(self,fromRow,fromColumn,toLine,toColumn)
        self.smartDecodeUrl=smartDecodeUrl
        self._url:paths.URLCompatible=url;

    def read(self)->str:
        """
        read the data at the specified location
        """
        data=self.url.read()
        if self.fromLine is None:
            return data
        lines=data.replace('\r','').split('\n')
        lines=lines[self.fromLine:self.toLine]
        lines[0]=lines[0][self.fromColumn:]
        lines[-1]=lines[-1][0:self.toColumn]
        return '\n'.join(lines)

    def assign(self,fileLocation:str,row:int=0,col:int=0)->None:
        """
        assign the value of this file location
        """
        m=self.FILE_LOCATION_REGEX.match(fileLocation)
        if m is not None:
            if m.group('row') is not None:
                row=m.group('row')
            if m.group('col') is not None:
                col=m.group('col')
        self.filename=fileLocation
        self._row=int(row)
        self._col=int(col)

    @property
    def url(self)->paths.URL:
        """
        The file to whom we are referring
        """
        return paths.asURL(self._url)
    @url.setter
    def url(self,url:paths.URLCompatible):
        self._url=url

    @property
    def filename(self)->str:
        return self.url.filePath
 
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
            if isinstance(v,int) and v>1:
                truths[k]=True
            elif v:
                truths[k]=True
        conditionalResults=[]
        for section in fmt.split('}'):
            section=section.rsplit('{',1)
            conditionalResults.append(section[0])
            if len(section)>1:
                cond=section[1].split('?',1)
                if cond[0] in truths:
                    conditionalResults.append(cond[1])
        return ''.join(conditionalResults)
        
    def __new_repr__(self)->str:
        return self.formatted('{filename}{row?:{row}{col?:{col}}}')
    
    def __repr__(self)->str:
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
            ret.append(self._url)
            ret.append(':')
        ret.append(LocationWithinFile.__repr__(self))
        return ''.join(ret)
FileLocationRange=FileLocation


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

    @property
    def fromRow(self):
        """
        the starting row/line in the file
        """
        r=None
        for loc in self.locations:
            if r is None or loc.fromRow<r:
                r=loc.fromRow
        return r
    row=fromRow
    line=fromRow
    fromLine=fromRow

    @property
    def toRow(self):
        """
        ending row/line in the file
        """
        r=None
        for loc in self.locations:
            if r is None or loc.toRow>r:
                r=loc.toRow
        return r
    toLine=toRow

    @property
    def fromColumn(self):
        """
        starting column/character for the given row in the file
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

    @property
    def toColumn(self):
        """
        ending column/character for the given row in the file
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
            ret.append(self.url.filePath)
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