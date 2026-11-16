"""B-1826 : le chemin propre d'un serveur ne choisit pas son exécutable."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services import encryption
from app.services import mcp_service as module
from app.services.mcp_service import MCPServer, MCPService


@pytest.mark.asyncio
@pytest.mark.parametrize("chiffre", [False, True])
async def test_le_serveur_ne_remplace_pas_le_chemin_de_resolution(tmp_path, monkeypatch, chiffre):
    fiable = tmp_path / "fiable"
    fourni = tmp_path / "fourni"
    fiable.mkdir()
    fourni.mkdir()
    for dossier in (fiable, fourni):
        executable = dossier / "python3"
        executable.write_text("témoin", encoding="utf-8")
        executable.chmod(0o755)

    service = MCPService(config_path=tmp_path / "serveurs.json")
    valeur = "chiffre-temoin" if chiffre else str(fourni)
    serveur = MCPServer(id="test", name="Témoin", command="python3", env={"PATH": valeur})
    service.servers[serveur.id] = serveur
    monkeypatch.setattr(module, "build_mcp_enriched_path", lambda: str(fiable))
    monkeypatch.setattr(encryption, "is_value_encrypted", lambda _valeur: chiffre)
    monkeypatch.setattr(encryption, "decrypt_value", lambda _valeur: str(fourni))
    processus = SimpleNamespace(
        pid=123, stdout=None, stderr=None, terminate=MagicMock(),
        kill=MagicMock(), wait=AsyncMock(return_value=0),
    )
    lancement = AsyncMock(return_value=processus)
    monkeypatch.setattr(module.asyncio, "create_subprocess_exec", lancement)
    monkeypatch.setattr(service, "_initialize_server", AsyncMock())
    monkeypatch.setattr(service, "_list_tools", AsyncMock())

    try:
        assert await service.start_server(serveur.id) is True
        assert lancement.call_args.args[0] == str(fiable / "python3")
    finally:
        if serveur.id in service._processes:
            await service.stop_server(serveur.id)


@pytest.mark.asyncio
async def test_commande_absente_du_chemin_de_l_application_n_est_pas_lancee(tmp_path, monkeypatch):
    fiable = tmp_path / "fiable"
    fourni = tmp_path / "fourni"
    fiable.mkdir()
    fourni.mkdir()
    executable = fourni / "python3"
    executable.write_text("témoin", encoding="utf-8")
    executable.chmod(0o755)

    service = MCPService(config_path=tmp_path / "serveurs.json")
    serveur = MCPServer(id="test", name="Témoin", command="python3", env={"PATH": str(fourni)})
    service.servers[serveur.id] = serveur
    monkeypatch.setattr(module, "build_mcp_enriched_path", lambda: str(fiable))
    monkeypatch.setattr(encryption, "is_value_encrypted", lambda _valeur: False)
    lancement = AsyncMock(side_effect=AssertionError("La commande ne doit pas être lancée"))
    monkeypatch.setattr(module.asyncio, "create_subprocess_exec", lancement)

    assert await service.start_server(serveur.id) is False
    lancement.assert_not_awaited()
    assert "Commande introuvable" in serveur.error
