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
from warnings import warn
from paths._callableValue import CallableValue
from paths._url import URL
from paths.urlTyping import UrlCompatible
from paths.search import findFilenamesOfType
from paths.errors import MalformedFilename


FilePathCompatible=UrlCompatible
FileUrlCompatible=FilePathCompatible


# Options:
# True/'always' - always overwrite existing files
# False/'error' - raise an error if the file already exists (default)
# 'ignore'/'skip' - do nothing if the file already exists
# 'newer' - keep the newer of the two files
OverwriteOptions=typing.Union[bool,typing.Literal['always','error','ignore','skip','newer']]


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
        return FilePath(path,relativeTo,maxParentLevels,maxChildLevels,makeAbsolute,shellReplace) # type: ignore # pylint: disable=too-many-function-args
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
    Force the location to be a native file path string

    Passing in None or empty string creates a path to the current directory

    :makeAbsolute: Make this always an absolute path
    :shellReplace: Whether or not to perform shell replacements or a dict of shell replacements.
        This can be dangerous because a if hacker can somehow cause your program to
        open file "./%SECRET_PASSWORD%" and the it throws "Unable to open file ./1234"
        For that reason, it is recommended to use shellReplace as a dict and only populate
        it with valid environment variables.
    """
    fileLocation=location
    if fileLocation is None or (isinstance(fileLocation,str) and not fileLocation):
        fileLocation='.'
    isFileString:typing.Optional[bool]=None
    while not isinstance(fileLocation,str):
        if isinstance(fileLocation,FilePath):
            isFileString=True
            fileLocation=fileLocation.filePath
        elif isinstance(fileLocation,pathlib.Path):
            isFileString=True
            fileLocation=str(fileLocation)
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


_PathBase = pathlib.WindowsPath if os.name == "nt" else pathlib.PosixPath
class FilePath(_PathBase,URL):
    """
    This expands upon pathlib.Path object
    to make it compatible with paths.URL, and also
    to add some missing features

    This is also more or less compatible with pathlib.Path
    """

    scheme="file"

    def __new__(cls,
        location:typing.Optional[FilePathCompatible],
        *args,
        **kwargs):
        """ """
        self = _PathBase.__new__(cls, '[BAD PATH]', '[BAD PATH]')
        #if location is None:
        #    location='.'
        #URL.__init__(self,location)
        return self

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
        _=makeAbsolute,shellReplace # used in __new__
        self.username=None
        self.password=None
        fileLocation:str=asFileString(location,makeAbsolute,shellReplace)
        self._pathlibPath=pathlib.Path(fileLocation)
        URL.__init__(self,location,relativeTo,maxParentLevels,maxChildLevels)

    def makeRelativeTo(self, # type: ignore
        relativeTo:"FilePathCompatible"
        )->"FilePath":
        """
        Get copy of this path, as it is re relative to another path

        That is, if we are "/home/bob/a/b" and relativeTo is "/home/bob/a/c"
        this would return "../b" because that is
        the relative path to get from "/home/bob/a/c" to "/home/bob/a/b"

        TODO: this needs tested. There are all kinds of edge
        cases in something like this!
        """
        from paths import PathStep
        relativeTo=asFilePath(relativeTo)
        # to compare, it needs to be all absolute, or all relative
        allRelative=False
        p1=self
        if p1.isFile:
            p1=p1.parent
        steps1:typing.List[PathStep]=[]
        steps2:typing.List[PathStep]=[]
        if not self.isAbsolute:
            if relativeTo.isAbsolute:
                steps1=list(self.pathSteps)
                allRelative=True
            else:
                steps1=list(relativeTo.absolute().pathSteps)
            steps2=list(relativeTo.pathSteps)
        elif not relativeTo.isAbsolute:
            steps1=list(self.pathSteps)
            steps2=list(relativeTo.absolute().pathSteps)
        # strip off common
        while steps1[0]=='.':
            steps1=steps1[1:]
        while steps2[0]=='.':
            steps2=steps2[1:]
        # compare it
        if allRelative:
            # strip off everything that is the same
            n=0
            for (n,(s1,s2)) in enumerate(zip(steps1,steps2)):
                if s1==s2:
                    steps1=steps1[1:]
                    steps2=steps2[1:]
                else:
                    break
            # go up so many directories
            ret=[PathStep('..') for _ in steps2]
            # then go down to where we wanted
            ret.extend(steps1[n:])
        else:
            # strip off everything that is the same
            n=0
            for (n,(s1,s2)) in enumerate(zip(steps1,steps2)):
                if s1==s2:
                    steps1=steps1[1:]
                    steps2=steps2[1:]
                else:
                    break
            # go up so many directories
            ret=[PathStep('..') for _ in steps2]
            # then go down to where we wanted
            ret.extend(steps1[n:])
        # create a new value with the result
        ret=self.__class__(self)
        ret.pathSteps=steps1
        return ret
    getRelativeTo=makeRelativeTo
    makeRelative=makeRelativeTo

    def makeRelativeFrom(self, # type: ignore
        fromPath:"FilePathCompatible"
        )->"FilePath":
        """
        Get a relative path from another path to this one
        """
        return asFilePath(fromPath).makeRelativeTo(self)
    getRelativeFrom=makeRelativeFrom

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
        for f in findFilenamesOfType(extensions,self._pathlibPath,recursive):
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

    def remove(self)->None:
        """
        Remove the file (if it exists)
        """
        if self._pathlibPath.is_dir():
            self._pathlibPath.rmdir()
        else:
            self._pathlibPath.unlink(True)
    rm=remove
    delete=remove

    @property
    def extension(self)->str:
        """
        File extension
        """
        return self._pathlibPath.suffix
    @property
    def ext(self)->str:
        """
        File extension
        """
        return self._pathlibPath.suffix

    def __truediv__(self, # type: ignore
        other:FilePathCompatible)->"FilePath":
        """
        Capture the Path "/" operator so it returns a FilePath
        """
        other=asFileString(other)
        combined=str(self._pathlibPath.__truediv__(other))
        return asFilePath(combined)
    def __rtruediv__(self, # type: ignore
        other:FilePathCompatible)->"FilePath":
        """
        Capture the Path "/" operator so it returns a FilePath
        """
        other=asFileString(other)
        return FilePath(str(self._pathlibPath.__rtruediv__(other)))

    @property
    def parse_parts(self):
        """
        Implement pathlib.Path.parse_parts
        """
        return self._pathlibPath.parse_parts # type: ignore # pylint: disable=no-member

    @property
    def parent(self)->"FilePath":
        """
        All of the child filenames
        """
        if self._pathlibPath.parent is None:
            raise FileNotFoundError(str(self)+'/..')
        drv=self._pathlibPath._drv # type: ignore # pylint: disable=protected-access
        root=self._pathlibPath._root # type: ignore # pylint: disable=protected-access
        parts=self._pathlibPath._parts # type: ignore # pylint: disable=protected-access
        if len(parts)==1 and (drv or root):
            raise FileNotFoundError(str(self)+'/..')
        parentPath=self._pathlibPath._from_parsed_parts(drv,root,parts[:-1]) # type: ignore # pylint: disable=protected-access
        return FilePath(parentPath)

    @property
    def root(self)->"FilePath": # type: ignore
        """
        All of the child filenames
        """
        if self._pathlibPath._root is not None: # type: ignore # pylint: disable=protected-access
            return FilePath(self._pathlibPath._root) # type: ignore # pylint: disable=protected-access
        if self._pathlibPath._drv is not None: # type: ignore # pylint: disable=protected-access
            return FilePath(self._pathlibPath._drv) # type: ignore # pylint: disable=protected-access
        if self._boundParentPath is not None:
            return asFilePath(self._boundParentPath).root # type: ignore
        return self

    @property
    def children(self)->typing.Generator["FilePath",None,None]:
        """
        iterate over the current directory
        """
        return self.iterdir()

    @property
    def files(self)->typing.Iterator["FilePath"]:
        """
        All of the child files
        """
        for c in self.children:
            if c.isFile:
                yield c

    @property
    def directories(self)->typing.Iterator["FilePath"]:
        """
        All of the child directories
        """
        for c in self.children:
            if c.isDir:
                yield c

    def dir(
        self,
        globExpression:typing.Union[None,str,typing.Pattern[str]]=None,
        recursive:bool=True
        )->typing.Generator["FilePath",None,None]:
        """
        Act like the system dir or ls command
        """
        return URL.dir(self,globExpression,recursive) # type: ignore
    ls=dir

    @property
    def isDirectory(self)->bool:
        """
        Is this a directory
        """
        return self._pathlibPath.is_dir()
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
            filename.pathlibPath.write_bytes(contents)
        return filename

    @property
    def pathlibPath(self)->pathlib.Path:
        """
        This path as a pathlib.Path object.
        """
        return pathlib.Path(self._pathlibPath)
    @pathlibPath.setter
    def pathlibPath(self,pathlibPath:FilePathCompatible):
        self.assign(pathlibPath)

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
        filename.symlink_to(linkTo)
    addFileSymlink=setFileSymlink

    def symlink_to(self, # type: ignore
        target:FilePathCompatible,
        target_is_directory:typing.Optional[bool]=None
        )->None:
        """
        Same as pathlib.Path.symlink_to
        """
        target=asFilePath(target)
        if target_is_directory is None:
            target_is_directory=target.isDirectory
        self._pathlibPath.symlink_to(str(target),target_is_directory)

    def is_dir(self)->bool:
        """
        Same as pathlib.Path.is_dir
        """
        return self._pathlibPath.is_dir()

    def is_mount(self)->bool:
        """
        Same as pathlib.Path.is_mount
        """
        return self._pathlibPath.is_mount() # type: ignore

    @property
    def suffix(self)->str:
        """
        Same as pathlib.Path.suffix
        """
        return self._pathlibPath.suffix

    def is_file(self)->bool:
        """
        Same as pathlib.Path.is_file
        """
        return self._pathlibPath.is_file()

    @property
    def exists(self)->CallableValue(bool): # type: ignore # pylint:disable=invalid-overridden-method
        """
        Return True if this file or directory exists, False otherwise
        """
        return self._pathlibPath.exists()

    def iterdir(self)->typing.Generator['FilePath',None,None]:
        """
        Same as pathlib.Path.iterdir
        """
        for pathlibPath in self._pathlibPath.iterdir():
            yield FilePath(pathlibPath)

    def read_text(self,
        encoding:typing.Optional[str]='utf-8',
        errors:typing.Optional[str]='ignore'
        )->str:
        """
        Same as pathlib.Path.read_text
        """
        return self._pathlibPath.read_text(encoding,errors)

    def write_text(self,
        data:typing.Any,
        encoding:typing.Optional[str]='utf-8',
        errors:typing.Optional[str]='ignore',
        newline:typing.Optional[str]=None
        )->int:
        """
        Same as pathlib.Path.write_text
        """
        if not isinstance(data,str):
            data=str(data)
        return self._pathlibPath.write_text(data,encoding,errors,newline)

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

    def makeDirs(self,
        relativePath:typing.Optional[FilePathCompatible]=None,
        inclusive:bool=True):
        """
        Make all directories exist leading up to this point

        :inclusive: if True, create this path as a directory as well
        """
        if relativePath is None:
            pth=self.absolute()
        else:
            pth=FilePath(relativePath,self).absolute()
        if not inclusive or self.exists:
            pth=pth.parent
        os.makedirs(str(pth))
    makedirs=makeDirs
    mkdirs=makeDirs
    makedir=makeDirs

    def mkdir(self,mode:int=0o777,parents:bool=False,exist_ok:bool=False):
        """
        DEPRECATED.

        The pathlib.Path function for this is completely
        different in its desgin (and not as nice).
        
        Use makeDir() instead.
        """
        msg="""
            DEPRECATED.

            The pathlib.Path function for this is completely
            different in its desgin (and not as nice).
            
            Use makeDir() instead.
            """
        warn(msg,DeprecationWarning,stacklevel=2)

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
    def parts(self # type: ignore
        )->typing.List[str]:
        """
        Parts of the path
        """
        return self._pathlibPath._parts.copy() # type: ignore # pylint: disable=protected-access

    @property
    def name(self)->str:
        """
        The final path component, if any.
        """
        return self.parts[-1]
    @name.setter
    def name(self,name:FilePathCompatible):
        """
        DEPRECATED.

        Don't know if this is intending to rename the
        object value, or the file itself.

        Either choose:
            self.parent/"otherName" # access a different file name
            self.renameFile("newName") # rename this file
        """
        msg="""
            DEPRECATED.

            Don't know if this is intending to rename the
            object value, or the file itself.

            Either choose:
                self.parent/"otherName" # access a different file name
                self.renameFile("newName") # rename this file
            """
        _=name
        warn(msg,DeprecationWarning,stacklevel=2)

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
            self._pathlibPath.lstat().st_mtime,
            tz=datetime.timezone.utc)

    def copy(self)->"FilePath": # type: ignore
        """
        DEPRECATED.

        This function is too ambiguious.
        You either meant:
            copyPath() to create a new path object
            copyFile() to copy file(s)
        so call that function, not this.
        """
        msg="""
            DEPRECATED.

            This function is too ambiguious.
            You either meant:
                copyPath() to create a new path object
                copyFile() to copy file(s)
            so call that function, not this.
            """
        warn(msg,DeprecationWarning,stacklevel=2)
        return self.copyPath()

    def copyPath(self)->"FilePath":
        """
        create a copy of this path
        """
        return self.__class__(self)

    def copyFile(self,
        destination:FilePathCompatible,
        overwrite:OverwriteOptions=False,
        recursive:bool=False
        )->"FilePath":
        """
        Copy this file to a new location

        :destination: the new location for the file
        :overwrite: whether or not to overwrite the destination if it already exists
        """
        import shutil
        destination=asFilePath(destination)
        if destination.exists() and not overwrite:
            raise FileExistsError(str(destination))
        if self.isDir:
            for c in self.children:
                if c.isDir:
                    # if it's not recursive, then we create the directory but not its contents
                    destination.makedirs(c.name)
                    if not recursive:
                        continue
                c.copyFile(destination/c.name,overwrite,recursive)
        else:
            if destination.exists():
                if overwrite=='newer':
                    if destination.lastModifiedTime>=self.lastModifiedTime:
                        return destination
                elif overwrite==('ignore','skip'):
                    return destination
                elif overwrite=='error':
                    raise FileExistsError(str(destination))
            shutil.copy2(str(self),str(destination))
        return destination
    copyFiles=copyFile

    def copyTree(self,
        destination:FilePathCompatible,
        overwrite:OverwriteOptions=False,
        recursive:bool=True
        )->"FilePath":
        """
        Recursively copy this file to a new location

        :destination: the new location for the file
        :overwrite: whether or not to overwrite the destination if it already exists
        """
        return self.copyFile(destination,overwrite,recursive)
    copytree=copyTree

    @property
    def isAbsolute(self)->bool:
        """
        Determine if this is an absolute path
        """
        return self._pathlibPath.is_absolute()

    def absolute(self)->"FilePath":
        """
        Same as pathlib.Path.absolute()
        """
        if self.isAbsolute:
            return self.copy()
        return FilePath(self._pathlibPath.absolute())

    def __hash__(self)->int:
        """
        Hashing function for adding to lookup dicts
        """
        return self.urlString.__hash__()

    def __str__(self)->str:
        return str(self._pathlibPath)

    def __repr__(self)->str:
        return str(self._pathlibPath)
FileUrl=FilePath
Filename=FilePath
FileName=FilePath


if __name__=='__main__':
    import sys
    filename=FileName('.')
    print(filename)
    print(filename.absolute())
    for c in filename.children:
        print(c)
    sys.exit(0)
