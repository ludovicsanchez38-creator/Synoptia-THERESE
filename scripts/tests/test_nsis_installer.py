"""Installeur NSIS : greffons, stub et désinstalleur prouvés, intrus refusés.

Les PE synthétiques reprennent la disposition relevée sur l'installeur 0.82
publié et le désinstalleur que 7-Zip 26 en reconstitue : stub de 52 736 octets,
sections .text/.rdata/.data/.ndata/.rsrc, seule .text exécutable, en-tête NSIS
aligné sur 512 octets, désinstalleur différent du stub dans .rsrc seulement.
"""
import copy
import importlib.util
import json
import re
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


def signed_pe(raw, certificate=b'certificat-test!', checksum=1234):
    """Signature synthétique, sans clé ni certificat réel : table Security en fin de PE."""
    result = bytearray(raw)
    result.extend(bytes(-len(result) % 8))
    optional = int.from_bytes(raw[0x3c:0x40], 'little') + 24
    security = optional + (112 if raw[optional:optional + 2] == b'\x0b\x02' else 96) + 32
    result[optional + 64:optional + 68] = checksum.to_bytes(4, 'little')
    result[security:security + 8] = len(result).to_bytes(4, 'little') + len(certificate).to_bytes(4, 'little')
    result.extend(certificate)
    return bytes(result)


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

    def test_signed_uninstaller_preserves_the_nsis_length_and_stub_checks(self):
        # L'en-tête de l'installeur porte lui aussi le checksum/Security du PE signé.
        installer = signed_pe(self.installer, checksum=8765)
        for checksum, certificate in ((1234, b'certificat-test!'), (4321, b'autre signature!')):
            with self.subTest(checksum=checksum):
                signed = signed_pe(self.uninstaller, certificate, checksum)
                self.assertEqual(nsis.verify_uninstaller(installer, signed, self.catalog)['sha256'], nsis.sha(signed))

    def test_signed_uninstaller_accepts_only_minimal_zero_alignment_padding(self):
        signed = signed_pe(self.uninstaller)
        self.assertEqual(nsis.verify_uninstaller(self.installer, signed, self.catalog)['sha256'], nsis.sha(signed))
        cases = {
            'huit octets nuls au-delà du minimum': self.uninstaller + bytes(8),
            # signed_pe ajoute un octet nul de moins : la longueur alignée reste
            # correcte, seul le contenu du remplissage doit faire refuser ce cas.
            'octet non nul dans le remplissage minimal': self.uninstaller + b'X',
        }
        for label, raw in cases.items():
            with self.subTest(label), self.assertRaisesRegex(ValueError, 'Données en trop ou manquantes'):
                nsis.verify_uninstaller(self.installer, signed_pe(raw), self.catalog)

    def test_signed_uninstaller_length_cannot_be_less_than_28(self):
        raw = nsis_exe(stub(resources=b'autre icone'), uninstall=True, payload=b'')
        signed = signed_pe(raw)
        with self.subTest(length=28):
            self.assertEqual(nsis.verify_uninstaller(self.installer, signed, self.catalog)['sha256'], nsis.sha(signed))
        altered = bytearray(raw)
        offset, _, _ = nsis.firstheader(raw)
        altered[offset + 24:offset + 28] = (27).to_bytes(4, 'little')
        # Le dernier octet de longueur est nul : sans la borne basse, il serait
        # absorbé par le padding et les autres contrôles accepteraient ce PE.
        with self.subTest(length=27), self.assertRaisesRegex(ValueError, 'Données en trop ou manquantes'):
            nsis.verify_uninstaller(self.installer, signed_pe(bytes(altered)), self.catalog)

    def test_signed_uninstaller_alterations_are_refused(self):
        header_changed = bytearray(stub(resources=b'autre icone'))
        header_changed[0x40] ^= 1
        cases = {
            'code': nsis_exe(stub(code=b'c0de'), uninstall=True),
            'en-tête hors ressources': nsis_exe(bytes(header_changed), uninstall=True),
            'drapeau': nsis_exe(stub()),
            'données hors longueur NSIS': self.uninstaller + b'intrus',
            'faux alignement': self.uninstaller + b'X',
        }
        for label, raw in cases.items():
            with self.subTest(label), self.assertRaises(ValueError):
                nsis.verify_uninstaller(self.installer, signed_pe(raw), self.catalog)
        with self.assertRaises(ValueError):
            nsis.verify_uninstaller(self.installer, signed_pe(self.uninstaller) + b'X', self.catalog)

    def test_uninstaller_certificate_cannot_hide_nsis_data_or_sections(self):
        signed = signed_pe(self.uninstaller)
        security = 0x98 + 96 + 32
        for offset, size in ((len(signed) + 8, 16), (0x400, len(signed) - 0x400),
                             (0x1000, len(signed) - 0x1000)):
            altered = bytearray(signed)
            altered[security:security + 8] = offset.to_bytes(4, 'little') + size.to_bytes(4, 'little')
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                nsis.verify_uninstaller(self.installer, bytes(altered), self.catalog)


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory(prefix='nsis-capture-')))
        self.raw = stub()
        self.catalog = fixture_catalog({'System.dll': self.raw})
        self.path = self.root / 'System.dll'
        self.path.write_bytes(self.raw)
        self.reference = self.root / nsis.UNSIGNED / nsis.sha(self.raw)

    def test_capture_is_bound_to_the_exact_inventory_digest(self):
        nsis.capture_plugin(self.path, self.catalog, self.root)
        self.assertEqual(self.reference.read_bytes(), self.raw)
        self.path.write_bytes(stub(code=b'intrus'))
        with self.assertRaisesRegex(ValueError, 'différent du verrou'):
            nsis.capture_plugin(self.path, self.catalog, self.root)
        self.assertEqual(self.reference.read_bytes(), self.raw)

    def test_unrelated_signing_inputs_are_not_copied_or_read(self):
        nsis.capture_plugin(self.root / 'therese.exe', self.catalog, self.root)
        self.assertFalse(self.reference.parent.exists())

    def test_resigning_uses_the_preserved_original_and_rejects_a_changed_plugin(self):
        nsis.capture_plugin(self.path, self.catalog, self.root)
        for certificate in (b'certificat-test!', b'autre signature!'):
            self.path.write_bytes(signed_pe(self.raw, certificate))
            nsis.capture_plugin(self.path, self.catalog, self.root)
            self.assertEqual(self.reference.read_bytes(), self.raw)
        self.path.write_bytes(signed_pe(stub(code=b'intrus')))
        with self.assertRaises(ValueError):
            nsis.capture_plugin(self.path, self.catalog, self.root)

    def test_callback_statically_captures_before_signing_and_throws_on_capture_failure(self):
        # Contrôle de structure seulement, sans exécution de PowerShell.
        script = (ROOT / 'scripts/sign_windows.ps1').read_text(encoding='utf-8')
        capture_guard = re.search(
            r"(?m)^[ \t]*&\s+python\s+\(Join-Path\s+\$PSScriptRoot\s+'nsis_installer\.py'\)"
            r"[ \t]+capture[ \t]+\$Path[ \t]*\r?\n"
            r"\s*if\s*\(\s*\$LASTEXITCODE\s+-ne\s+0\s*\)\s*"
            r"\{\s*throw\s+'[^'\r\n]+'\s*;?\s*\}", script)
        self.assertIsNotNone(capture_guard, 'La capture doit être suivie du contrôle de son code de sortie avec throw')
        self.assertLess(capture_guard.end(), script.index('Import-Module TrustedSigning'))
        self.assertLess(script.index('Import-Module TrustedSigning'), script.index('Invoke-TrustedSigning @params'))


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
        # Le checksum amont n'est pas supposé nul ou recalculable : il fait partie
        # des octets exacts épinglés, avant neutralisation des deux côtés.
        original = bytearray(stub())
        original[0x98 + 64:0x98 + 68] = (0x12345678).to_bytes(4, 'little')
        self.plugins = {'System.dll': bytes(original), 'nsis_tauri_utils.dll': stub(code=b'tauri'),
                        'LangDLL.dll': stub(code=b'lang')}
        self.catalog = fixture_catalog(self.plugins)
        for name, raw in self.plugins.items():
            source = self.root / name
            source.write_bytes(raw)
            nsis.capture_plugin(source, self.catalog, self.root)
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
        # Le passage non signé n'a besoin d'aucune copie avant signature.
        (self.root / nsis.UNSIGNED).rename(self.root / '.work-release/references-absentes')
        records = self.verify(self.layout())
        self.assertEqual(sorted(k for k in records if '!_internal' not in k), [
            '$PLUGINSDIR/System.dll', '$PLUGINSDIR/nsis_tauri_utils.dll', 'THERESE_0.83.0_x64-setup.exe!stub',
            'therese.exe', 'uninstall.exe', 'uninstall.exe!$PLUGINSDIR/LangDLL.dll',
            'uninstall.exe!$PLUGINSDIR/System.dll'])

    def test_signed_plugins_match_the_unsigned_inventory_in_both_containers(self):
        inner = {'$PLUGINSDIR/System.dll': signed_pe(self.plugins['System.dll'])}
        folder = self.layout(inner=inner)
        for name, raw in self.plugins.items():
            if name != 'LangDLL.dll':
                signed = signed_pe(raw)
                (folder / '$PLUGINSDIR' / name).write_bytes(signed)
        records = self.verify(folder)
        self.assertEqual(records['$PLUGINSDIR/System.dll']['sha256'], nsis.sha(signed_pe(self.plugins['System.dll'])))
        self.assertIn('uninstall.exe!$PLUGINSDIR/System.dll', records)

    def test_signed_plugin_with_changed_code_is_refused(self):
        folder = self.layout()
        for offset in (0x400, 0x600, 0xa00, 0x40, 0x88):
            altered = bytearray(signed_pe(self.plugins['System.dll']))
            altered[offset] ^= 1
            (folder / '$PLUGINSDIR/System.dll').write_bytes(altered)
            with self.subTest(offset=offset), self.assertRaisesRegex(ValueError, r'\$PLUGINSDIR/System.dll'):
                self.verify(folder)

    def test_signed_plugin_with_trailing_bytes_is_refused(self):
        folder = self.layout()
        (folder / '$PLUGINSDIR/System.dll').write_bytes(signed_pe(self.plugins['System.dll']) + b'intrus')
        with self.assertRaisesRegex(ValueError, r'\$PLUGINSDIR/System.dll'):
            self.verify(folder)

    def test_unsigned_plugin_with_only_a_changed_checksum_is_refused(self):
        folder = self.layout()
        altered = bytearray(self.plugins['System.dll'])
        altered[0x98 + 64] ^= 1
        (folder / '$PLUGINSDIR/System.dll').write_bytes(altered)
        with self.assertRaisesRegex(ValueError, r'\$PLUGINSDIR/System.dll'):
            self.verify(folder)

    def test_certificate_table_must_be_inside_file_and_outside_sections(self):
        original = signed_pe(self.plugins['System.dll'])
        security = 0x98 + 96 + 32
        # Le cas chevauchant se termine bien à EOF : le contrôle d'EOF seul
        # n'empêche pas de masquer des octets d'une section comme certificat.
        for offset, size in ((len(original) + 8, 16), (0x400, len(original) - 0x400),
                             (0, 16), (len(original), 0), (0x1001, 15)):
            altered = bytearray(original)
            altered[security:security + 8] = offset.to_bytes(4, 'little') + size.to_bytes(4, 'little')
            with self.subTest(offset=offset):
                self.assertIsNone(self.m.unsigned_pe_digest(bytes(altered)))
                folder = self.layout()
                (folder / '$PLUGINSDIR/System.dll').write_bytes(altered)
                with self.assertRaisesRegex(ValueError, r'\$PLUGINSDIR/System.dll'):
                    self.verify(folder)

    def test_signed_plugin_needs_an_exact_verified_unsigned_reference(self):
        folder = self.layout()
        (folder / '$PLUGINSDIR/System.dll').write_bytes(signed_pe(self.plugins['System.dll']))
        reference = self.root / '.work-release/nsis-unsigned' / nsis.sha(self.plugins['System.dll'])
        reference.write_bytes(stub(code=b'intrus'))
        with self.assertRaisesRegex(ValueError, r'\$PLUGINSDIR/System.dll'):
            self.verify(folder)
        reference.rename(reference.with_suffix('.absent'))
        with self.assertRaisesRegex(ValueError, r'\$PLUGINSDIR/System.dll'):
            self.verify(folder)

    def test_coherent_replacement_of_reference_and_signed_plugin_is_refused(self):
        replacement = stub(code=b'intrus')
        reference = self.root / nsis.UNSIGNED / nsis.sha(self.plugins['System.dll'])
        reference.write_bytes(replacement)
        for container in ('installer', 'uninstaller'):
            with self.subTest(container=container):
                inner = {'$PLUGINSDIR/System.dll': signed_pe(replacement)} if container == 'uninstaller' else None
                folder = self.layout(inner=inner)
                if container == 'installer':
                    (folder / '$PLUGINSDIR/System.dll').write_bytes(signed_pe(replacement))
                # Référence et greffon ont la même identité hors signature,
                # mais leur original ne correspond plus au SHA-256 du verrou.
                with self.assertRaisesRegex(ValueError, r'\$PLUGINSDIR/System.dll'):
                    self.verify(folder)

    def test_signed_uninstaller_and_its_signed_plugin_are_proven_together(self):
        folder = self.layout(inner={'$PLUGINSDIR/LangDLL.dll': signed_pe(self.plugins['LangDLL.dll'])})
        path = folder / 'uninstall.exe'
        path.write_bytes(signed_pe(path.read_bytes()))
        self.installer.write_bytes(signed_pe(self.installer.read_bytes(), checksum=8765))
        records = self.verify(folder)
        self.assertIn('uninstall.exe', records)
        self.assertIn('uninstall.exe!$PLUGINSDIR/LangDLL.dll', records)

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
