"""US-002 : endpoint de confirmation d'une action sensible.

POST /api/chat/confirm-tool exécute (ou annule) une action send_email mise en
attente par la boucle d'outils, après validation explicite de l'utilisateur.
"""
import app.routers.chat as chat_mod
import pytest
from app.services.tool_confirmations import register_pending


@pytest.mark.asyncio
async def test_confirm_tool_execute_apres_validation(client, monkeypatch):
    captured: dict = {}

    async def _spy(tool_name, arguments, session):
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
