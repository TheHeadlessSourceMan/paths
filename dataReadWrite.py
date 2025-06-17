"""
reading/writing data

this is specific to the needs of URL object and
is not intended for public consumption.
"""
import typing
from abc import abstractmethod
import time
from .mimeType import MimeType


class DataReadWrite:
    """
    reading/writing data

    this is specific to the needs of URL object and
    is not intended for public consumption.
    """

    def __init__(self)->None:
        self._data:typing.Union[None,bytearray,bytes]=None
        self._mimeType:typing.Optional[MimeType]=None
        self._idx:int=0
        self._dirty:bool=False # is there data that needs to be written

    @property
    @abstractmethod
    def protocol(self)->str:
        """
        the protocol in use
        """

    @property
    @abstractmethod
    def filePath(self)->typing.Optional[str]:
        """
        the protocol in use
        """

    @property
    def data(self)->bytes:
        """
        the remote data
        (will be read on demand)
        """
        if self._data is None:
            self._readFile()
        return self._data # type: ignore
    @data.setter
    def data(self,data:typing.Union[str,bytes]):
        self.write(data)

    @property
    def mimeType(self)->typing.Optional[MimeType]:
        """
        If the mime type is known, return it.  Otherwise attempt to guess.
        (this isn't the most sophisticated guessing in the world,
        but just enough to get by)

        It may need to pre-read the data to determine this.
        When in doubt returns "application/octet-stream" or "text/plain".
        Only if the data cannot be retrieved will it return None.

        NOTE: you can assign a mime type, which will be passed
            into HTTP accepts header.

        SEE ALSO: https://en.wikipedia.org/wiki/List_of_file_signatures
        """
        if self._mimeType is None:
            if self._data is None:
                first500=self.readBytes(500)
                if first500 is None:
                    return None
                isBinary=False
                try:
                    first500txt=first500.decode('utf-8')
                except UnicodeDecodeError:
                    isBinary=True
                if not isBinary:
                    if first500.startswith(b'MZ'):
                        self._mimeType=MimeType('application/zip')
                    elif first500.startswith(b'"%PDF"'):
                        self._mimeType=MimeType('application/pdf')
                    else:
                        self._mimeType=MimeType('application/octet-stream')
                else:
                    first500txt=first500txt.lstrip()
                    if first500txt[0]=='<':
                        if first500txt.find('<html')>=0:
                            self._mimeType=MimeType('text/html')
                        else:
                            self._mimeType=MimeType('application/xml')
                    elif first500txt[0]=='{':
                        self._mimeType=MimeType('application/json')
                    elif first500txt.startswith('---')\
                        and first500txt[3]!='-':
                        self._mimeType=MimeType('application/yaml')
                    elif len(first500txt.split(',',4))>3\
                        or len(first500txt.split('\t',4))>3:
                        self._mimeType=MimeType('text/csv')
                    else:
                        self._mimeType=MimeType('text/plain')
        return self._mimeType

    def write(self,
        data:typing.Union[str,bytes]
        )->None:
        """
        file-like object write method
        """
        self._dirty=True
        if isinstance(data,str):
            data=data.encode('utf-8')
        if self._data is None:
            self._data=bytearray(data)
        elif isinstance(self.data,bytes):
            self._data=bytearray(self._data)
            self._data.extend(data)
        else:
            self._data.extend(data)

    def close(self)->None:
        """
        file-like object close method
        """
        self.flush()
        self._data=None
        self._idx=0

    def flush(self)->None:
        """
        file-like object flush method
        """
        if self._dirty and self._data is not None:
            self._writeFile()
        self._dirty=False

    def readBytes(self,
        numBytes:typing.Optional[int]=None
        )->bytes:
        """
        file-like object read method
        """
        if numBytes is None:
            ret=self.data[self._idx:len(self.data)]
            self._idx=len(self.data)
        else:
            ret=self.data[self._idx:min(self._idx+numBytes,len(self.data))]
            self._idx+=len(ret)
        return ret

    def readString(self,
        numBytes:typing.Optional[int]=None,
        encoding:str='utf-8',
        errors:str='ignore'
        )->str:
        """
        file-like object read method

        TODO: use the auto decoder trick from loadAndSave.py
        """
        ret=self.readBytes(numBytes)
        return ret.decode(encoding,errors=errors)
    read=readString

    def readLines(self,
        numLines:typing.Optional[int]=None,
        encoding:str='utf-8',
        errors:str='ignore'
        )->typing.Generator[str,None,None]:
        """
        file-like object read method
        """
        if numLines is not None:
            data=self.read(None,encoding,errors)
            for i,line in enumerate(data.split('\n')):
                if i>=numLines:
                    return
                yield line
        else:
            for line in self.read(None,encoding,errors).split('\n'):
                yield line

    def _readFile(self)->None:
        """
        Physically go and read the file right now

        NOTE: can use EzFs if installed
        """
        try:
            import ezFs # type: ignore
            hasEzFs=True
        except ImportError:
            hasEzFs=False
        hasEzFs=False # TODO: it's busted again
        if hasEzFs:
            ez=ezFs.EzFs()
            f=ez.open(self.filePath,'rb')
            self._data=bytearray(f.read())
            f.close()
        else:
            if self.protocol=='file' and self.filePath is not None:
                f=open(self.filePath,'rb')
                self._data=bytearray(f.read())
                f.close()
            else:
                #  read typical things python can read, such as http and ftp
                from webfetch.WebFetch import WebFetch
                w=WebFetch()
                self._data,self._mimeType=w.fetchNow(self) # type: ignore

    def _writeFile(self)->None:
        """
        Physically go and write the file right now

        NOTE: can use EzFs if installed
        """
        try:
            import ezFs # type: ignore
            hasEzFs=True
        except ImportError:
            hasEzFs=False
        if hasEzFs:
            ez=ezFs.EzFs()
            f=ez.open(self.filePath,'wb')
            if self._data is not None:
                f.write(bytes(self._data))
            f.close()
        else:
            if self.protocol=='file' and self.filePath is not None:
                f=open(self.filePath,'wb')
                if self._data is not None:
                    f.write(bytes(self._data))
                f.close()
            else:
                raise NotImplementedError(
                    f'Unsupported protocol "{self.protocol}". It may help to install EzFs.') # noqa: E501 # pylint: disable=line-too-long

    def seek(self,
        idx:int,
        fromWhere:int=0
        )->None:
        """
        file-like object seek method
        """
        if fromWhere==0: # reference point is the beginning of the file
            self._idx=idx
        elif fromWhere==1: # reference point is the current file position
            self._idx+=idx
        elif fromWhere==2: # reference point is the end of the file
            self._idx=len(self.data)-idx

    def tell(self)->int:
        """
        file-like object tell method
        """
        return self._idx

    def watch(self,
        notifyFn:typing.Optional[typing.Callable]=None,
        pollInterval:float=1
        )->None:
        """
        If there is a notifyFn, will run forever (meant to be run threaded)

        If not, will return when the data has changed.

        :pollInterval: in decimal seconds
        """
        d=self._data
        while True:
            time.sleep(pollInterval)
            self.read()
            if self.data!=d:
                if notifyFn is None:
                    return
                else:
                    notifyFn(self)
