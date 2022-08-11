#!/usr/bin/env
# -*- coding: utf-8 -*-
"""
This represents a url type
"""
from abc import abstractmethod
import typing


class IURL:
    @property
    @abstractmethod
    def dirPath(self)->str:
        pass
    @property
    @abstractmethod
    def filename(self)->typing.Optional[str]:
        pass
    @abstractmethod
    def clear(self)->None:
        pass
    @abstractmethod
    def copy(self)->"IURL":
        pass
    @abstractmethod
    def call(self,**kwds)->str:
        pass
    __call__=call
    @property
    @abstractmethod
    def auth(self)->str:
        pass
    @abstractmethod
    def isLocalhost(self)->bool:
        pass
    @abstractmethod
    def getFilePath(self,
        enquote:bool=True,
        illegalChars:str=None,
        errors:str='exception'
        )->typing.Optional[str]:
        pass
    @property
    @abstractmethod
    def filePath(self)->typing.Optional[str]:
        pass
    @property
    @abstractmethod
    def protocol(self)->str:
        pass
    @property
    @abstractmethod
    def path(self)->str:
        pass
    @abstractmethod
    def sameDomain(self,other:typing.Any)->bool:
        pass
    domainMatches=sameDomain
    @property
    @abstractmethod
    def url(self)->str:
        pass
    name=url
    @abstractmethod
    def _encode(self)->str:
        pass
    @abstractmethod
    def _decode(self,data:str)->None:
        pass
    @property
    @abstractmethod
    def fullPath(self)->typing.Optional[str]:
        pass
    @property
    @abstractmethod
    def user(self)->typing.Optional[str]:
        pass
    @property
    @abstractmethod
    def host(self)->typing.Optional[str]:
        pass
    @abstractmethod
    def _getUrlString(self,url:typing.Any)->str:
        pass
    @property
    @abstractmethod
    def isFile(self)->bool:
        pass
    @property
    @abstractmethod
    def isDirectory(self)->bool:
        pass
    @abstractmethod
    def assign(self,
        url:typing.Optional[typing.Any],
        relativeTo:typing.Optional[typing.Any]=None,
        _useRelTo=True,
        _isDirectory=None
        )->None:
        pass
    setUrl=assign
