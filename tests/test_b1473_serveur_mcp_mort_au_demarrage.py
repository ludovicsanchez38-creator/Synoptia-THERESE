"""B-1473 (recette P-146, lot 5) : préréglages Time et Fetch.

1. Ils visaient `@modelcontextprotocol/server-fetch` et `server-time`, deux
   paquets npm qui n'existent pas (404 vérifié le 25/09/2026 par `npm view`).
   Les serveurs officiels sont en Python : `uvx mcp-server-fetch` et
   `uvx mcp-server-time` (README du dépôt modelcontextprotocol/servers,
   PyPI 2026.8.18).
2. Un serveur mort au démarrage laissait la requête `initialize` attendre
   ses 90 s, puis l'écran disait « Request timeout » sans la cause (npm 404).
"""

import asyncio
import sys
import time

import pytest
from app.services.mcp_service import MCPService
from httpx import AsyncClient

_MORT_AU_DEMARRAGE = (
    "import sys; "
    "sys.stderr.write('npm error 404 Not Found - GET https://registry.npmjs.org/paquet-absent\\n'); "
    "sys.exit(1)"
)


@pytest.mark.asyncio
async def test_un_serveur_mort_au_demarrage_echoue_vite_avec_sa_cause(tmp_path, monkeypatch):
    # La liste blanche des commandes n'est pas le sujet : le processus témoin est python.
    monkeypatch.setattr("app.services.mcp_service.validate_mcp_command", lambda *a, **k: None)
    service = MCPService(config_path=tmp_path / "mcp_servers.json")
    serveur = service.add_server(name="Témoin", command=sys.executable, args=["-c", _MORT_AU_DEMARRAGE])
    try:
        debut = time.monotonic()
        demarre = await asyncio.wait_for(service.start_server(serveur.id), timeout=30)
        duree = time.monotonic() - debut
        assert demarre is False
        assert duree < 10, f"échec dit en {duree:.0f} s"
        assert "404" in (service.servers[serveur.id].error or "")
    finally:
        await service.shutdown()


@pytest.mark.asyncio
async def test_fetch_et_time_visent_les_serveurs_officiels(client: AsyncClient):
    presets = {p["id"]: p for p in (await client.get("/api/mcp/presets")).json()}
    assert (presets["fetch"]["command"], presets["fetch"]["args"]) == ("uvx", ["mcp-server-fetch"])
    assert (presets["time"]["command"], presets["time"]["args"]) == ("uvx", ["mcp-server-time"])


@pytest.mark.asyncio
async def test_sans_uvx_l_installation_dit_quoi_installer(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda *a, **k: None)
    monkeypatch.setattr("app.services.mcp_service.resolve_mcp_command", lambda *a, **k: None)
    reponse = await client.post("/api/mcp/presets/time/install", json={})
    assert reponse.status_code == 422
    corps = reponse.json()
    detail = corps.get("detail") or corps.get("message") or str(corps)
    assert "uvx" in detail
    assert "https://docs.astral.sh/uv/" in detail
    assert "système" in detail
