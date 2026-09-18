"""
Unit tests for the URL class
"""
import unittest

from paths import URL, asUrl


class UrlTests(unittest.TestCase):
    """Verify public URL parsing, query, navigation, and copy behavior."""

    def test_query_parameters_are_decoded_and_encoded(self):
        """Query values decode on read and serialize safely after mutation."""
        url = URL("http://example.com/search?q=hello%20world")

        self.assertEqual(url["q"], "hello world")
        url["page"] = 2
        self.assertEqual(
            url.url,
            "http://example.com/search?q=hello%20world&page=2",
        )

    def test_relative_navigation_preserves_the_base_host(self):
        """Relative navigation resolves the path against the original host."""
        base = URL("http://example.com/one/two/index.html")

        result = base.relative("../image.png")

        self.assertEqual(result.host, "example.com")
        self.assertEqual(result.fullPath, "one/image.png")

    def test_copy_is_independent(self):
        """Changing a copied URL does not mutate the original URL."""
        original = asUrl("http://example.com/item")
        copied = original.copy()
        copied.host = "other.example"

        self.assertEqual(original.host, "example.com")
        self.assertEqual(copied.host, "other.example")


if __name__ == "__main__":
    unittest.main()
