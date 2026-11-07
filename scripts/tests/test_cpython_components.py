"""Régression de la contre-épreuve de relecture 6 : véritables octets v0.82.0."""
import gzip
import copy
import json
import shutil
import sys
import tempfile
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import system_libraries as system
import cpython_components as components


class CPythonComponentsTests(unittest.TestCase):
    def setUp(self):
        work = ROOT / '.work-t2/round7'
        work.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix='cpython-', dir=work))
        # Copier seulement les preuves nécessaires, sans roues ni sources de test.
        catalog = system.load_catalog(ROOT)
        names = [system.CATALOG, components.CATALOG, 'licenses/inventory.json',
                 catalog['evidence']['path'], catalog['macos_evidence']['path'], catalog['windows_evidence']['path'],
                 catalog['cpython']['evidence']['path'], catalog['cpython']['macos_evidence']['path'],
                 catalog['cpython']['windows_evidence']['path'],
                 'licenses/system-macos/License.rtf',
                 'licenses/system-windows/python-3.13.17-LICENSE.txt',
                 system.VS_LICENSE_TERMS, system.VS_DISTRIBUTABLE_LIST,
                 *{r['notice']['path'] for r in catalog['libraries'] + catalog['macos_libraries'] + catalog['windows_libraries']},
                 *{r['path'] for r in components.notice_files(catalog['cpython'])},
                 'scripts/system_libraries.py', 'scripts/cpython_components.py',
                 'scripts/nsis_installer.py', 'scripts/verify_packaged_licenses.py']
        for name in names:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        shutil.copyfile(ROOT / 'THIRD_PARTY_LICENSES', self.root / 'THIRD_PARTY_LICENSES')
        self.stdlib = self.root / 'stdlib'
        self.engine = self.root / 'src/frontend/src-tauri/binaries/backend-libs'
        entries = []
        for compressed in sorted((ROOT / 'scripts/tests/fixtures/cpython-3.13.17').glob('*.so.gz')):
            name = compressed.name.removesuffix('.gz')
            raw = gzip.decompress(compressed.read_bytes())
            hashes = {'pyexpat': '83b0fc81ac9b06f2871ef4c2c884954d8f0cf258d3408d7ddb5dc58e161709e0',
                      '_decimal': 'a7760dba58eb7feb93dfbb508d073383c5651943bda673591728037e779732f5'}
            self.assertEqual(system.sha(raw), hashes[name.split('.')[0]])
            source = self.stdlib / 'lib-dynload' / name
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(raw)
            relative = 'python3.13/lib-dynload/' + name
            target = self.engine / '_internal' / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            entries.append((relative, str(source), 'EXTENSION'))
        system.record_analysis(entries, self.root)
        for target, attribute, value in (
            (system.sysconfig, 'get_path', lambda name: str(self.stdlib)),
            (system.sys, 'version_info', (3, 13, 17)),
            (system.importlib.machinery, 'EXTENSION_SUFFIXES', ['.cpython-313-x86_64-linux-gnu.so']),
        ):
            mock = patch.object(target, attribute, value)
            mock.start()
            self.addCleanup(mock.stop)

    def test_real_extensions_cannot_receive_psf_only(self):
        manifest = system.build_inventory('Linux', self.root)
        self.assertEqual(len(manifest['files']), 2)
        for name, record in manifest['files'].items():
            with self.subTest(name=name):
                self.assertNotEqual(record['license'], 'PSF-2.0')
                self.assertEqual(len(record['components']), 2 if 'pyexpat' in name else 1)
                c = record['components'][0]
                self.assertEqual((c['id'], c['version'], c['license']),
                                 ('expat', '2.8.5', 'MIT') if 'pyexpat' in name else
                                 ('libmpdec', '2.5.1', 'BSD-2-Clause'))
        self.assertEqual(system.load_build(self.root), manifest)

    def old_notices(self):
        old = gzip.decompress((ROOT / 'scripts/tests/fixtures/cpython-3.13.17/THIRD_PARTY_LICENSES-round6.txt.gz').read_bytes())
        self.assertEqual(system.sha(old), '1a3b4b00637a184daca7a2f2bb0a96ccfee237892cf15a3ec9826beb8888c23a')
        return old

    def test_old_notices_are_rejected_even_with_matching_notice_hash(self):
        old = self.old_notices()
        (self.root / 'THIRD_PARTY_LICENSES').write_bytes(old)
        with self.assertRaisesRegex(ValueError, 'notice|Notice'):
            system.build_inventory('Linux', self.root)
        self.assertFalse((self.root / system.BUILD).exists())

    def test_real_deb_cli_refuses_old_notices_then_accepts_completed_notices(self):
        manifest = system.build_inventory('Linux', self.root)
        tree = self.root / 'deb-tree'
        (tree / 'DEBIAN').mkdir(parents=True)
        (tree / 'DEBIAN/control').write_text(
            'Package: therese-cpython-test\nVersion: 1\nArchitecture: amd64\n'
            'Maintainer: Test <test@example.test>\nDescription: CPython real binary counterproof\n')
        resource = tree / 'usr/lib/THERESE'
        shutil.copytree(self.engine, resource / 'binaries/backend-libs')
        artifact = self.root / 'src/frontend/src-tauri/target/release/bundle/deb/cpython.deb'
        artifact.parent.mkdir(parents=True)
        old = self.old_notices()
        complete = (ROOT / 'THIRD_PARTY_LICENSES').read_bytes()
        proof = self.root / '.work-release/installer-proofs/cpython.deb.json'
        for label, notices, expected_code in [('old', old, 1), ('complete', complete, 0)]:
            (self.root / 'THIRD_PARTY_LICENSES').write_bytes(notices)
            (resource / 'THIRD_PARTY_LICENSES').write_bytes(notices)
            manifest['notices_sha256'] = system.sha(notices)
            raw = json.dumps(manifest, ensure_ascii=False, indent=2) + '\n'
            (self.root / system.BUILD).write_text(raw)
            (resource / 'system-libraries.json').write_text(raw)
            subprocess.run(['dpkg-deb', '--build', '--root-owner-group', str(tree), str(artifact)],
                           capture_output=True, check=True)
            result = subprocess.run([sys.executable, '-B', str(self.root / 'scripts/verify_packaged_licenses.py'),
                                     '--platform', 'Linux'], capture_output=True, text=True)
            (self.root / (label + '-guard.log')).write_text(result.stdout + result.stderr)
            self.assertEqual(result.returncode, expected_code, result.stdout + result.stderr)
            if label == 'old':
                self.assertIn('Notices des composants CPython', result.stderr)
                self.assertFalse(proof.exists())
            else:
                import publish_release_artifacts as publisher
                self.assertEqual(publisher.verified_proofs([artifact], self.root), [proof])
                self.assertEqual(len(json.loads(proof.read_text())['files']), 2)

    def test_inventory_cannot_omit_or_relabel_incorporated_components(self):
        original = system.build_inventory('Linux', self.root)
        for kind in ('omitted', 'version', 'license', 'notice', 'psf', 'origin', 'source', 'catalog'):
            changed = copy.deepcopy(original)
            row = next(iter(changed['files'].values()))
            if kind == 'omitted':
                row['components'] = []
            elif kind in ('version', 'license'):
                row['components'][0][kind] = 'changed'
            elif kind == 'notice':
                row['components'][0]['notices'] = []
            elif kind == 'psf':
                row['license'] = 'PSF-2.0'
            elif kind == 'origin':
                row['origin'] = 'python:fake@1'
            elif kind == 'source':
                row['origin'] = 'python:fake@1'
                row['source_sha256'] = '0' * 64
            else:
                changed['cpython_catalog_sha256'] = '0' * 64
            (self.root / system.BUILD).write_text(json.dumps(changed))
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                system.load_build(self.root)

    def test_valid_cpython_name_with_unreviewed_bytes_is_rejected(self):
        binary = next((self.stdlib / 'lib-dynload').glob('pyexpat*'))
        binary.write_bytes(binary.read_bytes() + b'additional unreviewed code')
        source = {'path': str(binary), 'sha256': system.file_sha(binary)}
        with self.assertRaisesRegex(ValueError, 'hors catalogue'):
            system.classify(source, system.load_catalog(ROOT), [], {}, 'Linux')

    def test_real_fixtures_define_components_instead_of_importing_them(self):
        for prefix, symbol, version in [('pyexpat', 'PyExpat_XML_ExpatVersion', b'expat_2.8.5'),
                                         ('_decimal', 'mpd_version', b'2.5.1')]:
            binary = next((self.stdlib / 'lib-dynload').glob(prefix + '*'))
            symbols = subprocess.check_output(['readelf', '-Ws', str(binary)], text=True)
            self.assertTrue(any(line.split()[-1:] == [symbol] and ' UND ' not in line
                                for line in symbols.splitlines()))
            self.assertIn(version + b'\0', binary.read_bytes())

    def test_expat_embeds_separate_cc0_siphash(self):
        binary = next((self.stdlib / 'lib-dynload').glob('pyexpat*'))
        symbols = subprocess.check_output(['readelf', '-Ws', str(binary)], text=True)
        self.assertTrue(any(line.split()[-1:] == ['sip24_final'] and ' UND ' not in line
                            for line in symbols.splitlines()))
        record = components.identify(system.file_sha(binary), 'Linux', components.load(ROOT))
        by_id = {c['id']: c for c in record['components']}
        self.assertIn('expat-siphash', by_id)
        self.assertEqual(by_id['expat-siphash']['license'], 'CC0-1.0')
        notice = (ROOT / by_id['expat-siphash']['notices'][0]['path']).read_text()
        self.assertIn('William Ahern', notice)
        self.assertIn('CC0 Public Domain Dedication', notice)

    def test_libpython_declares_secret_labs_sre_under_cnri_permission(self):
        # Relecture signature 7 : le moteur SRE de Secret Labs est défini dans libpython
        # (PyInit__sre, sre_match...) et son attribution est dans les octets publiés.
        catalog = components.load(ROOT)
        row = next(f for f in catalog['files'] if f['name'] == 'libpython3.13.so.1.0')
        record = components.identify(row['sha256'], 'Linux', catalog)
        by_id = {c['id']: c for c in record['components']}
        self.assertIn('sre', by_id)
        sre = by_id['sre']
        self.assertTrue(sre['version'].startswith('2.2.2;'))
        self.assertIn('v3.13.17', sre['version'])
        header = (ROOT / sre['notices'][0]['path']).read_text()
        for token in ("Secret Labs' Regular Expression Engine", 'Copyright (c) 1997-2001 by Secret Labs AB',
                      "redistributed under CNRI's", 'Python 1.6 license'):
            with self.subTest(token=token):
                self.assertIn(token, header)
        self.assertEqual(sre['notices'][0]['upstream']['url'],
                         'https://raw.githubusercontent.com/python/cpython/v3.13.17/Modules/_sre/sre.c')
        cnri = next(n for n in sre['notices'] if n['path'] == 'licenses/cpython/LICENSE.txt')
        self.assertIn('CNRI LICENSE AGREEMENT FOR PYTHON 1.6.1', (ROOT / cnri['path']).read_text())
        evidence = json.loads((ROOT / catalog['evidence']['path']).read_text())
        self.assertIn('Modules/_sre/sre.c', evidence['source_files'])
        proof = next(f for f in evidence['files'] if f['sha256'] == row['sha256'])['incorporation_evidence']['sre']
        defined = {line.split()[-1] for line in proof['defined_symbols'] if ' UND ' not in line}
        self.assertLessEqual({'PyInit__sre', 'sre_match', 'sre_search', 'sre_ucs1_match',
                              'sre_ucs2_match', 'sre_ucs4_match'}, defined)
        self.assertIn('SRE 2.2.2 Copyright (c) 1997-2002 by Secret Labs AB', proof['strings'])
        # Les notices livrées portent la composition avec SRE ; celles qui l'omettent sont refusées.
        components.require_notices(ROOT, catalog)
        self.assertIn((sre['name'] + ' — ' + sre['version']).encode(),
                      (ROOT / 'THIRD_PARTY_LICENSES').read_bytes())
        stale = copy.deepcopy(catalog)
        stale['components'] = [c for c in stale['components'] if c['id'] != 'sre']
        for f in stale['files']:
            f['components'] = [c for c in f['components'] if c != 'sre']
        current = (self.root / 'THIRD_PARTY_LICENSES').read_text(encoding='utf-8')
        without_sre = current.replace(components.render(self.root, catalog),
                                      components.render(self.root, stale))
        self.assertNotEqual(without_sre, current)
        (self.root / 'THIRD_PARTY_LICENSES').write_text(without_sre, encoding='utf-8', newline='\n')
        with self.assertRaisesRegex(ValueError, 'Notices des composants CPython'):
            components.require_notices(self.root, components.load(self.root))

    def test_catalog_bindings_and_original_notices_cannot_be_changed(self):
        original = components.load(self.root)
        for kind in ('component', 'binding', 'version', 'duplicate'):
            changed = copy.deepcopy(original)
            if kind == 'component':
                changed['components'].pop()
            elif kind == 'binding':
                next(f for f in changed['files'] if f['components'])['components'] = []
            elif kind == 'version':
                changed['components'][0]['version'] = '999'
            else:
                changed['files'].append(changed['files'][0])
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                components.validate(changed, self.root)
        notice = original['components'][0]['notices'][0]
        (self.root / notice['path']).write_bytes(b'incomplete original')
        with self.assertRaisesRegex(ValueError, 'notice CPython modifiée'):
            components.load(self.root)

    def test_library_and_other_extensions_have_reviewed_compositions(self):
        catalog = components.load(ROOT)
        expected = {'libpython3.13.so.1.0': {'mimalloc', 'siphash', 'dtoa', 'cfuhash', 'gus',
                                         'unicode', 'locale-wrapper', 'getopt', 'unicode-string', 'sre'},
                    '_blake2': {'blake2'}, '_random': {'mt19937'},
                    '_md5': {'hacl', 'karamel'}, '_sha1': {'hacl', 'karamel'},
                    '_sha2': {'hacl', 'karamel'}, '_sha3': {'hacl', 'karamel'},
                    'unicodedata': {'unicode'}}
        for prefix, ids in expected.items():
            row = next(f for f in catalog['files'] if f['name'].split('.cpython')[0] == prefix)
            record = components.identify(row['sha256'], 'Linux', catalog)
            self.assertEqual({c['id'] for c in record['components']}, ids)
            components.verify_record({'sha256': row['sha256'], **record}, 'Linux', catalog)
        self.assertEqual(len(catalog['files']), 58)
        self.assertEqual(len(catalog['components']), 21)

    def test_complement_rejects_other_deb_before_creating_output(self):
        wrong = self.root / 'wrong.deb'
        wrong.write_bytes(b'not the published installer')
        target = self.root / 'complement/notices.txt'
        result = subprocess.run([sys.executable, '-B', str(self.root / 'scripts/cpython_components.py'),
                                 'complement', '--deb', str(wrong), '--output', str(target)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('SHA-256 du .deb', result.stderr)
        self.assertFalse(target.parent.exists())

    def test_original_headers_include_authors_and_full_permission(self):
        for filename, tokens in {
            'MT19937-LICENSE.txt': ['Makoto Matsumoto', 'Redistribution and use', 'THIS SOFTWARE'],
            'SipHash-LICENSE.txt': ['Marek Majkowski', 'Permission is hereby granted', 'THE SOFTWARE'],
            'HACL-LICENSE.txt': ['HACL* Contributors', 'Permission is hereby granted', 'THE SOFTWARE'],
            'libmpdec-LICENSE.txt': ['Stefan Krah', 'Redistribution and use', 'THIS SOFTWARE'],
            'expat-COPYING.txt': ['Clark Cooper', 'Permission is hereby granted', 'THE SOFTWARE'],
        }.items():
            text = (ROOT / 'licenses/cpython' / filename).read_text()
            for token in tokens:
                with self.subTest(filename=filename, token=token):
                    self.assertIn(token, text)


if __name__ == '__main__':
    unittest.main()
