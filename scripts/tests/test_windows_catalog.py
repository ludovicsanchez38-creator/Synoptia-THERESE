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
        self.assertEqual(len(catalog['windows_libraries']), 10)
        self.assertEqual(sum(r['distribution'] == 'python.org CPython 3.13.17 Windows x64'
                             for r in catalog['windows_libraries']), 7)
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

    # Décision de Ludo du 06/11/2026 (carte val-2026-11-06-24) : livrer le runtime
    # VC++ du redistribuable Visual Studio, notice « Distributable Code » jointe.
    # Empreintes des octets du runner (run 42266635353, artefact releve-Windows).
    VISUAL_STUDIO = {
        'msvcp140.dll': '7c26614e1d733892c2deac7e245ce115504b1d80592dd0a01b08e3e5a55f89ca',
        'msvcp140_1.dll': '206c931bf90fdad8816de3b5e2ef80b2bcaa9406c89ecc05fe6fddffe251e982',
        'vcomp140.dll': '95d4ce4a6802d1e18b5e0e1722cc30ea72ca7e033f83828f05c0b7b993fe7cbf',
    }

    def test_visual_studio_runtime_is_cataloged_with_microsoft_notice(self):
        catalog = system.load_catalog(ROOT)
        rows = {r['name']: r for r in catalog['windows_libraries'] if r['source_package'] == 'visual-studio-redist'}
        self.assertEqual(set(rows), set(self.VISUAL_STUDIO))
        notice = (ROOT / system.VS_REDIST_NOTICE).read_text(encoding='utf-8')
        rendered = system.render_notices(ROOT)
        for name, digest in self.VISUAL_STUDIO.items():
            row = rows[name]
            self.assertEqual((row['sha256'], row['version']), (digest, '14.51.36247.0'))
            self.assertEqual(row['notice']['path'], system.VS_REDIST_NOTICE)
            with patch.object(system, 'dpkg_identity', side_effect=AssertionError('Linux only')):
                record = system.match_system(Path(name), digest, catalog, 'Windows')
            self.assertEqual(record['origin'], 'system:Microsoft Visual C++ Redistributable@14.51.36247.0')
            self.assertEqual(record['license'], 'LicenseRef-Microsoft-Distributable-Code')
            self.assertFalse(record['source_required'])
            self.assertIn(name, notice)
            self.assertIn('SHA-256 : ' + digest, rendered)
        for passage in ('8. DISTRIBUTABLE CODE.', 'Distribution Requirements.', 'Distribution Restrictions.',
                        'Visual C++ Runtime Files', 'debug_nonredist', 'EULAID: VS2026_Comm_ENU.1033'):
            self.assertIn(passage, notice)
        self.assertIn(notice, rendered)

    def test_other_runtime_bytes_remain_rejected(self):
        catalog = system.load_catalog(ROOT)
        with tempfile.TemporaryDirectory() as directory:
            for name in ('msvcp140.dll', 'concrt140.dll'):
                path = Path(directory) / name
                path.write_bytes(b'MZ' + name.encode())
                source = {'path': str(path), 'sha256': system.file_sha(path)}
                with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'hors catalogue'):
                    system.classify(source, catalog, [], {}, 'Windows')

    def _validate_with_windows_evidence(self, mutate):
        catalog = json.loads((ROOT / system.CATALOG).read_text(encoding='utf-8'))
        real = system.checked_file

        def altered(root, item):
            raw = real(root, item)
            if item is catalog['windows_evidence']:
                data = json.loads(raw)
                mutate(data)
                return json.dumps(data).encode('utf-8')
            return raw
        with patch.object(system, 'checked_file', altered):
            system.validate_catalog(catalog, ROOT)

    def test_visual_studio_runtime_proof_is_closed(self):
        def entry(data, name):
            return next(e for e in data['visual_studio_redist']['libraries'] if e['catalog_row']['name'] == name)

        def path(name, value):
            return lambda d: entry(d, name).__setitem__('runner_path', value)

        def fourth(data):
            extra = copy.deepcopy(entry(data, 'msvcp140.dll'))
            extra['catalog_row']['name'] = 'concrt140.dll'
            data['visual_studio_redist']['libraries'].append(extra)

        vs_root = r'C:\Program Files\Microsoft Visual Studio\18\Enterprise\VC\Redist\MSVC\14.51.36231'
        self._validate_with_windows_evidence(lambda data: None)
        sabotages = {
            'refus remis': lambda d: d['excluded'].append({'name': 'msvcp140.dll'}),
            'JDK du runner': path('msvcp140.dll', r'C:\hostedtoolcache\windows\Java_Temurin-Hotspot_jdk'
                                                   r'\17.0.21-9\x64\bin\msvcp140.dll'),
            'ImageMagick': path('vcomp140.dll', r'C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\vcomp140.dll'),
            'OpenMP.LLVM': path('vcomp140.dll', vs_root + r'\x64\Microsoft.VC145.OpenMP.LLVM\vcomp140.dll'),
            'debug_nonredist': lambda d: d['visual_studio_redist'].__setitem__(
                'redist_root', vs_root + r'\debug_nonredist\x64'),
            'autre version MSVC': lambda d: d['visual_studio_redist'].__setitem__('redist_version', '14.52.0'),
            'version observée': lambda d: entry(d, 'msvcp140.dll')['version_observation'].__setitem__(
                'value', '14.51.36231.0'),
            'sans signataire': lambda d: entry(d, 'vcomp140.dll').__setitem__('authenticode_certificates', []),
            'notice modifiée': lambda d: d['visual_studio_redist']['notice'].__setitem__('sha256', '0' * 64),
            'conditions modifiées': lambda d: d['visual_studio_redist']['license_terms'].__setitem__(
                'sha256', '0' * 64),
            'liste modifiée': lambda d: d['visual_studio_redist']['distributable_list'].__setitem__(
                'sha256', '0' * 64),
            'licence': lambda d: entry(d, 'msvcp140_1.dll')['catalog_row'].__setitem__('license', 'MIT'),
            'quatrième DLL': fourth,
        }
        for label, mutate in sabotages.items():
            with self.subTest(sabotage=label), self.assertRaises(ValueError):
                self._validate_with_windows_evidence(mutate)

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
