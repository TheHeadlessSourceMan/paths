"""
navigate around a url, like with
    root,parent,children,siblings,...

this is specific to the needs of URL object and
is not intended for public consumption.
"""
from abc import abstractmethod
import typing
from .iUrl import IURL

class IUrlNavigation:
    @property
    @abstractmethod
    def isDirectory(self)->bool:
        pass
    @property
    @abstractmethod
    def url(self)->str:
        pass
    @property
    @abstractmethod
    def parent(self)->IURL:
        pass
    @property
    @abstractmethod
    def root(self)->IURL:
        pass
    @abstractmethod
    def subdir(self,
        url:typing.Optional[typing.Any]
        )->IURL:
        pass
    @abstractmethod
    def getRelativeUrl(self,
        url:typing.Optional[typing.Any]
        )->IURL:
        pass
    unRelativeUrl=getRelativeUrl
    relative=getRelativeUrl
    @abstractmethod
    def location(self)->str:
        pass
    @abstractmethod
    def getSibling(self,
        url:typing.Optional[typing.Any]
        )->IURL:
        pass
