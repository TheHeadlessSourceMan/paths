"""
Unit tests for FilePath objects
"""
import os
import tempfile
import unittest

from paths import FilePath, URL, asFilePath, asFileString, expandUserStr
from paths.errors import MalformedFilename


class FilePathTests(unittest.TestCase):
    """Verify FilePath path operations and URL morphology contracts."""

    def test_url_file_scheme_morphs_to_file_path(self):
        """A file:// URL created through URL uses the FilePath subclass."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = URL(f"file:///{tmpdir.replace(os.sep, '/')}")

        self.assertIsInstance(result, FilePath)
        self.assertIsNot(type(result), URL)

    def test_url_os_path_morphs_to_file_path(self):
        """A native filesystem path created through URL uses FilePath."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = URL(tmpdir)

        self.assertIsInstance(result, FilePath)
        self.assertIsNot(type(result), URL)

    def test_path_join_read_write_and_callable_exists(self):
        """Joined FilePath values can be written, read, and checked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = FilePath(tmpdir)
            child = root / "child.txt"

            child.write_text("hello")

            self.assertIsInstance(child, FilePath)
            self.assertTrue(child.exists)
            self.assertTrue(child.exists())
            self.assertEqual(child.read_text(), "hello")
            self.assertEqual(child.extension, ".txt")
            self.assertEqual(str(child.parent), str(root))

    def test_as_file_path_can_force_absolute_paths(self):
        """asFilePath optionally returns an absolute FilePath."""
        result = asFilePath(".", makeAbsolute=True)

        self.assertIsInstance(result, FilePath)
        self.assertTrue(result.isAbsolute)

    def test_as_file_string_rejects_non_file_urls(self):
        """Web URLs are not silently accepted as filenames."""
        with self.assertRaises(MalformedFilename):
            asFileString("https://example.com/file.txt")

    def test_expand_user_str_uses_custom_shell_replacements(self):
        """Custom replacement dictionaries expand supported shell forms."""
        result = expandUserStr(
            "$ROOT/${CHILD}/%LEAF%",
            {"ROOT": "base", "CHILD": "subdir", "LEAF": "file.txt"},
        )

        self.assertEqual(result, "base/subdir/file.txt")


if __name__ == "__main__":
    unittest.main()
