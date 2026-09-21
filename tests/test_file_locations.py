"""
Unit tests for text and file location objects.
"""
import unittest

from paths.fileLocation import UrlWithFileLocation
from paths.textLocation import TextLocation, TextLocationSinglePoint


class FileLocationTests(unittest.TestCase):
    """Verify range arithmetic and RFC 5147-like file-location fragments."""

    def test_text_location_point_converts_to_offsets(self) -> None:
        """A single point resolves to the correct character offset in text."""
        text = "one\ntwo\nthree"
        point = TextLocationSinglePoint(0, 1)

        self.assertEqual(point.asOffsetIntoText(text), 1)

    def test_text_location_range_set_operations(self) -> None:
        """Range operations return the correct overlap and intersection."""
        left = TextLocation(0, 1, 3, 4)
        right = TextLocation(2, 2, 5, 3)

        self.assertTrue(left.overlaps(right))
        intersection = left.intersection(right)
        self.assertIsNotNone(intersection)
        self.assertEqual(intersection.fromRow, 2)
        self.assertEqual(intersection.fromColumn, 2)
        self.assertEqual(intersection.toRow, 3)
        self.assertEqual(intersection.toColumn, 3)

    def test_file_location_parses_rfc5147_fragments(self) -> None:
        """Rows and columns are parsed from the fragment using RFC 5147 syntax."""
        location = UrlWithFileLocation("file:///tmp/example.txt#line=2-5&char=3-7")

        self.assertEqual(location.fromRow, 2)
        self.assertEqual(location.fromColumn, 3)
        self.assertEqual(location.toRow, 5)
        self.assertEqual(location.toColumn, 7)


if __name__ == "__main__":
    unittest.main()
