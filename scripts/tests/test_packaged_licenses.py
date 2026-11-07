"""Garde des installeurs : dispositions réelles des paquets Tauri, intrus toujours refusés.

Les dispositions viennent du run release 42355341201 (v0.83.0-alpha) et des
installeurs 0.82 publiés : Tauri retire le suffixe de cible des externalBin
(THERESE.app/Contents/MacOS/backend, backend.exe) et le binaire principal du
paquet porte le jeton de son type (__TAURI_BUNDLE_TYPE_VAR_DEB, _MSI, _NSS)
alors que target/release garde l'original (_UNK).
"""
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))

UNK = b'__TAURI_BUNDLE_TYPE_VAR_UNK'
NOTICES = b'fixture notices'
INVENTORY = b'fixture inventory'


def load():
    spec = importlib.util.spec_from_file_location('packaged', ROOT / 'scripts/verify_packaged_licenses.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pe(body=b'', signed=False, magic=0x20b):
    """PE minimal : en-tête MZ, signature PE, en-tête optionnel et répertoire de sécurité."""
    raw = bytearray(0x200)
    raw[:2] = b'MZ'
    raw[0x3c:0x40] = (0x80).to_bytes(4, 'little')
    raw[0x80:0x84] = b'PE\0\0'
    optional = 0x80 + 24
    raw[optional:optional + 2] = magic.to_bytes(2, 'little')
    security = optional + (112 if magic == 0x20b else 96) + 32
    if signed:
        raw[security:security + 8] = (0x1000).to_bytes(4, 'little') + (0x200).to_bytes(4, 'little')
    return bytes(raw) + body


def patched(raw, kind):
    index = raw.find(UNK)
    return raw[:index] + b'__TAURI_BUNDLE_TYPE_VAR_' + kind + raw[index + len(UNK):]


class LicenseNoticeTests(unittest.TestCase):
    def test_absent_or_stale_installed_notice_is_rejected(self):
        module = load()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with self.assertRaises(ValueError):
                module.check_directory(root, b'notice')
            notice = root / 'THIRD_PARTY_LICENSES'
            notice.write_bytes(b'stale')
            with self.assertRaises(ValueError):
                module.check_directory(root, b'notice')
            notice.write_bytes(b'notice')
            self.assertEqual(module.check_directory(root, b'notice'), 1)


class InstallerLayoutTests(unittest.TestCase):
    """Chaque test bâtit le build (target/release) et l'installeur extrait tels qu'observés."""

    @classmethod
    def setUpClass(cls):
        cls.m = load()
        cls.engine_payload = {'_internal/libfixture.dll': cls.m.system.sha(b'MZfixture')}
        cls.manifest = {'files': {'_internal/libfixture.dll': {
            'sha256': cls.m.system.sha(b'MZfixture'), 'license': 'MIT', 'origin': 'fixture'}}}

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='installer-layout-'))
        self.addCleanup(shutil.rmtree, self.root, True)
        (self.root / 'THIRD_PARTY_LICENSES').write_bytes(NOTICES)
        (self.root / '.work-release').mkdir()
        (self.root / '.work-release/system-libraries.json').write_bytes(INVENTORY)
        self.target = self.root / 'src/frontend/src-tauri/target/release'
        self.target.mkdir(parents=True)

    def write(self, path, raw):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return path

    def resources(self, folder):
        self.write(folder / 'THIRD_PARTY_LICENSES', NOTICES)
        self.write(folder / 'system-libraries.json', INVENTORY)
        self.write(folder / 'resources/guide-therese-0.83.pdf', b'%PDF-fixture')

    def verify(self, folder, platform, package=None, payload=None):
        calls = []

        def onefile(path):
            calls.append(path)
            return payload or self.engine_payload
        if package != 'nsis':
            with patch.object(self.m.system, 'onefile', onefile):
                records = self.m.verify_directory(folder, self.manifest, platform, self.root, package)
            return records, calls
        # Stub et désinstalleur : prouvés dans test_nsis_installer.py ; ici, aucun greffon inventorié.
        catalog = dict(self.m.nsis.load_catalog(ROOT), plugins=[])
        installer = self.write(self.root / 'THERESE_0.83.0_x64-setup.exe', b'MZinstalleur')
        with patch.object(self.m.system, 'onefile', onefile), \
                patch.object(self.m.nsis, 'load_catalog', return_value=catalog), \
                patch.object(self.m.nsis, 'verify_installer_stub', return_value={'origin': 'stub'}), \
                patch.object(self.m, 'verify_uninstaller', return_value=({'uninstall.exe': {}}, [])):
            records = self.m.verify_directory(folder, self.manifest, platform, self.root, package, installer)
        return records, calls

    # ---- macOS : THERESE.app/Contents/MacOS/backend (journal du run, étape Tauri) ----
    def macos_app(self, folder):
        app = folder / 'THERESE.app/Contents'
        self.write(app / 'Info.plist', b'<?xml version="1.0"?><plist/>')
        self.write(app / 'MacOS/therese', b'\xcf\xfa\xed\xfe' + b'main')
        self.write(app / 'MacOS/backend', b'\xcf\xfa\xed\xfe' + b'onefile')
        self.write(app / '_CodeSignature/CodeResources', b'<?xml version="1.0"?><plist/>')
        self.resources(app / 'Resources')
        return app

    def test_macos_engine_is_found_without_target_suffix(self):
        folder = self.root / 'updater-macos'
        app = self.macos_app(folder)
        records, calls = self.verify(folder, 'macOS')
        self.assertEqual(calls, [app / 'MacOS/backend'])
        self.assertEqual(list(records), ['THERESE.app/Contents/MacOS/backend!_internal/libfixture.dll'])

    def test_macos_intruders_and_old_names_still_fail(self):
        cases = {
            'dylib ajoutée': lambda app: self.write(app / 'Frameworks/libintrus.dylib', b'\xcf\xfa\xed\xfeX'),
            'ancien nom à côté': lambda app: self.write(app / 'MacOS/backend-aarch64-apple-darwin', b'\xcf\xfa\xed\xfeY'),
            'moteur hors de MacOS': lambda app: (app / 'MacOS/backend').rename(app / 'Resources/backend'),
            'moteur seulement sous l’ancien nom': lambda app: (app / 'MacOS/backend').rename(
                app / 'MacOS/backend-aarch64-apple-darwin'),
        }
        for index, (label, mutate) in enumerate(cases.items()):
            with self.subTest(label):
                folder = self.root / f'mac-{index}'
                mutate(self.macos_app(folder))
                with self.assertRaises(ValueError):
                    self.verify(folder, 'macOS')

    def test_macos_engine_payload_must_match_inventory(self):
        folder = self.root / 'dmg'
        self.macos_app(folder)
        with self.assertRaisesRegex(ValueError, 'modifiée'):
            self.verify(folder, 'macOS', payload={'_internal/libfixture.dll': '0' * 64})
        with self.assertRaisesRegex(ValueError, 'inventaire'):
            self.verify(folder, 'macOS', payload={'_internal/autre.dll': '0' * 64})

    def test_two_apps_means_two_engines_and_fails(self):
        folder = self.root / 'two'
        self.macos_app(folder)
        self.write(folder / 'Copie.app/Contents/MacOS/backend', b'\xcf\xfa\xed\xfeZ')
        with self.assertRaisesRegex(ValueError, 'Plusieurs moteurs'):
            self.verify(folder, 'macOS')

    # ---- Windows : extraction 7z du NSIS et image administrative du MSI ----
    def build_windows(self):
        original = pe(b'rodata __TAURI_BUNDLE_TYPE_VAR_NSS' + UNK + b' code')
        self.write(self.target / 'therese.exe', original)
        return original

    def nsis(self, folder, main):
        self.write(folder / 'therese.exe', main)
        self.write(folder / 'backend.exe', pe(b'onefile'))
        self.write(folder / '$PLUGINSDIR/modern-wizard.bmp', b'BMfixture')
        self.write(folder / 'uninstall.exe', pe(b'desinstalleur'))
        self.resources(folder)

    def test_nsis_main_binary_is_this_build_with_its_nsis_marker(self):
        original = self.build_windows()
        # Le littéral _NSS du match précède le jeton : seule la PREMIÈRE occurrence de _UNK change.
        folder = self.root / 'nsis'
        self.nsis(folder, patched(original, b'NSS'))
        records, calls = self.verify(folder, 'Windows', 'nsis')
        self.assertEqual(calls, [folder / 'backend.exe'])
        self.assertIn('therese.exe', records)

    def test_uninventoried_nsis_plugins_are_refused_all_at_once_with_their_digest(self):
        original = self.build_windows()
        folder = self.root / 'nsis-plugins'
        self.nsis(folder, patched(original, b'NSS'))
        for name in ('System.dll', 'nsDialogs.dll', 'StartMenu.dll', 'NSISdl.dll', 'nsis_tauri_utils.dll'):
            self.write(folder / '$PLUGINSDIR' / name, pe(name.encode()))
        with self.assertRaises(ValueError) as caught:
            self.verify(folder, 'Windows', 'nsis')
        message = str(caught.exception)
        self.assertEqual(message.count('sans inventaire'), 5)
        self.assertIn('$PLUGINSDIR/nsis_tauri_utils.dll (SHA-256 ', message)

    def test_windows_main_binary_from_elsewhere_fails(self):
        original = self.build_windows()
        cases = {
            'marqueur d’un autre paquet': patched(original, b'MSI'),
            'autre build non signé': pe(b'other build ' + UNK),
            'même build retouché après coup': patched(original, b'NSS').replace(b' code', b' c0de'),
        }
        for index, (label, main) in enumerate(cases.items()):
            with self.subTest(label):
                folder = self.root / f'win-{index}'
                self.nsis(folder, main)
                with self.assertRaisesRegex(ValueError, 'différent de ce build'):
                    self.verify(folder, 'Windows', 'nsis')

    def test_signed_windows_main_binary_is_left_to_the_signature_gate(self):
        self.build_windows()
        folder = self.root / 'signed'
        self.nsis(folder, pe(b'signed elsewhere', signed=True))
        records, _ = self.verify(folder, 'Windows', 'nsis')
        self.assertNotIn('therese.exe', records)

    def test_msi_admin_image_layout(self):
        original = self.build_windows()
        folder = self.root / 'msi'
        self.write(folder / 'THERESE_0.83.0_x64_en-US.msi', b'\xd0\xcf\x11\xe0admin image')
        install = folder / 'PFiles/THERESE'
        self.write(install / 'therese.exe', patched(original, b'MSI'))
        self.write(install / 'backend.exe', pe(b'onefile'))
        self.resources(install)
        records, calls = self.verify(folder, 'Windows', 'msi')
        self.assertEqual(calls, [install / 'backend.exe'])
        self.assertIn('PFiles/THERESE/therese.exe', records)
        # Un moteur loin de l'exécutable principal n'est pas le moteur installé.
        (install / 'backend.exe').rename(folder / 'backend.exe')
        with self.assertRaisesRegex(ValueError, 'Moteur onefile absent'):
            self.verify(folder, 'Windows', 'msi')

    def test_authenticode_detection_reads_the_security_directory(self):
        self.assertFalse(self.m.authenticode_signed(pe()))
        self.assertTrue(self.m.authenticode_signed(pe(signed=True)))
        self.assertTrue(self.m.authenticode_signed(pe(signed=True, magic=0x10b)))
        for raw in (b'MZ', b'\x7fELF' + bytes(0x200), pe().replace(b'PE\0\0', b'XX\0\0')):
            with self.assertRaises(ValueError):
                self.m.authenticode_signed(raw)

    def test_engine_name_follows_tauri_config(self):
        self.assertEqual(self.m.engine_name('macOS'), 'backend')
        self.assertEqual(self.m.engine_name('Windows'), 'backend.exe')

    # ---- Linux : usr/bin/therese du .deb porte _DEB, target/release garde _UNK ----
    def linux(self):
        original = b'\x7fELF' + b'rodata ' + UNK + b' code'
        self.write(self.target / 'therese', original)
        library = self.m.system.sha(b'\x7fELFlib')
        manifest = {'files': {'_internal/libfixture.so': {'sha256': library, 'license': 'MIT', 'origin': 'fixture'}}}
        actual = {'usr/lib/THERESE/binaries/backend-libs/_internal/libfixture.so': library}
        return original, manifest, actual

    def verify_linux(self, actual, manifest, package='deb'):
        catalog = self.m.system.load_catalog(ROOT)
        with patch.object(self.m.system, 'load_catalog', return_value=catalog):
            return self.m.verify_linux_files(actual, manifest, self.root, package)

    def test_deb_main_binary_is_this_build_with_its_deb_marker(self):
        original, manifest, actual = self.linux()
        for main in (patched(original, b'DEB'), original):
            with self.subTest(patched=main != original):
                records = self.verify_linux(dict(actual, **{'usr/bin/therese': self.m.system.sha(main)}), manifest)
                self.assertEqual(records['usr/bin/therese']['origin'], 'THERESE/Cargo.lock')

    def test_deb_foreign_or_misplaced_binaries_fail_all_at_once(self):
        original, manifest, actual = self.linux()
        sha = self.m.system.sha
        bad = dict(actual)
        bad['usr/bin/therese'] = sha(patched(original, b'APP'))       # marqueur d'un autre paquet
        bad['usr/lib/therese'] = sha(patched(original, b'DEB'))       # bon octets, mauvaise place
        bad['usr/lib/libintrus.so'] = sha(b'\x7fELFintrus')            # ajout de l'empaqueteur
        with self.assertRaises(ValueError) as caught:
            self.verify_linux(bad, manifest)
        self.assertEqual(str(caught.exception).count('hors inventaire'), 3)

    @unittest.skipUnless(shutil.which('dpkg-deb'), 'extracteur Debian requis')
    def test_real_deb_with_patched_main_binary(self):
        original, manifest, _ = self.linux()
        tree = self.root / 'tree'
        self.write(tree / 'DEBIAN/control',
                   b'Package: therese-layout-fixture\nVersion: 1\nArchitecture: all\n'
                   b'Maintainer: Fixture <fixture@example.test>\nDescription: layout test\n')
        resource = tree / 'usr/lib/THERESE'
        self.write(resource / 'binaries/backend-libs/_internal/libfixture.so', b'\x7fELFlib')
        self.write(resource / 'THIRD_PARTY_LICENSES', NOTICES)
        self.write(resource / 'system-libraries.json', INVENTORY)
        self.write(tree / 'usr/bin/backend', b'#!/bin/sh\nexec "$LIBS_DIR/backend" "$@"\n')
        artifact = self.root / 'THERESE_0.83.0_amd64.deb'
        catalog = self.m.system.load_catalog(ROOT)
        for main, accepted in ((patched(original, b'DEB'), True), (patched(original, b'RPM'), False)):
            with self.subTest(accepted=accepted):
                self.write(tree / 'usr/bin/therese', main)
                subprocess.run(['dpkg-deb', '--build', '--root-owner-group', str(tree), str(artifact)],
                               check=True, capture_output=True)
                with patch.object(self.m.system, 'load_catalog', return_value=catalog):
                    if accepted:
                        self.m.verify_deb(artifact, manifest, self.root)
                        proof = json.loads((self.root / '.work-release/installer-proofs'
                                            / (artifact.name + '.json')).read_text())
                        self.assertIn('usr/bin/therese', proof['files'])
                    else:
                        with self.assertRaisesRegex(ValueError, 'usr/bin/therese'):
                            self.m.verify_deb(artifact, manifest, self.root)


if __name__ == '__main__':
    unittest.main()
