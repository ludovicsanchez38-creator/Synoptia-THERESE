"""Contrats du générateur, exécutables sans le backend ni le réseau."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'third_party_licenses.py'


class LicensesTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('licenses', SCRIPT)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)

    def test_copyleft_expressions_and_notices(self):
        self.assertEqual(self.m.copyleft('MIT OR LGPL-2.1-or-later'), ['LGPL'])
        self.assertEqual(self.m.copyleft('AGPL-3.0-only AND GPL-2.0-or-later'), ['AGPL', 'GPL'])
        self.assertEqual(self.m.copyleft('MIT'), [])
        self.assertEqual(self.m.copyleft('GNU GENERAL PUBLIC LICENSE\nVersion 3'), ['GPL'])

    def test_archive_paths_are_not_extracted(self):
        self.assertTrue(self.m.is_notice('../../LICENSE'))
        self.assertFalse(self.m.is_notice('src/license_checker.py'))
        self.assertTrue(self.m.is_notice('package/licenses/THIRD_PARTY.txt'))

    def test_missing_changed_and_stale_output_fail(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / 'THIRD_PARTY_LICENSES'
            with self.assertRaises(ValueError):
                self.m.check_output(target, 'expected')
            target.write_text('stale')
            with self.assertRaises(ValueError):
                self.m.check_output(target, 'expected')
            target.write_text('expected')
            self.m.check_output(target, 'expected')

    def test_inventory_rejects_missing_package_and_empty_text(self):
        packages = [{'id': 'npm:a@1', 'artifact': 'https://example.test/a', 'integrity': 'sha256:a'}]
        with self.assertRaises(ValueError):
            self.m.validate_inventory(packages, [])
        with self.assertRaises(ValueError):
            self.m.validate_inventory(packages, [{'id': 'npm:a@1', 'notices': []}])

    def test_authors_alone_are_not_a_license(self):
        row = {'id': 'cargo:example@1', 'artifact': 'https://example.test/a', 'integrity': 'sha256:a'}
        with self.assertRaises(ValueError):
            self.m.validate_inventory([row], [{**row, 'notices': [{'path': 'AUTHORS', 'text': 'Authors list'}]}])

    def test_lock_digest_changes_even_if_versions_do_not(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'uv.lock').write_text('version = 1')
            first = self.m.lock_digest(root, ['uv.lock'])
            (root / 'uv.lock').write_text('version = 2')
            self.assertNotEqual(first, self.m.lock_digest(root, ['uv.lock']))

    def test_deterministic_text_deduplication(self):
        rows = [{'id': 'npm:b@1', 'license': 'MIT', 'notices': [{'path': 'LICENSE', 'text': 'same'}]},
                {'id': 'npm:a@1', 'license': 'GPL-3.0', 'notices': [{'path': 'COPYING', 'text': 'same'}]}]
        self.assertEqual(self.m.render(rows, 'digest'), self.m.render(list(reversed(rows)), 'digest'))
        self.assertEqual(self.m.render(rows, 'digest').count('\nsame\n'), 1)
        self.assertIn('GPL', self.m.render(rows, 'digest'))


if __name__ == '__main__':
    unittest.main()
