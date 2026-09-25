"""B-1478 (recette P-146, lot 5, KO-8) : mission d'Améliorer THÉRÈSE figée.

La mission vit dans le flux SSE de POST /api/agents/request. Quand le client
part (rechargement de la page), Starlette annule la portée anyio du flux ;
l'annulation est « de niveau » : chaque `await` du `finally` est annulé à son
tour, dont la mise à jour de l'AgentTask. Journal de la recette, 22:00:39 :
« Exception terminating connection … CancelledError: Cancelled via cancel
scope ». La mission restait `in_progress`, plan null, events vides, et
bloquait toute nouvelle mission (409 « déjà en cours »).

L'ancien test d'annulation levait un CancelledError ponctuel dans
l'orchestrateur, que le `finally` survit : il ne voyait pas ce cas. Celui-ci
rejoue le départ comme Starlette, portée annulée dans un groupe de tâches.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import anyio
import pytest
from app.models.processing import EtatTache, ProcessingTask
from app.models.schemas_agents import AgentRequest, AgentStreamChunk
from sqlmodel import select


def _git_factice():
    git = MagicMock()
    git.is_repo = AsyncMock(return_value=True)
    git.current_branch = AsyncMock(return_value="main")
    git.ensure_clean = AsyncMock(return_value=True)
    return git


@pytest.mark.asyncio
async def test_le_depart_du_client_termine_la_mission_annulee(client, tmp_path: Path):
    from app.models.database import get_session_context
    from app.models.entities_agents import AgentTask
    from app.routers import agents as agents_router

    repo = tmp_path / "depot"
    repo.mkdir()
    capture: dict[str, str] = {}
    bloque = asyncio.Event()

    class SwarmQuiReflechit:
        def __init__(self, _source_path: str):
            pass

        async def process_request(self, _message: str, task_id: str):
            capture["id"] = task_id
            yield AgentStreamChunk(type="agent_start", agent="zezette", content="départ", task_id=task_id, phase="spec")
            await bloque.wait()  # le modèle local travaille encore quand le client part
            yield AgentStreamChunk(type="done", content="fin", task_id=task_id, phase="review")

    premier = anyio.Event()
    with (
        patch("app.routers.agents._get_source_path", return_value=str(repo)),
        patch("app.routers.agents.GitService", return_value=_git_factice()),
        patch("app.routers.agents.SwarmOrchestrator", SwarmQuiReflechit),
    ):
        async with get_session_context() as session:
            reponse = await agents_router.agent_request(AgentRequest(message="Mission longue"), session)
            flux = reponse.body_iterator

            async def consommer():
                async for _morceau in flux:
                    premier.set()

            async with anyio.create_task_group() as groupe:
                groupe.start_soon(consommer)
                with anyio.fail_after(5):
                    await premier.wait()
                groupe.cancel_scope.cancel()  # Starlette : le client est parti
            await flux.aclose()

    async with get_session_context() as session:
        mission = (await session.execute(select(AgentTask).where(AgentTask.id == capture["id"]))).scalar_one()
        traitement = (await session.execute(
            select(ProcessingTask).where(ProcessingTask.type == "atelier", ProcessingTask.entity_id == capture["id"])
        )).scalars().first()
    assert mission.status == "cancelled", mission.status
    assert traitement is not None and traitement.state == EtatTache.CANCELLED, traitement.state if traitement else None
    # Personne n'a demandé l'arrêt : la mission ne se dit pas « annulée par l'utilisateur ».
    assert "par l'utilisateur" not in (mission.error or "")
    assert "rechargé" in (mission.error or ""), mission.error
