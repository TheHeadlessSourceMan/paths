"""
Unit tests for filename utils
"""
import os
import unittest
from unittest.mock import patch

from paths import (
    asPathlibPath,
    deSanitizeFilename,
    deSanitizePath,
    filenameSymbolToName,
    sanitizePath,
    sanitizePosixFilename,
    sanitizeWindowsFilename,
)


class FilenameUtilsTests(unittest.TestCase):
    """Verify filename and path sanitizing contracts and reversibility."""

    def test_windows_reserved_names_are_reversible(self) -> None:
        """Reserved Windows names are encoded and decoded without data loss."""
        for name in ("CON", "PRN", "AUX", "NUL", "COM3", "LPT1"):
            encoded = sanitizeWindowsFilename(name)
            self.assertEqual(encoded, f"_{name}_")
            self.assertEqual(deSanitizeFilename(encoded), name)

    def test_windows_reserved_prefixes_are_not_truncated(self) -> None:
        """Ordinary names beginning with a reserved name remain intact."""
        self.assertEqual(sanitizeWindowsFilename("CON-report"), "CON-report")

    def test_invalid_symbols_are_reversible(self) -> None:
        """Invalid symbols use explicit delimiter tokens reversibly."""
        for symbol in '<>:/\\|?*':
            encoded = sanitizeWindowsFilename(symbol, delimiter="-")
            self.assertEqual(
                encoded,
                f"-{filenameSymbolToName[symbol]}-",
            )
            self.assertEqual(
                deSanitizeFilename(encoded, delimiter="-"),
                symbol,
            )

    def test_windows_control_characters_are_reversible(self) -> None:
        """Windows control bytes use hexadecimal delimiter tokens."""
        encoded = sanitizeWindowsFilename("record\x1f.txt")

        self.assertEqual(encoded, "record_0x1F_.txt")
        self.assertEqual(deSanitizeFilename(encoded), "record\x1f.txt")

    def test_replacement_mode_is_lossy_and_predictable(self) -> None:
        """Replacement mode substitutes invalid Windows characters directly."""
        self.assertEqual(
            sanitizeWindowsFilename("report?.txt", replacement="-"),
            "report-.txt",
        )

    def test_posix_shell_symbols_are_encoded(self) -> None:
        """POSIX shell-sensitive symbols are encoded as named tokens."""
        encoded = sanitizePosixFilename("name;value")
        self.assertEqual(encoded, "name_SEMICOLON_value")
        self.assertEqual(deSanitizeFilename(encoded), "name;value")

    def test_environment_expansion_can_be_enabled_or_disabled(self) -> None:
        """Windows sanitation expands environment values only on request."""
        with patch.dict(os.environ, {"PATHS_TEST_FILENAME": "draft"}):
            self.assertEqual(
                sanitizeWindowsFilename("%PATHS_TEST_FILENAME%?.txt"),
                "draft_QUESTION_MARK_.txt",
            )
            self.assertEqual(
                sanitizeWindowsFilename(
                    "%PATHS_TEST_FILENAME%?.txt",
                    expandEnvironment=False,
                ),
                "%PATHS__TEST__FILENAME%_QUESTION_MARK_.txt",
            )

    def test_unknown_delimiter_tokens_are_left_unchanged(self) -> None:
        """Decoding leaves names with unknown delimiter tokens intact."""
        encoded = "record_UNKNOWN_token"

        self.assertEqual(deSanitizeFilename(encoded), encoded)

    def test_sanitize_path_round_trips_each_component(self) -> None:
        """Path sanitizing preserves the meaning of each component."""
        original = "/home/<project>/file"
        encoded = str(sanitizePath(original))
        decoded = list(deSanitizePath(encoded))
        expected = ["home", encoded.split(os.sep)[-2], "file"]
        self.assertEqual(decoded[-3:], expected)

    def test_path_separator_options_control_splitting(self) -> None:
        """Callers can split only on forward slashes when required."""
        self.assertEqual(
            list(
                deSanitizePath(
                    "first/second\\third",
                    useBackSlashSeparator=False,
                )
            ),
            ["first", "second\\third"],
        )

    def test_as_pathlib_path_rejects_non_file_urls(self) -> None:
        """Local conversion rejects URLs without a filesystem location."""
        with self.assertRaises(FileNotFoundError):
            asPathlibPath("https://example.com/report.txt")


if __name__ == "__main__":
    unittest.main()
