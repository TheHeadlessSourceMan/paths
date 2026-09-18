"""
A location within some text.
"""
import typing
if typing.TYPE_CHECKING:
    from .fileLocation import FileLocationCompatible


class TextLocationSinglePoint:
    """
    A single index point within some text.

    Basically just a row and column, but this
    makes them easily comparable.
    """

    def __init__(self,row:int,column:int):
        self.row=row
        self.column=column

    def asOffsetIntoText(self,text:str)->int:
        """
        Convert this point into an offset in the given text

        NOTE: this has to look up carriage returns every time,
        so if you do a lot of this, it may be better to use a
        stored index table, eg, generated from rowOffsets().
        """
        idx=0
        if self.row<0:
            # handle negative row indices as offset from end
            offsets=self.rowOffsets(text) # cheapest way is get all offsets
            if -self.row>len(offsets):
                raise IndexError(f'Cannot get line {-self.row} in text that has only {len(offsets)} lines.') # noqa: E501 # pylint: disable=line-too-long
            idx=offsets[self.row+1]
        elif self.row>0:
            idx=-1
            for _ in range(self.row):
                lastIdx=idx+1
                idx=text.find('\n',lastIdx)
                if idx==-1:
                    raise IndexError(f'Cannot get line {self.row} in text that has only {lastIdx} lines.') # noqa: E501 # pylint: disable=line-too-long
        if self.column!=0:
            nextIdx=text.find('\n',idx)
            if nextIdx==-1:
                nextIdx=len(text)
            if self.column<1:
                # handle negative column indices as offset from end of row
                if idx-nextIdx<self.column:
                    raise IndexError(f'Cannot get column {self.column} in text row that has only {nextIdx-idx} characters.') # noqa: E501 # pylint: disable=line-too-long
                idx+=nextIdx+self.column
            else:
                if idx+self.column>nextIdx-idx:
                    raise IndexError(f'Cannot get column {self.column} in text row that has only {nextIdx-idx} characters.') # noqa: E501 # pylint: disable=line-too-long
                idx+=self.column
        return idx

    def rowOffsets(self,text:str)->typing.List[int]:
        """
        Generate a table of row offsets
        """
        ret=[0]
        idx=-1
        while True:
            lastIdx=idx+1
            idx=text.find('\n',lastIdx)
            if idx==-1:
                break
            ret.append(idx)
        return ret

    def copy(self)->'TextLocationSinglePoint':
        """
        Create a copy of this point
        """
        return TextLocationSinglePoint(self.row,self.column)

    def max(self,
        other:typing.Union[
            'TextLocationSinglePoint',
            typing.Iterable['TextLocationSinglePoint']]
        )->'TextLocationSinglePoint':
        """
        Returns the maximum of this and one or more other points
        """
        if hasattr(other,'__iter__'):
            mmax=self
            for item in other: # type: ignore
                if item>mmax:
                    mmax=item
            return mmax
        if other>self: # type: ignore
            return other # type: ignore
        return self

    def min(self,
        other:typing.Union[
            'TextLocationSinglePoint',
            typing.Iterable['TextLocationSinglePoint']]
        )->'TextLocationSinglePoint':
        """
        Returns the maximminimum of this and one or more other points
        """
        if hasattr(other,'__iter__'):
            mmax=self
            for item in other: # type: ignore
                if item<mmax:
                    mmax=item
            return mmax
        if other<self: # type: ignore
            return other # type: ignore
        return self

    def __cmp__(self,other:'TextLocationSinglePoint')->int:
        """
        Like the old __cmp__ dunder, but
        respects array-style negative numbers
        Returns
            -1: a<b
             0: a=b
             1: a>b

        NOTE: Since this has no knowledge of the length of the
        thing being indexed, handling negatives is a little tricky.
        Therefore, negatives are always preferred.  That is, 999999<-2
        will always return True, even if the document is 1 byte long.
        """
        def _cmpVal(a:int,b:int)->int:
            if a<0:
                if b<0:
                    if a>b:
                        return -1
                    return a<b
                return a
            if b<0:
                return b
            if a<b:
                return -1
            return a>b
        rowCmp=_cmpVal(self.row,other.row)
        if rowCmp==0:
            return _cmpVal(self.column,other.column)
        return rowCmp

    def __lt__(self,other:'TextLocationSinglePoint')->bool:
        return self.__cmp__(other)<0

    def __le__(self,other:'TextLocationSinglePoint')->bool:
        return self.__cmp__(other)<=0

    def __gt__(self,other:'TextLocationSinglePoint')->bool:
        return self.__cmp__(other)>0

    def __ge__(self,other:'TextLocationSinglePoint')->bool:
        return self.__cmp__(other)>=0

    def __eq__(self, # type: ignore
        other:'TextLocationSinglePoint')->bool:
        return self.__cmp__(other)==0


