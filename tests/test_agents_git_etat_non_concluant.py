"""B-027 — un git muet ne doit pas se lire comme « dépôt propre ».

02/09/2026. `is_repo()` avait reçu son tri-état en BUG-163 ; `status()` non.
La chaîne transformait donc tout échec en feu vert :

    _run          -> (1, "", "Timeout")        # ou (128, "", "fatal: ...")
    status()      -> ""                        # `out if code == 0 else ""`
    ensure_clean()-> not "".strip() == True    # « le dépôt est propre »
    swarm.py:194  -> la mission part                 sur les modifications
                                                     non enregistrées de
                                                     l'utilisateur.

Second maillon du même défaut : `current_branch()` renvoyait `"main"` quand
git n'avait rien répondu — une branche INVENTÉE, que swarm passe ensuite comme
base à `create_worktree`, et que le routeur compare à `"main"` pour autoriser
un merge ou un rollback.

L'attendu suit celui de BUG-163 : `None` veut dire « je n'ai pas pu vérifier »,
jamais « tout va bien ».
"""

from __future__ import annotations

from pathlib import Path

import pytest

ECHECS = [
    pytest.param((1, "", "Timeout"), id="git-muet-timeout"),
    pytest.param((128, "", "fatal: not a git repository"), id="git-code-128"),
]


def _git_avec_run(monkeypatch, resultat, chemin):
    from app.services.agents.git_service import GitService

    git = GitService(str(chemin))

    async def faux_run(*_args, **_kwargs):
        return resultat

    monkeypatch.setattr(git, "_run", faux_run)
    return git


class TestUnGitEnEchecNAffirmePasQueLeDepotEstPropre:
    @pytest.mark.parametrize("echec", ECHECS)
    @pytest.mark.asyncio
    async def test_status_ne_maquille_pas_l_echec_en_chaine_vide(
        self, tmp_path: Path, monkeypatch, echec
    ):
        git = _git_avec_run(monkeypatch, echec, tmp_path)
        assert await git.status() is None, (
            "status() rend une chaîne vide sur échec : indiscernable d'un dépôt "
            "réellement sans modification"
        )

    @pytest.mark.parametrize("echec", ECHECS)
    @pytest.mark.asyncio
    async def test_ensure_clean_ne_rend_pas_vrai_sur_un_git_en_echec(
        self, tmp_path: Path, monkeypatch, echec
    ):
        git = _git_avec_run(monkeypatch, echec, tmp_path)
        assert await git.ensure_clean() is None, (
            "ensure_clean() rend True alors que git n'a rien dit : l'Atelier "
            "lance la mission sur des modifications non enregistrées"
        )

    @pytest.mark.parametrize("echec", ECHECS)
    @pytest.mark.asyncio
    async def test_current_branch_n_invente_pas_main(
        self, tmp_path: Path, monkeypatch, echec
    ):
        git = _git_avec_run(monkeypatch, echec, tmp_path)
        assert await git.current_branch() is None, (
            "current_branch() invente 'main' : ce nom repart comme base de "
            "worktree, et autorise merge et rollback"
        )

    @pytest.mark.asyncio
    async def test_un_depot_reellement_propre_reste_propre(
        self, tmp_path: Path, monkeypatch
    ):
        """Verrou : le tri-état ne doit pas noircir le cas nominal."""
        git = _git_avec_run(monkeypatch, (0, "", ""), tmp_path)
        assert await git.status() == ""
        assert await git.ensure_clean() is True

    @pytest.mark.asyncio
    async def test_un_depot_reellement_sale_reste_sale(
        self, tmp_path: Path, monkeypatch
    ):
        git = _git_avec_run(monkeypatch, (0, " M src/backend/app/main.py", ""), tmp_path)
        assert await git.ensure_clean() is False


class TestLesConsommateursRefusentUnEtatNonConcluant:
    """Les portes de l'Atelier doivent refuser, et dire POURQUOI honnêtement."""

    @pytest.mark.asyncio
    async def test_agent_request_refuse_un_etat_de_depot_inconnu(
        self, tmp_path: Path, monkeypatch
    ):
        """La porte d'entrée d'une mission : c'est elle qui protège le travail
        non enregistré de l'utilisateur."""
        from app.models.schemas_agents import AgentRequest
        from app.routers import agents as routeur
        from fastapi import HTTPException

        depot = tmp_path / "THERESE"
        (depot / ".git").mkdir(parents=True)

        class GitMuetSurLeStatut:
            def __init__(self, *_a, **_k):
                pass

            async def is_repo(self):
                return True

            async def current_branch(self):
                return "main"

            async def ensure_clean(self):
                return None

        monkeypatch.setattr(routeur, "GitService", GitMuetSurLeStatut)
        monkeypatch.setattr(routeur, "_get_source_path", lambda *a, **k: str(depot))

        with pytest.raises(HTTPException) as leve:
            await routeur.agent_request(
                AgentRequest(message="ajoute un bouton", source_path=str(depot)),
                session=None,
            )

        assert leve.value.status_code == 503, (
            "un état de dépôt non lu est présenté comme un constat "
            f"(status={leve.value.status_code})"
        )
        assert "n'a pas répondu" in str(leve.value.detail).lower(), leve.value.detail

    @pytest.mark.asyncio
    async def test_approve_refuse_une_branche_non_lue(self, db_session):
        """Sans tri-état, `None != "main"` refusait en accusant l'utilisateur
        d'être sur une autre branche."""
        from unittest.mock import AsyncMock, MagicMock, patch

        from app.models.entities_agents import AgentTask
        from app.routers import agents as routeur
        from fastapi import HTTPException

        tache = AgentTask(
            title="Mission",
            status="review",
            source_path="/tmp/repo",
            branch_name="agent/mission-b027",
        )
        db_session.add(tache)
        await db_session.commit()

        git = MagicMock()
        git.current_branch = AsyncMock(return_value=None)
        git.ensure_clean = AsyncMock(return_value=None)
        git.merge = AsyncMock(return_value=True)

        with (
            patch("app.routers.agents.GitService", return_value=git),
            pytest.raises(HTTPException) as leve,
        ):
            await routeur.approve_task(tache.id, db_session)

        git.merge.assert_not_awaited()
        assert leve.value.status_code == 503, leve.value.status_code
        assert "n'a pas répondu" in str(leve.value.detail).lower(), leve.value.detail

    @pytest.mark.asyncio
    async def test_git_status_outil_ne_dit_pas_aucun_changement_sur_un_echec(self):
        from app.services.agents.tools import AgentToolExecutor

        class GitMuet:
            async def status(self):
                return None

        executeur = AgentToolExecutor.__new__(AgentToolExecutor)
        executeur._git = GitMuet()

        rendu = await executeur.git_status()
        assert "aucun changement" not in rendu.lower(), (
            f"l'outil affirme un dépôt sans changement sur un git muet : {rendu!r}"
        )

    @pytest.mark.asyncio
    async def test_la_garde_de_branche_refuse_une_branche_non_lue(self):
        """`None.startswith` levait un AttributeError nu : la garde d'écriture
        doit refuser explicitement, pas planter."""
        from app.services.agents.tools import BranchGuard

        class GitMuet:
            async def current_branch(self):
                return None

        with pytest.raises(PermissionError):
            await BranchGuard(GitMuet()).check()
