"""
B-118 : `scripts/check-tauri-versions.sh` cessait de contrôler sans le dire.

Le contrôle compare sept paires crate Rust / paquet npm avant chaque release.
Mesuré le 02/09/2026 sur des copies des vrais fichiers de verrous :

- un CRATE renommé dans Cargo.lock : le script s'arrête à la paire suivante,
  code 1, **aucun message** - l'affectation `rust_ver=$(grep ... )` échoue sous
  `set -euo pipefail` et tue le script avant la branche SKIP, qui est donc du
  code mort ;
- un PAQUET npm renommé dans package-lock.json : « SKIP », `return`, `errors`
  jamais incrémenté, puis « Toutes les versions Tauri sont alignées » et
  **code 0** - une paire n'a pas été vérifiée et le contrôle se déclare vert.

L'invariant posé ici, celui de la fiche : une paire attendue et introuvable est
un ÉCHEC du contrôle, et il se nomme.

Les tests travaillent sur une copie du script et des verrous réels dans
`tmp_path` : rien n'est écrit dans le dépôt.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "scripts" / "check-tauri-versions.sh"
CARGO_LOCK = RACINE / "src" / "frontend" / "src-tauri" / "Cargo.lock"
PKG_LOCK = RACINE / "src" / "frontend" / "package-lock.json"


@pytest.fixture
def bac_a_sable(tmp_path: Path) -> Path:
    """Copie du script et des deux verrous, arborescence identique au dépôt."""
    (tmp_path / "scripts").mkdir()
    (tmp_path / "src" / "frontend" / "src-tauri").mkdir(parents=True)
    shutil.copy(SCRIPT, tmp_path / "scripts" / SCRIPT.name)
    shutil.copy(CARGO_LOCK, tmp_path / "src" / "frontend" / "src-tauri" / "Cargo.lock")
    shutil.copy(PKG_LOCK, tmp_path / "src" / "frontend" / "package-lock.json")
    return tmp_path


def _lancer(bac: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(bac / "scripts" / SCRIPT.name)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=bac,
    )


def _renommer_le_crate(bac: Path, ancien: str, nouveau: str) -> None:
    chemin = bac / "src" / "frontend" / "src-tauri" / "Cargo.lock"
    texte = chemin.read_text(encoding="utf-8")
    marqueur = f'name = "{ancien}"'
    assert marqueur in texte, f"{ancien} absent du Cargo.lock de référence"
    chemin.write_text(texte.replace(marqueur, f'name = "{nouveau}"'), encoding="utf-8")


def _renommer_le_paquet_npm(bac: Path, ancien: str, nouveau: str) -> None:
    chemin = bac / "src" / "frontend" / "package-lock.json"
    verrou = json.loads(chemin.read_text(encoding="utf-8"))
    cle = f"node_modules/{ancien}"
    assert cle in verrou["packages"], f"{ancien} absent du package-lock de référence"
    verrou["packages"][f"node_modules/{nouveau}"] = verrou["packages"].pop(cle)
    chemin.write_text(json.dumps(verrou), encoding="utf-8")


class TestUnePaireIntrouvableEstUnEchec:
    def test_temoin_les_verrous_du_depot_passent(self, bac_a_sable: Path):
        """Sans ce témoin, un correctif qui échoue toujours passerait pour bon."""
        resultat = _lancer(bac_a_sable)
        assert resultat.returncode == 0, resultat.stdout + resultat.stderr
        assert "Toutes les versions Tauri sont alignées." in resultat.stdout

    def test_un_crate_renomme_est_nomme_et_fait_echouer(self, bac_a_sable: Path):
        _renommer_le_crate(bac_a_sable, "tauri-plugin-fs", "tauri-plugin-filesystem")

        resultat = _lancer(bac_a_sable)
        sortie = resultat.stdout + resultat.stderr

        assert "tauri-plugin-fs" in sortie, (
            "le contrôle s'arrête sans nommer la paire perdue : "
            f"sortie={sortie!r}"
        )
        assert resultat.returncode != 0
        assert "Toutes les versions Tauri sont alignées." not in resultat.stdout

    def test_un_paquet_npm_renomme_fait_echouer(self, bac_a_sable: Path):
        _renommer_le_paquet_npm(bac_a_sable, "@tauri-apps/plugin-fs", "@tauri-apps/plugin-filesystem")

        resultat = _lancer(bac_a_sable)
        sortie = resultat.stdout + resultat.stderr

        assert "@tauri-apps/plugin-fs" in sortie
        assert "Toutes les versions Tauri sont alignées." not in resultat.stdout, (
            "une paire non vérifiée, et le contrôle se déclare vert"
        )
        assert resultat.returncode != 0

    def test_les_six_autres_paires_sont_quand_meme_controlees(self, bac_a_sable: Path):
        """Un échec ne doit pas masquer l'état des autres paires : le releaseur
        veut la liste complète, pas le premier arrêt."""
        _renommer_le_crate(bac_a_sable, "tauri-plugin-fs", "tauri-plugin-filesystem")

        resultat = _lancer(bac_a_sable)

        assert "tauri-plugin-updater" in resultat.stdout
        assert "tauri-plugin-mic-recorder" in resultat.stdout
