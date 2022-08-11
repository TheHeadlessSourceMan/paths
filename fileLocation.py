"""
A location without a filename.

Broken into its own object so multifile locations can have one
url, but many locations
"""
import typing
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
    def line(self):
        """
        same as row
        """
        return self.fromRow
    @line.setter
    def line(self,line:typing.Optional[int]):
        self.fromRow=line

    @property
    def fromLine(self):
        """
        same as fromRow
        """
        return self.fromRow
    @fromLine.setter
    def fromLine(self,fromLine:typing.Optional[int]):
        self.fromRow=fromLine

    @property
    def toLine(self):
        """
        same as toRow
        """
        return self.toRow
    @toLine.setter
    def toLine(self,toLine:typing.Optional[int]):
        self.toRow=toLine

    @property
    def row(self):
        """
        the row/line in the file
        """
        return self.fromRow
    @row.setter
    def row(self,row):
        self.fromRow=row

    @property
    def fromRow(self):
        """
        the starting row/line in the file
        """
        return self._fromRow
    @fromRow.setter
    def fromRow(self,fromRow:typing.Optional[int]):
        if fromRow is None:
            fromRow=0
        self._fromRow=fromRow

    @property
    def toRow(self):
        """
        ending row/line in the file
        """
        return self._toRow
    @toRow.setter
    def toRow(self,toRow:typing.Optional[int]):
        if toRow is None:
            toRow=-1
        self._toRow=toRow

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
                ret.append('%d'%self.fromColumn)
            if self.toLine is not None:
                ret.append('-%d'%self.toLine)
                if self.toColumn is not None:
                    ret.append('-%d'%self.toColumn)
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

    def __init__(self,url:paths.URLCompatible,
        fromRow:typing.Optional[int]=None,
        fromColumn:typing.Optional[int]=None,
        toLine:typing.Optional[int]=None,
        toColumn:typing.Optional[int]=None,
        smartDecodeUrl=True):
        """ """
        LocationWithinFile.__init__(fromRow,fromColumn,toLine,toColumn)
        self.smartDecodeUrl=smartDecodeUrl
        self._url:paths.URL=paths.asURL(url)

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

    @property
    def url(self)->paths.URL:
        """
        The file to whom we are referring
        """
        return self._url
    @url.setter
    def url(self,url:paths.URLCompatible):
        self._url=paths.asURL(url)

    def __repr__(self)->str:
        r"""
        Get this location as a string.  Eg:
            /home/tjones/file.txt:3

        If there is no associated file/url then will simply say
            Line 3
        """
        ret:typing.List[str]=[]
        if self.url is None:
            if self.line is not None:
                ret.append('Line ')
        elif self.url.protocol=='file' and self.url.filePath is not None:
            ret.append(self.url.filePath)
            ret.append(':')
        else:
            ret.append(str(self.url))
            ret.append(':')
        ret.append(LocationWithinFile.__repr__(self))
        return ''.join(ret)


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