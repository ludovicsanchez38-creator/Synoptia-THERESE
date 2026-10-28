"""US-002 : endpoint de confirmation d'une action sensible.

POST /api/chat/confirm-tool exécute (ou annule) une action send_email mise en
attente par la boucle d'outils, après validation explicite de l'utilisateur.
"""
from unittest.mock import MagicMock

import app.routers.chat as chat_mod
import pytest
from app.services.context import ContextWindow
from app.services.llm import StreamEvent
from app.services.tool_confirmations import register_pending


@pytest.mark.asyncio
async def test_confirm_tool_execute_apres_validation(client, monkeypatch):
    captured: dict = {}

    async def _spy(tool_name, arguments, session, conversation_id=None):
        captured["tool"] = tool_name
        captured["args"] = arguments
        return "Email envoyé à x@y.fr"

    monkeypatch.setattr(chat_mod, "execute_workspace_tool", _spy)

    cid = register_pending("send_email", {"to": "x@y.fr", "subject": "S", "body": "B"})
    resp = await client.post(
        "/api/chat/confirm-tool", json={"confirmation_id": cid, "approved": True}
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "executed"
    assert "envoyé" in data["result"].lower()
    assert captured["tool"] == "send_email"


@pytest.mark.asyncio
async def test_confirm_tool_annulation_n_execute_pas(client, monkeypatch):
    called = {"executed": False}

    async def _spy(*args, **kwargs):
        called["executed"] = True
        return "?"

    monkeypatch.setattr(chat_mod, "execute_workspace_tool", _spy)

    cid = register_pending("send_email", {"to": "x@y.fr"})
    resp = await client.post(
        "/api/chat/confirm-tool", json={"confirmation_id": cid, "approved": False}
    )

    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"
    assert called["executed"] is False


@pytest.mark.asyncio
async def test_confirm_tool_id_inconnu_renvoie_404(client):
    resp = await client.post(
        "/api/chat/confirm-tool", json={"confirmation_id": "inconnu", "approved": True}
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_confirm_tool_route_send_email_mcp_vers_le_service_mcp(client, monkeypatch):
    """BUG-121 : à la confirmation, un send_email MCP ('{server_id}__send_email')
    doit être exécuté via le service MCP, pas via execute_workspace_tool."""

    class _Result:
        success = True
        result = "Email MCP envoyé à x@y.fr"
        error = None

    captured: dict = {}

    class _FakeMCP:
        async def execute_tool_call(self, name, arguments):
            captured["name"] = name
            captured["args"] = arguments
            return _Result()

    async def _fail_workspace(*args, **kwargs):
        raise AssertionError("execute_workspace_tool ne doit pas être appelé pour un outil MCP")

    monkeypatch.setattr(chat_mod, "get_mcp_service", lambda: _FakeMCP())
    monkeypatch.setattr(chat_mod, "execute_workspace_tool", _fail_workspace)

    cid = register_pending("therese__send_email", {"to": "x@y.fr", "subject": "S", "body": "B"})
    resp = await client.post(
        "/api/chat/confirm-tool", json={"confirmation_id": cid, "approved": True}
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "executed"
    assert "envoyé" in data["result"].lower()
    assert captured["name"] == "therese__send_email"


@pytest.mark.asyncio
async def test_confirm_tool_route_web_search_vers_le_moteur(client, monkeypatch):
    """Sans ce routage, la carte de web_search appellerait execute_workspace_tool
    et rendrait « Outil inconnu » : l'utilisateur confirme, rien ne part."""
    captured: dict = {}

    async def _spy(arguments):
        captured["args"] = arguments
        return "3 résultats"

    async def _fail_workspace(*args, **kwargs):
        raise AssertionError("web_search n'est pas un outil workspace")

    class Modele:
        config = None

        def prepare_context(self, messages):
            return ContextWindow(messages=messages)

        async def continue_with_tool_results(self, context, **kwargs):
            captured["context"] = context
            captured["suite"] = kwargs
            yield StreamEvent(type="text", content="Voici les horaires de Marseille issus de la recherche.")
            yield StreamEvent(type="done", input_tokens=40, output_tokens=20)

    monkeypatch.setattr(chat_mod, "execute_web_search", _spy)
    monkeypatch.setattr(chat_mod, "execute_workspace_tool", _fail_workspace)
    monkeypatch.setattr(chat_mod, "get_llm_service", lambda: Modele())
    monkeypatch.setattr(chat_mod, "_attribution", lambda _: ("test", "test"))
    tracker = MagicMock()
    monkeypatch.setattr(chat_mod, "get_token_tracker", lambda: tracker)

    cid = register_pending("web_search", {"query": "horaire marseille"})
    resp = await client.post(
        "/api/chat/confirm-tool", json={"confirmation_id": cid, "approved": True}
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "executed"
    assert captured["args"] == {"query": "horaire marseille"}
    assert data["result"] == "Voici les horaires de Marseille issus de la recherche."
    assert captured["context"].messages[-1].content == "horaire marseille"
    assert captured["suite"]["tool_results"][0].result == "3 résultats"
    assert captured["suite"]["tool_calls"][0].name == "web_search"
    assert captured["suite"]["tools"] is None
    tracker.record_usage.assert_called_once()


@pytest.mark.asyncio
async def test_confirm_tool_route_create_contact_vers_la_memoire(client, monkeypatch):
    captured: dict = {}

    async def _spy(tool_name, arguments, session, **kwargs):
        captured["tool"] = tool_name
        captured["args"] = arguments
        return '{"id": "c1", "name": "Martin"}'

    async def _fail_workspace(*args, **kwargs):
        raise AssertionError("create_contact n'est pas un outil workspace")

    monkeypatch.setattr(chat_mod, "execute_memory_tool", _spy)
    monkeypatch.setattr(chat_mod, "execute_workspace_tool", _fail_workspace)

    cid = register_pending("create_contact", {"first_name": "Martin"})
    resp = await client.post(
        "/api/chat/confirm-tool", json={"confirmation_id": cid, "approved": True}
    )

    assert resp.status_code == 200
    assert resp.json()["status"] == "executed"
    assert captured["tool"] == "create_contact"
