"""Installeur NSIS : greffons, stub et désinstalleur prouvés, intrus refusés.

Les PE synthétiques reprennent la disposition relevée sur l'installeur 0.82
publié et le désinstalleur que 7-Zip 26 en reconstitue : stub de 52 736 octets,
sections .text/.rdata/.data/.ndata/.rsrc, seule .text exécutable, en-tête NSIS
aligné sur 512 octets, désinstalleur différent du stub dans .rsrc seulement.
"""
import copy
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))

import nsis_installer as nsis  # noqa: E402

SECTIONS = [('.text', 0x1000, 0x400, 0x200, 0x60000020), ('.rdata', 0x2000, 0x600, 0x200, 0x40000040),
            ('.data', 0x3000, 0x800, 0x200, 0xc0000040), ('.ndata', 0x4000, 0, 0, 0xc0000080),
            ('.rsrc', 0x5000, 0xa00, 0x400, 0x40000040)]
ENTRY = 0x1010


def stub(code=b'code', resources=b'icone', entry=ENTRY, flags=None):
    """Stub PE32 minimal : sections à leurs places, ressources dans .rsrc."""
    raw = bytearray(0x1000)
    raw[:2] = b'MZ'
    raw[0x3c:0x40] = (0x80).to_bytes(4, 'little')
    raw[0x80:0x84] = b'PE\0\0'
    raw[0x86:0x88] = len(SECTIONS).to_bytes(2, 'little')
    raw[0x94:0x96] = (0xe0).to_bytes(2, 'little')
    raw[0x98:0x9a] = (0x10b).to_bytes(2, 'little')
    raw[0x98 + 16:0x98 + 20] = entry.to_bytes(4, 'little')
    table = 0x98 + 0xe0
    for index, (name, address, pointer, size, characteristics) in enumerate(SECTIONS):
        entry_raw = bytearray(40)
        entry_raw[:8] = name.encode().ljust(8, b'\0')
        entry_raw[8:24] = (size or 0x100).to_bytes(4, 'little') + address.to_bytes(4, 'little') \
            + size.to_bytes(4, 'little') + pointer.to_bytes(4, 'little')
        value = (flags or {}).get(name, characteristics)
        entry_raw[36:40] = value.to_bytes(4, 'little')
        raw[table + 40 * index:table + 40 * index + 40] = entry_raw
    raw[0x400:0x400 + len(code)] = code
    raw[0x600:0x604] = b'rdat'
    raw[0xa00:0xa00 + len(resources)] = resources
    return bytes(raw)


def nsis_exe(stub_bytes, uninstall=False, payload=b'donnees', extra=b''):
    header = (1 if uninstall else 0).to_bytes(4, 'little') + b'\xef\xbe\xad\xdeNullsoftInst'
    header += (64).to_bytes(4, 'little') + (28 + len(payload)).to_bytes(4, 'little')
    return stub_bytes + header + payload + extra


def code_sha(stub_bytes):
    return nsis.sha(b''.join(stub_bytes[p:p + s] for _, _, p, s, _ in SECTIONS[:3]))


def fixture_catalog(plugins):
    catalog = copy.deepcopy(nsis.load_catalog(ROOT))
    catalog['stub'].update(code_sha256=code_sha(stub()), entry_point=ENTRY)
    catalog['plugins'] = [dict(name=name, sha256=nsis.sha(raw), archive='nsis-3.11',
                               member='nsis-3.11/Plugins/x86-unicode/' + name, license='Zlib', notices=['nsis'])
                          for name, raw in plugins.items()]
    return catalog


