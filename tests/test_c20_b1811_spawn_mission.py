"""Un agent lancé dans l'Atelier occupe le verrou pendant sa mission."""

import asyncio
import json

import pytest
from app.models.database import get_session_context
from app.models.entities_agents import AgentTask
from app.models.schemas_agents import SpawnAgentRequest
from app.routers import agents
from app.services.agents.runtime import AgentEvent, AgentRuntime
from fastapi import HTTPException
from sqlmodel import select
from starlette.requests import ClientDisconnect


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


@pytest.mark.asyncio
@pytest.mark.parametrize("interruption", ["fermeture", "sans_fin"])
async def test_spawn_interrompu_n_est_pas_consigne_comme_termine(
    db_session, monkeypatch, interruption,
):
    monkeypatch.setattr(agents, "_get_source_path", lambda: None)

    async def execution_fictive(_runtime, _instruction):
        yield AgentEvent(type="chunk", content="Début seulement")

    monkeypatch.setattr(AgentRuntime, "run", execution_fictive)
    demande = SpawnAgentRequest(profile_id="writer", instruction="Mission", model="local:test")
    reponse = await agents.spawn_agent(demande, db_session)
    flux = reponse.body_iterator
    premier = json.loads((await anext(flux))[6:])
    if interruption == "fermeture":
        await flux.aclose()
    else:
        suite = [json.loads(chunk[6:]) async for chunk in flux]
        assert suite and suite[-1]["type"] == "error"

    async with get_session_context() as session:
        tache = await session.get(AgentTask, premier["task_id"])
        assert tache.status == ("cancelled" if interruption == "fermeture" else "error")
        assert tache.error
        assert tache.id not in agents._running_agent_tasks


@pytest.mark.asyncio
async def test_deconnexion_asgi_pendant_envoi_du_fragment_interrompt_la_mission(db_session, monkeypatch):
    monkeypatch.setattr(agents, "_get_source_path", lambda: None)

    async def execution_fictive(_runtime, _instruction):
        yield AgentEvent(type="chunk", content="Début seulement")
        yield AgentEvent(type="done", content="Fin")

    monkeypatch.setattr(AgentRuntime, "run", execution_fictive)
    reponse = await agents.spawn_agent(
        SpawnAgentRequest(profile_id="writer", instruction="Mission", model="local:test"), db_session,
    )
    premier_envoye = asyncio.Event()
    evenements = []

    async def recevoir():
        await premier_envoye.wait()
        return {"type": "http.disconnect"}

    async def envoyer(message):
        if message["type"] == "http.response.body" and message["body"]:
            evenements.append(json.loads(message["body"][6:]))
            premier_envoye.set()
            await asyncio.Event().wait()

    await reponse({"type": "http", "asgi": {"spec_version": "2.3"}}, recevoir, envoyer)
    await reponse.body_iterator.aclose()
    assert [event["type"] for event in evenements] == ["chunk"]
    async with get_session_context() as session:
        tache = await session.get(AgentTask, evenements[0]["task_id"])
        assert tache.status == "cancelled"
        assert "interrompue" in tache.error.lower()


@pytest.mark.asyncio
@pytest.mark.parametrize("version_asgi", ["2.3", "2.4"])
async def test_deconnexion_avant_le_flux_libere_la_mission_et_autorise_un_nouveau_depart(
    db_session, monkeypatch, version_asgi,
):
    monkeypatch.setattr(agents, "_get_source_path", lambda: None)
    executions = []

    async def execution_fictive(_runtime, _instruction):
        executions.append(True)
        yield AgentEvent(type="done", content="Terminé")

    monkeypatch.setattr(AgentRuntime, "run", execution_fictive)
    demande = SpawnAgentRequest(profile_id="writer", instruction="Mission", model="local:test")
    reponse = await agents.spawn_agent(demande, db_session)
    premiere = (await db_session.execute(select(AgentTask))).scalars().one()
    identifiant = premiere.id
    debut_envoi = asyncio.Event()

    async def recevoir():
        await debut_envoi.wait()
        return {"type": "http.disconnect"}

    async def envoyer(message):
        if message["type"] == "http.response.start":
            debut_envoi.set()
            if version_asgi == "2.4":
                raise OSError("déconnexion fictive")
            await asyncio.Event().wait()

    scope = {"type": "http", "asgi": {"spec_version": version_asgi}}
    if version_asgi == "2.4":
        with pytest.raises(ClientDisconnect):
            await reponse(scope, recevoir, envoyer)
    else:
        await reponse(scope, recevoir, envoyer)

    assert executions == []
    async with get_session_context() as session:
        nouvelle = await agents.spawn_agent(demande, session)
        evenements = [json.loads(chunk[6:]) async for chunk in nouvelle.body_iterator]
    assert evenements[-1]["type"] == "done"
    async with get_session_context() as session:
        interrompue = await session.get(AgentTask, identifiant)
        assert interrompue.status == "cancelled"
        assert "interrompue" in interrompue.error.lower()
        assert identifiant not in agents._running_agent_tasks


@pytest.mark.asyncio
@pytest.mark.parametrize(("type_evenement", "statut"), [("done", "done"), ("error", "error")])
async def test_deconnexion_pendant_envoi_terminal_conserve_le_resultat(
    db_session, monkeypatch, type_evenement, statut,
):
    monkeypatch.setattr(agents, "_get_source_path", lambda: None)

    async def execution_fictive(_runtime, _instruction):
        yield AgentEvent(type=type_evenement, content="Résultat fictif")

    monkeypatch.setattr(AgentRuntime, "run", execution_fictive)
    reponse = await agents.spawn_agent(
        SpawnAgentRequest(profile_id="writer", instruction="Mission", model="local:test"), db_session,
    )
    envoye = asyncio.Event()
    evenements = []

    async def recevoir():
        await envoye.wait()
        return {"type": "http.disconnect"}

    async def envoyer(message):
        if message["type"] == "http.response.body" and message["body"]:
            evenements.append(json.loads(message["body"][6:]))
            envoye.set()
            await asyncio.Event().wait()

    await reponse({"type": "http", "asgi": {"spec_version": "2.3"}}, recevoir, envoyer)
    async with get_session_context() as session:
        tache = await session.get(AgentTask, evenements[0]["task_id"])
        assert tache.status == statut
        assert (tache.error is not None) is (type_evenement == "error")
        assert tache.id not in agents._running_agent_tasks


@pytest.mark.asyncio
@pytest.mark.parametrize(("type_evenement", "statut"), [("done", "done"), ("error", "error")])
async def test_fermeture_apres_evenement_terminal_conserve_le_statut(
    db_session, monkeypatch, type_evenement, statut,
):
    monkeypatch.setattr(agents, "_get_source_path", lambda: None)

    async def execution_fictive(_runtime, _instruction):
        yield AgentEvent(type=type_evenement, content="Résultat")

    monkeypatch.setattr(AgentRuntime, "run", execution_fictive)
    reponse = await agents.spawn_agent(
        SpawnAgentRequest(profile_id="writer", instruction="Mission", model="local:test"), db_session,
    )
    flux = reponse.body_iterator
    terminal = json.loads((await anext(flux))[6:])
    await flux.aclose()
    async with get_session_context() as session:
        tache = await session.get(AgentTask, terminal["task_id"])
        assert tache.status == statut
