"""
Miscellaneous functions for working with paths
"""
import typing


def skipEmptyLines(
    lines:typing.Union[str,typing.Iterable[str]]
    )->typing.Generator[str,None,None]:
    """
    Iterate over a series of lines, skipping empty ones
    """
    if isinstance(lines,str):
        lines=lines.replace('\r','').split('\n')
    for line in lines:
        if line:
            yield line

class StrWithFileLocation:
    """
    A string with the file location reference where it came from
    """
    def __init__(self,s:typing.Any,filename:str='',lineNo:int=0):
        self.lineNo:int=lineNo
        self.filename=filename
        if not isinstance(s,str):
            s=str(s)
        self.s=s

    def split(self,
        splitters:typing.Optional[str]=None,
        maxSplit:typing.Optional[int]=None
        )->typing.List["StrWithFileLocation"]:
        """
        Implement the standard string split() function
        """
        if maxSplit is None:
            maxSplit=-1
        return [
            StrWithFileLocation(x,filename=self.filename,lineNo=self.lineNo)
            for x in self.s.split(splitters,maxSplit)]
    def __eq__(self,other:typing.Any):
        return self.s==str(other)
    def __hash__(self):
        return hash(self.s)
    def __repr__(self):
        return self.s
strWithFileLocation=StrWithFileLocation
