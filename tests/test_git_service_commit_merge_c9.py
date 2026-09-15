"""B-852 et B-853 (cycle 9) : deux silences du service git de l'Atelier.

- `commit(files=[...])` ignorait le code de retour de chaque `git add` : un
  chemin erroné échouait en silence, puis « nothing to commit » rendait None
  et l'appelant concluait que la mission n'avait rien produit (B-852).
- `merge()` basculait sur la branche cible et n'y revenait pas si la fusion
  échouait : après l'`--abort`, l'arbre de travail restait sur la cible alors
  que l'appelant se croyait encore sur la branche d'agent (B-853).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from app.services.agents.git_service import GitCommitEchoue, GitService


def _git(depot: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(depot), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def depot(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.email", "test@example.test")
    _git(tmp_path, "config", "user.name", "Test")
    _git(tmp_path, "config", "commit.gpgsign", "false")
    (tmp_path / "a.txt").write_text("v1\n", encoding="utf-8")
    _git(tmp_path, "add", "a.txt")
    _git(tmp_path, "commit", "-q", "-m", "initial")
    return tmp_path


@pytest.mark.asyncio
async def test_un_chemin_introuvable_fait_echouer_le_commit(depot: Path) -> None:
    (depot / "a.txt").write_text("v2\n", encoding="utf-8")
    service = GitService(depot)
    with pytest.raises(GitCommitEchoue) as attrape:
        await service.commit("modification", files=["inexistant.txt"])
    assert "inexistant.txt" in str(attrape.value)


@pytest.mark.asyncio
async def test_un_merge_en_conflit_revient_sur_la_branche_de_depart(depot: Path) -> None:
    _git(depot, "checkout", "-q", "-b", "agent")
    (depot / "a.txt").write_text("agent\n", encoding="utf-8")
    _git(depot, "commit", "-q", "-am", "agent")
    _git(depot, "checkout", "-q", "main")
    (depot / "a.txt").write_text("main\n", encoding="utf-8")
    _git(depot, "commit", "-q", "-am", "main")
    _git(depot, "checkout", "-q", "agent")

    service = GitService(depot)
    assert await service.merge("agent", into="main") is False
    assert _git(depot, "rev-parse", "--abbrev-ref", "HEAD") == "agent"
    assert _git(depot, "status", "--porcelain") == ""
