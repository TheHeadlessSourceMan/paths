"""
Unit tests for the URL class
"""
import unittest
import typing
import re
import os
import tempfile
from unittest.mock import Mock, patch

import paths
from paths import URL, asUrl, NonIterableDirectory, UnknownBaseDirectory


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

    def test_comparison_and_same_domain_ignore_subdomain(self):
        """URL comparisons use paths while sameDomain ignores subdomains."""
        first = URL("http://www.example.com/a")
        second = first.copy()

        self.assertEqual(first, second)
        second.subdomain = None
        self.assertEqual(first, second)
        self.assertTrue(first.sameDomain(second))
        second.host = "other.example.com"
        self.assertTrue(first.sameDomain(second))
        second.host = "other.example.net"
        self.assertFalse(first.sameDomain(second))

    def test_relative_navigation_normalizes_parent_paths(self):
        """Relative paths normalize parent traversal against the base URL."""
        url = URL("file://top_dir/parent_dir/child_dir/")

        self.assertEqual(url.relative("child/").fullPath,
                         "top_dir/parent_dir/child_dir/child/")
        self.assertEqual(url.relative("../").fullPath,
                         "top_dir/parent_dir/")
        self.assertIsNone(url.relative("../../../").fullPath)

    def test_auth_fragment_and_encoding_helpers(self):
        """Authentication, fragments, and encoding helpers expose values."""
        url = URL("http://user:secret@api.v2.example.com/items#section")

        self.assertEqual(url.auth, "user:secret")
        self.assertEqual(url.host, "api.v2.example.com")
        self.assertEqual(url.domain, "example.com")
        self.assertEqual(url.subdomain, "api.v2")
        self.assertEqual(url.fragment, "section")
        self.assertEqual(URL.fragValueToRange("2-5,7-9"), (7, 9))
        self.assertEqual(URL.urlencode("two words"), "two%20words")
        self.assertEqual(URL.urldecode("two%20words"), "two words")

    def test_url_helpers_cover_directory_and_hyperlink_behavior(self):
        """URL helpers classify extensionless web paths and produce links."""
        directory = URL("https://example.com/items")
        document = URL("https://example.com/report.txt")

        self.assertTrue(directory.isDirectory)
        self.assertTrue(document.isDirectory)
        self.assertIn(
            'href="https://example.com/items"', directory.hyperlink())
        self.assertEqual(document.extension, "txt")
        self.assertEqual(document.ext, "txt")
        self.assertEqual(document.fileExtension, "txt")

    def test_call_passes_query_parameters_to_read(self):
        """Calling a URL adds temporary query parameters before reading."""
        url = URL("https://example.com/search")

        with patch.object(URL, "read", return_value="response") as read:
            parameters:typing.Dict[str, typing.Any] = {"page": 2}
            self.assertEqual(url.call(**parameters), "response")

        read.assert_called_once()

    def test_command_line_accepts_help(self):
        """The module command line accepts help and empty argument lists."""
        self.assertEqual(paths.cmdline(["--help"]), 0)
        self.assertEqual(paths.cmdline([]), 0)

    def test_mapping_operations_reject_path_indexes(self):
        """Query mapping operations reject indexes intended for path steps."""
        url = URL("https://example.com/items?old=value")

        with self.assertRaises(TypeError):
            url[0] = "value"
        with self.assertRaises(TypeError):
            del url[0]
        del url["old"]
        self.assertIsNone(url["old"])

    def test_fragment_setter_and_auth_setter_cover_empty_values(self):
        """Explicit fragment and authentication assignments update state."""
        url = URL("https://example.com/items")

        url.fragment = "row:10"
        self.assertEqual(url.fragment, "row:10")
        self.assertEqual(url.fragments["row"], "10")
        url.auth = "user"
        self.assertEqual(url.username, "user")
        self.assertIsNone(url.password)
        url.auth = ""
        self.assertEqual(url.auth, "")

    def test_path_and_full_path_setters_normalize_and_validate(self):
        """Path setters normalize and reject malformed full paths."""
        url = URL("https://example.com/items/file.txt")

        url.path = "one/./two/three/.."
        self.assertEqual(url.path, "one/two/")
        url.fullPath = "report.txt"
        self.assertEqual(url.fullPath, "report.txt")
        with self.assertRaises(Exception):
            url.path = "one/../../report.txt"
        with self.assertRaises(Exception):
            url.fullPath = "one//two.txt"

    def test_url_string_encoding_modes_and_replace_helpers(self):
        """URL serialization preserves escapes and supports replacement."""
        url = URL("https://example.com/a%20b/report.txt")

        self.assertEqual(str(url), "https://example.com/a%20b/report.txt")
        url.ignoreAlreadyEncoded = False
        self.assertIn("%2520", str(url))
        self.assertEqual(
            url.replace("report", "summary").resource,
            "summary.txt",
        )
        self.assertEqual(
            url.replace("report", "summary")
                .replace(re.compile("summary"), "final").resource,
            "final.txt",
        )

    def test_directory_and_absolute_error_helpers(self):
        """Directory iteration and relative absolute conversion fail."""
        relative = URL("https://example.com/items/report.txt")
        self.assertIs(relative.absolute(), relative)
        hostless = URL("https://example.com/items/report.txt")
        hostless.host = None
        with self.assertRaises(UnknownBaseDirectory):
            hostless.absolute()
        with self.assertRaises(NonIterableDirectory):
            list(URL("https://example.com/items").iterdir())

    def test_browser_and_alias_helpers(self):
        """Browser opening and aliases pass through to their adapters."""
        url = URL("https://example.com/items")
        browser = Mock()
        with patch("webbrowser.get", return_value=browser):
            self.assertIs(url.openInBrowser(newWindow=True), browser)
        browser.open.assert_called_once_with(str(url), 1, True)
        self.assertEqual(url.user, url.username)
        url.user = "alice"
        self.assertEqual(url.username, "alice")
        url.protocol = "https"
        self.assertEqual(url.scheme, "https")

    def test_file_url_and_file_classification_helpers(self):
        """File conversion, extension, and classification helpers work."""
        temporary = tempfile.NamedTemporaryFile(suffix=".TXT", delete=False)
        temporary.write(b"hello")
        temporary.close()
        try:
            url = URL(temporary.name)
            self.assertEqual(url.extension, "txt")
            self.assertEqual(url.filePath, temporary.name)
            self.assertFalse(url.isDirectory)
            self.assertTrue(url.isTextFile)
            self.assertFalse(url.isBinaryFile)
        finally:
            os.unlink(temporary.name)
        with self.assertRaises(DeprecationWarning):
            _ = url.isFile
        with self.assertRaises(NotImplementedError):
            _ = url.filename


if __name__ == "__main__":
    unittest.main()
