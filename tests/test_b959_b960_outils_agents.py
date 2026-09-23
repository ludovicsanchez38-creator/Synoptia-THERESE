"""B-960 (cycle 11, 23/09/2026) : relevé du second lecteur de carte.

`git_diff` affichait « Aucun diff » quand git échouait : base introuvable,
dépôt absent ou git injoignable passaient pour un diff vide. Même principe que
BUG-163 : ne jamais confondre « je n'ai pas pu lire » avec « il n'y a rien ».
"""

from __future__ import annotations

from pathlib import Path

from app.services.agents.git_service import GitService
from app.services.agents.tools import AgentToolExecutor


class _GitEnEchec(GitService):
    async def _run(self, *args: str, timeout: float = 30.0):
        return 128, "", "fatal: ambiguous argument 'main...HEAD': unknown revision"


class _GitSansChangement(GitService):
    async def _run(self, *args: str, timeout: float = 30.0):
        return 0, "", ""


async def test_b960_un_echec_de_git_n_est_pas_un_diff_vide(tmp_path: Path):
    sortie = await AgentToolExecutor(str(tmp_path), git_service=_GitEnEchec(tmp_path)).git_diff()
    assert sortie != "Aucun diff"
    assert "chec" in sortie and "unknown revision" in sortie, sortie


async def test_b960_un_diff_reellement_vide_reste_aucun_diff(tmp_path: Path):
    sortie = await AgentToolExecutor(str(tmp_path), git_service=_GitSansChangement(tmp_path)).git_diff()
    assert sortie == "Aucun diff"
