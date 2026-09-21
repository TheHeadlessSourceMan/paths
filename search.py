"""
Tools to search paths
"""
import typing
import enum
import os
import re
from pathlib import Path
from paths.urlTyping import URLCompatible,asURL
import stringTools


osIsCaseSensitive=not os.name=='nt'


# Common file extension types
C_SOURCE_EXTENSIONS=('.c',)
C_HEADER_EXTENSIONS=('.h',)
C_FILE_EXTENSIONS=C_SOURCE_EXTENSIONS+C_HEADER_EXTENSIONS
CPP_SOURCE_EXTENSIONS=C_SOURCE_EXTENSIONS+('.cpp','.cxx')
CPP_HEADER_EXTENSIONS=C_HEADER_EXTENSIONS+('.hpp','.hxx')
CPP_FILE_EXTENSIONS=CPP_SOURCE_EXTENSIONS+CPP_HEADER_EXTENSIONS
PYTHON_FILE_EXTENSIONS=('.py',)
JAVA_FILE_EXTENSIONS=('.java',)
JAVASCRIPT_EXTENSIONS=('.js',)
TYPESCRIPT_EXTENSIONS=('.ts',)
JSX_EXTENSIONS=('.jsx','.tsx')
ALL_JAVASCRIPT_EXTENSIONS=\
    JAVA_FILE_EXTENSIONS+\
    TYPESCRIPT_EXTENSIONS+\
    JSX_EXTENSIONS
SOURCE_CODE_FILE_EXTENSIONS=\
    CPP_FILE_EXTENSIONS+\
    PYTHON_FILE_EXTENSIONS+\
    JAVA_FILE_EXTENSIONS+\
    ALL_JAVASCRIPT_EXTENSIONS

JPEG_EXTENSIONS=('.jpg','.jpe','.jpeg','.jfif')
RASTER_IMAGE_EXTENSIONS=\
    JPEG_EXTENSIONS+\
    ('.png','.bmp','.gif')
VECTOR_IMAGE_EXTENSIONS=('.svg','.dxf')
IMAGE_EXTENSIONS=\
    RASTER_IMAGE_EXTENSIONS+\
    VECTOR_IMAGE_EXTENSIONS

MPEG_EXTENSIONS=('.mpg','.mpe','.mpeg','.mp4','.mp5')
VIDEO_EXTENSIONS=\
    MPEG_EXTENSIONS+\
    ('.avi','.vp8','.flv')


def isFileOfType(
    filename:typing.Union[str,Path,URLCompatible],
    extensions:typing.Iterable[str]
    )->bool:
    """
    Determine if a file matches one of a set of extensions
    """
    from paths import URL
    if isinstance(filename,Path):
        return filename.suffix in extensions
    if not isinstance(filename,URL):
        filename=URL(filename)
    return filename.extension in extensions


def isCodeFile(
    filename:typing.Union[str,Path,URLCompatible]
    )->bool:
    """
    Determine if a file is source code of some kind
    """
    return isFileOfType(filename,SOURCE_CODE_FILE_EXTENSIONS)


def isCppFile(
    filename:typing.Union[str,Path,URLCompatible]
    )->bool:
    """
    Determine if a file is c/c++ source code
    """
    return isFileOfType(filename,CPP_FILE_EXTENSIONS)


def findDirectoriesContainingFileTypes(
    parentDirs:typing.Union[str,Path,typing.Iterable[typing.Union[str,Path]]],
    fileExtensions:typing.Iterable[str],
    onlyHighestLevel:bool=False,
    )->typing.Generator[Path,None,None]:
    """
    Find all directories containing specified file types
    """
    if isinstance(parentDirs,str):
        yield from findDirectoriesContainingFileTypes(
            Path(parentDirs),fileExtensions,onlyHighestLevel)
    elif isinstance(parentDirs,Path):
        tape=[]
        matchesDir=False
        for item in parentDirs.iterdir():
            if item.is_dir():
                tape.append(item)
            elif isFileOfType(item,fileExtensions):
                matchesDir=True
        if matchesDir:
            yield parentDirs
            if not onlyHighestLevel:
                yield from findDirectoriesContainingFileTypes(
                    tape,fileExtensions,onlyHighestLevel)
        elif tape:
            yield from findDirectoriesContainingFileTypes(
                tape,fileExtensions,onlyHighestLevel)
    else:
        for d in parentDirs:
            yield from findDirectoriesContainingFileTypes(
                d,fileExtensions,onlyHighestLevel)


