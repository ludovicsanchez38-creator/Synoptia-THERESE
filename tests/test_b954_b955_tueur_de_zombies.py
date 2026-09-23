"""B-954 et B-955 (cycle 11, 23/09/2026) : le nettoyage de démarrage du moteur.

B-955 : `_kill_zombie_backends` supprimait `~/.therese/qdrant/.lock` en dur,
sans tenir compte de `THERESE_DATA_DIR`. Un test l'appelle : lancée sur
DreamQuest SYN, la suite du dépôt a supprimé le verrou Qdrant du vrai profil de
la machine (instance arrêtée, aucune donnée métier touchée). Le nettoyage vise
désormais le dossier de données effectif, comme `config.py`.

B-954 (revue Codex du diff de B-949) : le `pgrep` de ce nettoyage héritait
encore du `LD_LIBRARY_PATH` du bundle PyInstaller.

Chaque test isole `HOME` et `THERESE_DATA_DIR` dans des dossiers temporaires.
"""

from __future__ import annotations

import subprocess
import sys
import types
from pathlib import Path

# Importé ici, avant toute simulation de sys.frozen : sous gel, l'import de
# main.py écrit un diagnostic dans ~/.therese/logs (BUG-009). Relevé par la
# seconde revue Codex (R-3) : lancé seul, le test B-954 l'aurait écrit dans
# le vrai profil.
import main as point_d_entree  # noqa: E402
import pytest

BUNDLE = "/usr/lib/THERESE/binaries/backend-libs/_internal"
ORIGINE = "/usr/local/lib/du-poste"


@pytest.fixture
def maison(monkeypatch, tmp_path: Path) -> Path:
    maison = tmp_path / "maison"
    (maison / ".therese" / "qdrant").mkdir(parents=True)
    (maison / ".therese" / "qdrant" / ".lock").write_text("", encoding="utf-8")
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: maison))
    # expanduser lit HOME (POSIX) ou USERPROFILE (Windows), pas Path.home.
    monkeypatch.setenv("HOME", str(maison))
    monkeypatch.setenv("USERPROFILE", str(maison))
    monkeypatch.setattr(sys, "platform", "linux")
    return maison


def _intercepter(monkeypatch) -> list[tuple[list[str], dict]]:
    appels: list[tuple[list[str], dict]] = []

    def faux_run(commande, **kwargs):
        appels.append((commande, kwargs))
        return types.SimpleNamespace(stdout="", returncode=1)

    monkeypatch.setattr(subprocess, "run", faux_run)
    return appels


class TestB955VerrouDuProfilEffectif:
    def test_avec_therese_data_dir_le_profil_de_la_maison_est_intact(self, maison, monkeypatch, tmp_path: Path):
        donnees = tmp_path / "profil-jetable"
        (donnees / "qdrant").mkdir(parents=True)
        (donnees / "qdrant" / ".lock").write_text("", encoding="utf-8")
        monkeypatch.setenv("THERESE_DATA_DIR", str(donnees))
        _intercepter(monkeypatch)
        point_d_entree._kill_zombie_backends()

        assert not (donnees / "qdrant" / ".lock").exists(), "le verrou du profil effectif est nettoyé"
        assert (maison / ".therese" / "qdrant" / ".lock").exists(), "le profil de la maison n'est pas touché"

    def test_sans_therese_data_dir_le_profil_par_defaut_est_nettoye(self, maison, monkeypatch):
        monkeypatch.delenv("THERESE_DATA_DIR", raising=False)
        _intercepter(monkeypatch)
        point_d_entree._kill_zombie_backends()

        assert not (maison / ".therese" / "qdrant" / ".lock").exists()


class TestB954PgrepSansBibliothequesDuBundle:
    def test_pgrep_recoit_le_ld_library_path_d_origine(self, maison, monkeypatch, tmp_path: Path):
        monkeypatch.setenv("THERESE_DATA_DIR", str(tmp_path / "profil-jetable"))
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setenv("LD_LIBRARY_PATH", f"{BUNDLE}:{ORIGINE}")
        monkeypatch.setenv("LD_LIBRARY_PATH_ORIG", ORIGINE)
        appels = _intercepter(monkeypatch)
        point_d_entree._kill_zombie_backends()

        pgrep = [kwargs for commande, kwargs in appels if commande[0] == "pgrep"]
        assert pgrep, "pgrep n'a pas été lancé"
        env = pgrep[0].get("env")
        assert env is not None, "pgrep hérite de l'environnement du bundle"
        assert env.get("LD_LIBRARY_PATH") == ORIGINE
