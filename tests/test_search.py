"""Tests for search utilities."""

import os
import re
import tempfile
import unittest
from pathlib import Path

from paths.search import (
    FileMatcher,
    MatchType,
    findDirectoriesContainingFileTypes,
    findFiles,
    globToRegex,
    globToRegexStr,
)


class SearchTests(unittest.TestCase):
    """Verify glob expansion, pattern matching, and recursive file lookup."""

    def test_glob_to_regex_str_matches_wildcards(self):
        """The glob converter handles '*' and '?' as expected."""
        self.assertEqual(globToRegexStr("*.py"), r"^[^/]*\.py$")
        self.assertEqual(globToRegexStr("data?.csv"), r"^data.\.csv$")

    def test_glob_to_regex_compiles_case_insensitive_patterns(self):
        """Regex generation respects case sensitivity settings."""
        regex = globToRegex("*.PY", caseSensitive=False)

        self.assertIsInstance(regex, re.Pattern)
        self.assertIsNotNone(regex.match("script.py"))
        self.assertIsNotNone(regex.match("SCRIPT.PY"))
        self.assertIsNone(regex.match("script.txt"))

    def test_file_matcher_matches_paths_and_extensions(self):
        """Matcher combines path string matching with extension filtering."""
        matcher = FileMatcher("notes", MatchType.SimpleStringMatch, extensions=(".txt",))

        self.assertTrue(matcher.matches("/tmp/notes.txt"))
        self.assertTrue(matcher.matches(Path("/tmp/notes.txt")))
        self.assertFalse(matcher.matches("/tmp/other.txt"))
        self.assertFalse(matcher.matches("/tmp/notes.py"))

    def test_file_matcher_glob_matches_filename_in_path(self):
        """Filename glob patterns apply to files found beneath a directory."""
        matcher = FileMatcher("*.txt", MatchType.GlobMatch)

        self.assertTrue(matcher.matches("/tmp/notes.txt"))
        self.assertFalse(matcher.matches("/tmp/notes.py"))

    def test_find_files_recurses_and_filters_extensions(self):
        """findFiles yields files under nested directories and honors extension limits."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            nested = root / "nested"
            nested.mkdir()

            keep = root / "alpha.txt"
            nested_keep = nested / "beta.txt"
            skip = nested / "gamma.py"

            for path in (keep, nested_keep, skip):
                path.write_text("sample", encoding="utf-8")

            matches = sorted(
                path.relative_to(root).as_posix()
                for path in findFiles(
                    startDirs=root,
                    recursive=True,
                    extensions=(".txt",),
                )
            )

            self.assertEqual(matches, ["alpha.txt", "nested/beta.txt"])

    def test_find_files_advances_past_empty_start_directory(self):
        """An exhausted directory iterator advances to the next start directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            empty = root / "empty"
            populated = root / "populated"
            empty.mkdir()
            populated.mkdir()
            (populated / "result.txt").write_text("sample", encoding="utf-8")

            matches = list(
                findFiles(startDirs=(empty, populated), recursive=False)
            )

            self.assertEqual(matches, [populated / "result.txt"])

    def test_find_directories_containing_file_types(self):
        """Directories are reported when they contain a matching file type."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = root / "src"
            source_dir.mkdir()
            empty_dir = root / "empty"
            empty_dir.mkdir()

            (source_dir / "main.py").write_text("print('hi')\n", encoding="utf-8")
            (source_dir / "notes.md").write_text("# notes\n", encoding="utf-8")

            matches = sorted(
                str(path.relative_to(root))
                for path in findDirectoriesContainingFileTypes(
                    root,
                    fileExtensions=(".py",),
                    onlyHighestLevel=True,
                )
            )

            self.assertEqual(matches, ["src"])
            self.assertNotIn("empty", matches)


if __name__ == "__main__":
    unittest.main()
