"""B-957 et B-958 (cycle 11, 23/09/2026) : deux relevés du lecteur de carte.

B-957 : `search_codebase` passait le motif à grep sans `-e`. Un motif qui
commence par « - », par exemple `--timeout` ou `-> None`, recherches plausibles
pour un agent qui lit du code, était pris pour une option de grep.

B-958 : `GitService._run` ne rattrapait que l'annulation et le délai. Sans git
dans le PATH (fréquent sous Windows), `create_subprocess_exec` lève
`FileNotFoundError` et `is_repo` levait au lieu de rendre `None`, le « contrôle
non concluant » que promet BUG-163.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from app.services.agents import git_service as module_git
from app.services.agents.git_service import GitService
from app.services.agents.tools import AgentToolExecutor

# Revue Codex R-4 : seuls les tests de search_codebase dépendent de grep ; les
# tests B-958 simulent git absent et doivent tourner aussi sur un poste sans grep.
grep_requis = pytest.mark.skipif(shutil.which("grep") is None, reason="grep requis")


@pytest.fixture
def depot(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    source.mkdir()
    (source / "reglages.py").write_text(
        'OPTIONS = ["--timeout=30", "--verbose"]\n'
        "def lire() -> None:\n"
        "    return None\n",
        encoding="utf-8",
    )
    return source


@grep_requis
@pytest.mark.parametrize("motif", ["--timeout", "-> None"])
async def test_un_motif_qui_commence_par_un_tiret_est_cherche_tel_quel(depot: Path, motif: str):
    sortie = await AgentToolExecutor(str(depot)).search_codebase(motif, "*.py")
    assert "reglages.py" in sortie, sortie
    assert motif in sortie, sortie


@grep_requis
async def test_un_motif_ordinaire_fonctionne_toujours(depot: Path):
    sortie = await AgentToolExecutor(str(depot)).search_codebase("def lire", "*.py")
    assert "reglages.py:2:" in sortie, sortie


async def test_sans_git_joignable_is_repo_n_est_pas_concluant(monkeypatch, tmp_path: Path):
    async def git_introuvable(*args, **kwargs):
        raise FileNotFoundError(2, "No such file or directory", "git")

    monkeypatch.setattr(module_git.asyncio, "create_subprocess_exec", git_introuvable)
    assert await GitService(tmp_path).is_repo() is None


async def test_sans_git_joignable_run_rend_un_echec_lisible(monkeypatch, tmp_path: Path):
    async def git_introuvable(*args, **kwargs):
        raise FileNotFoundError(2, "No such file or directory", "git")

    monkeypatch.setattr(module_git.asyncio, "create_subprocess_exec", git_introuvable)
    code, sortie, erreur = await GitService(tmp_path)._run("status")
    assert code != 0 and sortie == ""
    assert erreur, "l'échec doit rester lisible"
