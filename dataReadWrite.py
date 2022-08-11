"""
reading/writing data

this is specific to the needs of URL object and
is not intended for public consumption.
"""
import typing
from abc import abstractmethod
import time


class DataReadWrite:
    """
    reading/writing data

    this is specific to the needs of URL object and
    is not intended for public consumption.
    """

    def __init__(self):
        self._data:typing.Optional[bytearray]=None
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
    def data(self)->str:
        """
        the remote data
        (will be read on demand)
        """
        if self._data is None:
            self._readFile()
        return self._data
    @data.setter
    def data(self,data:typing.Union[str,bytes]):
        self.write(data)

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

    def read(self,
        numBytes:typing.Optional[int]=None
        )->str:
        """
        file-like object read method

        TODO: use the auto decoder trick from loadAndSave.py
        """
        return self.readBytes(numBytes).decode('utf-8','ignore')

    def readLines(self,
        numLines:typing.Optional[int]=None
        )->typing.Generator[str,None,None]:
        """
        file-like object read method
        """
        if numLines is not None:
            for i,line in enumerate(self.read().split('\n')):
                if i>=numLines:
                    return
                yield line
        else:
            for line in self.read().split('\n'):
                yield line

    def _readFile(self)->None:
        """
        Physically go and read the file right now

        NOTE: can use EzFs if installed
        """
        try:
            import ezFs
            hasEzFs=True
        except ImportError:
            hasEzFs=False
        if hasEzFs:
            ez=ezFs.EzFs()
            f=ez.open(self.filePath,'rb')
            self._data=bytearray(f.read())
            f.close()
        else:
            if self.protocol=='file':
                f=open(self.filePath,'rb')
                self._data=bytearray(f.read())
                f.close()
            else:
                # TODO: read typical things python can read, such as http and ftp
                raise NotImplementedError()

    def _writeFile(self)->None:
        """
        Physically go and write the file right now

        NOTE: can use EzFs if installed
        """
        try:
            import ezFs
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
            if self.protocol=='file':
                f=open(self.filePath,'wb')
                if self._data is not None:
                    f.write(bytes(self._data))
                f.close()
            else:
                # TODO: read typical things python can read, such as http and ftp
                raise NotImplementedError()

    def seek(self,
        idx:int,
        fromWhere:int=0
        )->None:
        """
        file-like object seek method
        """
        if fromWhere==0: # means your reference point is the beginning of the file
            self._idx=idx
        elif fromWhere==1: # means your reference point is the current file position
            self._idx+=idx
        elif fromWhere==2: # means your reference point is the end of the file
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