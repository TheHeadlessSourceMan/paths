"""
Unit tests for MAC address helpers.
"""
import sys
import types
import unittest
from unittest.mock import patch

from paths.macAddress import MacAddress


class MacAddressTests(unittest.TestCase):
    """Verify MAC address normalization, formatting, and comparisons."""

    def test_assign_strips_separators_and_uppercases(self):
        """Input values are canonicalized to a 12-digit uppercase hex string."""
        address = MacAddress(" aa:bb-cc:dd-ee:ff ")

        self.assertEqual(address.formatted(), "AA:BB:CC:DD:EE:FF")

    def test_formatted_supports_custom_separators_and_case(self):
        """Custom separators and lowercase mode are honored during formatting."""
        address = MacAddress("aabbccddeeff")

        self.assertEqual(address.formatted("-"), "AA-BB-CC-DD-EE-FF")
        self.assertEqual(address.formatted("-", lowercase=True), "aa-bb-cc-dd-ee-ff")
        self.assertEqual(address.formatted("."), "AA.BB.CC.DD.EE.FF")

    def test_equality_compares_strings_and_mac_addresses(self):
        """Equality normalizes both kinds of inputs before comparing."""
        first = MacAddress("00-11-22-33-44-55")

        self.assertEqual(first, MacAddress("001122334455"))
        self.assertEqual(first, "00:11:22:33:44:55")
        self.assertNotEqual(first, "00:11:22:33:44:56")

    def test_repr_matches_the_default_formatter(self):
        """The repr output remains the standard colon-delimited format."""
        address = MacAddress("aa-bb-cc-dd-ee-ff")

        self.assertEqual(repr(address), "AA:BB:CC:DD:EE:FF")

    def test_ip_lookup_reads_the_arp_table(self):
        """ARP lookups resolve the IP for a standard formatted MAC address."""
        k_runner = types.ModuleType("k_runner")
        osrun_mod = types.ModuleType("k_runner.osrun")

        def fake_osrun(command):
            self.assertEqual(command, "arp -a")
            return types.SimpleNamespace(
                stdout=(
                    "Interface: 192.168.0.1 --- 0x2\n"
                    "Internet Address  Physical Address\n"
                    "192.168.0.2  00-11-22-33-44-55\n"
                )
            )

        osrun_mod.osrun = fake_osrun
        k_runner.osrun = osrun_mod

        with patch.dict(
            sys.modules,
            {"k_runner": k_runner, "k_runner.osrun": osrun_mod},
        ):
            address = MacAddress("001122334455")
            self.assertEqual(address.ip, "192.168.0.2")


if __name__ == "__main__":
    unittest.main()
