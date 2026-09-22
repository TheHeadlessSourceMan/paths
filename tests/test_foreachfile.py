"""
Unit tests for foreachFile functionality
"""
from pathlib import Path
import typing
import unittest
from paths import MatchType
from paths.foreachfile import forEachFile,forEachFoundFile


SAMPLE_DATA_DIR=Path(__file__).resolve().parent/"sample_data"


class ForeachFileTests(unittest.TestCase):
    """
    Unit tests for foreachFile functionality.
    """

    def test_forEachFile(self)->None:
        """
        Test that forEachFile can run a shell command on each file found.
        """
        files=[SAMPLE_DATA_DIR/"lines.txt",SAMPLE_DATA_DIR/"blank.txt"]
        cmd=r"echo {FILE}"
        results=list(forEachFile(cmd,files))
        self.assertEqual(len(results),len(files))

    def test_forEachFoundFile(self)->None:
        """
        Test that forEachFoundFile can run a shell command on each file found.
        """
        cmd=r"echo {FILE}"
        results=forEachFoundFile(
            cmd,"*.txt",MatchType.GlobMatch,startDirs=str(SAMPLE_DATA_DIR)) # type: ignore # noqa: E501
        filesFound:typing.List[str]=[]
        for result in results:
            filesFound.append(Path(result.stdOutErr.strip()).name)
        self.assertEqual("blank.txt" in filesFound, True)
        self.assertEqual("lines.txt" in filesFound, True)
        self.assertEqual("l2_subdir_2_file_1.txt" in filesFound, True)

if __name__ == "__main__":
    unittest.main()
