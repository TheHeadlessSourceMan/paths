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

    def test_cgi_parameters_use_form_urlencoded_decoding(self):
        """CGI query names and values follow form URL-encoding rules."""
        url = URL(
            "http://example.com/search?"
            "first+name=Jane+Doe&language=C%2B%2B&"
            "expression=a%26b%3Dc&check=%E2%9C%93&encoded%26name=value"
        )

        self.assertEqual(url["first name"], "Jane Doe")
        self.assertEqual(url["language"], "C++")
        self.assertEqual(url["expression"], "a&b=c")
        self.assertEqual(url["check"], "\u2713")
        self.assertEqual(url["encoded&name"], "value")

    def test_cgi_parameters_preserve_blank_and_repeated_values(self):
        """Blank fields and every ordered value for a name survive parsing."""
        url = URL(
            "http://example.com/search?empty=&flag&choice=first&choice=last"
        )

        self.assertEqual(url["empty"], "")
        self.assertEqual(url["flag"], "")
        self.assertEqual(url["choice"], ["first", "last"])

    def test_cgi_parameters_split_only_on_first_equals(self):
        """The first equals sign separates each name from its value."""
        url = URL("http://example.com/search?formula=a=b=c&=empty-name")

        self.assertEqual(url["formula"], "a=b=c")
        self.assertEqual(url[""], "empty-name")

    def test_cgi_parameters_only_use_ampersand_as_separator(self):
        """A semicolon in a query value is data, not a field separator."""
        url = URL("http://example.com/search?mode=fast;debug=true&enabled=yes")

        self.assertEqual(url["mode"], "fast;debug=true")
        self.assertIsNone(url["debug"])
        self.assertEqual(url["enabled"], "yes")

    def test_cgi_parameters_ignore_empty_ampersand_fields(self):
        """Empty sequences between separators do not create parameters."""
        url = URL("http://example.com/search?&&first=1&&second=2&&")

        self.assertEqual(
            list(url.cgi.items()),
            [("first", "1"), ("second", "2")],
        )

    def test_cgi_parameters_decode_percent_encoding_once(self):
        """Valid escapes decode once and malformed escapes remain literal."""
        url = URL(
            "http://example.com/search?"
            "lower=%7e&double=%2526&malformed=%ZZ&nul=%00&invalid=%FF"
        )

        self.assertEqual(url["lower"], "~")
        self.assertEqual(url["double"], "%26")
        self.assertEqual(url["malformed"], "%ZZ")
        self.assertEqual(url["nul"], "\x00")
        self.assertEqual(url["invalid"], "\ufffd")

    def test_cgi_query_ends_at_fragment_and_accepts_query_delimiters(self):
        """Slash and question mark are data; hash starts a fragment."""
        url = URL(
            "http://example.com/search?"
            "path=/one/two&question=what?now&hash=%23"
            "#not=a-parameter"
        )

        self.assertEqual(url["path"], "/one/two")
        self.assertEqual(url["question"], "what?now")
        self.assertEqual(url["hash"], "#")
        self.assertIsNone(url["not"])

    def test_cgi_parameter_names_are_case_sensitive(self):
        """CGI query names preserve case and remain distinct."""
        url = URL("http://example.com/search?Name=upper&name=lower")

        self.assertEqual(url["Name"], "upper")
        self.assertEqual(url["name"], "lower")

    def test_repeated_cgi_parameters_round_trip(self):
        """Serializing and reparsing retains every repeated parameter value."""
        original = URL(
            "http://example.com/search?tag=one&tag=two+words&tag=three%2Bfour"
        )

        reparsed = URL(str(original))

        self.assertEqual(
            reparsed["tag"],
            ["one", "two words", "three+four"],
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
