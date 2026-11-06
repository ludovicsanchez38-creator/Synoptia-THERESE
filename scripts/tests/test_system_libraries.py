"""Contre-épreuves des octets embarqués et des sources système."""
import copy
import importlib.util
import json
import sys
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))


class SystemLibraryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import system_libraries
        cls.m = system_libraries

    def setUp(self):
        (ROOT / '.work-t2/round6').mkdir(parents=True, exist_ok=True)
        self.folder = Path(tempfile.mkdtemp(prefix='system-test-', dir=ROOT / '.work-t2/round6'))

    def test_native_detection_does_not_depend_on_suffix(self):
        (self.folder / 'unusual').write_bytes(b'\x7fELFhidden')
        (self.folder / 'ordinary.txt').write_text('plain data')
        self.assertEqual(set(self.m.scan_tree(self.folder)), {'unusual'})

    def test_symlink_outside_tree_blocks(self):
        (self.folder / 'escape.so').symlink_to('/usr/lib')
        with self.assertRaises(ValueError):
            self.m.scan_tree(self.folder)

    def test_uninventoried_changed_or_unknown_license_blocks(self):
        data = b'\x7fELFlibrary'
        records = {'libfixture.so': {'sha256': self.m.sha(data), 'license': 'MIT', 'origin': 'fixture'}}
        actual = {'libfixture.so': self.m.sha(data)}
        self.m.verify_files(actual, records)
        for mutation in ('extra', 'hash', 'license', 'missing'):
            a, r = copy.deepcopy(actual), copy.deepcopy(records)
            if mutation == 'extra':
                a['libhidden.so'] = self.m.sha(data)
            elif mutation == 'hash':
                a['libfixture.so'] = '0' * 64
            elif mutation == 'license':
                r['libfixture.so']['license'] = 'UNKNOWN'
            else:
                a.clear()
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.m.verify_files(a, r)

    def test_windows_ucrt_is_never_embedded(self):
        # Relevé du 06/11/2026 : PyInstaller ramassait l'UCRT (44 api-ms-win-*,
        # ucrtbase) dans le dossier du JDK du runner. Composant de Windows 10+.
        toc = [('api-ms-win-crt-runtime-l1-1-0.dll', 'C:/jdk/bin/api-ms-win-crt-runtime-l1-1-0.dll', 'BINARY'),
               ('ucrtbase.dll', 'C:/jdk/bin/ucrtbase.dll', 'BINARY'),
               ('API-MS-WIN-CORE-FILE-L1-1-0.DLL', 'C:/x/API-MS-WIN-CORE-FILE-L1-1-0.DLL', 'BINARY'),
               ('python313.dll', 'C:/py/python313.dll', 'BINARY'),
               ('msvcp140.dll', 'C:/x/msvcp140.dll', 'BINARY')]
        self.assertEqual([e[0] for e in self.m.without_windows_ucrt(toc)], ['python313.dll', 'msvcp140.dll'])
        data = b'MZucrt'
        for name in ('ucrtbase.dll', 'sous/api-ms-win-core-heap-l1-1-0.dll'):
            records = {name: {'sha256': self.m.sha(data), 'license': 'MIT', 'origin': 'fixture'}}
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'UCRT'):
                self.m.verify_files({name: self.m.sha(data)}, records)

    def test_backend_spec_drops_windows_ucrt_before_recording_origins(self):
        spec = (ROOT / 'src/backend/backend.spec').read_text(encoding='utf-8')
        filtre = spec.index('a.binaries = _system_module.without_windows_ucrt(a.binaries)')
        self.assertLess(filtre, spec.index('_system_module.record_analysis('))
        self.assertIn('if sys.platform == "win32":', spec[filtre - 200:filtre])

    def test_rendered_notices_have_unix_line_endings(self):
        # THIRD_PARTY_LICENSES est versionné en LF (.gitattributes) ; deux
        # notices Windows amont (LICENSE.txt de python.org, conditions
        # Microsoft) gardent leurs CRLF : le rendu doit les normaliser.
        self.assertNotIn('\r', self.m.render_notices(ROOT))

    def test_catalog_has_exact_18_libraries_and_three_source_packages(self):
        catalog = self.m.load_catalog(ROOT)
        self.assertEqual(len(catalog['libraries']), 18)
        self.assertEqual({s['package'] for s in catalog['sources']}, {'readline', 'gdbm', 'glibc'})
        self.assertEqual(len(catalog['sources']), 11)
        self.assertEqual(sum(s['size'] for s in catalog['sources']), 23299768)

    def test_catalog_omitted_source_or_unknown_license_is_rejected(self):
        original = self.m.load_catalog(ROOT)
        for kind in ('source', 'license', 'version', 'hash', 'downgrade'):
            catalog = copy.deepcopy(original)
            if kind == 'source':
                catalog['sources'] = catalog['sources'][1:]
            else:
                row = next(r for r in catalog['libraries'] if r['name'] == 'libreadline.so.8')
                if kind == 'downgrade':
                    row['license'], row['source_required'] = 'MIT', False
                else:
                    row[{'license': 'license', 'version': 'version', 'hash': 'sha256'}[kind]] = 'UNKNOWN'
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                self.m.validate_catalog(catalog, ROOT)

    def test_dpkg_metadata_and_hash_must_both_match(self):
        row = next(r for r in self.m.load_catalog(ROOT)['libraries'] if r['name'] == 'libreadline.so.8')
        with patch.object(self.m, 'dpkg_identity', return_value=(row['package'], 'WRONG', row['source_package'], row['source_version'])):
            with self.assertRaisesRegex(ValueError, 'paquet'):
                self.m.match_system(Path('/lib/libreadline.so.8'), row['sha256'], self.m.load_catalog(ROOT), 'Linux')

    def test_source_assembly_rejects_corrupted_cached_bytes(self):
        catalog = self.m.load_catalog(ROOT)
        source = catalog['sources'][0]
        cache = self.folder / 'cache'
        cache.mkdir()
        (cache / source['filename']).write_bytes(b'wrong source')
        with self.assertRaisesRegex(ValueError, 'Source système altérée'):
            self.m.assemble_sources(self.folder / 'assembled', ROOT, cache=cache)
        self.assertFalse((self.folder / 'assembled/system-libraries.lock.json').exists())

    def test_same_soname_with_other_bytes_is_rejected(self):
        with patch.object(self.m, 'dpkg_identity', side_effect=AssertionError('hash first')):
            with self.assertRaisesRegex(ValueError, 'hors catalogue'):
                self.m.match_system(Path('/lib/libreadline.so.8'), '0' * 64, self.m.load_catalog(ROOT), 'Linux')

    def test_arbitrary_library_in_python_stdlib_is_not_assigned_psf(self):
        stdlib = self.folder / 'stdlib'
        directory = stdlib / 'lib-dynload'
        directory.mkdir(parents=True)
        library = directory / 'unlisted.so'
        library.write_bytes(b'\x7fELFnot-python')
        source = {'path': str(library), 'sha256': self.m.file_sha(library)}
        with (patch.object(self.m.sysconfig, 'get_path', return_value=str(stdlib)),
              patch.object(self.m.sys, 'version_info', (3, 13, 17)),
              self.assertRaisesRegex(ValueError, 'hors catalogue')):
            self.m.classify(source, self.m.load_catalog(ROOT), [], {}, 'Linux')

    def test_support_sources_in_readme_explain_lgpl_replacement(self):
        import copyleft_sources
        text = copyleft_sources.readme(json.loads((ROOT / copyleft_sources.MANIFEST).read_text()))
        self.assertIn('dpkg-source -x', text)
        self.assertIn('THERESE_BACKEND_LIBS', text)
        self.assertIn('libmvec', text)


class InstallerContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / '.work-t2/round6').mkdir(parents=True, exist_ok=True)
        import verify_packaged_licenses
        cls.m = verify_packaged_licenses

    def tar(self, contents, links=()):
        import io, tarfile
        data = io.BytesIO()
        with tarfile.open(fileobj=data, mode='w') as archive:
            for name, raw in contents.items():
                info = tarfile.TarInfo(name)
                info.size = len(raw)
                archive.addfile(info, io.BytesIO(raw))
            for name, target in links:
                info = tarfile.TarInfo(name)
                info.type = tarfile.SYMTYPE
                info.linkname = target
                archive.addfile(info)
        data.seek(0)
        return tarfile.open(fileobj=data)

    def test_debian_scan_includes_hidden_binary_and_internal_symlink(self):
        with self.tar({'usr/lib/backend-libs/hidden': b'\x7fELFexample',
                       'usr/lib/THIRD_PARTY_LICENSES': b'notices'},
                      [('usr/lib/backend-libs/libtest.so', 'hidden')]) as archive:
            files, notices, inventories = self.m.scan_tar(archive)
        self.assertEqual(len(files), 2)
        self.assertEqual(files['usr/lib/backend-libs/hidden'], files['usr/lib/backend-libs/libtest.so'])
        self.assertEqual(notices, [b'notices'])
        self.assertEqual(inventories, [])

    def test_debian_scan_refuses_external_symlink(self):
        with self.tar({}, [('usr/lib/backend-libs/libescape.so', '/lib/libc.so.6')]) as archive:
            with self.assertRaises(ValueError):
                self.m.scan_tar(archive)

    def test_backend_mutations_and_bundler_added_library_block(self):
        h = self.m.system.sha(b'\x7fELFexample')
        expected = {'schema': 1, 'files': {'_internal/libtest.so':
                    {'sha256': h, 'license': 'MIT', 'origin': 'fixture'}}}
        good = {'usr/lib/THERESE/binaries/backend-libs/_internal/libtest.so': h}
        self.assertEqual(len(self.m.verify_linux_files(good, expected)), 1)
        for kind in ('inside', 'outside', 'missing', 'changed'):
            actual = dict(good)
            if kind == 'inside':
                actual['usr/lib/THERESE/binaries/backend-libs/hidden'] = h
            elif kind == 'outside':
                actual['usr/lib/hidden'] = h
            elif kind == 'missing':
                actual.clear()
            else:
                actual[next(iter(actual))] = '0' * 64
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                self.m.verify_linux_files(actual, expected)

    def test_onefile_inspection_hashes_native_data_entries_too(self):
        from types import SimpleNamespace
        import sys
        archive = SimpleNamespace(toc={'hidden': (0, 0, 0, 0, 'x'), 'plain': ()},
                                  extract=lambda n: b'MZnative' if n == 'hidden' else b'text')
        reader = SimpleNamespace(CArchiveReader=lambda p: archive)
        with patch.dict(sys.modules, {'PyInstaller.archive.readers': reader}):
            self.assertEqual(self.m.system.onefile(Path('fixture')), {'hidden': self.m.system.sha(b'MZnative')})

    def test_publication_proof_binds_final_installer_and_inventory(self):
        import publish_release_artifacts as pub
        folder = Path(tempfile.mkdtemp(prefix='proof-test-', dir=ROOT / '.work-t2/round6'))
        artifact = folder / 'fixture.deb'
        artifact.write_bytes(b'installer')
        (folder / '.work-release/installer-proofs').mkdir(parents=True)
        inventory = folder / '.work-release/system-libraries.json'
        inventory.write_bytes(b'inventory')
        target = folder / '.work-release/installer-proofs/fixture.deb.json'
        target.write_text(json.dumps({'artifact': artifact.name, 'artifact_sha256': self.m.system.file_sha(artifact),
            'build_inventory_sha256': self.m.system.file_sha(inventory), 'files': {'native': {}}}))
        self.assertEqual(pub.verified_proofs([artifact], folder), [target])
        artifact.write_bytes(b'changed')
        with self.assertRaises(ValueError):
            pub.verified_proofs([artifact], folder)

    def test_appimage_is_published_only_with_other_guarded_artifacts(self):
        import publish_release_artifacts as pub
        folder = Path(tempfile.mkdtemp(prefix='appimage-test-', dir=ROOT / '.work-t2/round6'))
        (folder / 'deb').mkdir()
        (folder / 'appimage').mkdir()
        (folder / 'deb/test.deb').write_bytes(b'deb')
        (folder / 'appimage/test.AppImage').write_bytes(b'image')
        self.assertEqual(len(pub.artifacts(folder, 'Linux')), 2)

    @unittest.skipUnless(shutil.which('dpkg-deb'), 'extracteur Debian requis')
    def test_real_deb_container_passes_then_rejects_added_library(self):
        import subprocess
        folder = Path(tempfile.mkdtemp(prefix='deb-test-', dir=ROOT / '.work-t2/round6'))
        tree = folder / 'tree'
        (tree / 'DEBIAN').mkdir(parents=True)
        (tree / 'DEBIAN/control').write_text(
            'Package: therese-license-fixture\nVersion: 1\nArchitecture: all\n'
            'Maintainer: Fixture <fixture@example.test>\nDescription: license gate test\n')
        resource = tree / 'usr/lib/THERESE'
        library = resource / 'binaries/backend-libs/_internal/libfixture.so'
        library.parent.mkdir(parents=True)
        library.write_bytes(b'\x7fELFfixture')
        manifest = {'files': {'_internal/libfixture.so': {
            'sha256': self.m.system.file_sha(library), 'origin': 'fixture', 'license': 'MIT'}}}
        (folder / '.work-release').mkdir()
        (folder / '.work-release/system-libraries.json').write_text(json.dumps(manifest))
        (folder / 'THIRD_PARTY_LICENSES').write_bytes(b'fixture notices')
        (resource / 'system-libraries.json').write_text(json.dumps(manifest))
        (resource / 'THIRD_PARTY_LICENSES').write_bytes(b'fixture notices')
        artifact = folder / 'fixture.deb'
        for changed in (False, True):
            if changed:
                (library.parent / 'unlisted').write_bytes(b'\x7fELFnot-in-inventory')
            subprocess.run(['dpkg-deb', '--build', '--root-owner-group', str(tree), str(artifact)],
                           check=True, capture_output=True)
            catalog = self.m.system.load_catalog(ROOT)
            with patch.object(self.m.system, 'load_catalog', return_value=catalog):
                if changed:
                    with self.assertRaisesRegex(ValueError, 'inventaire'):
                        self.m.verify_deb(artifact, manifest, folder)
                else:
                    self.m.verify_deb(artifact, manifest, folder)
                    proof = folder / '.work-release/installer-proofs/fixture.deb.json'
                    self.assertTrue(proof.is_file())

    def test_package_resources_must_include_identical_inventory(self):
        folder = Path(tempfile.mkdtemp(prefix='resource-test-', dir=ROOT / '.work-t2/round6'))
        (folder / '.work-release').mkdir()
        (folder / '.work-release/system-libraries.json').write_bytes(b'inventory')
        (folder / 'THIRD_PARTY_LICENSES').write_bytes(b'notices')
        self.m.check_resources([b'notices'], [b'inventory'], folder)
        for inventories in ([], [b'stale'], [b'inventory', b'stale']):
            with self.subTest(inventories=inventories), self.assertRaises(ValueError):
                self.m.check_resources([b'notices'], inventories, folder)