class CatalogTests(unittest.TestCase):
    def test_versioned_catalog_is_bound_to_tauri_and_its_notices(self):
        catalog = nsis.load_catalog(ROOT)
        self.assertEqual({p['name'] for p in catalog['plugins']},
                         {'LangDLL.dll', 'NSISdl.dll', 'StartMenu.dll', 'System.dll', 'nsDialogs.dll',
                          'nsis_tauri_utils.dll'})
        for mutate in (lambda c: c.update(tauri_cli='9.9.9'),
                       lambda c: c['notices'][0].update(sha256='0' * 64),
                       lambda c: c['plugins'][0].update(license='LicenseRef-inconnue'),
                       lambda c: c['plugins'].append(dict(c['plugins'][0])),
                       lambda c: c['plugins'][-1].update(sha256='0' * 64),
                       lambda c: c['archives'][0].update(url='https://example.test/nsis.zip')):
            changed = copy.deepcopy(catalog)
            mutate(changed)
            with self.subTest(changed=json.dumps(changed)[:60]), self.assertRaises(ValueError):
                nsis.validate(changed, ROOT)

    def test_plugin_needs_both_name_and_digest(self):
        catalog = nsis.load_catalog(ROOT)
        system = next(p for p in catalog['plugins'] if p['name'] == 'System.dll')
        self.assertIn('Plugins/x86-unicode/System.dll', nsis.plugin(catalog, 'System.dll', system['sha256'])['origin'])
        self.assertIsNone(nsis.plugin(catalog, 'Intrus.dll', system['sha256']))
        self.assertIsNone(nsis.plugin(catalog, 'System.dll', '0' * 64))

    def test_notices_carry_mit_text_lzma_exception_and_every_digest(self):
        text = nsis.render_notices(ROOT)
        self.assertIn('Tauri Programme within The Commons Conservancy', text)
        self.assertIn('SPECIAL EXCEPTION FOR LZMA COMPRESSION MODULE', text)
        self.assertIn('Yaroslav Faybishenko', text)
        self.assertNotIn('\r', text)
        for row in nsis.load_catalog(ROOT)['plugins']:
            self.assertIn(row['sha256'], text)
        self.assertIn(text, (ROOT / 'THIRD_PARTY_LICENSES').read_text(encoding='utf-8'))


class StubTests(unittest.TestCase):
    def setUp(self):
        self.catalog = fixture_catalog({})
        self.installer = nsis_exe(stub())
        self.uninstaller = nsis_exe(stub(resources=b'autre icone'), uninstall=True, payload=b'desinstallation')

    def test_installer_stub_and_uninstaller_built_on_it(self):
        self.assertIn('lzma_solid', nsis.verify_installer_stub(self.installer, self.catalog)['origin'])
        self.assertEqual(nsis.verify_uninstaller(self.installer, self.uninstaller, self.catalog)['sha256'],
                         nsis.sha(self.uninstaller))

    def test_altered_stubs_are_refused(self):
        cases = {
            'code retouché': stub(code=b'c0de'),
            'point d’entrée déplacé': stub(entry=ENTRY + 4),
            'ressources exécutables': stub(flags={'.rsrc': 0x60000020}),
        }
        for label, altered in cases.items():
            with self.subTest(label), self.assertRaises(ValueError):
                nsis.verify_installer_stub(nsis_exe(altered), self.catalog)
        with self.assertRaisesRegex(ValueError, 'drapeau'):
            nsis.verify_installer_stub(nsis_exe(stub(), uninstall=True), self.catalog)

    def test_uninstaller_must_share_the_installer_stub(self):
        header_changed = bytearray(stub(resources=b'autre icone'))
        header_changed[0x40] = 1                              # hors ressources, hors code
        cases = {
            'en-tête différent': nsis_exe(bytes(header_changed), uninstall=True),
            'code différent': nsis_exe(stub(code=b'c0de'), uninstall=True),
            'sans drapeau': nsis_exe(stub(resources=b'autre icone')),
            'octets ajoutés': nsis_exe(stub(), uninstall=True, extra=b'X'),
            'stub plus long': nsis_exe(stub() + bytes(512), uninstall=True),
        }
        for label, uninstaller in cases.items():
            with self.subTest(label), self.assertRaises(ValueError):
                nsis.verify_uninstaller(self.installer, uninstaller, self.catalog)


