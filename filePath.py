"""
This expands upon pathlib.Path object
to make it compatible with paths.URL, and also
to add some missing features
"""
import typing
import os
import pathlib
import datetime
from _url import URL
from urlTyping import UrlCompatible
from search import findFilenamesOfType


FilePathCompatible=typing.Union[pathlib.Path,"FilePath",UrlCompatible]


def asFilePath(path:FilePathCompatible)->"FilePath":
    """
    Force the path to be a file path
    """
    if not isinstance(path,FilePath):
        return FilePath(path)
    return path


class FilePath(pathlib.Path,URL):
    """
    This expands upon pathlib.Path object
    to make it compatible with paths.URL, and also
    to add some missing features
    """
    def __init__(self,location:FilePathCompatible):
        pathlib.Path.__init__(self,location)
        URL.__init__(self,location)

    def findFilenamesOfType(
        self,
        extensions:typing.Union[None,str,typing.Iterable[str]]=None,
        recursive:bool=True
        )->typing.Generator["FilePath",None,None]:
        """
        Depth-first file search.

        Yields only files, never directories.

        :extensions: limit results to one or more extensions
            (extensions must include the dot, for instance [".c",".cpp"])
        :recursive: default=true
        """
        for f in findFilenamesOfType(extensions,self,recursive):
            yield FilePath(f)

    @property
    def extension(self)->str:
        """
        File extension
        """
        return self.suffix
    @property
    def ext(self)->str:
        """
        File extension
        """
        return self.suffix

    def makedirs(self,inclusive:bool):
        """
        Make all directories exist leading up to this point

        :inclusive: if True, create this path as a directory as well
        """
        pth=self.absolute()
        if not inclusive:
            pth=pth.parent
        os.makedirs(pth)
    mkdirs=makedirs

    @property
    def filename(self)->str:
        """
        Short filename
        """
        return pathlib.Path.name

    @property
    def expandvars(self)->"FilePath":
        """
        Expand shell variables
        """
        return os.path.expandvars(str(self))

    @property
    def lastModifiedTime(self)->datetime.datetime:
        """
        Get the file modification time
        """
        return datetime.datetime.fromtimestamp(
            pathlib.Path.lstat(self).st_mtime,
            tz=datetime.timezone.utc)

    def absolute(self)->"AbsoluteFilePath":
        return AbsoluteFilePath(self)


def asAbsoluteFilePath(path:FilePathCompatible)->"AbsoluteFilePath":
    """
    Force the path to be absolute
    """
    if not isinstance(path,AbsoluteFilePath):
        return AbsoluteFilePath(path)
    return path


class AbsoluteFilePath(FilePath):
    """
    Explicit absolute path.

    Sure, you could check any paths with .is_absolute()
    but this makes it explicit and simple to specify
    what a function takes.
    """

    def __init__(self,location:FilePathCompatible):
        location=os.path.abspath(os.path.expandvars(str(location)))
        FilePath.__init__(self,location)
