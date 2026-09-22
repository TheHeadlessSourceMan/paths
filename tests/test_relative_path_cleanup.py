"""Verify relative path normalization and native path conversion."""
import os
import unittest

from paths.relativePathCleanup import cleanup, cleanupOsPath


class RelativePathCleanupTests(unittest.TestCase):
    """Verify relative path normalization and native path conversion."""

    def test_normalizes_separators_and_dot_segments(self):
        """Mixed separators and dot segments collapse to one clean path."""
        self.assertEqual(
            cleanup(r"child\./leaf/../file", "root/base"),
            "root/base/child/file",
        )

    def test_preserves_absolute_urls(self):
        """Absolute URLs keep scheme and host while normalizing segments."""
        self.assertEqual(
            cleanup("https://example.com/a/../b", "ignored"),
            "https://example.com/b",
        )

    def test_removes_trailing_separators(self):
        """Trailing separators are removed from normalized relative paths."""
        self.assertEqual(cleanup("child///", "root"), "root/child")

    def test_cleanup_os_path_uses_native_separator(self):
        """OS-specific cleanup returns a path using the platform separator."""
        result = cleanupOsPath("child/leaf", "root")
        expected = os.path.join("root", "child", "leaf")
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
