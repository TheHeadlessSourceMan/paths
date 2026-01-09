"""
A list of file locations
"""
import typing
from .fileLocation import FileLocation,FileLocationCompatible,asFileLocation
from . import UrlCompatible,asUrl,isFileLocationCompatible


FileLocationSetCompatible=typing.Union[
    FileLocationCompatible,typing.Iterable[FileLocationCompatible]]
FileLocationListCompatible=FileLocationSetCompatible
FileLocationsCompatible=FileLocationSetCompatible
UrlLocationSetCompatible=FileLocationSetCompatible
UrlLocationListCompatible=FileLocationSetCompatible
UrlLocationsCompatible=FileLocationSetCompatible

def asFileLocationSet(files:FileLocationListCompatible)->"FileLocationSet":
    """
    Always get a FileLocationList.  If it already is one, simply return it.
    """
    if isinstance(files,FileLocationList):
        return files
    return FileLocationList(files)
asFileLocationList=asFileLocationSet
asFileLocations=asFileLocationSet
asUrlLocationSet=asFileLocationSet
asUrlLocationList=asFileLocationSet
asUrlLocations=asFileLocationSet


def isFileLocationSetCompatible(something:typing.Any)->bool:
    """
    Check to see if something is compatible
    with a list of file locations
    """
    if isinstance(something,FileLocationSet):
        return True
    if isFileLocationCompatible(something):
        return True
    if hasattr(something,'__iter__'):
        for x in something:
            return isFileLocationCompatible(x)
    return False
isFileLocationListCompatible=isFileLocationSetCompatible
isFileLocationsCompatible=isFileLocationSetCompatible
isUrlLocationListCompatible=isFileLocationSetCompatible
isUrlLocationListCompatible=isFileLocationSetCompatible
isUrlLocationsCompatible=isFileLocationSetCompatible


class FileLocationSet:
    """
    A set of file locations
    """
    def __init__(self,
        files:typing.Optional[FileLocationListCompatible]=None):
        """ """
        self._locations:typing.Set[FileLocation]=set()
        if files is not None:
            self.append(files)

    def clear(self)->None:
        """
        Clear out the set of locations
        """
        self._locations=set()

    def copy(self)->'FileLocationSet':
        """
        Create a copy of this set
        """
        return FileLocationSet(self)

    def assign(self,
        files:typing.Optional[FileLocationListCompatible]=None
        )->None:
        """
        Assign all values
        """
        self.clear()
        if files is not None:
            self.append(files)

    def append(self,
        fileLocations:typing.Optional[FileLocationListCompatible]=None
        )->None:
        """
        Assign more values
        """
        if fileLocations is not None:
            if isFileLocationCompatible(fileLocations):
                self._locations.add(
                    FileLocation(fileLocations)) # type: ignore
            else:
                for fileLocation in fileLocations: # type: ignore
                    self._locations.add(
                        FileLocation(fileLocation))
    add=append
    extend=append

    def remove(self,
        removeLocations:typing.Optional[FileLocationListCompatible]=None
        )->None:
        """
        Remove everything that contains the given fileLocations

        NOTE: this will also crop existing locations. For instance:
            if self.locations contains file.txt:100-110
            and removeLocations contains file.txt:105-115
            we will keep file.txt:100-105
        """
        if removeLocations is None:
            return
        for removeLocation in asFileLocationSet(removeLocations):
            for location in self._locations:
                if location.overlaps(removeLocation):
                    self._locations.remove(location)
                    cropped=location-removeLocation
                    if cropped is not None:
                        # if it is completely contained,we can leave
                        # the whole thing removed but if not,
                        # we need to re-add a cropped version
                        if isinstance(cropped,tuple):
                            # the difference has split the item into two
                            self._locations.add(cropped[0])
                            self._locations.add(cropped[1])
                        else:
                            self._locations.add(cropped)
    subtract=remove

    def union(self,
        fileLocations:typing.Optional[FileLocationListCompatible]
        )->'FileLocationSet':
        """
        Get a new fileLocationList consisting of this list and another list
        (NOTE: the + operator will also do this)
        """
        result=self.copy()
        result.add(fileLocations)
        return result
    combination=union

    def __add__(self,
        fileLocations:typing.Optional[FileLocationListCompatible]
        )->'FileLocationSet':
        """
        Use the + operator to create a new set consisting of a combination of both sets
        """
        return self.union(fileLocations)

    def difference(self,
        fileLocations:typing.Optional[FileLocationListCompatible]
        )->'FileLocationSet':
        """
        Get a new fileLocationList consisting of this list
        with regions from another list removed
        (NOTE: the - operator will also do this)
        """
        result=self.copy()
        result.remove(fileLocations)
        return result

    def __sub__(self,fileLocations:typing.Optional[FileLocationListCompatible]
        )->'FileLocationSet':
        """
        Use the - operator to create a new set consisting of this set, with
        another set removed from it.
        """
        return self.difference(fileLocations)

    def intersection(self,
        fileLocations:typing.Optional[FileLocationListCompatible]
        )->'FileLocationSet':
        """
        Get a new fileLocationList consisting of this list
        with regions but only where it intersects another set of regions
        (NOTE: the - operator will also do this)
        """
        result=FileLocationSet()
        if fileLocations is None:
            return result
        fileLocations=asFileLocationSet(fileLocations)
        for a in fileLocations:
            for b in self:
                c=a.intersection(b)
                if c is not None:
                    result.add(c)
        result.reduce()
        return result

    def reduce(self)->None:
        """
        Reduce this location set by combining overlapping regions

        eg. reducing [file.txt:100-200, file.txt:150-250]
        results in [file.txt:100-250]
        """
        locations=list(self._locations)
        result=[]
        stopIndex=len(locations)-1
        for idx,a in enumerate(locations):
            if idx==stopIndex:
                break
            for b in locations[idx+1:]:
                if a.overlaps(b):
                    result.append(a.union(b))
        self._locations=set(result)

    def __iter__(self)->typing.Iterator[FileLocation]:
        return iter(self._locations)

    def __len__(self)->int:
        return len(self._locations)

    def getByFile(self,
        filename:UrlCompatible
        )->typing.Generator[FileLocation]:
        """
        Get locations for a specific file
        """
        filename=asUrl(filename)
        for location in self:
            if location.url==filename:
                yield location

    def contains(self,other:FileLocationCompatible)->bool:
        """
        Does this entirely contain a location?
        """
        other=asFileLocation(other)
        for location in self._locations:
            if location.contains(other):
                return True
        return False

    def containedBy(self,other:FileLocationCompatible)->bool:
        """
        Is this entirely contained by a location?
        """
        other=asFileLocation(other)
        for location in self._locations:
            if location.containedBy(other):
                return True
        return False

    def overlaps(self,other:FileLocationCompatible)->bool:
        """
        Does this contain or overlap a location?
        """
        other=asFileLocation(other)
        for location in self._locations:
            if location.overlaps(other):
                return True
        return False

    def __repr__(self)->str:
        return '\n'.join([repr(location) for location in self._locations])

FileLocations=FileLocationSet
FileLocationList=FileLocationSet
UrlLocationSet=FileLocationSet
UrlLocations=FileLocationSet
UrlLocationList=FileLocationSet
