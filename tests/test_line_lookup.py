"""
Unit tests for lineLookup functionality.
"""
from pathlib import Path
import unittest

from paths.lineLookup import LineLookup


SAMPLE_DATA_DIR=Path(__file__).resolve().parent/"sample_data"
LINES_FILE=SAMPLE_DATA_DIR/"lines.txt"


def read_lines_sample()->str:
    with open(LINES_FILE,"r",newline="") as f:
        return f.read()


class LineLookupTests(unittest.TestCase):
    """
    Unit tests for lineLookup functionality.
    """

    def test_initialization(self) -> None:
        """
        Test that the object can be correctly initialized
        from either file or data.
        """
        filename=str(LINES_FILE)
        data=read_lines_sample()
        ll_1=LineLookup(filename,data=None)
        self.assertIsInstance(ll_1,LineLookup)
        ll_2=LineLookup("",data=data)
        self.assertIsInstance(ll_2,LineLookup)
        self.assertEqual(ll_1.data,ll_2.data)
        self.assertEqual(ll_1.totalBeforeLine[0],0)

    def test_array_like_functionality(self) -> None:
        """
        Test that the object behaves like an array
        with respect to line numbers.
        """
        filename=str(LINES_FILE)
        ll=LineLookup(filename,data=None)
        self.assertIsInstance(ll,LineLookup)
        self.assertEqual(len(ll),10)
        lineNum=5
        expectedText=read_lines_sample().splitlines(True)[lineNum-1]
        self.assertEqual(ll[lineNum],expectedText)

    def test_character_position(self) -> None:
        """
        Test that the calculation of row,col
        to character offset is correct.
        """
        filename=str(LINES_FILE)
        ll=LineLookup(filename,data=None)
        self.assertIsInstance(ll,LineLookup)
        lineNum=5
        charPos=ll.position(lineNum,1)
        self.assertIsInstance(charPos,int)
        lineSet=read_lines_sample().splitlines(True)[:lineNum-1]
        expected=sum(len(line) for line in lineSet)
        self.assertEqual(charPos,expected)

    def test_lookup(self) -> None:
        """
        Test that the calculation of character offset
        to row,col is correct.
        """
        filename=str(LINES_FILE)
        ll=LineLookup(filename,data=None)
        self.assertIsInstance(ll,LineLookup)
        lineNum=5
        colNum=3
        lineSet=read_lines_sample().splitlines(True)[:lineNum-1]
        pos=sum(len(line) for line in lineSet)+colNum-1
        fileLocation=ll.lookup(pos)
        self.assertEqual(fileLocation.row,lineNum)
        self.assertEqual(fileLocation.col,colNum)

    def test_get_lines(self) -> None:
        """
        Test that retrieving lines from a
        specific line number works correctly.
        """
        filename=str(LINES_FILE)
        ll=LineLookup(filename,data=None)
        self.assertIsInstance(ll,LineLookup)
        fromLineNum=5
        toLineNum=7
        lines=ll.getLines(fromLineNum,toLineNum)
        lineSet=read_lines_sample().splitlines(True)[fromLineNum-1:toLineNum]
        expected="".join(lineSet)
        self.assertEqual(lines,expected)

if __name__ == "__main__":
    unittest.main()
