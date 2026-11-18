"""B-1886 : un PE étranger avec table de certificats factice passe la garde."""

import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


class ExecutableEtrangerTests(unittest.TestCase):
    def load(self, name):
        self.enterContext(patch.object(sys, "path", [str(ROOT / "scripts"), *sys.path]))
        spec = importlib.util.spec_from_file_location(name, ROOT / "scripts/verify_packaged_licenses.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_un_executable_etranger_ne_passe_pas_par_sa_seule_table_pe(self):
        module = self.load("licences_c20")

        raw = bytearray(0x200)
        raw[:2] = b"MZ"
        raw[0x3C:0x40] = (0x80).to_bytes(4, "little")
        raw[0x80:0x84] = b"PE\0\0"
        optional = 0x80 + 24
        raw[optional:optional + 2] = (0x20B).to_bytes(2, "little")
        security = optional + 112 + 4 * 8
        raw[security:security + 8] = (0x1000).to_bytes(4, "little") + (0x200).to_bytes(4, "little")
        etranger = bytes(raw) + b"binaire tiers, aucune signature reelle"
        self.assertTrue(module.authenticode_signed(etranger))
        self.assertNotEqual(module.system.sha(etranger), module.system.sha(b"binaire de ce build"))

        dossier = Path("/virtuel/installeur")
        moteur = dossier / "backend.exe"
        principal = dossier / "therese.exe"
        fichiers = {moteur: b"MZmoteur", principal: etranger}
        ancien_rglob, ancien_is_file, ancien_open, ancien_read_bytes = Path.rglob, Path.is_file, Path.open, Path.read_bytes
        self.enterContext(patch.object(Path, "rglob", lambda p, motif: iter(fichiers) if p == dossier and motif == "*" else (iter(()) if p == dossier else ancien_rglob(p, motif))))
        self.enterContext(patch.object(Path, "is_file", lambda p: True if p in fichiers else ancien_is_file(p)))
        self.enterContext(patch.object(Path, "open", lambda p, *a, **kw: io.BytesIO(fichiers[p]) if p in fichiers else ancien_open(p, *a, **kw)))
        self.enterContext(patch.object(Path, "read_bytes", lambda p: fichiers[p] if p in fichiers else ancien_read_bytes(p)))
        self.enterContext(patch.object(module, "check_resources", lambda *_: None))
        self.enterContext(patch.object(module, "engine_name", lambda _: "backend.exe"))
        self.enterContext(patch.object(module, "built_digests", lambda *_: {module.system.sha(b"binaire de ce build")}))
        self.enterContext(patch.object(module.system, "onefile", lambda _: {}))
        self.enterContext(patch.object(module.system, "verify_files", lambda *_: None))

        with self.assertRaises(ValueError):
            module.verify_directory(dossier, {"files": {}}, "Windows", package="msi")

    def test_un_pe_etranger_signe_bien_forme_est_compare_au_build(self):
        module = self.load("licences_c20_pe")
        tmp_path = Path(self.enterContext(tempfile.TemporaryDirectory()))

        entete = bytearray(0x200)
        entete[:2] = b"MZ"
        entete[0x3C:0x40] = (0x80).to_bytes(4, "little")
        entete[0x80:0x84] = b"PE\0\0"
        optional = 0x80 + 24
        entete[optional:optional + 2] = (0x20B).to_bytes(2, "little")
        original = bytes(entete) + b"rodata " + module.BUNDLE_TOKEN + b" code de ce build"
        binaire_build = tmp_path / module.TAURI / "target/release/therese.exe"
        binaire_build.parent.mkdir(parents=True)
        binaire_build.write_bytes(original)

        certificat = b"certificat-test!"
        security = optional + 112 + 4 * 8

        def signer_fictivement(contenu):
            resultat = bytearray(contenu)
            resultat.extend(b"\0" * (-len(resultat) % 8))
            offset = len(resultat)
            resultat[optional + 64:optional + 68] = (1234).to_bytes(4, "little")
            resultat[security:security + 8] = offset.to_bytes(4, "little") + len(certificat).to_bytes(4, "little")
            resultat.extend(certificat)
            return resultat

        meme_build = signer_fictivement(original.replace(module.BUNDLE_TOKEN, module.BUNDLE_TYPES["msi"], 1))
        etranger = signer_fictivement(bytes(entete) + b"programme etranger " + module.BUNDLE_TYPES["msi"] + b" autre code")

        offset = int.from_bytes(etranger[security:security + 4], "little")
        self.assertTrue(offset % 8 == 0 and offset + len(certificat) == len(etranger))
        self.assertTrue(module.authenticode_signed(etranger))
        empreinte_etrangere = module.unsigned_pe_digest(etranger)
        self.assertIsNotNone(empreinte_etrangere)
        empreintes_build = module.built_digests(tmp_path, "Windows", "msi", normalized=True)
        self.assertTrue(empreintes_build and empreinte_etrangere not in empreintes_build)
        self.assertIn(module.unsigned_pe_digest(meme_build), empreintes_build)

        dossier = tmp_path / "installeur"
        dossier.mkdir()
        (dossier / "backend.exe").write_bytes(b"MZmoteur")
        principal = dossier / "therese.exe"
        self.enterContext(patch.object(module, "check_resources", lambda *_: None))
        self.enterContext(patch.object(module, "engine_name", lambda _: "backend.exe"))
        self.enterContext(patch.object(module.system, "onefile", lambda _: {}))
        self.enterContext(patch.object(module.system, "verify_files", lambda *_: None))
        appels_normalises = []
        built_digests = module.built_digests

        def suivre_empreintes(root, platform, package, normalized=False):
            appels_normalises.append(normalized)
            return built_digests(root, platform, package, normalized=normalized)

        self.enterContext(patch.object(module, "built_digests", suivre_empreintes))
        principal.write_bytes(meme_build)
        self.assertIn("therese.exe", module.verify_directory(dossier, {"files": {}}, "Windows", tmp_path, "msi"))
        self.assertEqual(appels_normalises, [False, True])

        appels_normalises.clear()
        principal.write_bytes(etranger)
        with self.assertRaisesRegex(ValueError, "Exécutable principal différent de ce build"):
            module.verify_directory(dossier, {"files": {}}, "Windows", tmp_path, "msi")
        self.assertEqual(appels_normalises, [False, True])


if __name__ == "__main__":
    unittest.main()
