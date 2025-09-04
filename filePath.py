"""
This expands upon pathlib.Path object
to make it compatible with paths.URL, and also
to add some missing features
"""
import typing
import os
import re
import pathlib
import datetime
from ._url import URL
from .urlTyping import UrlCompatible
from .search import findFilenamesOfType
from .errors import MalformedFilename


FilePathCompatible=UrlCompatible


def asFilePath(
    path:typing.Optional[FilePathCompatible],
    relativeTo:typing.Optional[FilePathCompatible]=None,
    maxParentLevels:typing.Optional[int]=None,
    maxChildLevels:typing.Optional[int]=None,
    makeAbsolute:bool=False,
    shellReplace:typing.Union[bool,typing.Dict[str,typing.Any]]=False
    )->"FilePath":
    """
    Force the path to be a file path

    Passing in None or empty string creates a path to the current directory

    :makeAbsolute: Make this always an absolute path
    :shellReplace: Whether or not to perform shell replacements or a dict of shell replacements.
        This can be dangerous because a if hacker can somehow cause your program to
        open file "./%SECRET_PASSWORD%" and the it throws "Unable to open file ./1234"
        For that reason, it is recommended to use shellReplace as a dict and only populate
        it with valid environment variables.
    """
    if not isinstance(path,FilePath):
        return FilePath(
            path,relativeTo,maxParentLevels,maxChildLevels,makeAbsolute,shellReplace) # type: ignore
    if makeAbsolute and not path.isAbsolute:
        return path.absolute()
    return path
asFilename=asFilePath
asFileName=asFilePath
asFileUrl=asFilePath


def asAbsoluteFilePath(
    path:typing.Optional[FilePathCompatible],
    relativeTo:typing.Optional[FilePathCompatible]=None,
    maxParentLevels:typing.Optional[int]=None,
    maxChildLevels:typing.Optional[int]=None,
    makeAbsolute:bool=True,
    shellReplace:typing.Union[bool,typing.Dict[str,typing.Any]]=False
    )->"FilePath":
    """
    Force the path to be absolute

    Passing in None or empty string creates a path to the current directory

    :makeAbsolute: Make this always an absolute path
    :shellReplace: Whether or not to perform shell replacements or a dict of shell replacements.
        This can be dangerous because a if hacker can somehow cause your program to
        open file "./%SECRET_PASSWORD%" and the it throws "Unable to open file ./1234"
        For that reason, it is recommended to use shellReplace as a dict and only populate
        it with valid environment variables.
    """
    return asFilePath(path,relativeTo,
        maxParentLevels,maxChildLevels,makeAbsolute,shellReplace)
asAbsoluteFilename=asAbsoluteFilePath
asAbsoluteFileName=asAbsoluteFilePath
asAbsoluteFileUrl=asAbsoluteFilePath


def expandUserStr(
    path:typing.Optional[FilePathCompatible],
    shellReplace:typing.Union[bool,typing.Dict[str,typing.Any]]=True
    )->str:
    """
    Replacement for os.path.expanduser that allows for
    a custom variable dictionary for security.

    Expands:
      - ~ and ~/... using variables['HOME'] or system default
      - $VAR and ${VAR} (Unix-style)
      - %VAR% (Windows-style)

    :param path: The input path string
    :shellReplace: Whether or not to perform shell replacements or a dict of shell replacements.
        This can be dangerous because a if hacker can somehow cause your program to
        open file "./%SECRET_PASSWORD%" and the it throws "Unable to open file ./1234"
        For that reason, it is recommended to use shellReplace as a dict and only populate
        it with valid environment variables.
    :return: Expanded path string
    """
    pathStr:str=''
    if path is None or not path:
        pathStr='.'
    elif isinstance(path,str):
        pathStr=path
    elif not isinstance(path,str):
        if isinstance(path,FilePath):
            # treat anything like a FilePath as already expanded
            return path.filename
        pathStr=asFileString(path)
    if isinstance(shellReplace,bool):
        if shellReplace:
            pathStr=os.path.expanduser(str(path))
    elif shellReplace: # no sense doing anything if empty
        # make sure it's all strings
        replacements:typing.Dict[str,str]={}
        for k,v in shellReplace:
            replacements[k]=str(v)
        # repeatedly make replacements
        pathBefore=''
        limit=100 # prevent infinite loops
        for _ in range(limit):
            pathBefore=pathStr
            # Expand ~ using HOME from variables or fallback
            if pathStr.startswith("~"):
                home=replacements.get("HOME",os.path.expanduser("~"))
                if pathStr=="~":
                    pathStr=home
                elif pathStr.startswith("~/"):
                    pathStr=os.path.join(home,pathStr[2:])
                # Leave ~username as-is (not expanding usernames)
            # Replace $VAR and ${VAR} (Unix-style)
            def replaceDollar(match:typing.Match[str])->str:
                var_name=match.group(1) or match.group(2)
                return replacements.get(var_name,match.group(0))  # leave as-is if not found
            pathStr=re.sub(r'\$(\w+)|\${(\w+)}',replaceDollar,pathStr)
            # Replace %VAR% (Windows-style)
            def replacePercent(match:typing.Match[str])->str:
                k=match.group(1)
                return replacements.get(k,match.group(0))  # leave as-is if not found
            pathStr=re.sub(r'%([^%]+)%',replacePercent,pathStr)
            if pathBefore==pathStr:
                # No substitutions made this round, so we're done
                break
    return pathStr


