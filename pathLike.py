"""
A simple general-purpose path which could be applied to anything
(filenames, tree location, url, html dom, etc...)
"""
import typing
import urllib.parse
from .paramDict import ParamDict


class PathStep:
    """
    A single step in the path

    This consists of a name and optional parameters,
    for example, this path is technically valid
        http://fooblatz.com/this?a=10&b=11/that?a=20&b=30
    So the parameters would always be the same
    """

    def __init__(self,raw:str):
        self._name:str=''
        self.params:ParamDict=ParamDict()
        self._hash:typing.Optional[int]=None # type: ignore
        self.assign(raw)

    @property
    def name(self)->str:
        """
        the name of the path step
        """
        return self._name
    @name.setter
    def name(self,name:str)->None:
        self._name=name
        self._hash=None

    def assign(self,raw:str)->None:
        """
        Assign the value of this path step

        This will split out any parameters, such as
            name?a=1&b=2
        """
        self._hash=None
        parts=raw.split('?',1)
        self.name=urllib.parse.unquote(parts[0])
        self.params=ParamDict()
        if len(parts)>1:
            parts=parts[1].split('&')
            for part in parts:
                kv=[urllib.parse.unquote(x) for x in part.split('=',1)]
                if len(kv)<2:
                    kv.append('True')
                if kv[0] in self.params:
                    existing:typing.Union[None,str,typing.List[str]]=\
                        self.params.get(kv[0])
                    if existing is None:
                        self.params[kv[0]]=kv[1]
                    elif hasattr(existing,'__iter__')\
                        and not isinstance(existing,str):
                        existing.append(kv[1])
                    else:
                        self.params[kv[0]]=[existing,kv[1]]
                else:
                    self.params[kv[0]]=kv[1]

    def __hash__(self)->int: # type: ignore
        """
        get an order-independent hash of this item
        """
        if self._hash is None:
            hashStr=[self._name]
            for k,v in sorted(self.params.items()):
                hashStr.append(f'{k}={v}')
            self._hash=hash('&'.join(hashStr))
        return self._hash

    def __eq__(self,other:typing.Any)->bool:
        """
        Can compare to other PathStep or a simple str.

        If this has parameters, then the other must match
        all parameters as well!

        NOTE: this is immune to order, though.
            "x?a=1&b=2" == "x?b=2&a=1"
        """
        if isinstance(other,str):
            other=PathStep(other)
        elif not isinstance(other,PathStep):
            return False
        if self.name!=other.name:
            return False
        return hash(self)==hash(other)

    def __repr__(self)->str:
        return f'{urllib.parse.quote(self._name)}{self.params.queryString}'