class TextLocation:
    """
    A location within some text.
    """

    @typing.overload
    def __init__(self, # type: ignore
        fromRow:TextLocationSinglePoint,
        fromColumn:None=None,
        toRow:typing.Optional[TextLocationSinglePoint]=None,
        toColumn:None=None,
        location:None=None):
        """
        :fromRow: can be used as location to make ordered-parameters easier
        :location: fill in any missing to/from row/column with this location
        """

    @typing.overload
    def __init__(self, # type: ignore
        fromRow:typing.Optional[int]=None,
        fromColumn:typing.Optional[int]=None,
        toRow:typing.Optional[int]=None,
        toColumn:typing.Optional[int]=None,
        location:typing.Optional['FileLocationCompatible']=None):
        """
        :fromRow: can be used as location to make ordered-parameters easier
        :location: fill in any missing to/from row/column with this location
        """

    @typing.overload
    def __init__(self, # type: ignore
        fromRow:'FileLocationCompatible'):
        """
        :fromRow: can be used as location to make ordered-parameters easier
        """

    def __init__(self,
        fromRow:typing.Union[None,
            int,'FileLocationCompatible',TextLocationSinglePoint]=None,
        fromColumn:typing.Optional[int]=None,
        toRow:typing.Union[None,int,TextLocationSinglePoint]=None,
        toColumn:typing.Optional[int]=None,
        location:typing.Optional['FileLocationCompatible']=None):
        """
        :fromRow: can be used as location to make ordered-parameters easier
        :location: fill in any missing to/from row/column with this location
        """
        self.fromPoint=TextLocationSinglePoint(0,0)
        self.toPoint=TextLocationSinglePoint(-1,-1)
        TextLocation.assign(self,fromRow,fromColumn,toRow,toColumn,location)

    def asOffsetIntoText(self,text:str)->typing.Tuple[int,int]:
        """
        Convert this location tinto an offset in the given text
        """
        return (
            self.fromPoint.asOffsetIntoText(text),
            self.toPoint.asOffsetIntoText(text))

    def rowOffsets(self,text:str)->typing.List[int]:
        """
        Generate a table of row offsets
        """
        return self.toPoint.rowOffsets(text)

    def getFromText(self,text:str)->str:
        """
        Extract text at this location from the given text
        """
        startIdx,endIdx=self.asOffsetIntoText(text)
        return text[startIdx:endIdx]

    def assign(self,
        fromRow:typing.Union[None,int,'FileLocationCompatible',
            TextLocationSinglePoint,'TextLocation']=None,
        fromColumn:typing.Optional[int]=None,
        toRow:typing.Union[None,int,TextLocationSinglePoint]=None,
        toColumn:typing.Optional[int]=None,
        location:typing.Union[None,
            'FileLocationCompatible','TextLocation']=None)->None:
        """
        :fromRow: can be used as location to make ordered-parameters easier
        :location: fill in any missing to/from row/column with this location
        """
        if fromRow is not None:
            if isinstance(fromRow,TextLocationSinglePoint):
                self.fromPoint=fromRow.copy()
                fromRow=None
            elif not isinstance(fromRow,int):
                location=fromRow
                fromRow=None
        if toRow is not None:
            if isinstance(toRow,TextLocationSinglePoint):
                self.toPoint=toRow.copy()
                toRow=None
        if location is not None:
            if not isinstance(location,TextLocation):
                from .fileLocation import asFileLocation
                location=asFileLocation(location)
            if fromRow is None:
                fromRow=location.fromRow
            if fromColumn is None:
                fromColumn=location.fromColumn
            if toRow is None:
                toRow=location.toRow
            if toColumn is None:
                toColumn=location.toColumn
        if fromRow is not None:
            self.fromPoint.row=fromRow
        if fromColumn is not None:
            self.fromPoint.column=fromColumn
        if toRow is not None:
            self.toPoint.row=toRow
        if toColumn is not None:
            self.toPoint.column=toColumn

    def copy(self)->"TextLocation":
        """
        Create a copy of this location within file
        """
        return TextLocation(
            self.fromPoint.row,
            self.fromPoint.column,
            self.toPoint.row,
            self.toPoint.column)

    def __eq__(self,__o: object)->bool:
        """
        Compare to another location
        """
        if isinstance(__o,TextLocation):
            return self.fromPoint==__o.fromPoint and self.toPoint==__o.toPoint
        elif hasattr(__o,'location'):
            return self==getattr(__o,'location')
        elif isinstance(__o,str):
            from .fileLocation import UrlWithFileLocation
            return self==UrlWithFileLocation(__o)
        return False

    def openEditor(self,editor:typing.Optional[str]=None):
        """
        shortcut to call the openEditor tool
        """
        import openEditor
        openEditor.openEditor(self,editor=editor) # type: ignore

    def contains(self,other:'TextLocation')->bool:
        """
        Does this entirely contain another location?
        """
        return other.fromPoint<=self.fromPoint and other.toPoint>=self.toPoint

    def containedBy(self,other:'TextLocation')->bool:
        """
        Is this entirely contained by another location?
        """
        return other.contains(self)

    def overlaps(self,other:'TextLocation')->bool:
        """
        Does this contain or overlap another location?
        """
        # if either point in the other item is within
        # the range of this item, return True
        if other.fromPoint<=self.toPoint\
            and other.fromPoint>=self.fromPoint:
            return True
        if other.toPoint<=self.toPoint\
            and other.toPoint>=self.fromPoint:
            return True
        # or if other completely contains this
        return other.contains(self)

    def union(self,
        other:'TextLocation',fillGaps:bool=True
        )->'TextLocation':
        """
        Return a new location that is a combination of this location
        and another location.

        :fillGaps: if it is file.txt:100-110 and file.txt:200-210, should
            we return file.txt:100-210, or raise a ValueError exception?
        """
        if not fillGaps and not self.overlaps(other):
            raise ValueError(f'Regions {self} and {other} are discontigious')
        fromPoint=self.fromPoint.min(other.fromPoint)
        toPoint=self.fromPoint.max(other.toPoint)
        return TextLocation(fromPoint,None,toPoint)

    def difference(self,
        other:'TextLocation'
        )->typing.Union[None,
            'TextLocation',
            typing.Tuple['TextLocation','TextLocation']]:
        """
        Return a new location that is a this location
        with another location removed from it.

        returns None if this causes the location to completely disappear
        NOTE: this could result in this being split into two, eg.
            file.txt:100..400 - file.txt:200..300 =
                (file.txt:100..200, file.txt:300-400)
        """
        if not self.overlaps(other):
            # nothing will be removed
            return self.copy()
        if other.contains(self):
            # the entire thing will be removed
            return None
        if self.fromPoint<other.fromPoint:
            if self.toPoint>other.toPoint:
                # this splits us in half!
                return (
                    TextLocation(self.fromPoint,None,other.fromPoint),
                    TextLocation(other.toPoint,None,self.toPoint))
            fromPoint=other.fromPoint
            toPoint=self.toPoint
        else:
            fromPoint=self.fromPoint
            toPoint=other.toPoint
        return TextLocation(fromPoint,None,toPoint)

    def intersection(self,
        other:'TextLocation'
        )->typing.Optional['TextLocation']:
        """
        Return a new location that is a combination of the parts of
        this location and of another location that overlap.

        returns None if there are no parts in common causing the
        location to completely disappear
        """
        if not self.overlaps(other):
            # they do not overlap, so intersection is empty
            return None
        fromPoint=self.fromPoint.max(other.fromPoint)
        toPoint=self.toPoint.min(other.toPoint)
        return TextLocation(fromPoint,None,toPoint)

    @property
    def fromRow(self)->int:
        """
        same as fromRow
        """
        return self.fromPoint.row
    @fromRow.setter
    def fromRow(self,fromRow:typing.Optional[int]=None):
        self.fromPoint.row=0 if fromRow is None else fromRow
    @property
    def fromLine(self)->int:
        """
        same as fromRow
        """
        return self.fromPoint.row
    @fromLine.setter
    def fromLine(self,fromLine:typing.Optional[int]=None):
        self.fromPoint.row=0 if fromLine is None else fromLine
    @property
    def line(self)->int:
        """
        same as fromRow
        """
        return self.fromPoint.row
    @line.setter
    def line(self,fromLine:typing.Optional[int]=None):
        self.fromPoint.row=0 if fromLine is None else fromLine
    @property
    def row(self)->int:
        """
        same as fromRow
        """
        return self.fromPoint.row
    @row.setter
    def row(self,row:typing.Optional[int]=None):
        self.fromPoint.row=0 if row is None else row

    @property
    def toRow(self)->int:
        """
        same as toRow
        """
        return self.toPoint.row
    @toRow.setter
    def toRow(self,toRow:typing.Optional[int]=None):
        self.toPoint.row=-1 if toRow is None else toRow
    @property
    def toLine(self)->int:
        """
        same as toRow
        """
        return self.toPoint.row
    @toLine.setter
    def toLine(self,toLine:typing.Optional[int]=None):
        self.toPoint.row=-1 if toLine is None else toLine

    @property
    def numRows(self)->int:
        """
        numnber of rows
        """
        return self.toPoint.row-self.fromPoint.row+1
    @numRows.setter
    def numRows(self,numRows:typing.Optional[int]=None):
        if numRows is None or numRows<=0:
            numRows=1
        self.toRow=self.fromRow+numRows-1
    @property
    def numLines(self)->int:
        """
        same as numRows
        """
        return self.numRows
    @numLines.setter
    def numLines(self,numLines:typing.Optional[int]):
        self.numRows=numLines

    @property
    def fromColumn(self)->int:
        """
        starting column/character for the given row in the file
        """
        return self.fromPoint.column
    @fromColumn.setter
    def fromColumn(self,fromColumn:typing.Optional[int]=None):
        self.fromPoint.column=0 if fromColumn is None else fromColumn
    @property
    def fromCol(self)->int:
        """
        starting column/character for the given row in the file
        """
        return self.fromPoint.column
    @fromCol.setter
    def fromCol(self,fromCol:typing.Optional[int]=None):
        self.fromPoint.column=0 if fromCol is None else fromCol
    @property
    def col(self)->int:
        """
        starting column/character for the given row in the file
        """
        return self.fromPoint.column
    @col.setter
    def col(self,fromColumn:typing.Optional[int]=None):
        self.fromPoint.column=0 if fromColumn is None else fromColumn
    @property
    def column(self)->int:
        """
        starting column/character for the given row in the file
        """
        return self.fromPoint.column
    @column.setter
    def column(self,column:typing.Optional[int]=None):
        self.fromPoint.column=0 if column is None else column

    @property
    def toColumn(self)->int:
        """
        ending column/character for the given row in the file
        """
        return self.toPoint.column
    @toColumn.setter
    def toColumn(self,toColumn:typing.Optional[int]=None):
        self.toPoint.column=0 if toColumn is None else toColumn
    @property
    def toCol(self)->int:
        """
        ending column/character for the given row in the file
        """
        return self.toPoint.column
    @toCol.setter
    def toCol(self,toCol:typing.Optional[int]=None):
        self.toPoint.column=0 if toCol is None else toCol

    def __repr__(self)->str:
        """
        string representation of this object
        """
        ret=[]
        if self.line is not None:
            ret.append('%d'%self.line)
            if self.fromColumn!=-1:
                ret.append(':%d'%self.fromColumn)
            if self.toRow!=-1:
                ret.append('-%d'%self.toRow)
                if self.toColumn!=-1:
                    ret.append(':%d'%self.toColumn)
        return ''.join(ret)
