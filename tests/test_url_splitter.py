"""
Unit tests for URL splitting and assignment.
"""
import unittest

from paths import URL
from paths._url import URL as BaseURL


def make_base_url(value=None, relative_to=None):
    """Create a base URL instance without URL.__new__ subclass morphing."""
    url = object.__new__(BaseURL)
    BaseURL.__init__(url, value, relative_to)
    return url


class UrlSplitterTests(unittest.TestCase):
    """Verify URL parsing behavior owned by paths.urlSplitter.urlAssign."""

    def test_web_url_components_and_query_are_split(self):
        """Existing legacy web URL parsing assertions live here now."""
        url = URL("http://www.fooblatz.com/the/path/file.php?name=val")

        self.assertEqual(url.protocol, "http")
        self.assertEqual(url.host, "www.fooblatz.com")
        self.assertEqual(url.domain, "fooblatz.com")
        self.assertEqual(url.subdomain, "www")
        self.assertIsNone(url.port)
        self.assertEqual(url.path, "the/path")
        self.assertEqual(url.resource, "file.php")
        self.assertEqual(url.fullPath, "the/path/file.php")
        self.assertIsNone(url.filePath)
        self.assertEqual(url["name"], "val")

    def test_ip_url_auth_and_port_are_split(self):
        """Existing legacy IP URL parsing assertions live here now."""
        url = URL("http://ralph:secret@192.168.1.47:400/")

        self.assertEqual(url.protocol, "http")
        self.assertEqual(url.username, "ralph")
        self.assertEqual(url.password, "secret")
        self.assertEqual(url.host, "192.168.1.47")
        self.assertEqual(url.domain, "192.168.1.47")
        self.assertIsNone(url.subdomain)
        self.assertEqual(url.port, 400)
        self.assertIsNone(url.resource)
        self.assertIsNone(url.fullPath)
        self.assertIsNone(url.filePath)

    def test_assigning_none_clears_existing_parts(self):
        """Assigning None exits after clearing the existing URL state."""
        url = make_base_url("http://example.com/path/file.txt?x=1#frag=yes")

        url.assign(None, None)

        self.assertEqual(url.scheme, "")
        self.assertIsNone(url.host)
        self.assertIsNone(url.port)
        self.assertEqual(url.path, "")
        self.assertFalse(url.isUNC)
        self.assertEqual(url.fragment, "")
        self.assertEqual(list(url.cgi.items()), [])
        self.assertEqual(url.fragments, {})

    def test_assigning_blank_string_clears_existing_parts(self):
        """Blank strings are normalized to None by _getUrlString."""
        url = make_base_url("http://example.com/path/file.txt?x=1#frag=yes")

        url.assign("   ", None)

        self.assertEqual(url.scheme, "")
        self.assertIsNone(url.host)
        self.assertIsNone(url.port)
        self.assertEqual(url.path, "")
        self.assertEqual(url.fragment, "")
        self.assertEqual(list(url.cgi.items()), [])

    def test_assigning_url_object_copies_mutable_parts(self):
        """Assigning a URL object copies query and fragment dictionaries."""
        original = URL("http://example.com/one/two.txt?tag=one#row=2")
        copied = make_base_url(original)

        copied.cgi["tag"] = "changed"
        copied.fragments["row"] = "9"

        self.assertEqual(original.cgi["tag"], "one")
        self.assertEqual(original.fragments["row"], "2")
        self.assertEqual(copied.cgi["tag"], "changed")
        self.assertEqual(copied.fragments["row"], "9")

    def test_file_url_prefer_local_rewrites_host_to_path(self):
        """file://name is treated as local when prefer-local is enabled."""
        url = make_base_url("file://folder/report.txt")

        self.assertEqual(url.protocol, "file")
        self.assertEqual(url.host, "localhost")
        self.assertEqual(url.fullPath, "folder/report.txt")

    def test_file_url_can_preserve_nonlocal_host(self):
        """Disabling prefer-local preserves the host in file://host/path."""
        url = make_base_url(None)
        url.filesUrlPreferLocal = False

        url.assign("file://server/share.txt", None)

        self.assertEqual(url.protocol, "file")
        self.assertEqual(url.host, "server")
        self.assertEqual(url.fullPath, "share.txt")
        self.assertFalse(url.isUNC)

    def test_windows_drive_path_is_normalized_to_file_url_parts(self):
        """Drive-letter paths are normalized into file URL components."""
        url = make_base_url("c:/the/path/file.txt")

        self.assertEqual(url.protocol, "file")
        self.assertEqual(url.host, "localhost")
        self.assertEqual(url.path, "c:/the/path")
        self.assertEqual(url.resource, "file.txt")
        self.assertEqual(url.fullPath, "c:/the/path/file.txt")

    def test_filename_line_and_char_suffix_becomes_fragment(self):
        """file.txt:line,char suffixes are converted to RFC 5147 fragments."""
        url = make_base_url("file.txt:10-11,3-7")

        self.assertEqual(url.protocol, "file")
        self.assertEqual(url.fullPath, "file.txt")
        self.assertEqual(url.fragment, "line=10,11;char=3,7")
        self.assertEqual(url.fragments, {"line": "10,11", "char": "3,7"})

    def test_url_file_fragment_is_parsed_without_suffix_rewrite(self):
        """Existing URL fragments are parsed directly into fragment fields."""
        url = URL("file:///tmp/example.txt#line=2-5&char=3-7")

        self.assertEqual(url.protocol, "file")
        self.assertEqual(url.path, "tmp")
        self.assertEqual(url.resource, "example.txt")
        self.assertEqual(url.fragments, {"line": "2-5", "char": "3-7"})

    def test_file_url_unc_form_marks_unc(self):
        """The file://///server/share form is split as a UNC path."""
        url = URL(r"file://///myserver/path/somefile.doc")

        self.assertEqual(url.protocol, "file")
        self.assertEqual(url.host, "myserver")
        self.assertTrue(url.isUNC)


if __name__ == "__main__":
    unittest.main()
