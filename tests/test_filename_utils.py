"""
Unit tests for filename utils
"""
import unittest

from paths import (
    deSanitizeFilename,
    deSanitizePath,
    filenameSymbolToName,
    sanitizePath,
    sanitizePosixFilename,
    sanitizeWindowsFilename,
)


class FilenameUtilsTests(unittest.TestCase):
    """Verify filename and path sanitizing contracts and reversibility."""

    def test_windows_reserved_names_are_reversible(self):
        """Reserved Windows names are encoded and decoded without data loss."""
        for name in ("CON", "PRN", "AUX", "NUL", "COM3", "LPT1"):
            encoded = sanitizeWindowsFilename(name)
            self.assertEqual(encoded, f"_{name}_")
            self.assertEqual(deSanitizeFilename(encoded), name)

    def test_invalid_symbols_are_reversible(self):
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

    def test_posix_shell_symbols_are_encoded(self):
        """POSIX shell-sensitive symbols are encoded as named tokens."""
        encoded = sanitizePosixFilename("name;value")
        self.assertEqual(encoded, "name_SEMICOLON_value")
        self.assertEqual(deSanitizeFilename(encoded), "name;value")

    def test_sanitize_path_round_trips_each_component(self):
        """Path sanitizing preserves the meaning of each component."""
        original = "/home/<project>/file"
        encoded = str(sanitizePath(original))
        decoded = list(deSanitizePath(encoded))
        self.assertEqual(decoded[-3:], ["home", "<project>", "file"])


if __name__ == "__main__":
    unittest.main()