class InstallerGuardTests(unittest.TestCase):
    """Passage complet par verify_directory, 7-Zip simulé pour le seul désinstalleur."""

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('packaged', ROOT / 'scripts/verify_packaged_licenses.py')
        cls.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.m)

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='nsis-guard-'))
        self.addCleanup(shutil.rmtree, self.root, True)
        (self.root / '.work-release').mkdir()
        (self.root / 'THIRD_PARTY_LICENSES').write_bytes(b'notices')
        (self.root / '.work-release/system-libraries.json').write_bytes(b'inventory')
        main = b'MZ' + bytes(0x3e) + b'__TAURI_BUNDLE_TYPE_VAR_UNK'
        main = main[:0x3c] + (0x80).to_bytes(4, 'little') + main[0x40:]
        main = main.ljust(0x200, b'\0')
        main = main[:0x80] + b'PE\0\0' + bytes(20) + (0x20b).to_bytes(2, 'little') + main[0x9a:]
        target = self.root / 'src/frontend/src-tauri/target/release'
        target.mkdir(parents=True)
        (target / 'therese.exe').write_bytes(main)
        self.main = main.replace(b'_VAR_UNK', b'_VAR_NSS', 1)
        self.plugins = {'System.dll': b'MZsystem', 'nsis_tauri_utils.dll': b'MZtauri', 'LangDLL.dll': b'MZlang'}
        self.catalog = fixture_catalog(self.plugins)
        self.installer = self.root / 'THERESE_0.83.0_x64-setup.exe'
        self.installer.write_bytes(nsis_exe(stub(), payload=b'installeur'))
        self.manifest = {'files': {'_internal/x.dll': {'sha256': '0' * 64, 'license': 'MIT', 'origin': 'fixture'}}}

    def layout(self, inner=None, uninstaller=True):
        folder = self.root / 'installer-inspection/nsis'
        for name, raw in {'therese.exe': self.main, 'backend.exe': b'MZonefile', 'THIRD_PARTY_LICENSES': b'notices',
                          'system-libraries.json': b'inventory', '$PLUGINSDIR/System.dll': self.plugins['System.dll'],
                          '$PLUGINSDIR/nsis_tauri_utils.dll': self.plugins['nsis_tauri_utils.dll'],
                          '$PLUGINSDIR/modern-wizard.bmp': b'BMimage'}.items():
            (folder / name).parent.mkdir(parents=True, exist_ok=True)
            (folder / name).write_bytes(raw)
        if uninstaller:
            (folder / 'uninstall.exe').write_bytes(nsis_exe(stub(resources=b'icone desinstalleur'), uninstall=True))
        self.inner = inner if inner is not None else {'$PLUGINSDIR/LangDLL.dll': self.plugins['LangDLL.dll'],
                                                      '$PLUGINSDIR/System.dll': self.plugins['System.dll']}
        return folder

    def verify(self, folder):
        def extract(path, out):
            self.assertEqual(path.name, 'uninstall.exe')
            for name, raw in self.inner.items():
                (out / name).parent.mkdir(parents=True, exist_ok=True)
                (out / name).write_bytes(raw)
            return out
        with patch.object(self.m.nsis, 'load_catalog', return_value=self.catalog), \
                patch.object(self.m.system, 'onefile', return_value={'_internal/x.dll': '0' * 64}), \
                patch.object(self.m, 'extract_nsis', side_effect=extract):
            return self.m.verify_directory(folder, self.manifest, 'Windows', self.root, 'nsis', self.installer)

    def test_every_native_file_of_the_nsis_installer_is_proven(self):
        records = self.verify(self.layout())
        self.assertEqual(sorted(k for k in records if '!_internal' not in k), [
            '$PLUGINSDIR/System.dll', '$PLUGINSDIR/nsis_tauri_utils.dll', 'THERESE_0.83.0_x64-setup.exe!stub',
            'therese.exe', 'uninstall.exe', 'uninstall.exe!$PLUGINSDIR/LangDLL.dll',
            'uninstall.exe!$PLUGINSDIR/System.dll'])

    def test_intruders_are_refused_all_at_once(self):
        folder = self.layout(inner={'$PLUGINSDIR/LangDLL.dll': b'MZautre', 'cache.dll': self.plugins['System.dll']})
        (folder / '$PLUGINSDIR/System.dll').write_bytes(b'MZmodifie')
        (folder / '$PLUGINSDIR/Intrus.dll').write_bytes(self.plugins['System.dll'])
        (folder / '$PLUGINSDIR/sous/System.dll').parent.mkdir()
        (folder / '$PLUGINSDIR/sous/System.dll').write_bytes(self.plugins['System.dll'])
        with self.assertRaises(ValueError) as caught:
            self.verify(folder)
        message = str(caught.exception)
        for name in ('$PLUGINSDIR/System.dll', '$PLUGINSDIR/Intrus.dll', '$PLUGINSDIR/sous/System.dll',
                     'uninstall.exe!$PLUGINSDIR/LangDLL.dll', 'uninstall.exe!cache.dll'):
            self.assertIn(name + ' (SHA-256 ', message)

    def test_missing_or_foreign_uninstaller_fails(self):
        with self.assertRaisesRegex(ValueError, 'Désinstalleur NSIS absent'):
            self.verify(self.layout(uninstaller=False))
        folder = self.layout()
        (folder / 'uninstall.exe').write_bytes(nsis_exe(stub(code=b'autre'), uninstall=True))
        with self.assertRaisesRegex(ValueError, 'uninstall.exe'):
            self.verify(folder)

    def test_msi_never_accepts_nsis_plugins(self):
        folder = self.layout()
        with patch.object(self.m.nsis, 'load_catalog', return_value=self.catalog), \
                patch.object(self.m.system, 'onefile', return_value={'_internal/x.dll': '0' * 64}):
            with self.assertRaisesRegex(ValueError, r'\$PLUGINSDIR/System.dll'):
                self.m.verify_directory(folder, self.manifest, 'Windows', self.root, 'msi')


if __name__ == '__main__':
    unittest.main()
