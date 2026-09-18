"""
Tests for file path tools
"""
import unittest

import paths
from paths.filePathTools import (
    encodeFilePath,
    enquoteFilePath,
    filenameFixer,
    illegalCharsForOs,
)


class FilePathToolsTests(unittest.TestCase):
    """Verify filename quoting, validation, and repair helpers."""

    def test_enquote_file_path_only_when_needed(self):
        """Paths with spaces are quoted and embedded quotes are escaped."""
        self.assertEqual(enquoteFilePath("plain.txt"), "plain.txt")
        self.assertEqual(
            enquoteFilePath('two words "here".txt'),
            r'"two words \"here\".txt"',
        )

    def test_encode_file_path_raises_for_illegal_characters(self):
        """Illegal characters raise DecodeError by default."""
        with self.assertRaises(paths.DecodeError):
            encodeFilePath("bad:name.txt", osName="nt")

    def test_encode_file_path_can_replace_illegal_characters(self):
        """Illegal characters can be replaced instead of raising."""
        self.assertEqual(
            encodeFilePath(
                "bad:name.txt",
                enquote=False,
                osName="nt",
                errors="_",
            ),
            "bad_name.txt",
        )

    def test_filename_fixer_replaces_illegal_characters_anywhere(self):
        """filenameFixer replaces symbols even at the first position."""
        self.assertEqual(
            filenameFixer(":bad:name.txt", osName="nt"),
            "_bad_name.txt",
        )

    def test_illegal_chars_for_os_includes_common_windows_characters(self):
        """The Windows set includes characters Windows rejects."""
        illegal = illegalCharsForOs("nt")

        for symbol in '<>:"/\\|?*':
            self.assertIn(symbol, illegal)


if __name__ == "__main__":
    unittest.main()