def findSourceCodeDirectories(
    parentDirs:typing.Union[str,Path,typing.Iterable[typing.Union[str,Path]]],
    sourceCodeExtensions:typing.Iterable[str]=SOURCE_CODE_FILE_EXTENSIONS,
    onlyHighestLevel:bool=False
    )->typing.Generator[Path,None,None]:
    """
    Find all directories containing source code file types
    """
    yield from findDirectoriesContainingFileTypes(
        parentDirs,sourceCodeExtensions,onlyHighestLevel)


def findImageDirectories(
    parentDirs:typing.Union[str,Path,typing.Iterable[typing.Union[str,Path]]],
    imageExtensions:typing.Iterable[str]=IMAGE_EXTENSIONS,
    onlyHighestLevel:bool=False
    )->typing.Generator[Path,None,None]:
    """
    Find all directories containing image file types
    """
    yield from findDirectoriesContainingFileTypes(
        parentDirs,imageExtensions,onlyHighestLevel)


def findMakefileDirectories(
    parentDirs:typing.Union[str,Path,typing.Iterable[typing.Union[str,Path]]],
    onlyHighestLevel:bool=False
    )->typing.Generator[Path,None,None]:
    """
    Find all directories containing makefiles
    """
    if isinstance(parentDirs,str):
        yield from findMakefileDirectories(
            Path(parentDirs),onlyHighestLevel)
    elif isinstance(parentDirs,Path):
        tape=[]
        matchesDir=False
        for item in parentDirs.iterdir():
            if item.is_dir():
                tape.append(item)
            elif item.name.lower() in ('make','makefile') \
                or item.suffix in ('.mak',):
                #
                matchesDir=True
        if matchesDir:
            yield parentDirs
            if not onlyHighestLevel:
                yield from findMakefileDirectories(
                    tape,onlyHighestLevel)
        elif tape:
            yield from findMakefileDirectories(
                tape,onlyHighestLevel)
    else:
        for d in parentDirs:
            yield from findMakefileDirectories(
                d,onlyHighestLevel)


class MatchType(enum.Enum):
    """
    Used to indicate what type of match a string represents
    """
    SimpleStringMatch=0
    GlobMatch=1
    PythonRegexMatch=2


def findFilenamesOfType(
    extensions:typing.Union[None,str,typing.Iterable[str]]=None,
    startDirs:typing.Union[
        Path,str,
        typing.Iterable[typing.Union[Path,str]]]='.',
    recursive:bool=True
    )->typing.Generator[Path,None,None]:
    """
    Depth-first file search.

    Yields only files, never directories.

    :startDirs: one or more directories to start searching at
        if not specified, use working directory
    :extensions: limit results to one or more extensions
        (extensions must include the dot, for instance [".c",".cpp"])
    :recursive: default=true
    """
    tape:typing.List[Path]
    if isinstance(startDirs,Path):
        if not startDirs.is_dir():
            return
        tape=[startDirs]
    elif isinstance(startDirs,str):
        startDirs=Path(startDirs)
        if not startDirs.is_dir():
            return
        tape=[startDirs]
    else:
        tape=[Path(startDir) for startDir in startDirs]
    if isinstance(extensions,str):
        extensions=(extensions,)
    for currentDir in tape:
        for filename in currentDir.iterdir():
            if filename.is_dir():
                if recursive:
                    tape.append(filename) # noqa: E501 # pylint: disable=modified-iterating-list
            elif extensions is None or filename.suffix in extensions:
                yield filename


def globToRegexStr(glob:str)->str:
    """
    Convert a Unix-style glob pattern to a regular expression string.

    Example:
        '*.txt'      -> '^.*\\.txt$'
        '**/*.py'    -> '^(?:.*/)?[^/]*\\.py$'
        'data?.csv'  -> '^data.{1}\\.csv$'
    """
    ret=['^'] # TODO: Do I want to do this, or .*
    for c in glob:
        if c=='*':
            if ret and ret[-1] in ('[^/]*','.*'):
                # last character was *, so overwrite it as **
                ret[-1]='.*'
            else:
                ret.append('[^/]*')
        elif c=='?':
            # ? is single character match
            ret.append('.')
        else:
            ret.append(re.escape(c))
    ret.append('$')
    return ''.join(ret)