class PathLike:
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
        p=Path("../clams",relativeTo="/home/~rthomas/crustaceans/oysters/").reduced()
        print(p) => "/home/~rthomas/crustaceans/clams"
    And this can be easily done with the + operator
        Path(r"c:\directory\wrong_dir")+r"..\file.txt"
        returns "c:\directory\file.txt"

    Change separators:
        p=Path("this|is|the|path",separators=('|'))
        p.separators=('/')
        print(p) => "this/is/the/path"

    Inheriting changes:
        base=Path("/home/fred/stuff")
        readme=Path("readme.txt",base,inheritChanges=True)
        print(readme) => "/home/fred/stuff/readme.txt"
        base.add("../other_stuff")
        print(readme) => "/home/fred/other_stuff/readme.txt"
        readme.stopInheritingChanges() # no longer watch for changes to base
        base.add("../stuff_i_dont_care_about")
        print(readme) => "/home/fred/other_stuff/readme.txt"
    """

    def __init__(self,
        path:typing.Optional["PathCompatible"],
        relativeTo:typing.Optional["PathCompatible"]=None,
        separators:typing.Sequence[str]='/\\',
        inheritChanges:bool=False,
        maxParentLevels:typing.Optional[int]=None,
        maxChildLevels:typing.Optional[int]=None
        ):
        """
        :separators: all separators that can denote a path break
            the first separator is used as the join
        :inheritChanges: if True, changes to this will result in changes to the
            derived path.  If False (default) the returned path is new.
        :maxParentLevels: the maximum number of parent levels to allow
            in a relative path - for security, recommend setting this to 0
        :maxChildLevels: the maximum number of child levels to allow
            in a relative path
        """
        self._pathSteps:typing.List[PathStep]=[]
        self.separators:typing.Sequence[str]=separators
        self._boundParentPath:typing.Optional["PathLike"]=None
        if path is not None:
            if isinstance(relativeTo,PathLike) and inheritChanges:
                self._boundParentPath=relativeTo
                self.assign(path)
            else:
                self.assign(path,relativeTo,maxParentLevels,maxChildLevels)

    @property
    def params(self)->ParamDict:
        """
        The params part of the url
        """
        return self._pathSteps[-1].params

    def assign(self,
        path:"PathCompatible",
        relativeTo:typing.Optional["PathCompatible"]=None,
        maxParentLevels:typing.Optional[int]=None,
        maxChildLevels:typing.Optional[int]=None):
        """
        Assign the value of this path

        :maxParentLevels: the maximum number of parent levels to allow
            in a relative path - for security, recommend setting this to 0
        :maxChildLevels: the maximum number of child levels to allow
            in a relative path
        """
        # munch on relativeTo first, in case they passed in self
        if relativeTo is not None and (
            not isinstance(relativeTo,PathLike)\
            or id(relativeTo)==id(self)):
            relativeTo=PathLike(relativeTo,
                maxParentLevels=maxParentLevels,maxChildLevels=maxChildLevels)
        # make path always a string
        if not isinstance(path,str):
            if isinstance(path,PathLike):
                path=str(path)
            elif hasattr(path,'__iter__'):
                path=self.separators[0].join([str(ps) for ps in path])
            else:
                path=str(path)
        # split it out
        if len(self.separators)>1:
            for s in self.separators[1:]:
                path=path.replace(s,self.separators[0])
        pathParts=path.split(self.separators[0])
        # assign it
        if relativeTo is None or self._firstPathIsAbsolute(pathParts[0]):
            # either there is nothing it is relative to
            # or it is absolute and it will clobber relativeTo anyway
            self._pathSteps=[PathStep(ps) for ps in pathParts]
        else:
            # add relativeTo first, then the path
            # TODO: support maxParentLevels and maxChildLevels
            self._pathSteps=[ps for ps in relativeTo]
            self._pathSteps.extend([PathStep(ps) for ps in pathParts])

    @staticmethod
    def _firstPathIsAbsolute(first:str)->bool:
        """
        This is defined as starting with either
        '/' or 'something:/' or 'x|/'
        """
        return (not first)\
            or first.endswith(':')\
            or (len(first)==2 and first[1]=='|')

    @property
    def isAbsolute(self)->bool:
        """
        This is defined as starting with either
        '/' or 'something:/' or 'x|/'
        """
        return len(self)>0 and self._firstPathIsAbsolute(str(self[0]))
    @property
    def isRelative(self)->bool:
        """
        This is defined as not starting with either
        '/' or 'something:/' or 'x|/'
        """
        return self.isAbsolute is False

    def copy(self)->"PathLike":
        """
        Create a copy of this path
        """
        return PathLike(self,separators=self.separators)

    @property
    def pathSteps(self)->typing.Iterable[PathStep]:
        """
        steps in the path
        """
        return iter(self._pathSteps)
    @pathSteps.setter
    def pathSteps(self,pathSteps:typing.Iterable[PathStep])->None:
        self._pathSteps=[ps for ps in pathSteps]

    def makeRelativeTo(self,relativeTo:"PathCompatible")->"PathLike":
        """
        Get copy of this path, as it is re relative to another path

        That is, if we are "/home/bob/a/b" and relativeTo is "/home/bob/a/c"
        this would return "../b" because that is
        the relative path to get from "/home/bob/a/c" to "/home/bob/a/b"
        """
        raise NotImplementedError()
    getRelativeTo=makeRelativeTo
    makeRelative=makeRelativeTo

    def makeRelativeFrom(self,fromPath:"PathCompatible")->"PathLike":
        """
        Get a relative path from another path to this one
        """
        return asPath(fromPath).makeRelativeTo(self)
    getRelativeFrom=makeRelativeFrom

    def getRelative(self,
        relative:"PathCompatible",
        inheritChanges:bool=False,
        maxParentLevels:typing.Optional[int]=None,
        maxChildLevels:typing.Optional[int]=None
        )->'PathLike':
        """
        Get a path relative to this one

        :inheritChanges: if True, changes to this will result in changes to the
            derived path. If False(default) the returned path is a new object.
        :maxParentLevels: the maximum number of parent levels to allow
            in a relative path - for security, recommend setting this to 0
        :maxChildLevels: the maximum number of child levels to allow
            in a relative path

        NOTE: given existing path x, these are equivalent:
            1) y=Path(relativePath,x)
            2) y=x.getRelative(relativePath)
            3) y=x+relativePath
        """
        return PathLike(relative,self,separators=self.separators,
            inheritChanges=inheritChanges,
            maxParentLevels=maxParentLevels,
            maxChildLevels=maxChildLevels)
    get=getRelative

    def __add__(self,relative:"PathCompatible")->'PathLike':
        """
        Get a new path relative to this one

        NOTE: given existing path x, these are equivalent:
            1) y=Path(relativePath,x)
            2) y=x.getRelative(relativePath)
            3) y=x+relativePath
        """
        return PathLike(relative,self,separators=self.separators)

    def append(self,path:"PathCompatible")->None:
        """
        adjust this path by another path
        """
        self.assign(path,self)
        self.reduce()
    cd=append
    chdir=append
    add=append

    def reduce(self)->None:
        """
        Reduce this path by removing unnecessary elements
            eg Path("./x//y/z/../") => "./x/y"
        """
        first=True
        ret:typing.List[PathStep]=[]
        for ps in self._pathSteps:
            sps=str(ps)
            if first or sps not in ('','.'):
                first=False
                if sps=='..' and ret:
                    ret.pop()
                else:
                    ret.append(ps)
        self._pathSteps=ret

    def reduced(self)->"PathLike":
        """
        get a reduced copy of this path
        """
        p=self.copy()
        p.reduce()
        return p

    def __iter__(self)->typing.Generator[PathStep,None,None]:
        if self._boundParentPath is not None:
            yield from self._boundParentPath
        yield from self._pathSteps

    @typing.overload
    def __getitem__(self,idx:slice)->typing.Iterable[PathStep]:
        ...
    @typing.overload
    def __getitem__(self,idx:typing.Union[int,str])->PathStep:
        ...
    def __getitem__(self,idx:typing.Union[int,str,slice]
        )->typing.Union[PathStep,typing.Iterable[PathStep]]:
        """access like [str] or dict"""
        if isinstance(idx,str):
            return getattr(self,idx)
        if self._boundParentPath is not None:
            parentLen=len(self._boundParentPath)
            if isinstance(idx,int):
                if idx<parentLen:
                    return self._boundParentPath[idx]
                return self._pathSteps[idx-parentLen]
            elif idx.stop<parentLen:
                # slice is entirely in the bound parent
                return self._boundParentPath[idx]
            elif idx.start>parentLen:
                # slice is entirely within our data
                return self._pathSteps[idx.start-parentLen:idx.stop-parentLen]
            ret=self._pathSteps[idx.start:]
            ret.extend(self._pathSteps[0:idx.stop-parentLen])
            return ret
        # the simple condition, we have no bound parent to worry about
        return self._pathSteps[idx]

    def __len__(self)->int:
        """access like [str]"""
        if self._boundParentPath is None:
            return len(self._pathSteps)
        return len(self._boundParentPath)+len(self._pathSteps)

    #def __getattr__(self,__name:str) -> typing.Any:
    #    """
    #    where possible, access like an object member
    #    """
    #    if __name in ('_pathSteps',) and not self._pathSteps:
    #        return ''
    #    return getattr(self._pathSteps,__name)

    def matchesPath(self,path:'PathCompatible')->bool:
        """
        Determine if another path matches this path
        """
        path=asPath(path)
        if path.isRelative!=self.isRelative:
            return False
        if len(path)!=len(self):
            return False
        for a,b in zip(path,self):
            if a!=b:
                return False
        return True

    def __eq__(self,other:typing.Any)->bool:
        """
        Comparison operator is based on other.matchesPath(self)
        """
        return hasattr(other,'matchesPath') and other.matchesPath(self)

    def __hash__(self)->int:
        return hash(str(self))

    def startswith(self,path:'PathCompatible')->bool:
        """
        similar to str.startswith()
        """
        for a,b in zip(asPath(path),self):
            if a!=b:
                return False
        return True

    def reversed(self)->"PathLike":
        """
        Get a reversed copy of the path

        Analogous to list.reversed()
        """
        r=self.copy()
        r.reverse()
        return r

    def reverse(self):
        """
        Reverse the path

        (this will break the link for any
        inherited changes)
        """
        self.stopInheritingChanges()
        self._pathSteps.reverse()

    def stopInheritingChanges(self)->None:
        """
        If this path is inheriting changes, will
        break the link and freeze the path to
        whatever the bound path is at the present time.
        """
        if self._boundParentPath is not None:
            self._pathSteps=[step for step in self]
            self._boundParentPath=None

    def endswith(self,path:'PathCompatible')->bool:
        """
        similar to str.endswith()
        """
        path=asPath(path)
        for a,b in zip(path.reversed(),self.reversed()):
            if a!=b:
                return False
        return True

    def matchesPathAt(self,subPath:'PathCompatible',atPosition:int)->bool:
        """
        check to see if it matches a particular sub-path at the specified point
        """
        subPath=asPath(subPath)
        if subPath and len(subPath)<=len(self)-atPosition:
            for ours,theirs in zip(
                subPath,
                self[atPosition:atPosition+len(subPath)]):
                if ours!=theirs:
                    return False
            return True
        return False

    def contains(self,subPath:'PathCompatible')->bool:
        """
        check to see if it contains a particular sub-path
        """
        subPath=asPath(subPath)
        if subPath:
            for i,step in enumerate(self):
                if step==subPath[0]:
                    if self.matchesPathAt(subPath,i):
                        return True
        return False

    def __repr__(self)->str:
        return self.separators[0].join([str(step) for step in iter(self)])


PathCompatible=typing.Union[str,PathLike,typing.Iterable[str]]
def asPath(path:PathCompatible)->PathLike:
    """
    Always return a Path
    if path is already a Path, simply return it
    otherwise create a Path from it
    """
    if not isinstance(path,PathLike):
        path=PathLike(path)
    return path

class HasMatchesPath(typing.Protocol):
    """
    Any class that has a matchesPath() function
    """
    def matchesPath(self,path:PathCompatible)->bool:
        """
        Determine if this object matches the given path
        """
        return True

TreePath=PathLike
