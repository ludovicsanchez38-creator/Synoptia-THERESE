"""Contre-épreuves du catalogue Windows et de son refus par défaut."""
import copy
import importlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
cpython = importlib.import_module('cpython_components')
system = importlib.import_module('system_libraries')


class WindowsCatalogTests(unittest.TestCase):
    def test_reviewed_windows_files_are_bound_to_separate_proofs(self):
        catalog = system.load_catalog(ROOT)
        self.assertEqual(len(catalog['cpython']['windows_files']), 21)
        self.assertEqual(len(catalog['windows_libraries']), 7)
        rows = catalog['cpython']['windows_files']
        for name, expected in (('_bz2.pyd', {'bzip2-1.0.8'}),
                               ('_lzma.pyd', {'liblzma-5.2.5'}),
                               ('_decimal.pyd', {'libmpdec-4.0.0'}),
                               ('_sqlite3.pyd', {'pysqlite'})):
            row = next(f for f in rows if f['name'] == name)
            record = cpython.identify(row['sha256'], 'Windows', catalog['cpython'])
            self.assertEqual({c['id'] for c in record['components']}, expected)
        self.assertIsNone(cpython.identify('0' * 64, 'Windows', catalog['cpython']))

    def test_system_windows_identity_is_checked_without_dpkg(self):
        catalog = system.load_catalog(ROOT)
        row = next(r for r in catalog['windows_libraries'] if r['name'] == 'libssl-3.dll')
        with patch.object(system, 'dpkg_identity', side_effect=AssertionError('Linux only')):
            record = system.match_system(Path(row['name']), row['sha256'], catalog, 'Windows')
        self.assertEqual(record['catalog_sha256'], row['sha256'])
        for field, value in (('binary_package_url', 'https://example.test/lib.msi'),
                             ('binary_member', 'other.dll'),
                             ('binary_package_sha256', '0' * 64),
                             ('license', 'UNKNOWN')):
            changed = copy.deepcopy(catalog)
            next(r for r in changed['windows_libraries'] if r['name'] == row['name'])[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                system.validate_catalog(changed, ROOT)

    def test_unreviewed_windows_extension_remains_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'unknown.pyd'
            path.write_bytes(b'MZunreviewed')
            source = {'path': str(path), 'sha256': system.file_sha(path)}
            with self.assertRaisesRegex(ValueError, 'hors catalogue'):
                system.classify(source, system.load_catalog(ROOT), [], {}, 'Windows')

    def test_visual_studio_dlls_have_no_catalog_rows(self):
        catalog = system.load_catalog(ROOT)
        names = {r['name'].lower() for r in catalog['windows_libraries']}
        names.update(r['name'].lower() for r in catalog['cpython']['windows_files'])
        self.assertFalse(names & {'msvcp140.dll', 'msvcp140_1.dll', 'vcomp140.dll'})

    def test_linux_and_macos_rows_remain_byte_identical_to_head(self):
        def exact_array(raw, key):
            tail = raw.split(('"' + key + '":').encode(), 1)[1].lstrip().decode('utf-8')
            _, end = json.JSONDecoder().raw_decode(tail)
            return tail[:end].encode('utf-8')

        for path, keys in ((system.CATALOG, ('libraries', 'macos_libraries')),
                           (cpython.CATALOG, ('components', 'files', 'macos_components', 'macos_files'))):
            old = subprocess.check_output(['git', 'show', 'HEAD:' + path], cwd=ROOT)
            new = (ROOT / path).read_bytes()
            for key in keys:
                with self.subTest(path=path, key=key):
                    self.assertEqual(exact_array(new, key), exact_array(old, key))
        for path in ('licenses/system-linux/evidence-v0820.json',
                     'licenses/cpython/evidence-v0820.json',
                     'licenses/system-macos/evidence-v0830.json',
                     'licenses/cpython/evidence-v0830-macos.json'):
            with self.subTest(path=path):
                self.assertEqual((ROOT / path).read_bytes(),
                                 subprocess.check_output(['git', 'show', 'HEAD:' + path], cwd=ROOT))
