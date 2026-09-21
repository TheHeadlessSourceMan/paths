"""Unit tests for HTTP method conversion."""
import unittest

from paths import HttpMethod, asHttpMethod


class HttpMethodTests(unittest.TestCase):
    """Verify HTTP method enum values and conversion behavior."""

    def test_enum_contains_supported_methods(self):
        """All supported HTTP methods are represented by the enum."""
        self.assertEqual(
            [method.name for method in HttpMethod],
            ["GET", "POST", "UPDATE", "DELETE", "OPTIONS"],
        )
        self.assertEqual(
            [method.value for method in HttpMethod],
            ["GET", "POST", "UPDATE", "DELETE", "OPTIONS"],
        )

    def test_enum_input_is_returned_unchanged(self):
        """Passing an enum member preserves its identity."""
        method = HttpMethod.POST

        self.assertIs(asHttpMethod(method), method)

    def test_string_input_is_case_insensitive(self):
        """String methods are normalized to uppercase enum members."""
        self.assertIs(asHttpMethod("get"), HttpMethod.GET)
        self.assertIs(asHttpMethod("PoSt"), HttpMethod.POST)
        self.assertIs(asHttpMethod("OPTIONS"), HttpMethod.OPTIONS)

    def test_enum_values_are_converted_to_members(self):
        """Enum values resolve to their corresponding enum members."""
        self.assertIs(asHttpMethod(HttpMethod.DELETE.value), HttpMethod.DELETE)

    def test_unknown_method_raises_value_error(self):
        """Unsupported method names are rejected by enum construction."""
        with self.assertRaises(ValueError):
            asHttpMethod("PATCH")


if __name__ == "__main__":
    unittest.main()