def expanduser(
    path:typing.Optional[FilePathCompatible],
    shellReplace:typing.Union[bool,typing.Dict[str,typing.Any]]=True
    )->"FilePath":
    """
    Replacement for os.path.expanduser that allows for
    a custom variable dictionary for security.

    Expands:
      - ~ and ~/... using variables['HOME'] or system default
      - $VAR and ${VAR} (Unix-style)
      - %VAR% (Windows-style)

    :param path: The input path string
    :shellReplace: Whether or not to perform shell replacements or a dict of shell replacements.
        This can be dangerous because a if hacker can somehow cause your program to
        open file "./%SECRET_PASSWORD%" and the it throws "Unable to open file ./1234"
        For that reason, it is recommended to use shellReplace as a dict and only populate
        it with valid environment variables.
    :return: Expanded path as FilePath
    """
    if shellReplace is not None and isinstance(path,FilePath):
        # treat anything like a FilePath as already expanded
        return path
    return FilePath(expandUserStr(path,shellReplace))
expandvars=expanduser


def asFileString(
    location:typing.Optional[FilePathCompatible],
    makeAbsolute:bool=False,
    shellReplace:typing.Union[bool,typing.Dict[str,typing.Any]]=False
    )->str:
    """
    Force the location to be a file path string

    Passing in None or empty string creates a path to the current directory

    :makeAbsolute: Make this always an absolute path
    :shellReplace: Whether or not to perform shell replacements or a dict of shell replacements.
        This can be dangerous because a if hacker can somehow cause your program to
        open file "./%SECRET_PASSWORD%" and the it throws "Unable to open file ./1234"
        For that reason, it is recommended to use shellReplace as a dict and only populate
        it with valid environment variables.
    """
    fileLocation=location
    if fileLocation is None or not fileLocation:
        fileLocation='.'
    isFileString:typing.Optional[bool]=None
    while not isinstance(fileLocation,str):
        if isinstance(fileLocation,(FilePath,pathlib.Path)):
            isFileString=True
            fileLocation=str(location)
        elif isinstance(fileLocation,URL):
            isFileString=fileLocation.isFile
            fileLocation=str(fileLocation)
        elif hasattr(fileLocation,'url'):
            member=fileLocation.url # type: ignore
            if callable(member) \
                and not hasattr(member,'__self__') \
                or member.__self__ is fileLocation: # type: ignore
                # We can call a callable who is a member of the class,
                # or even a member of no class, but if it a member
                # of a different class, then we do not want to call it.
                # That is, we do not want to call a returned object
                # just because it has a __call__() method
                fileLocation=member() # type: ignore
            else:
                fileLocation=member
        else:
            raise MalformedFilename(
                '[Unknown]',
                f'Unable to obtain filename from type {fileLocation.__class__.__name__}')
        if fileLocation is None or not fileLocation:
            fileLocation='.'
            raise MalformedFilename(str(fileLocation),'Empty or missing filename')
    if isFileString is None:
        fileLocationSplit=fileLocation.split(':',1)
        isFileString=False
        if len(fileLocationSplit)<2 \
            or len(fileLocationSplit[0])<2 \
            or fileLocationSplit[0].find('/')>=0 \
            or fileLocationSplit[0].find('\\')>=0 \
            or fileLocationSplit[0]=='file':
            #
            isFileString=True
    if not isFileString:
        raise MalformedFilename(fileLocation,'Does not look like a filename')
    # from here on out, it is always a string
    if shellReplace:
        fileLocation=expandUserStr(fileLocation)
    if makeAbsolute:
        fileLocation=os.path.abspath(fileLocation)
    return fileLocation


