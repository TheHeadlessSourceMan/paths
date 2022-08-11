"""
Handy way of adding loading/saving to any data type.

Simply derive class MyClass(LoadAndSave) and then implement
_encode(self)->data and _decode(self,data)

This will let you load not only local files, but more advanced stuff like html and ftp.

If ezFs is installed, it gets even more wild, allowing access into
online file stores, compressed files, and more!
"""
from abc import abstractmethod
import typing
from .iUrl import IURL
from .urlTyping import URLCompatible


ParamsDict=typing.Dict[str,typing.Any]


class ILoadAndSaveBytes:
    @abstractmethod
    def decode(self,data:bytes)->None:
        pass
    @abstractmethod
    def decodeBytes(self,data:bytes)->None:
        pass
    @abstractmethod
    def encode(self)->bytes:
        pass
    @abstractmethod
    def encodeBytes(self)->bytes:
        pass
    @property
    @abstractmethod
    def filename(self)->typing.Optional[IURL]:
        pass
    @property
    @abstractmethod
    def url(self)->typing.Union[IURL,None]:
        pass
    @abstractmethod
    def canLoad(self)->bool:
        pass
    @abstractmethod
    def canSave(self)->bool:
        pass
    @abstractmethod
    def load(self,filename:URLCompatible=None,
        altDecoder:typing.Optional[typing.Callable[[bytes],None]]=None,
        altDecoderParams:typing.Optional[ParamsDict]=None
        )->None:
        pass
    @abstractmethod
    def save(self,filename:URLCompatible=None,
        altEncoder:typing.Optional[typing.Callable[...,bytes]]=None,
        altEncoderParams:typing.Optional[ParamsDict]=None
        )->None:
        pass

class ILoadAndSave(ILoadAndSaveBytes):
    @abstractmethod
    def _detectEncoding(self,data:bytes)->str:
        pass
    @abstractmethod
    def _decodeBytes(self, # pylint: disable=arguments-differ
        data:bytes,
        errors:str='ignore',
        altDecoder:typing.Optional[typing.Callable[[str],str]]=None,
        altDecoderParams:typing.Optional[ParamsDict]=None
        )->None:
        pass
    @abstractmethod
    def _encodeBytes(self, # pylint: disable=arguments-differ
        altEncoder:typing.Optional[typing.Callable[[str],str]]=None,
        altEncoderParams:typing.Optional[ParamsDict]=None
        )->bytes:
        pass
    @abstractmethod
    def decode(self,data:typing.Union[bytes,str])->None:
        pass
    @abstractmethod
    def encode(self)->str: #type: ignore
        pass
    def load(self,  # type: ignore
        filename:URLCompatible=None,
        altDecoder:typing.Optional[typing.Callable[[str],str]]=None,
        altDecoderParams:typing.Optional[ParamsDict]=None
        )->None:
        pass
    def save(self, # type: ignore
        filename:typing.Optional[URLCompatible]=None,
        altEncoder:typing.Optional[typing.Callable[...,str]]=None,
        altEncoderParams:typing.Optional[ParamsDict]=None
        )->None:
        pass