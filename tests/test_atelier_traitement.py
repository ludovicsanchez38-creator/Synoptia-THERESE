"""Phase 3 du chantier 0.46 - l'Atelier est un traitement visible et honnête.

Contrats (design V2.1) : une mission crée un ProcessingTask type `atelier`
lié à l'AgentTask (`entity_id`), vivant au registre runtime PENDANT le flux,
et l'état final est COHÉRENT avec celui de l'AgentTask sur tous les chemins
de sortie (succès, erreur, annulation/déconnexion).
"""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models.processing import EtatTache, ProcessingTask
from app.models.schemas_agents import AgentStreamChunk
from sqlmodel import select


def _git_factice():
    git = MagicMock()
    git.is_repo = AsyncMock(return_value=True)
    git.current_branch = AsyncMock(return_value="main")
    git.ensure_clean = AsyncMock(return_value=True)
    return git


async def _traitement_atelier(agent_task_id: str) -> ProcessingTask | None:
    from app.models.database import get_session_context

    async with get_session_context() as session:
        resultat = await session.execute(
            select(ProcessingTask).where(
                ProcessingTask.type == "atelier",
                ProcessingTask.entity_id == agent_task_id,
            )
        )
        return resultat.scalars().first()


def _task_id_du_flux(texte: str) -> str:
    ligne = next(
        ligne for ligne in texte.splitlines() if '"task_id"' in ligne
    )
    return json.loads(ligne.removeprefix("data: "))["task_id"]


class TestLaMissionEstUnTraitement:
    @pytest.mark.asyncio
    async def test_nominal_running_pendant_done_apres(self, client, tmp_path: Path):
        repo = tmp_path / "repo-a"
        repo.mkdir()
        constats: dict[str, object] = {}

        class FakeSwarm:
            def __init__(self, _source_path: str):
                pass

            async def process_request(self, _message: str, task_id: str):
                # PENDANT le flux : le traitement existe, tourne, et son
                # adaptateur est vivant (annulable depuis le panneau).
                from app.services import task_registry

                traitement = await _traitement_atelier(task_id)
                constats["pendant_state"] = traitement.state if traitement else None
                constats["pendant_vivant"] = (
                    task_registry.est_vivante(traitement.id) if traitement else False
                )
                yield AgentStreamChunk(
                    type="done", content="Terminé", task_id=task_id, phase="review",
                )

        with (
            patch("app.routers.agents._get_source_path", return_value=str(repo)),
            patch("app.routers.agents.GitService", return_value=_git_factice()),
            patch("app.routers.agents.SwarmOrchestrator", FakeSwarm),
        ):
            reponse = await client.post(
                "/api/agents/request", json={"message": "Mission nominale"},
            )

        assert reponse.status_code == 200, reponse.text
        assert constats["pendant_state"] == EtatTache.RUNNING
        assert constats["pendant_vivant"] is True

        traitement = await _traitement_atelier(_task_id_du_flux(reponse.text))
        assert traitement is not None
        assert traitement.state == EtatTache.DONE
        assert "Mission nominale" in traitement.label

    @pytest.mark.asyncio
    async def test_une_erreur_termine_failed(self, client, tmp_path: Path):
        repo = tmp_path / "repo-b"
        repo.mkdir()

        class SwarmEnPanne:
            def __init__(self, _source_path: str):
                pass

            async def process_request(self, _message: str, task_id: str):
                yield AgentStreamChunk(
                    type="agent_start", agent="katia", content="départ",
                    task_id=task_id, phase="spec",
                )
                raise RuntimeError("orchestrateur en panne")

        with (
            patch("app.routers.agents._get_source_path", return_value=str(repo)),
            patch("app.routers.agents.GitService", return_value=_git_factice()),
            patch("app.routers.agents.SwarmOrchestrator", SwarmEnPanne),
        ):
            reponse = await client.post(
                "/api/agents/request", json={"message": "Mission en panne"},
            )

        traitement = await _traitement_atelier(_task_id_du_flux(reponse.text))
        assert traitement is not None
        assert traitement.state == EtatTache.FAILED
        assert "panne" in (traitement.error or "")

    @pytest.mark.asyncio
    async def test_une_annulation_termine_cancelled_et_reste_coherente(
        self, client, tmp_path: Path
    ):
        """Déconnexion ou annulation : CancelledError traverse le flux - le
        ProcessingTask finit `cancelled`, comme l'AgentTask, jamais un
        `running` fantôme."""
        repo = tmp_path / "repo-c"
        repo.mkdir()
        capture: dict[str, str] = {}

        class SwarmAnnule:
            def __init__(self, _source_path: str):
                pass

            async def process_request(self, _message: str, task_id: str):
                capture["agent_task_id"] = task_id
                yield AgentStreamChunk(
                    type="agent_start", agent="katia", content="départ",
                    task_id=task_id, phase="spec",
                )
                raise asyncio.CancelledError()

        with (
            patch("app.routers.agents._get_source_path", return_value=str(repo)),
            patch("app.routers.agents.GitService", return_value=_git_factice()),
            patch("app.routers.agents.SwarmOrchestrator", SwarmAnnule),
        ):
            try:
                await client.post(
                    "/api/agents/request", json={"message": "Mission annulée"},
                )
            except BaseException:
                pass  # le CancelledError peut traverser le client de test

        traitement = await _traitement_atelier(capture["agent_task_id"])
        assert traitement is not None
        assert traitement.state == EtatTache.CANCELLED

        from app.models.database import get_session_context
        from app.models.entities_agents import AgentTask

        async with get_session_context() as session:
            resultat = await session.execute(
                select(AgentTask).where(AgentTask.id == capture["agent_task_id"])
            )
            agent_task = resultat.scalar_one_or_none()
        assert agent_task is not None
        assert agent_task.status == "cancelled", (
            "les deux cycles de vie doivent dire la même chose"
        )
