"""B-1825 : un démarrage MCP inachevé ne laisse aucun processus vivant."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services import mcp_service as module
from app.services.mcp_service import MCPServer, MCPServerStatus, MCPService
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_arret_volontaire_pendant_initialisation_reste_arrete(tmp_path, monkeypatch):
    from app.routers import mcp

    service = MCPService(config_path=tmp_path / "serveurs.json")
    serveur = MCPServer(id="test", name="Témoin", command="python")
    service.servers[serveur.id] = serveur
    initialisation = asyncio.Event()
    terminaison = asyncio.Event()

    async def initialiser(_identifiant):
        initialisation.set()
        await terminaison.wait()
        raise RuntimeError("Le processus vient de se fermer")

    processus = SimpleNamespace(
        pid=123, stdout=None, stderr=None, terminate=MagicMock(side_effect=terminaison.set),
        kill=MagicMock(), wait=AsyncMock(return_value=0),
    )
    monkeypatch.setattr(mcp, "get_mcp_service", lambda: service)
    monkeypatch.setattr(module, "validate_mcp_command", lambda *_: None)
    monkeypatch.setattr(module, "resolve_mcp_command", lambda *_: "python")
    monkeypatch.setattr(module.asyncio, "create_subprocess_exec", AsyncMock(return_value=processus))
    monkeypatch.setattr(service, "_initialize_server", initialiser)

    app = FastAPI()
    app.include_router(mcp.router, prefix="/api/mcp")
    route = f"/api/mcp/servers/{serveur.id}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        demarrage = asyncio.create_task(client.post(f"{route}/start"))
        try:
            await asyncio.wait_for(initialisation.wait(), timeout=2)
            arret = await client.post(f"{route}/stop")
            reponse = await asyncio.wait_for(demarrage, timeout=2)
            assert arret.status_code == 200, arret.text
            assert reponse.status_code == 200, reponse.text
            assert reponse.json()["status"] == "stopped"
            assert serveur.status == MCPServerStatus.STOPPED
            assert serveur.error is None
            assert not service._processes and not service._reader_tasks and not service._stderr_reader_tasks
            processus.terminate.assert_called_once()
        finally:
            terminaison.set()
            await asyncio.gather(demarrage, return_exceptions=True)
            await service.shutdown()


@pytest.mark.asyncio
@pytest.mark.parametrize("etape", ["création", "initialisation", "outils"])
@pytest.mark.parametrize("nombre_arrets", [1, 2])
@pytest.mark.parametrize("nombre_demarrages", [1, 2])
async def test_b2066_rejeux_d_arret_et_de_demarrage(
    tmp_path, monkeypatch, etape, nombre_arrets, nombre_demarrages,
):
    service = MCPService(config_path=tmp_path / "serveurs.json")
    serveur = MCPServer(id="test", name="Témoin", command="python")
    service.servers[serveur.id] = serveur
    atteint = asyncio.Event()
    poursuivre = asyncio.Event()
    processus = SimpleNamespace(
        pid=123, stdout=None, stderr=None, terminate=MagicMock(),
        kill=MagicMock(), wait=AsyncMock(return_value=0),
    )

    async def suspendre(phase):
        if phase == etape:
            atteint.set()
            await poursuivre.wait()

    async def creer(*_args, **_options):
        await suspendre("création")
        return processus

    creation = AsyncMock(side_effect=creer)
    monkeypatch.setattr(module, "validate_mcp_command", lambda *_: None)
    monkeypatch.setattr(module, "resolve_mcp_command", lambda *_: "python")
    monkeypatch.setattr(module.asyncio, "create_subprocess_exec", creation)

    async def initialiser(_identifiant):
        await suspendre("initialisation")

    async def lister(_identifiant):
        await suspendre("outils")

    monkeypatch.setattr(service, "_initialize_server", initialiser)
    monkeypatch.setattr(service, "_list_tools", lister)
    demarrages = [asyncio.create_task(service.start_server(serveur.id)) for _ in range(nombre_demarrages)]
    arrets = []
    try:
        await asyncio.wait_for(atteint.wait(), timeout=2)
        arrets = [asyncio.create_task(service.stop_server(serveur.id)) for _ in range(nombre_arrets)]
        # Laisse les demandes s'inscrire avant de libérer la création simulée.
        await asyncio.sleep(0)
        assert serveur.id in service._arrets_demandes
        poursuivre.set()
        assert await asyncio.wait_for(asyncio.gather(*arrets), timeout=2) == [True] * nombre_arrets
        assert await asyncio.wait_for(asyncio.gather(*demarrages), timeout=2) == [False] * nombre_demarrages
        assert serveur.status == MCPServerStatus.STOPPED and serveur.error is None
        assert not service._demarrages and not service._arrets_demandes
        assert not service._processes and not service._reader_tasks and not service._stderr_reader_tasks
        creation.assert_awaited_once()
        processus.terminate.assert_called_once()
    finally:
        poursuivre.set()
        await asyncio.gather(*demarrages, *arrets, return_exceptions=True)
        await service.shutdown()


@pytest.mark.asyncio
async def test_echec_initialisation_arrete_processus_et_lecteurs(tmp_path, monkeypatch):
    service = MCPService(config_path=tmp_path / "serveurs.json")
    serveur = MCPServer(id="test", name="Témoin", command="python")
    service.servers[serveur.id] = serveur
    attendre = asyncio.Event()

    async def lecture():
        await attendre.wait()
        return b""

    processus = SimpleNamespace(
        pid=123, stdout=SimpleNamespace(readline=lecture),
        stderr=SimpleNamespace(readline=lecture), terminate=MagicMock(),
        kill=MagicMock(), wait=AsyncMock(return_value=0),
    )
    monkeypatch.setattr(module, "validate_mcp_command", lambda *_: None)
    monkeypatch.setattr(module, "resolve_mcp_command", lambda *_: "python")
    monkeypatch.setattr(module.asyncio, "create_subprocess_exec", AsyncMock(return_value=processus))
    lecteurs = []

    async def initialisation_en_echec(identifiant):
        lecteurs.extend((service._reader_tasks[identifiant], service._stderr_reader_tasks[identifiant]))
        raise RuntimeError("échec témoin")

    monkeypatch.setattr(service, "_initialize_server", initialisation_en_echec)

    try:
        assert await service.start_server(serveur.id) is False
        assert serveur.status == MCPServerStatus.ERROR
        assert "échec témoin" in serveur.error
        processus.terminate.assert_called_once()
        assert serveur.id not in service._processes
        assert serveur.id not in service._reader_tasks
        assert serveur.id not in service._stderr_reader_tasks
        assert len(lecteurs) == 2 and all(lecteur.done() for lecteur in lecteurs)
    finally:
        if serveur.id in service._processes:
            await service.stop_server(serveur.id)


@pytest.mark.asyncio
async def test_annulation_initialisation_arrete_aussi_processus_et_lecteurs(tmp_path, monkeypatch):
    service = MCPService(config_path=tmp_path / "serveurs.json")
    serveur = MCPServer(id="test", name="Témoin", command="python")
    service.servers[serveur.id] = serveur
    attente = asyncio.Event()
    initialisation_demarree = asyncio.Event()
    lecteurs = []

    async def lecture():
        await attente.wait()
        return b""

    processus = SimpleNamespace(
        pid=123, stdout=SimpleNamespace(readline=lecture),
        stderr=SimpleNamespace(readline=lecture), terminate=MagicMock(),
        kill=MagicMock(), wait=AsyncMock(return_value=0),
    )

    async def initialisation_suspendue(identifiant):
        lecteurs.extend((service._reader_tasks[identifiant], service._stderr_reader_tasks[identifiant]))
        initialisation_demarree.set()
        await attente.wait()

    monkeypatch.setattr(module, "validate_mcp_command", lambda *_: None)
    monkeypatch.setattr(module, "resolve_mcp_command", lambda *_: "python")
    monkeypatch.setattr(module.asyncio, "create_subprocess_exec", AsyncMock(return_value=processus))
    monkeypatch.setattr(service, "_initialize_server", initialisation_suspendue)

    try:
        demarrage = asyncio.create_task(service.start_server(serveur.id))
        await initialisation_demarree.wait()
        demarrage.cancel()
        with pytest.raises(asyncio.CancelledError):
            await demarrage
        processus.terminate.assert_called_once()
        assert serveur.status == MCPServerStatus.ERROR
        assert serveur.id not in service._processes
        assert len(lecteurs) == 2 and all(lecteur.done() for lecteur in lecteurs)
    finally:
        if serveur.id in service._processes:
            await service.stop_server(serveur.id)


@pytest.mark.asyncio
@pytest.mark.parametrize("etape", ["write", "drain"])
async def test_pipe_ferme_nettoie_la_requete_avant_un_nouveau_demarrage(tmp_path, monkeypatch, etape):
    service = MCPService(config_path=tmp_path / "serveurs.json")
    serveur = MCPServer(id="test", name="Témoin", command="python")
    service.servers[serveur.id] = serveur
    premiere_entree = SimpleNamespace(write=MagicMock(), drain=AsyncMock())
    if etape == "write":
        premiere_entree.write.side_effect = BrokenPipeError("pipe fermé")
    else:
        premiere_entree.drain.side_effect = BrokenPipeError("pipe fermé")

    premiere_fin = asyncio.Event()
    premier = SimpleNamespace(
        pid=123, stdin=premiere_entree, stdout=None, stderr=None,
        terminate=MagicMock(side_effect=premiere_fin.set), kill=MagicMock(),
        wait=AsyncMock(side_effect=premiere_fin.wait),
    )
    seconde_fin = asyncio.Event()
    messages = []

    async def repondre():
        demande = json.loads(messages[-1])
        if "id" in demande:
            await service._handle_server_message(serveur.id, {"id": demande["id"], "result": {}})

    second = SimpleNamespace(
        pid=124, stdin=SimpleNamespace(write=lambda message: messages.append(message), drain=repondre),
        stdout=None, stderr=None, terminate=MagicMock(side_effect=seconde_fin.set),
        kill=MagicMock(), wait=AsyncMock(side_effect=seconde_fin.wait),
    )
    monkeypatch.setattr(module, "validate_mcp_command", lambda *_: None)
    monkeypatch.setattr(module, "resolve_mcp_command", lambda *_: "python")
    monkeypatch.setattr(module.asyncio, "create_subprocess_exec", AsyncMock(side_effect=[premier, second]))

    try:
        assert await service.start_server(serveur.id) is False
        assert serveur.status == MCPServerStatus.ERROR
        premier.terminate.assert_called_once()
        assert not service._processes
        assert not service._pending_requests
        assert not service._pending_timestamps
        assert not service._pending_deadlines

        assert await service.start_server(serveur.id) is True
        assert serveur.status == MCPServerStatus.RUNNING
        assert not service._pending_requests
        assert not service._pending_timestamps
        assert not service._pending_deadlines
    finally:
        if serveur.id in service._processes:
            await service.stop_server(serveur.id)
