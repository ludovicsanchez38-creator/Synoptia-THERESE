"""Scanner et diff de project.sync - purs et fail-closed (0.45, phase 4).

Contrats du design V2.1 :
- hash SYSTÉMATIQUE (le préfiltre taille+mtime a été retiré au challenge) ;
- stat avant/après le hash : un fichier qui bouge pendant la lecture est
  « instable », exclu du plan, jamais indexé à moitié ;
- fail-closed : racine absente, volume changé ou erreur de parcours font
  ÉCHOUER le scan - un montage débranché ne produit jamais un plan de
  retrait massif ;
- un lien symbolique qui sort de la racine est ignoré et journalisé ;
- le diff classe : nouveau -> indexer, empreinte différente -> reindexer,
  disparu -> retirer (avec l'identité prévue), possédé par un autre
  périmètre -> conflit, sinon inchangé.
"""

from pathlib import Path

import pytest
from app.services.project_sync import (
    EntreeScannee,
    ErreurDeScan,
    calculer_diff,
    scanner_racine,
)


@pytest.fixture
def racine(tmp_path: Path) -> Path:
    d = tmp_path / "dossier-projet"
    d.mkdir()
    (d / "notes.txt").write_text("des notes", encoding="utf-8")
    (d / "rapport.md").write_text("# rapport", encoding="utf-8")
    sous = d / "sous-dossier"
    sous.mkdir()
    (sous / "annexe.txt").write_text("annexe", encoding="utf-8")
    return d


class TestLeScanner:
    @pytest.mark.asyncio
    async def test_scanne_et_hashe_tout(self, racine):
        entrees = await scanner_racine(racine)

        chemins = {e.chemin for e in entrees}
        assert chemins == {
            str(racine / "notes.txt"),
            str(racine / "rapport.md"),
            str(racine / "sous-dossier" / "annexe.txt"),
        }
        for e in entrees:
            assert len(e.sha256) == 64
            assert e.taille > 0
            assert e.mtime_ns > 0

    @pytest.mark.asyncio
    async def test_ignore_caches_git_et_non_indexables(self, racine):
        (racine / ".cachette").write_text("x", encoding="utf-8")
        git = racine / ".git"
        git.mkdir()
        (git / "objet.txt").write_text("x", encoding="utf-8")
        nm = racine / "node_modules"
        nm.mkdir()
        (nm / "paquet.txt").write_text("x", encoding="utf-8")
        (racine / "binaire.exe").write_bytes(b"\x00\x01")

        entrees = await scanner_racine(racine)

        chemins = {Path(e.chemin).name for e in entrees}
        assert chemins == {"notes.txt", "rapport.md", "annexe.txt"}

    @pytest.mark.asyncio
    async def test_racine_absente_echoue_sans_rien_produire(self, tmp_path):
        with pytest.raises(ErreurDeScan):
            await scanner_racine(tmp_path / "debranchee")

    @pytest.mark.asyncio
    async def test_un_symlink_sortant_est_ignore(self, racine, tmp_path):
        dehors = tmp_path / "ailleurs.txt"
        dehors.write_text("hors racine", encoding="utf-8")
        (racine / "evade.txt").symlink_to(dehors)

        entrees = await scanner_racine(racine)

        assert "evade.txt" not in {Path(e.chemin).name for e in entrees}

    @pytest.mark.asyncio
    async def test_un_fichier_qui_bouge_pendant_le_hash_est_instable(
        self, racine, monkeypatch
    ):
        """stat avant/après : si le fichier change pendant la lecture, on ne
        sait pas ce qu'on a hashé - il est exclu du plan, pas indexé à moitié."""
        from app.services import project_sync as module

        cible = racine / "notes.txt"
        vrai_hash = module._hacher

        def hash_qui_derange(chemin: Path) -> str:
            resultat = vrai_hash(chemin)
            if chemin == cible:
                cible.write_text("changé pendant la lecture", encoding="utf-8")
            return resultat

        monkeypatch.setattr(module, "_hacher", hash_qui_derange)

        entrees = await scanner_racine(racine)

        assert "notes.txt" not in {Path(e.chemin).name for e in entrees}
        assert {Path(e.chemin).name for e in entrees} == {"rapport.md", "annexe.txt"}


class TestLeDiff:
    def _entree(self, chemin: str, sha: str = "a" * 64) -> EntreeScannee:
        return EntreeScannee(chemin=chemin, taille=10, mtime_ns=1, sha256=sha)

    def test_nouveau_modifie_disparu_inchange(self):
        scannees = [
            self._entree("/r/nouveau.txt"),
            self._entree("/r/modifie.txt", sha="b" * 64),
            self._entree("/r/inchange.txt", sha="c" * 64),
        ]
        referentiel = {
            "/r/modifie.txt": ("id-modifie", "x" * 64),
            "/r/inchange.txt": ("id-inchange", "c" * 64),
            "/r/disparu.txt": ("id-disparu", "d" * 64),
        }

        diff = calculer_diff(scannees, referentiel, proprietaires={})

        assert [o.chemin for o in diff.indexer] == ["/r/nouveau.txt"]
        assert [o.chemin for o in diff.reindexer] == ["/r/modifie.txt"]
        assert [(o.chemin, o.file_id_prevu) for o in diff.retirer] == [
            ("/r/disparu.txt", "id-disparu")
        ]
        assert diff.inchanges == 1

    def test_un_chemin_possede_ailleurs_est_un_conflit(self):
        """Jamais de reclassement silencieux : un fichier global ou d'un autre
        projet est montré en conflit, pas indexé sous ce projet."""
        scannees = [self._entree("/r/confisque.txt")]
        proprietaires = {"/r/confisque.txt": ("global", None)}

        diff = calculer_diff(scannees, {}, proprietaires=proprietaires)

        assert diff.indexer == []
        assert [o.chemin for o in diff.conflits] == ["/r/confisque.txt"]
