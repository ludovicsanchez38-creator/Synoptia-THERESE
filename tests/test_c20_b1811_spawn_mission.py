"""Un agent lancé dans l'Atelier occupe le verrou pendant sa mission."""

import pytest
from app.models.database import get_session_context
from app.models.entities_agents import AgentTask
from app.models.schemas_agents import SpawnAgentRequest
from app.routers import agents
from app.services.agents.runtime import AgentEvent, AgentRuntime
from fastapi import HTTPException
from sqlmodel import select


@pytest.mark.asyncio
async def test_spawn_en_cours_bloque_une_seconde_mission(client, monkeypatch):
    constats = {}
    demande = SpawnAgentRequest(profile_id="writer", instruction="Mission", model="local:test")
    monkeypatch.setattr(agents, "_get_source_path", lambda: None)

    async def execution_fictive(_runtime, _instruction):
        async with get_session_context() as session:
            resultat = await session.execute(
                select(AgentTask).where(AgentTask.status.in_(["pending", "in_progress"]))
            )
            actives = list(resultat.scalars())
            constats["missions"] = len(actives)
            constats["annulable"] = bool(
                actives and actives[0].id in agents._running_agent_tasks
            )
            try:
                await agents.spawn_agent(demande, session)
            except HTTPException as exc:
                constats["seconde"] = exc.status_code
            else:
                constats["seconde"] = 200
        yield AgentEvent(type="done", content="Terminé")

    monkeypatch.setattr(AgentRuntime, "run", execution_fictive)
    reponse = await client.post("/api/agents/spawn", json=demande.model_dump())

    assert reponse.status_code == 200
    assert constats["seconde"] == 409
    assert constats["missions"] == 1
    assert constats["annulable"] is True


@pytest.mark.asyncio
@pytest.mark.parametrize(("type_evenement", "statut"), [("done", "done"), ("error", "error")])
async def test_spawn_libere_et_consigne_la_mission(client, monkeypatch, type_evenement, statut):
    monkeypatch.setattr(agents, "_get_source_path", lambda: None)

    async def execution_fictive(_runtime, _instruction):
        yield AgentEvent(type=type_evenement, content="Résultat fictif")

    monkeypatch.setattr(AgentRuntime, "run", execution_fictive)
    reponse = await client.post("/api/agents/spawn", json={
        "profile_id": "writer", "instruction": "Mission", "model": "local:test",
    })
    assert reponse.status_code == 200
    async with get_session_context() as session:
        taches = (await session.execute(select(AgentTask))).scalars().all()
        assert len(taches) == 1
        assert taches[0].status == statut
        assert taches[0].id not in agents._running_agent_tasks
        assert (taches[0].error is not None) is (type_evenement == "error")
