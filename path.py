"""
A simple general-purpose path which could be applied to anything
(filenames, tree location, url, html dom, etc...)
"""
import typing


class Path:
    r"""
    A simple general-purpose path which could be applied to anything
    (filenames, tree location, url, html dom, etc...)

    Supports:
        any combination of "\" and "/" as the path separator
        "." and ".."

    Can be accessed like an array of path elements:
        p=Path("/a/b/c")
        p[1]="B"
        print(p) => "/a/B/c"

    Can be relative to another path:
        p=Path("../clams",relativeTo="/home/~rthomas/crustations/oysters/").reduced()
        print(p) => "/home/~rthomas/crustations/clams"
    And this can be easily done with the + operator
        Path(r"c:\directory\wrongdir")+r"..\file.txt" => "c:\directory\file.txt"

    Change separators:
        p=Path("this|is|the|path",separators=('|'))
        p.separators=('/')
        print(p) => "this/is/the/path"
    """

    def __init__(self,
        path:typing.Optional["PathCompatible"],
        relativeTo:typing.Optional["PathCompatible"]=None,
        separators:typing.Sequence[str]='/\\'):
        """
        :separators: all separators that can denote a path break
            the first separator is used as the join
        """
        self._pathElements:typing.List[str]=[]
        self.separators:typing.Sequence[str]=separators
        if path is not None:
            self.assign(path,relativeTo)

    def assign(self,
        path:"PathCompatible",
        relativeTo:typing.Optional["PathCompatible"]=None):
        """
        Assign the value of this path
        """
        if not isinstance(path,str):
            if isinstance(path,Path):
                path=str(path)
            elif hasattr(path,'__iter__'):
                path=self.separators[0].join(path)
            else:
                path=str(path)
        if relativeTo is not None and relativeTo:
            self.assign(path)
            if not self.isAbsolute:
                if not isinstance(relativeTo,Path):
                    relativeTo=Path(relativeTo)
                # prepend the relativeTo path before this one
                current=self._pathElements
                self._pathElements=list(relativeTo._pathElements)
                self._pathElements.extend(current)
        else:
            if len(self.separators)>1:
                for s in self.separators[1:]:
                    path=path.replace(s,self.separators[0])
            self._pathElements=path.split(self.separators[0])

    @property
    def isAbsolute(self)->bool:
        """
        This is defined as starting with either
        '/' or '*:/'
        """
        if self._pathElements: 
            if not self._pathElements[0] or self._pathElements[0][-1]==':':
                return True
        return False

    def copy(self)->"Path":
        """
        Create a copy of this path
        """
        return Path(self,separators=self.separators)

    def getRelative(self,relative:"PathCompatible")->'Path':
        """
        Get a path relative to this one

        NOTE: given existing path x, these are equivilent:
            1) y=Path(relativePath,x)
            2) y=x.getRelative(relativePath)
            3) y=x+relativePath
        """
        return Path(relative,self,separators=self.separators)
    get=getRelative

    def __add__(self,relative:"PathCompatible")->'Path':
        """
        Get a path relative to this one

        NOTE: given existing path x, these are equivilent:
            1) y=Path(relativePath,x)
            2) y=x.getRelative(relativePath)
            3) y=x+relativePath
        """
        return Path(relative,self,separators=self.separators)

    def reduce(self)->None:
        """
        Reduce this path by removing unnecessary elements
            eg Path("./x//y/z/../") => "./x/y"
        """
        first=True
        ret:typing.List[str]=[]
        for el in self._pathElements:
            if first or el not in ('','.'):
                first=False
                if el=='..' and ret:
                    ret.pop()
                else:
                    ret.append(el)
        self._pathElements=ret

    def reduced(self)->"Path":
        """
        get a reduced copy of this path
        """
        p=self.copy()
        p.reduce()
        return p

    def __iter__(self)->typing.Iterator[str]:
        return iter(self._pathElements)

    @typing.overload
    def __getitem__(self,idx:slice)->typing.Iterable[str]: ...
    @typing.overload
    def __getitem__(self,idx:typing.Union[int,str])->str: ...
    def __getitem__(self,idx:typing.Union[int,str,slice])->typing.Union[str,typing.Iterable[str]]:
        """access like [str] or dict"""
        if isinstance(idx,str):
            return getattr(self,idx)
        return self._pathElements[idx]
    typing.SupportsIndex

    def __len__(self)->int:
        """access like [str]"""
        return len(self._pathElements)

    def __getattr__(self, __name: str) -> typing.Any:
        """
        where possible, access like an object member
        """
        return getattr(self._pathElements,__name)

    def matchesPath(self,path:'PathCompatible')->bool:
        """
        Determine if another path matches this path
        """
        path=asPath(path)
        if len(path)!=len(self):
            return False
        for a,b in zip(path,self):
            if a!=b:
                return False
        return True

    def __equ__(self,other:typing.Any)->bool:
        """
        Comparison operator is based on other.matchesPath(self)
        """
        return hasattr(other,'matchesPath') and other.matchesPath(self)

    def __repr__(self)->str:
        return self.separators[0].join(self._pathElements)


PathCompatible=typing.Union[str,Path,typing.Iterable[str]]
def asPath(path:PathCompatible)->Path:
    if not isinstance(path,Path):
        path=Path(path)
    return path

class HasMatchesPath(typing.Protocol):
    def matchesPath(self,path:PathCompatible)->bool:
        ...

TreePath=Path