class FilePath(pathlib.Path,URL):
    """
    This expands upon pathlib.Path object
    to make it compatible with paths.URL, and also
    to add some missing features
    """
    def __init__(self,
        location:typing.Optional[FilePathCompatible]=None,
        relativeTo:typing.Optional[FilePathCompatible]=None,
        maxParentLevels:typing.Optional[int]=None,
        maxChildLevels:typing.Optional[int]=None,
        makeAbsolute:bool=False,
        shellReplace:typing.Union[bool,typing.Dict[str,typing.Any]]=False):
        """
        Passing in None or empty string creates a path to the current directory

        :makeAbsolute: Make this always an absolute path
        :shellReplace: Whether or not to perform shell replacements or a dict of shell replacements.
            This can be dangerous because a if hacker can somehow cause your program to
            open file "./%SECRET_PASSWORD%" and the it throws "Unable to open file ./1234"
            For that reason, it is recommended to use shellReplace as a dict and only populate
            it with valid environment variables.
        """
        fileLocation:str=asFileString(location,makeAbsolute,shellReplace)
        pathlib.Path.__init__(self,fileLocation) # type: ignore
        URL.__init__(self,location,relativeTo,maxParentLevels,maxChildLevels)

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

    def replace(self, # type: ignore # pylint: disable=arguments-differ
        replaceThis:typing.Union[str,typing.Pattern[str]],
        withThis:typing.Union[str,typing.Any]
        )->"FilePath":
        """
        Does everything that str.replace() does, so url.replace(x,y)
        is exactly the same as Url(str(url).replace(x,y))
        Also, if you pass in a compiled regex for replaceThis,
        it is smart enough to use the regex.sub() instead

        NOTE: if you are trying to replace something with path separators,
        always use "/"
        NOTE: if your replacement makes this an un-parsable Url(),
        that's on you!
        """
        url=URL.replace(self,replaceThis,withThis)
        fp=url.filePath
        if fp is None:
            raise ValueError(str(url))
        return FilePath(fp)

    def dir(
        self,
        globExpression:typing.Union[None,str,typing.Pattern[str]]=None,
        recursive:bool=True
        )->typing.Generator["FilePath",None,None]:
        """
        Act like the system dir or ls command
        """
        if globExpression is not None and isinstance(globExpression,str):
            raise NotImplementedError() # TODO: need to convert from glob to regex
        for result in self.findFilenamesOfType(recursive=recursive):
            if globExpression is not None:
                if not result.isAbsolute:
                    resultStr=str(result.absolute())
                else:
                    resultStr=str(result)
                if globExpression.match(resultStr) is not None:
                    yield result
            else:
                yield result
    ls=dir

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

    def __truediv__(self, # type: ignore
        other:FilePathCompatible)->"FilePath":
        """
        Capture the Path "/" operator so it returns a FilePath
        """
        other=asFileString(other)
        return FilePath(pathlib.Path.__truediv__(self,other)) # type: ignore
    def __rtruediv__(self, # type: ignore
        other:FilePathCompatible)->"FilePath":
        """
        Capture the Path "/" operator so it returns a FilePath
        """
        other=asFileString(other)
        return FilePath(pathlib.Path.__rtruediv__(self,other)) # type: ignore

    @property
    def parent(self)->"FilePath":
        """
        All of the child filenames
        """
        if pathlib.Path.parent is None:
            raise FileNotFoundError(str(self)+'/..')
        drv=self._drv
        root=self._root
        parts=self._parts
        if len(parts)==1 and (drv or root):
            raise FileNotFoundError(str(self)+'/..')
        parentPath=self._from_parsed_parts(drv,root,parts[:-1])
        return FilePath(parentPath)

    @property
    def root(self)->"FilePath": # type: ignore
        """
        All of the child filenames
        """
        if self._root is not None:
            return FilePath(self._root)
        if self._drv is not None:
            return FilePath(self._drv)
        if self._boundParentPath is not None:
            return asFilePath(self._boundParentPath).root # type: ignore
        return self

    @property
    def children(self)->typing.Iterator["FilePath"]:
        """
        All of the child filenames
        """
        for c in self.iterdir():
            yield FilePath(c)

    @property
    def files(self)->typing.Iterator["FilePath"]:
        """
        All of the child files
        """
        for c in self.children:
            if c.is_file():
                yield c

    @property
    def directories(self)->typing.Iterator["FilePath"]:
        """
        All of the child directories
        """
        for c in self.children:
            if c.is_dir():
                yield c

    @property
    def isDirectory(self)->bool:
        """
        Is this a directory
        """
        return self.is_dir()
    @isDirectory.setter
    def isDirectory(self,isDirectory:bool):
        _=isDirectory
        raise NotImplementedError()

    def __len__(self)->int:
        """
        Act like a list of filenames
        """
        return len([c for c in self.children])

    def __getitem__(self, # type: ignore
        idx:typing.Union[int,FilePathCompatible]
        )->"FilePath":
        """
        Act like a list of filenames
        """
        if isinstance(idx,int):
            for i,c in enumerate(self.children):
                if i==idx:
                    return c
            raise IndexError()
        result=self/idx
        if not result.exists():
            raise IndexError()
        return result

    def __setitem__(self,
        idx:typing.Union[int,FilePathCompatible],
        contents:typing.Union[str,bytes,"FilePath"]):
        """
        Act like a list of filenames
        """
        if isinstance(idx,int):
            for i,c in enumerate(self.children):
                if i==idx:
                    self.set(c,contents)
                    return
            raise IndexError()
        self.set(idx,contents)

    def set(self,
        filename:FilePathCompatible,
        contents:typing.Union[str,bytes,"FilePath"]='',
        ifExists:typing.Union[
            None,
            typing.Type[Exception],
            typing.Callable[["FilePath"],bool],
            typing.Callable[["str"],bool]]=FileExistsError
        )->"FilePath":
        """
        Set the contents of a file in this directory

        :contents: either data, or a FilePath if you want
            to create a shortcut
        Returns the FilePath object of what was written
        in case you want to mess with it.
        """
        if isinstance(contents,FilePath):
            return self.setFileShortcut(
                filename,contents,ifExists)
        return self.setFileContents(
            filename,contents,ifExists)

    def get(self,
        filename:FilePathCompatible,
        default:None
        )->typing.Optional["FilePath"]:
        """
        Get a filename within this directory
        """
        filename=self/filename
        if filename.exists():
            return filename
        return default

    def setFileContents(self,
        filename:FilePathCompatible,
        contents:typing.Union[str,bytes]='',
        ifExists:typing.Union[
            None,
            typing.Type[Exception],
            typing.Callable[["FilePath"],bool],
            typing.Callable[["str"],bool]]=FileExistsError
        )->"FilePath":
        """
        Set the contents of a file in this directory

        Returns the FilePath object of what was written
        in case you want to mess with it.
        """
        filename=self/filename
        self.ensureNotExists(filename,ifExists)
        if isinstance(contents,bytes):
            filename.write_bytes(contents)
        return filename

    def setFileShortcut(self,
        filename:FilePathCompatible,
        linkTo:FilePathCompatible,
        ifExists:typing.Union[
            None,
            typing.Type[Exception],
            typing.Callable[["FilePath"],bool],
            typing.Callable[["str"],bool]]=FileExistsError):
        """
        Set a filename as a shortcut to another filename.

        On windows a shortcut is a particular thing,
        but on other oses this is the same as setFileSymlink()
        """
        if os.name=='nt':
            # NOTE: if linkTo is a URL, should create a .url not a .lnk
            self.ensureNotExists(filename,ifExists)
            raise NotImplementedError()
        else:
            self.setFileSymlink(filename,linkTo)

    def ensureNotExists(self,
        filename:FilePathCompatible,
        ifExists:typing.Union[
            None,
            typing.Type[Exception],
            typing.Callable[["FilePath"],bool],
            typing.Callable[["str"],bool]]=FileExistsError
        )->bool:
        """
        Ensure that a filename does not exist

        :ifExists: an exception to throw if the file exists
            or None
            or a function to call to ask the user what to do (must return bool)
        """
        filename=self/filename
        exists=not filename.exists()
        if exists and ifExists is not None:
            if isinstance(ifExists,Exception):
                raise ifExists(str(filename)) # type: ignore
            ifExists(filename) # type: ignore
        return not exists

    def ensureExists(self,
        filename:FilePathCompatible,
        ifNotExists:typing.Union[
            None,
            typing.Type[Exception],
            typing.Callable[["FilePath"],bool],
            typing.Callable[["str"],bool]]=FileNotFoundError
        )->bool:
        """
        Ensure that a filename exists

        :ifExists: an exception to throw if the file exists
            or None
            or a function to call to ask the user what to do (must return bool)
        """
        filename=self/filename
        exists=not filename.exists()
        if exists and ifNotExists is not None:
            if isinstance(ifNotExists,Exception):
                raise ifNotExists(str(filename)) # type: ignore
            ifNotExists(filename) # type: ignore
        return not exists

    def setFileSymlink(self,
        filename:FilePathCompatible,
        linkTo:FilePathCompatible,
        ifExists:typing.Union[
            None,
            typing.Type[Exception],
            typing.Callable[["FilePath"],bool],
            typing.Callable[["str"],bool]]=FileExistsError):
        """
        Set a filename as a symbolic link to another filename.

        :ifExists: an exception to throw if the file exists
            or None
            or a function to call to ask the user what to do (must return bool)
        """
        linkTo=asFilePath(linkTo)
        if not linkTo.exists():
            # if the target is missing, that's always an error
            raise FileNotFoundError(f'Link target "{linkTo}" is missing')
        filename=self/filename
        self.ensureNotExists(filename,ifExists)
        filename.symlink_to(str(linkTo),linkTo.is_dir())
    addFileSymlink=setFileSymlink

    def __eq__(self, # type: ignore
        other:FilePathCompatible
        )->bool:
        """
        Is this the same as another filename?
        """
        return self.absolute()==asFileString(other,True)

    @property
    def isCwd(self)->bool:
        """
        Is this the current working directory
        """
        return self==''

    @property
    def descendents(self)->typing.Iterator["FilePath"]:
        """
        All descendent files as a flat list
        """
        return self.findFilenamesOfType()
    @property
    def flat(self)->typing.Iterator["FilePath"]:
        """
        All descendent files as a flat list
        """
        return self.findFilenamesOfType()

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
        return self.name
    @filename.setter
    def filename(self,filename:FilePathCompatible):
        self.name=filename

    @property
    def name(self)->str:
        """The final path component, if any."""
        parts = self._parts
        if len(parts) == (1 if (self._drv or self._root) else 0):
            return ''
        return parts[-1]
    @name.setter
    def name(self,name:FilePathCompatible):
        # TODO: does this constitute a system rename?
        if not isinstance(name,str):
            name=asFilePath(name).name
        self._parts[-1]=name

    @property
    def expandvars(self)->"FilePath":
        """
        Expand shell variables
        """
        return FilePath(os.path.expandvars(str(self)))

    @property
    def lastModifiedTime(self)->datetime.datetime:
        """
        Get the file modification time
        """
        return datetime.datetime.fromtimestamp(
            pathlib.Path.lstat(self).st_mtime,
            tz=datetime.timezone.utc)

    def absolute(self)->"FilePath":
        return FilePath(pathlib.Path.absolute(self))
FileUrl=FilePath
Filename=FilePath
FileName=FilePath


if __name__=='__main__':
    import sys
    filename=FileName()
    print(filename)
    print(filename.absolute())
    for c in filename.children:
        print(c)
    sys.exit(0)
