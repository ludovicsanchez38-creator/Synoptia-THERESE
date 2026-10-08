"""Tests purs : octets et parseur, aucune compilation/exécution du profil."""
from __future__ import annotations

import unittest
from pathlib import Path

from verify_profile import ADDITION, expected_diff, parse_sbpl, validate_candidate

HERE = Path(__file__).resolve().parent


class TargetedProfileTests(unittest.TestCase):
    def setUp(self):
        self.base = (HERE / "preimage-chrome.sb").read_bytes()
        self.candidate = (HERE / "chrome.sb").read_bytes()

    def test_exact_candidate(self):
        result = validate_candidate(self.base, self.candidate)
        self.assertEqual(result["added_rules"], 3)
        self.assertFalse(result["admitted"])
        self.assertFalse(result["compiled_or_executed_profile"])

    def test_original_prefix_and_forms(self):
        self.assertTrue(self.candidate.startswith(self.base))
        self.assertEqual(parse_sbpl(self.candidate.decode())[:-3], parse_sbpl(self.base.decode()))

    def test_forward_diff_exact(self):
        self.assertEqual((HERE / "PROFILE.diff").read_text(),
                         expected_diff(self.base.decode(), self.candidate.decode()))

    def test_inverse_diff_exact(self):
        self.assertEqual((HERE / "PROFILE-INVERSE.diff").read_text(),
                         expected_diff(self.base.decode(), self.candidate.decode(), inverse=True))

    def test_missing_rule_refused(self):
        self.assert_rejected(self.candidate.replace(
            b'(allow mach-lookup (global-name "com.apple.CARenderServer"))\n', b""))

    def test_iokit_wildcard_refused(self):
        self.assert_rejected(self.candidate.replace(b'"AGXDeviceUserClient"', b'"*"'))

    def test_other_iokit_class_refused(self):
        self.assert_rejected(self.candidate.replace(b'"IOSurfaceRootUserClient"', b'"OtherUserClient"'))

    def test_global_mach_refused(self):
        self.assert_rejected(self.candidate + b"(allow mach-lookup)\n")

    def test_pasteboard_refused(self):
        self.assert_rejected(self.candidate + b'(allow mach-lookup (global-name "com.apple.pasteboard.1"))\n')

    def test_network_permission_refused(self):
        self.assert_rejected(self.candidate + b"(allow network*)\n")

    def test_original_rule_modified_refused(self):
        self.assert_rejected(self.candidate.replace(b"(deny default)", b"(allow default)"))

    def test_modified_preimage_refused(self):
        with self.assertRaisesRegex(ValueError, "préimage"):
            validate_candidate(self.base + b"; change\n", self.candidate)

    def test_parser_rejects_unbalanced(self):
        with self.assertRaises(ValueError):
            parse_sbpl(ADDITION + "(")

    def test_parser_rejects_unterminated_string(self):
        with self.assertRaises(ValueError):
            parse_sbpl('(allow mach-lookup (global-name "broken))')

    def assert_rejected(self, candidate):
        with self.assertRaisesRegex(ValueError, "delta"):
            validate_candidate(self.base, candidate)


if __name__ == "__main__":
    unittest.main(verbosity=2)
