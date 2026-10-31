"""Chaque texte de licence ajouté en supplément cite une source encore verrouillée.

Correctifs 0.83 : la montée de filelock en 4.2.5 (Unlicense → MIT) laissait la
preuve du supplément `Unlicense.json` citer filelock 3.20.3, absent du verrou,
alors que six crates Cargo reçoivent toujours ce texte. Une preuve qui cite une
archive que la release n'inventorie plus ne prouve plus rien.
"""
import hashlib
import json
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))
import third_party_licenses as licenses  # noqa: E402


def _texte_servi(chemin):
    brut = (ROOT / chemin).read_bytes()
    return licenses.source_text(brut, {'json_text': chemin.endswith('.json')})


class ProvenanceDesSupplementsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lignes = {r['id']: r for r in json.loads((ROOT / licenses.INVENTORY).read_text(encoding='utf-8'))['packages']}
        cls.surcharges = json.loads((ROOT / 'licenses/overrides.json').read_text(encoding='utf-8'))
        cls.preuves = [p for p in json.loads((ROOT / 'licenses/attribution-sources.json').read_text(encoding='utf-8'))
                       if 'source_package' in p]

    def _servi_par(self, chemin):
        return {k for k, v in self.surcharges.items() if any(n.get('local_path') == chemin for n in v.get('notices', []))}

    def test_chaque_preuve_cite_un_paquet_verrouille(self):
        self.assertGreaterEqual(len(self.preuves), 7)
        for preuve in self.preuves:
            with self.subTest(fichier=preuve['file']):
                self.assertTrue(preuve['source_package'] in self.lignes,
                                f"{preuve['source_package']} n'est plus dans le verrou")

    def test_une_archive_citee_est_celle_du_verrou(self):
        for preuve in [p for p in self.preuves if 'archive_integrity' in p]:
            with self.subTest(fichier=preuve['file']):
                ligne = self.lignes[preuve['source_package']]
                self.assertEqual(preuve['archive'], ligne['artifact'])
                self.assertEqual(preuve['archive_integrity'], ligne['integrity'])

    def test_un_texte_declare_inchange_est_celui_de_la_source(self):
        for preuve in [p for p in self.preuves if p['transformation'].startswith('Texte intégral inchangé')]:
            with self.subTest(fichier=preuve['file']):
                texte = _texte_servi(preuve['file'])
                self.assertEqual(hashlib.sha256(texte.encode()).hexdigest(), preuve['source_text_sha256'])

    def test_chaque_supplement_prouve_est_reellement_servi(self):
        for preuve in self.preuves:
            with self.subTest(fichier=preuve['file']):
                self.assertTrue(self._servi_par(preuve['file']))

    def test_unlicense_cite_l_archive_d_un_paquet_qu_il_sert(self):
        preuve = next(p for p in self.preuves if p['file'] == 'licenses/supplements/Unlicense.json')
        ligne = self.lignes[preuve['source_package']]
        self.assertIn(preuve['source_package'], self._servi_par(preuve['file']))
        self.assertIn('Unlicense', ligne['license'])
        dossier = ligne['artifact'].rsplit('/', 1)[1].removesuffix('.crate')
        self.assertEqual(preuve['source_notice'], f'{dossier}/UNLICENSE')
        self.assertRegex(preuve.get('member_sha256', ''), r'^[a-f0-9]{64}$')


if __name__ == '__main__':
    unittest.main()
