"""Contre-épreuves du catalogue macOS sur les empreintes publiées."""
import copy
import hashlib
import importlib
import io
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
cpython = importlib.import_module('cpython_components')
system = importlib.import_module('system_libraries')


class MacOSCatalogTests(unittest.TestCase):
    def test_three_new_natives_have_their_reviewed_components(self):
        catalog = system.load_catalog(ROOT)
        for prefix, expected in (
            ('_lzma.', {'liblzma-5.2.3'}),
            ('_sqlite3.', {'pysqlite', 'sqlite-3.50.4'}),
        ):
            row = next(f for f in catalog['cpython']['macos_files']
                       if f['name'].startswith(prefix))
            record = cpython.identify(row['sha256'], 'macOS', catalog['cpython'])
            self.assertEqual({c['id'] for c in record['components']}, expected)
        row = next(r for r in catalog['macos_libraries'] if r['name'] == 'libncurses.6.dylib')
        with patch.object(system, 'dpkg_identity', side_effect=AssertionError('Linux only')):
            record = system.match_system(Path(row['name']), row['sha256'], catalog, 'macOS')
        self.assertEqual(record['license'], 'X11')

    def test_upstream_notice_replay_refuses_altered_copy(self):
        import macos_sources

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path = root / 'source.tar.gz'
            source = b'prefix\nBEGIN\noriginal notice\nEND\nsuffix\n'
            with tarfile.open(archive_path, 'w:gz') as archive:
                member = tarfile.TarInfo('source/COPYING')
                member.size = len(source)
                archive.addfile(member, io.BytesIO(source))
            notice_path = root / 'notice.txt'
            notice_path.write_bytes(b'BEGIN\noriginal notice\nEND\n')
            def sha(raw):
                return hashlib.sha256(raw).hexdigest()
            proof = {
                'sha256': sha(archive_path.read_bytes()), 'size': archive_path.stat().st_size,
                'members': [{
                    'path': 'source/COPYING', 'sha256': sha(source), 'size': len(source),
                    'extraction': {'start': 'BEGIN\n', 'end': 'END\n'},
                    'notice': {'path': 'notice.txt', 'sha256': sha(notice_path.read_bytes())},
                }],
            }
            self.assertEqual(macos_sources.verify_archive(archive_path, proof, root), 1)
            notice_path.write_bytes(b'BEGIN\naltered notice\nEND\n')
            proof['members'][0]['notice']['sha256'] = sha(notice_path.read_bytes())
            with self.assertRaisesRegex(ValueError, 'Notice amont différente'):
                macos_sources.verify_archive(archive_path, proof, root)

    def test_cpython_file_requires_its_reviewed_macos_evidence(self):
        catalog = cpython.load(ROOT)
        row = next(f for f in catalog['macos_files'] if f['name'].startswith('pyexpat.'))
        record = cpython.identify(row['sha256'], 'macOS', catalog)
        self.assertEqual(record['cpython_sha256'], row['sha256'])
        self.assertEqual({c['id'] for c in record['components']}, {'expat', 'expat-siphash'})
        self.assertIsNone(cpython.identify('0' * 64, 'macOS', catalog))

    def test_macos_system_file_needs_proof_but_not_dpkg(self):
        catalog = system.load_catalog(ROOT)
        row = next(r for r in catalog['macos_libraries'] if r['name'] == 'libssl.3.dylib')
        with patch.object(system, 'dpkg_identity', side_effect=AssertionError('dpkg is Linux only')):
            record = system.match_system(Path(row['name']), row['sha256'], catalog, 'macOS')
        self.assertEqual(record['catalog_sha256'], row['sha256'])
        with self.assertRaisesRegex(ValueError, 'hors catalogue'):
            system.match_system(Path(row['name']), '0' * 64, catalog, 'macOS')

    def test_macos_identity_and_license_changes_are_rejected(self):
        original = system.load_catalog(ROOT)
        for key, value in (('binary_package_url', 'https://example.test/python.pkg'),
                           ('binary_member', 'wrong/member'),
                           ('binary_package_sha256', '0' * 64),
                           ('license', 'UNKNOWN')):
            changed = copy.deepcopy(original)
            row = next(r for r in changed['macos_libraries'] if r['name'] == 'libssl.3.dylib')
            row[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                system.validate_catalog(changed, ROOT)

    def test_unknown_macos_extension_remains_rejected(self):
        work = ROOT / '.work-t2/round7'
        work.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=work) as directory:
            stdlib = Path(directory)
            binary = stdlib / 'lib-dynload/pyexpat.cpython-313-darwin.so'
            binary.parent.mkdir()
            binary.write_bytes(b'\xcf\xfa\xed\xfeunreviewed')
            source = {'path': str(binary), 'sha256': system.file_sha(binary)}
            with (patch.object(system.sysconfig, 'get_path', return_value=str(stdlib)),
                  patch.object(system.sys, 'version_info', (3, 13, 17)),
                  patch.object(system.sys, 'stdlib_module_names', frozenset({'pyexpat'})),
                  patch.object(system.importlib.machinery, 'EXTENSION_SUFFIXES', ['.cpython-313-darwin.so']),
                  self.assertRaisesRegex(ValueError, 'hors catalogue')):
                system.classify(source, system.load_catalog(ROOT), [], {}, 'macOS')

    def test_linux_catalog_rows_are_byte_identical_to_base(self):
        # Empreintes figées des tranches relues : un clone superficiel de la CI
        # n'a pas l'historique, et comparer à HEAD ne prouve rien.
        import hashlib
        import json as _json

        def exact_array(raw, key):
            tail = raw.split(('"' + key + '":').encode(), 1)[1].lstrip().decode('utf-8')
            _, end = _json.JSONDecoder().raw_decode(tail)
            return tail[:end].encode('utf-8')

        expected = {
            'licenses/system-libraries.lock.json:libraries': 'e66c6dcbb43399a84dcaa92a68272c3098440221c1c3a2a50225509459d48a3f',
            'licenses/cpython-components.lock.json:components': 'bbce12bd0a722ef7ba9d91ff851685cb8571180e75345fc445b0768ad6c22647',
            'licenses/cpython-components.lock.json:files': '446a02c3f2acfef8df12d0d6b8ebd7aee5adbc0d0bf344e6bfca61f742bd5583',
            'licenses/system-linux/evidence-v0820.json': '4f07135c401682864b09c69d89c23b28852a712106c8088ba0dced64ca5b02c6',
            'licenses/cpython/evidence-v0820.json': '11116ab401bbff6d8e2c09c3292d9385bc7f1682a448bbfb98a0b0b778dcb151',
        }
        for name, digest in expected.items():
            path, _, key = name.partition(':')
            raw = (ROOT / path).read_bytes()
            with self.subTest(name=name):
                self.assertEqual(hashlib.sha256(exact_array(raw, key) if key else raw).hexdigest(), digest)


if __name__ == '__main__':
    unittest.main()