def globToRegex(
    glob:str,
    caseSensitive:bool=osIsCaseSensitive
    )->typing.Pattern[str]:
    """
    Create a regex from a glob expression
    """
    flags=0
    if not caseSensitive:
        flags|=re.IGNORECASE
    return re.compile(globToRegexStr(glob),flags)


class FileMatcher:
    """
    A general-purpose file matcher
    """

    def __init__(self,
        match:typing.Union[None,str,typing.Pattern]=None,
        matchType:MatchType=MatchType.SimpleStringMatch,
        caseSensitive:bool=osIsCaseSensitive,
        extensions:typing.Union[None,str,typing.Iterable[str]]=None,
        ):
        """ """
        self._match=match
        self._matchType=matchType
        self._caseSensitive=caseSensitive
        self._extensions=extensions
        self._regex:typing.Optional[typing.Pattern[str]]=None

    @property
    def regex(self)->typing.Pattern[str]:
        """
        Get/set this match pattern as a python regular expressions
        """
        if self._regex is None:
            regexStrs=[]
            if isinstance(self._match,re.Pattern):
                self._matchType=MatchType.PythonRegexMatch
                if not self._extensions:
                    self._regex=self._match
                    return self._regex
                regexStrs.append(self._match.pattern)
            if self._matchType==MatchType.PythonRegexMatch:
                if self._match is not None \
                    and isinstance(self._match,str) \
                    and str(self._match).strip():
                    regexStrs.append('.*/'+self._match)
            elif self._matchType==MatchType.GlobMatch:
                if self._match is not None \
                    and isinstance(self._match,str) \
                    and str(self._match).strip():
                    regexStrs.append(globToRegexStr(self._match))
            elif self._matchType==MatchType.SimpleStringMatch:
                if self._match is not None \
                    and isinstance(self._match,str) \
                    and str(self._match).strip():
                    regexStrs.append('.*/'+re.escape(self._match))
            else:
                raise NotImplementedError
            if self._extensions:
                extns=[]
                for ext in self._extensions:
                    if ext.startswith('.'):
                        ext=ext[1:]
                    ext=f'(.*[.]{ext}$)'
                    extns.append(ext)
                if len(extns)>1:
                    regexStrs.append('('+('|'.join(extns))+')')
                elif len(extns)==1:
                    regexStrs.append(extns[0])
            if not regexStrs:
                regexStr='.*'
            elif len(regexStrs)==1:
                regexStr=regexStrs[0]
            else:
                regexStr='&'.join([f'({s})' for s in regexStrs])
            self.regex=regexStr
        return self._regex # type: ignore
    @regex.setter
    def regex(self,regex:typing.Union[str,typing.Pattern[str]]):
        if isinstance(regex,str):
            flags=0
            if not self._caseSensitive:
                flags|=re.IGNORECASE
            regex=re.compile(regex,flags)
        self._regex=regex

    def matches(self,filename:typing.Union[str,Path,URLCompatible])->bool:
        """
        Determine if a filename matches these criteria
        """
        if not isinstance(filename,str):
            if isinstance(filename,Path):
                filename=str(filename)
            else:
                filename=str(asURL(filename))
        return self.regex.match(filename) is not None
    __eq__=matches #type: ignore


class FileWalker:
    """
    A generator to traverse over a set of files.
    """

    def __init__(self,
        startDirs:typing.Union[
            Path,str,
            typing.Iterable[typing.Union[Path,str]]]='.',
        recursive:bool=True,
        depthFirst:bool=False,
        yeildDirectories:bool=False):
        """ """
        if isinstance(startDirs,(str,Path)):
            startDirs=(startDirs,)
        if not startDirs:
            startDirs=['.']
        self._tape:typing.List[Path]=[Path(p) for p in startDirs]
        self._visited:typing.Set[Path]=set()
        self._currentDirectory:typing.Generator[Path]=[] # type: ignore
        self.recursive=recursive
        self.depthFirst=depthFirst
        self.yeildDirectories=yeildDirectories

    def __iter__(self):
        return self

    def __next__(self)->Path:
        while True:
            while not self._currentDirectory:
                while not self._tape:
                    raise StopIteration
                self._currentDirectory=self._tape.pop(0).iterdir()
            try:
                filename=next(self._currentDirectory)
            except StopIteration:
                # generators are always truthy, so reset explicitly
                # or the outer loop never advances to the next tape entry
                self._currentDirectory=[]
                continue
            if filename in self._visited:
                continue
            self._visited.add(filename)
            if filename.is_dir():
                if self.recursive:
                    if self.depthFirst:
                        self._tape.insert(0,filename)
                    else:
                        self._tape.append(filename)
                if self.yeildDirectories:
                    return filename
            else:
                return filename


