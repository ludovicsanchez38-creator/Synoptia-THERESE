"""B-961 et B-962 (cycle 11, 23/09/2026) : relevés du quatrième lecteur de carte.

B-961 : `list_directory` compare le chemin résolu de chaque entrée à la racine
NON résolue du dépôt. Dès que le dépôt est désigné par un lien symbolique,
chaque appel rend « Erreur : ... ». Sous macOS, l'arbre de travail que swarm.py
crée pour Zézette sous `tempfile.gettempdir()` passe par /var -> /private/var.

B-962 : `search_codebase` ignorait le code de sortie de grep ; un motif
invalide (code 2) s'affichait « Aucun résultat ».
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from app.services.agents.tools import AgentToolExecutor


@pytest.fixture
def depot_par_un_lien(tmp_path: Path) -> Path:
    reel = tmp_path / "private" / "depot"
    (reel / "src").mkdir(parents=True)
    (reel / "src" / "module.py").write_text("VALEUR = 1\n", encoding="utf-8")
    (reel / "LISEZMOI.md").write_text("titre\n", encoding="utf-8")
    lien = tmp_path / "var"
    try:
        lien.symlink_to(tmp_path / "private", target_is_directory=True)
    except OSError as exc:
        # Revue Codex R-6 : sous Windows, créer un lien exige un privilège ou le
        # mode développeur (erreur 1314). Seul ce cas est sauté.
        if getattr(exc, "winerror", None) == 1314:
            pytest.skip("liens symboliques indisponibles sur ce poste Windows")
        raise
    return lien / "depot"


async def test_b961_list_directory_par_un_lien_liste_le_depot(depot_par_un_lien: Path):
    sortie = await AgentToolExecutor(str(depot_par_un_lien)).list_directory(".")
    assert not sortie.startswith("Erreur"), sortie
    assert "LISEZMOI.md" in sortie and "src" in sortie, sortie


async def test_b961_list_directory_d_un_sous_dossier_par_un_lien(depot_par_un_lien: Path):
    sortie = await AgentToolExecutor(str(depot_par_un_lien)).list_directory("src")
    assert not sortie.startswith("Erreur"), sortie
    # Revue Codex R-5 : séparateur du système (src\module.py sous Windows).
    assert str(Path("src") / "module.py") in sortie, sortie


@pytest.mark.skipif(shutil.which("grep") is None, reason="grep requis")
async def test_b962_un_motif_invalide_est_une_erreur(tmp_path: Path):
    (tmp_path / "a.py").write_text("x = [1]\n", encoding="utf-8")
    sortie = await AgentToolExecutor(str(tmp_path)).search_codebase("[", "*.py")
    assert not sortie.startswith("Aucun résultat"), sortie
    assert sortie.startswith("Erreur"), sortie


@pytest.mark.skipif(shutil.which("grep") is None, reason="grep requis")
async def test_b962_aucune_correspondance_reste_aucun_resultat(tmp_path: Path):
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    sortie = await AgentToolExecutor(str(tmp_path)).search_codebase("introuvable", "*.py")
    assert sortie.startswith("Aucun résultat"), sortie
