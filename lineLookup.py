"""
used to convert a file offset into a row,col location
or vice-versa

The reason this is its own class is you can gain
efficiencies by on-demand precalculating how many characters
per line.
"""
import typing
import itertools
import bisect
from paths import UrlWithFileLocation,UrlCompatible,Url

class LineLookup:
    """
    used to convert a file offset into a row,col location
    or vice-versa

    The reason this is its own class is you can gain
    efficiencies by on-demand precalculating how many characters
    per line.
    """
    def __init__(self,
        filename:UrlCompatible,
        data:typing.Optional[str]=None):
        """ """
        self.filename:Url=Url(filename)
        if data is None:
            data=self.filename.read()
        self.data:str=data
        self._totalBeforeLine:typing.Optional[typing.List[int]]=None

    @property
    def totalBeforeLine(self)->typing.List[int]:
        """
        Total number if characters before each line
        """
        if self._totalBeforeLine is None:
            a=[len(x)+1 for x in self.data.split('\n')]
            self._totalBeforeLine=list(itertools.accumulate(a))
        return self._totalBeforeLine

    def getLines(self,start:int,end:typing.Optional[int]=None)->str:
        """
        Get a set of lines as a string
        """
        if end is None:
            end=start
        tbl=self.totalBeforeLine
        s=tbl[start]
        e=len(self.data) if end>=len(tbl) else self.totalBeforeLine[end+1]
        return self.data[s:e]

    def __getitem__(self,idx:typing.Union[int,typing.Tuple[int,int]])->str:
        if isinstance(idx,tuple):
            return self.getLines(idx[0],idx[1])
        return self.getLines(idx)

    def reverseLookup(self,
        row:typing.Union[int,UrlWithFileLocation],
        col:typing.Optional[int]=None
        )->int:
        """
        reverse lookup to determine character position based
        upon row and column

        :row: can either be a row number or
            a FileLocation (which has the row & col inside it)
        """
        if isinstance(row,UrlWithFileLocation):
            col=row.col
            row2=row.row
            if row2 is None:
                row2=1
        if col is None:
            col=1
        total=0
        if typing.cast(int,row)>0:
            total+=self.totalBeforeLine[typing.cast(int,row)-1]
        total+=col
        return total
    position=reverseLookup
    rlookup=reverseLookup

    def lookup(self,pos:int)->UrlWithFileLocation:
        """
        given a file position, returns FileLocation

        CAUTION: pos is a character position, not necessarily a byte position.
        For single-byte character encodings this is the same thing,
        but for multi-byte you cannot take this for granted!
        """
        row=bisect.bisect(self.totalBeforeLine,pos)
        col=pos
        if row>0:
            col=pos-self.totalBeforeLine[row-1]
        return UrlWithFileLocation(self.filename,fromRow=row+1,fromColumn=col+1)
    location=lookup
