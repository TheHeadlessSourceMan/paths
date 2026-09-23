"""
Unit tests for fileWatch functionality.
"""
import os
from pathlib import Path
import time
import typing
import unittest
import datetime
import threading


SAMPLE_DATA_DIR=Path(__file__).resolve().parent/"sample_data"


if os.name=="nt":
    from paths.fileWatch import ( # pylint: disable=ungrouped-imports
        watchForFileChange,waitForFileChange,FileChange,FileChangeType)
else:
    FileChange=typing.Any # type: ignore
    FileChangeType=typing.Any # type: ignore


class FileWatchTests(unittest.TestCase):
    """
    Unit tests for fileWatch functionality.
    """

    @unittest.skipUnless(os.name=="nt","fileWatch uses Windows directory notifications") # noqa: E501
    def test_watch_for_file_change(self)->None:
        """
        Test that a file can be watched for changes.
        """
        import random
        timeThreshold=datetime.datetime.now()
        filename=SAMPLE_DATA_DIR/"random.txt"
        reportedChanges:typing.List[FileChange]=[]
        def on_change_callback(change:FileChange)->bool:
            reportedChanges.append(change)
            return True
        t=watchForFileChange(filename,on_change_callback)
        with open(filename,"w") as f:
            f.write(str(random.random()))
            f.close()
        for _ in range(100):
            if reportedChanges:
                break
            time.sleep(0.1)
        if not reportedChanges:
            self.fail("File change was not reported within the expected time.")
        else:
            self.assertGreater(reportedChanges[0].timestamp,timeThreshold)
            self.assertEqual(reportedChanges[0].changeType,
                FileChangeType.UPDATE)
            self.assertEqual(filename.resolve(),
                reportedChanges[0].filename.resolve())
            self.assertNotEqual(str(reportedChanges[0]),"")
        t.join()

    @unittest.skipUnless(os.name=="nt","fileWatch uses Windows directory notifications") # noqa: E501
    def test_wait_for_file_change(self)->None:
        """
        Test that waiting for a file change works correctly.
        """
        import random
        timeThreshold=datetime.datetime.now()
        filename=SAMPLE_DATA_DIR/"random.txt"
        reportedChanges:typing.List[FileChange]=[]
        def on_change_callback(change:FileChange)->bool:
            reportedChanges.append(change)
            return True
        def changerFn():
            time.sleep(0.25)
            with open(filename,"w") as f:
                f.write(str(random.random()))
                f.close()
        t=threading.Thread(target=changerFn)
        t.start()
        waitForFileChange(filename,on_change_callback)
        if not reportedChanges:
            self.fail("File change callback was not invoked.")
        else:
            self.assertGreater(reportedChanges[0].timestamp,timeThreshold)
            self.assertEqual(reportedChanges[0].changeType,
                FileChangeType.UPDATE)
            self.assertEqual(filename.resolve(),
                reportedChanges[0].filename.resolve())
            self.assertNotEqual(str(reportedChanges[0]),"")
        t.join()

if __name__ == "__main__":
    unittest.main()
