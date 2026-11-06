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

    def test_linux_and_macos_rows_remain_byte_identical_to_review(self):
        # Empreintes figées des tranches relues : un clone superficiel de la CI
        # n'a pas l'historique, et comparer à HEAD ne prouve rien.
        import hashlib

        def exact_array(raw, key):
            tail = raw.split(('"' + key + '":').encode(), 1)[1].lstrip().decode('utf-8')
            _, end = json.JSONDecoder().raw_decode(tail)
            return tail[:end].encode('utf-8')

        expected = {
            'licenses/system-libraries.lock.json:libraries': 'e66c6dcbb43399a84dcaa92a68272c3098440221c1c3a2a50225509459d48a3f',
            'licenses/system-libraries.lock.json:macos_libraries': '348871bb2245e775d7a8b54f358dfe5c98ecdf5d0de3fd3527436e261a067c2a',
            'licenses/cpython-components.lock.json:components': 'bbce12bd0a722ef7ba9d91ff851685cb8571180e75345fc445b0768ad6c22647',
            'licenses/cpython-components.lock.json:files': '446a02c3f2acfef8df12d0d6b8ebd7aee5adbc0d0bf344e6bfca61f742bd5583',
            'licenses/cpython-components.lock.json:macos_components': '7df04effeedb9754fcc482f6a8d077ee9176f20878db3aec3768608e9ce532c9',
            'licenses/cpython-components.lock.json:macos_files': 'f686d164a8854478a0a209a643b385bbd2ad210bbc72babe6879016b0c9de604',
            'licenses/system-linux/evidence-v0820.json': '4f07135c401682864b09c69d89c23b28852a712106c8088ba0dced64ca5b02c6',
            'licenses/cpython/evidence-v0820.json': '11116ab401bbff6d8e2c09c3292d9385bc7f1682a448bbfb98a0b0b778dcb151',
            'licenses/system-macos/evidence-v0830.json': 'f27d2e7e6df3847f4c88b6f59517e4c625fa2b55dc88788f5ce6c9fb4234d624',
            'licenses/cpython/evidence-v0830-macos.json': 'e960f6fa65026e40ae37af91ae64b0cea16a09ce2ea5bc21caaca1aabd4ed786',
        }
        for name, digest in expected.items():
            path, _, key = name.partition(':')
            raw = (ROOT / path).read_bytes()
            with self.subTest(name=name):
                self.assertEqual(hashlib.sha256(exact_array(raw, key) if key else raw).hexdigest(), digest)
