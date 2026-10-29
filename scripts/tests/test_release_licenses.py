"""Contrats du générateur, exécutables sans le backend ni le réseau."""
import importlib.util
import json
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

    def test_check_rejects_platform_dependent_line_endings(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'THIRD_PARTY_LICENSES'
            target.write_bytes('Licence tierce\r\nTexte complet\r\n'.encode('utf-8'))
            with self.assertRaises(ValueError):
                self.m.check_output(target, 'Licence tierce\nTexte complet\n')
            target.write_bytes('Licence tierce\nTexte complet\n'.encode('utf-8'))
            self.m.check_output(target, 'Licence tierce\nTexte complet\n')

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

    def test_unknown_python_source_is_not_silently_omitted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for file in ['package-lock.json', 'src/frontend/package-lock.json']:
                path = root / file
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps({'packages': {}}))
            cargo = root / 'src/frontend/src-tauri/Cargo.lock'
            cargo.parent.mkdir(parents=True)
            cargo.write_text('package = []')
            (root / 'uv.lock').write_text(
                '[[package]]\nname = "thirdparty"\nversion = "1"\n'
                '[package.source]\ngit = "https://example.invalid/library"\n'
            )
            (root / 'licenses').mkdir()
            for name in ['native-components.lock.json', 'runtime-wheels.lock.json']:
                (root / 'licenses' / name).write_text('[]')
            with self.assertRaises(ValueError):
                self.m.locked_packages(root)

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
