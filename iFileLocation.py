"""
A location without a filename.

Broken into its own object so multifile locations can have one
url, but many locations
"""
from abc import abstractmethod
import typing
import paths


class ILocationWithinFile:
    @property
    @abstractmethod
    def fromRow(self):
        pass
    row=fromRow
    line=fromRow
    fromLine=fromRow
    @property
    @abstractmethod
    def toRow(self):
        pass
    toLine=toRow
    @property
    @abstractmethod
    def fromColumn(self):
        pass
    @property
    @abstractmethod
    def toColumn(self):
        pass


class IFileLocation(ILocationWithinFile):
    @abstractmethod
    def read(self)->str:
        pass
    @property
    @abstractmethod
    def url(self)->paths.IURL:
        pass


class IMultiFileLocation(IFileLocation):
    @property
    @abstractmethod
    def fileLocations(self)->typing.Generator[IFileLocation,None,None]:
        pass
    @property
    @abstractmethod
    def fromRow(self):
        pass
    @property
    @abstractmethod
    def toRow(self):
        pass
    @property
    @abstractmethod
    def fromColumn(self):
        pass
    @property
    @abstractmethod
    def toColumn(self):
        pass


class IMessageLocation:
    pass


class IFileLocationError(IMessageLocation,Exception):
    pass