"""B-1153, garantie 6 : git dans le worktree de mission n'exécute aucun code
posé par l'agent ni venu de la configuration globale.

En fin de mission, THÉRÈSE lance `git add -A`, `git commit` et des `git diff`
dans le worktree, hors du bac à sable. Avant : les hooks du dépôt de
l'utilisateur s'exécutaient (et `pre-commit` lit une configuration que l'agent
peut réécrire), un `.gitattributes` écrit par l'agent faisait tourner les
pilotes `filter` et `textconv` de la configuration globale, et un `.git`
réécrit dans le worktree redirigeait git vers un faux dépôt.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from app.services.agents.git_service import GitService


def _git(depot: Path, *args: str, env: dict | None = None) -> str:
    return subprocess.run(["git", "-C", str(depot), *args], check=True, capture_output=True, text=True, env=env).stdout.strip()


@pytest.fixture
def poste(tmp_path: Path, monkeypatch):
    """Un dépôt, une configuration globale piégée et des témoins."""
    temoins = tmp_path / "temoins"
    temoins.mkdir()
    globale = tmp_path / "gitconfig-global"
    globale.write_text(
        "[user]\n\tname = Léa Martin\n\temail = lea@exemple.fr\n"
        f'[filter "piege"]\n\tclean = "touch {temoins}/filter; cat"\n'
        f'[diff "piege"]\n\ttextconv = "touch {temoins}/textconv; cat"\n',
        encoding="utf-8",
    )
    for variable in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL", "GIT_DIR", "GIT_WORK_TREE"):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(globale))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("HOME", str(tmp_path))

    depot = tmp_path / "depot"
    depot.mkdir()
    _git(depot, "init", "-q", "-b", "main")
    (depot / "lisez-moi.txt").write_text("base\n", encoding="utf-8")
    _git(depot, "add", "-A")
    _git(depot, "commit", "-q", "-m", "base")
    crochet = depot / ".git" / "hooks" / "pre-commit"
    crochet.write_text(f"#!/bin/sh\ntouch {temoins}/hook\n", encoding="utf-8")
    crochet.chmod(0o755)
    return depot, temoins


@pytest.mark.asyncio
async def test_le_commit_de_mission_n_execute_ni_hook_ni_pilote_ni_faux_depot(poste, tmp_path: Path):
    depot, temoins = poste
    worktree = tmp_path / "mission"
    assert await GitService(depot).create_worktree(worktree, "agent/mission", "main")
    mission = await GitService.pour_mission(worktree)

    # Ce que l'agent écrit dans son worktree :
    (worktree / ".gitattributes").write_text("*.txt filter=piege diff=piege\n", encoding="utf-8")
    (worktree / "lisez-moi.txt").write_text("modifié par l'agent\n", encoding="utf-8")
    faux = worktree / ".faux-git"
    subprocess.run(["git", "init", "-q", "--bare", str(faux)], check=True, capture_output=True)
    (faux / "hooks" / "pre-commit").write_text(f"#!/bin/sh\ntouch {temoins}/faux\n", encoding="utf-8")
    (faux / "hooks" / "pre-commit").chmod(0o755)
    (worktree / ".git").write_text(f"gitdir: {faux}\n", encoding="utf-8")

    empreinte = await mission.commit("travail de l'agent")
    fichiers = await mission.diff_files(base="main")
    await mission.diff(base="main")

    assert empreinte, "le commit de mission doit réussir"
    assert sorted(p.name for p in temoins.iterdir()) == [], "du code a tourné pendant le commit ou le diff"
    assert _git(depot, "rev-parse", "agent/mission") == empreinte, "le commit doit aller sur la vraie branche"
    assert _git(depot, "log", "-1", "--format=%an <%ae>", "agent/mission") == "Léa Martin <lea@exemple.fr>"
    assert {f["file_path"] for f in fichiers} >= {"lisez-moi.txt", ".gitattributes"}
