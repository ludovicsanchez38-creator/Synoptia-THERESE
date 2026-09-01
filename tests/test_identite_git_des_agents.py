"""Un agent doit pouvoir commiter sur une machine sans identite git globale.

Trouve le 01/09/2026 : deux tests nouvellement branches passaient en local et
echouaient sur l'integration continue. La cause n'etait pas dans les tests.

`GitService.init()` lancait un `git init` nu, et `commit()` ne posait aucune
identite. Sur une machine ou `user.email` et `user.name` ne sont pas
configures globalement, le commit echoue et la methode rend None sans que rien
ne le signale. Les agents de THERESE commitent dans des arbres de travail :
sur le poste d'un utilisateur qui n'a jamais configure git, leur travail
disparaissait.

L'identite est celle de l'agent, pas celle de l'utilisateur : elle est donc
posee LOCALEMENT au depot, sans jamais toucher la configuration globale.
"""

import subprocess

import pytest


@pytest.mark.asyncio
async def test_un_commit_reussit_sans_identite_globale(tmp_path, monkeypatch):
    from app.services.agents.git_service import GitService

    # On coupe toute configuration globale et systeme, comme sur une machine neuve.
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "absent-global"))
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", str(tmp_path / "absent-system"))
    monkeypatch.delenv("GIT_AUTHOR_NAME", raising=False)
    monkeypatch.delenv("GIT_AUTHOR_EMAIL", raising=False)
    monkeypatch.delenv("GIT_COMMITTER_NAME", raising=False)
    monkeypatch.delenv("GIT_COMMITTER_EMAIL", raising=False)

    depot = tmp_path / "depot"
    depot.mkdir()
    git = GitService(depot)
    assert await git.init()
    (depot / "fichier.txt").write_text("contenu", encoding="utf-8")

    empreinte = await git.commit("premier commit")
    assert empreinte, "le commit a echoue faute d'identite : le travail de l'agent disparait"

    journal = subprocess.run(
        ["git", "log", "--oneline"], cwd=depot, capture_output=True, text=True
    )
    assert "premier commit" in journal.stdout


@pytest.mark.asyncio
async def test_l_identite_est_locale_au_depot(tmp_path):
    """On ne touche jamais la configuration git de l'utilisateur."""
    from app.services.agents.git_service import GitService

    depot = tmp_path / "depot"
    depot.mkdir()
    git = GitService(depot)
    await git.init()

    locale = subprocess.run(
        ["git", "config", "--local", "user.email"], cwd=depot,
        capture_output=True, text=True,
    )
    assert locale.stdout.strip(), "aucune identite locale posee"
