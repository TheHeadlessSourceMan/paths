"""
A simple path which could be applied to anything
(filenames, tree location, url, html dom, etc...)
"""
import typing


class Path:
    """
    A simple path which could be applied to anything
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
    """

    def __init__(self,
        path:typing.Optional["PathCompatible"],
        relativeTo:typing.Optional["PathCompatible"]=None):
        """
        """
        self._pathElements:typing.List[str]=[]
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
                path='/'.join(path)
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
            self._pathElements=path.replace('\\','/').split('/')

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
        return Path(self)

    def getRelative(self,relative:"PathCompatible"):
        """
        Get a path relative to this one
        """
        return Path(relative,self)
    get=getRelative

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

    def __iter__(self)->typing.Iterable[str]:
        return iter(self._pathElements)

    def __getattr__(self, __name: str) -> typing.Any:
        return getattr(self._pathElements,__name)

    def __repr__(self)->str:
        return '/'.join(self._pathElements)


PathCompatible=typing.Union[str,Path,typing.Iterable[str]]
def asPath(path:PathCompatible)->Path:
    if not isinstance(path,Path):
        path=Path(path)
    return path

TreePath=Path