def findFiles(
    match:typing.Union[None,str,typing.Pattern[str]]=None,
    matchType:MatchType=MatchType.SimpleStringMatch,
    extensions:typing.Union[None,str,typing.Iterable[str]]=None,
    startDirs:typing.Union[
        Path,str,
        typing.Iterable[typing.Union[Path,str]]]='.',
    recursive:bool=True,
    depthFirst:bool=False,
    caseSensitive:bool=osIsCaseSensitive
    )->typing.Generator[Path,None,None]:
    """
    Versitile, general-purpose file search
    """
    matcher=FileMatcher(match,matchType,caseSensitive,extensions)
    for file in FileWalker(startDirs,recursive,depthFirst):
        if matcher==file:
            yield file
find=findFiles
search=findFiles


def fileFilter(
    src:typing.Union[str,Path,typing.Iterable[typing.Union[str,Path]]],
    match:typing.Optional[stringTools.MatchLike]=None,
    matchStringAs:stringTools.MatchStringAs="exact",
    ignorecase:bool=False,
    includeExtension:bool=False,
    includePath:bool=False
    )->typing.Iterable[Path]:
    """
    Simply filter a list of files without asking where it came
    from or if it even exists.

    This uses the stringTools stringFilter for speed and versatility.
    """
    if isinstance(src,(str,Path)):
        src=(src,)
    t:typing.List[typing.Tuple[str,Path]]=[]
    for s in src:
        if not isinstance(s,Path):
            p=Path(s)
        else:
            p=s
        if match is None:
            yield p
            continue
        if includePath:
            s=str(p.absolute())
        elif includeExtension:
            s=p.name
        else:
            s=p.stem
        t.append((s,p))
    for _,p in stringTools.tupleStringFilter(t,match,matchStringAs,ignorecase):
        yield p


def cmdline(args:typing.Iterable[str])->int:
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    printHelp=False
    match=""
    recursive=False
    matchType=MatchType.GlobMatch
    extensions:typing.List[str]=[]
    caseSensitive:bool=osIsCaseSensitive
    startDirs:typing.List[str]=[]
    depthFirst:bool=False
    for arg in args:
        if arg.startswith('-'):
            kw=arg.split('=',1)
            k=kw[0].lower()
            if k in ('-h','--help'):
                printHelp=True
            elif k.startswith('--ext') and len(kw)>1:
                extensions.extend([
                    s.strip() for s in kw[1].replace(';',',').split(',')])
            elif k in ('--case','--casesensitive'):
                if len(kw)>1 and kw[1]:
                    caseSensitive=kw[1][0].lower() in ('y','t','1')
                else:
                    caseSensitive=True
            elif k in ('-r','--r'):
                if len(kw)>1 and kw[1]:
                    recursive=kw[1][0].lower() in ('y','t','1')
                else:
                    recursive=True
            elif k in ('--re','--regex'):
                matchType=MatchType.PythonRegexMatch
            elif k in ('--depth','--depthfirst','--deapth','--deapthfirst'):
                if len(kw)>1 and kw[1]:
                    depthFirst=kw[1][0].lower() in ('y','t','1')
                else:
                    depthFirst=True
        else:
            if match:
                startDirs.append(match)
            match=arg
    if printHelp:
        print("USAGE: search.py [flags] [in_dir ...] [match]")
        print("FLAGS:")
        print("  -h ................. print this help")
        print("  --help ............. print this help")
        print("  -r[=y/n] ........... recursive")
        print("  --re[gex] .......... match by regex")
        print("  --depth[first][=y/n] ....... perform depth-first search")
        print("  --ext[ension[s]]=e1,e2,e3 .. match by extensions")
        print("  --case[sensitive][=y/n] .... match case sensitivity")
        return 1
    for f in findFiles(match,matchType,extensions,
        startDirs,recursive,depthFirst,caseSensitive):
        print(f.absolute())
    return 0


if __name__=='__main__':
    import sys
    sys.exit(cmdline(sys.argv[1:]))
