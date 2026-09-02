"""
B-117 : `scripts/bump-version.sh` sautait la régénération de l'index des noms
dès qu'on le lançait d'ailleurs que la racine du dépôt.

Tout le script travaille sur `$ROOT` (calculé depuis `dirname $0`, l.20) sauf le
dernier bloc, qui testait `[ -f scripts/index-des-noms.mjs ]` et écrivait
`> docs/INDEX-DES-NOMS.md` en chemin RELATIF. Lancé depuis un autre dossier, la
condition est fausse : le bloc est sauté en silence et le script sort en succès.
C'est exactement le défaut que son propre commentaire (l.126-129) dit avoir
corrigé après la release 0.57.0, où la CI backend rougissait sur
`test_index_des_noms.py` une fois le tag déjà poussé.

Le test ne lance JAMAIS le vrai script sur le dépôt (un bump est irréversible en
release) : il construit une racine jetable dans `tmp_path` avec les sept fichiers
de version, un générateur bidon et un `node` bidon, puis lance le script depuis
un dossier tiers - la condition de la fiche.

Bornes : `sed -i ''` est de la syntaxe BSD, ce script ne tourne que sur macOS ;
la CI Ubuntu saute donc ces deux tests.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="rejoue un script bash de CI ou de release : sur le runner Windows, bash invoque WSL sans distribution (constate le 02/09/2026, run 33674744677)",
)

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "scripts" / "bump-version.sh"

SORTIE_DU_GENERATEUR = "# Index des noms (généré par le stub de test)"

FICHIERS_DE_VERSION = {
    "pyproject.toml": '[project]\nname = "therese"\nversion = "0.1.0"\n',
    "package.json": '{\n  "name": "therese",\n  "version": "0.1.0"\n}\n',
    "src/frontend/package.json": '{\n  "name": "therese-frontend",\n  "version": "0.1.0"\n}\n',
    "src/frontend/src-tauri/tauri.conf.json": '{\n  "version": "0.1.0"\n}\n',
    "src/frontend/src-tauri/Cargo.toml": '[package]\nname = "therese"\nversion = "0.1.0"\n',
    "src/backend/app/config.py": '    app_version: str = "0.1.0"\n',
    "src/backend/app/__init__.py": '__version__ = "0.1.0"\n',
}

pytestmark = pytest.mark.skipif(
    sys.platform != "darwin",
    reason="bump-version.sh utilise « sed -i '' » (BSD) : il ne tourne que sur macOS",
)


@pytest.fixture
def racine_jetable(tmp_path: Path) -> Path:
    """Une racine de dépôt minimale, avec un générateur d'index et un node bidon."""
    racine = tmp_path / "depot"
    for relatif, contenu in FICHIERS_DE_VERSION.items():
        cible = racine / relatif
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_text(contenu, encoding="utf-8")

    (racine / "docs").mkdir()
    (racine / "scripts").mkdir(exist_ok=True)
    shutil.copy(SCRIPT, racine / "scripts" / SCRIPT.name)
    (racine / "scripts" / "index-des-noms.mjs").write_text(
        "console.log('inutilise : node est bidon')\n", encoding="utf-8"
    )

    binaires = tmp_path / "bin"
    binaires.mkdir()
    faux_node = binaires / "node"
    faux_node.write_text(f"#!/bin/sh\necho \"{SORTIE_DU_GENERATEUR}\"\n", encoding="utf-8")
    faux_node.chmod(0o755)

    (tmp_path / "ailleurs").mkdir()
    return racine


def _lancer_depuis_ailleurs(racine: Path) -> subprocess.CompletedProcess:
    """Le cas de la fiche : le script est lancé par son chemin, d'un autre dossier.

    PATH réduit à dessein : npm, cargo et uv sont absents, donc les branches
    « ATTENTION » du script s'exécutent et rien ne part sur le réseau. Seul
    `node` est fourni, en bidon.
    """
    environnement = dict(os.environ)
    environnement["PATH"] = f"{racine.parent / 'bin'}{os.pathsep}/usr/bin{os.pathsep}/bin"
    return subprocess.run(
        ["bash", str(racine / "scripts" / "bump-version.sh"), "9.9.9"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=racine.parent / "ailleurs",
        env=environnement,
    )


class TestLIndexEstRegenereQuelQueSoitLeDossierCourant:
    def test_lance_hors_racine_l_index_est_bien_regenere(self, racine_jetable: Path):
        resultat = _lancer_depuis_ailleurs(racine_jetable)

        index = racine_jetable / "docs" / "INDEX-DES-NOMS.md"
        assert index.exists(), (
            "l'index n'a pas été régénéré depuis un autre dossier courant : "
            f"sortie={resultat.stdout!r}"
        )
        assert SORTIE_DU_GENERATEUR in index.read_text(encoding="utf-8")
        assert resultat.returncode == 0, resultat.stdout + resultat.stderr

    def test_un_generateur_absent_fait_echouer_bruyamment(self, racine_jetable: Path):
        """« S'exécute ou échoue bruyamment » : un saut silencieux est ce qui a
        laissé partir la 0.57.0 avec une CI rouge après le tag."""
        (racine_jetable / "scripts" / "index-des-noms.mjs").unlink()

        resultat = _lancer_depuis_ailleurs(racine_jetable)
        sortie = resultat.stdout + resultat.stderr

        assert resultat.returncode != 0, sortie
        assert "index-des-noms" in sortie.lower() or "INDEX-DES-NOMS" in sortie
