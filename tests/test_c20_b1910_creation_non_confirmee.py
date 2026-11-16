"""La bulle ne doit pas annoncer une création sans succès explicite."""

import json
from unittest.mock import AsyncMock

import pytest
from app.services.tool_confirmations import register_pending


@pytest.mark.asyncio
@pytest.mark.parametrize("nom", ["create_contact", "create_project", "create_task", "create_invoice"])
@pytest.mark.parametrize("donnees", [{}, {"id": "fictif"}, {"success": None}, {"success": 1}, []])
async def test_confirmation_ne_pretend_pas_creer_sans_succes(client, monkeypatch, nom, donnees):
    from app.routers import chat

    brut = json.dumps(donnees)
    monkeypatch.setattr(chat, "execute_memory_tool", AsyncMock(return_value=brut))
    monkeypatch.setattr(chat, "execute_workspace_tool", AsyncMock(return_value=brut))
    identifiant = register_pending(nom, {"_provenance_documents": "sans_document"})
    reponse = await client.post("/api/chat/confirm-tool", json={
        "confirmation_id": identifiant, "approved": True,
    })
    assert reponse.status_code == 200
    texte = reponse.json()["result"].lower()
    assert "créé" not in texte and "créée" not in texte
    assert "confirm" in texte


@pytest.mark.asyncio
async def test_message_de_succes_contredit_par_le_json_n_est_pas_annonce(client, monkeypatch):
    from app.routers import chat

    brut = json.dumps({"success": False, "message": "Contact créé."})
    monkeypatch.setattr(chat, "execute_memory_tool", AsyncMock(return_value=brut))
    identifiant = register_pending("create_contact", {"_provenance_documents": "sans_document"})
    reponse = await client.post("/api/chat/confirm-tool", json={
        "confirmation_id": identifiant, "approved": True,
    })
    assert reponse.status_code == 200
    assert "Contact créé" not in reponse.json()["result"]


@pytest.mark.asyncio
async def test_contact_existant_n_est_pas_presente_comme_une_creation(client, monkeypatch):
    from app.routers import chat

    brut = json.dumps({"success": True, "already_existed": True})
    monkeypatch.setattr(chat, "execute_memory_tool", AsyncMock(return_value=brut))
    identifiant = register_pending("create_contact", {"_provenance_documents": "sans_document"})
    reponse = await client.post("/api/chat/confirm-tool", json={
        "confirmation_id": identifiant, "approved": True,
    })
    assert "existe déjà" in reponse.json()["result"]
    assert "Contact créé" not in reponse.json()["result"]


@pytest.mark.asyncio
async def test_contact_existant_signale_les_champs_non_enregistres(client, monkeypatch):
    from app.routers import chat

    brut = json.dumps({"success": False, "already_existed": True, "champs_ignores": ["notes"]})
    monkeypatch.setattr(chat, "execute_memory_tool", AsyncMock(return_value=brut))
    identifiant = register_pending("create_contact", {"_provenance_documents": "sans_document"})
    reponse = await client.post("/api/chat/confirm-tool", json={
        "confirmation_id": identifiant, "approved": True,
    })
    assert "notes" in reponse.json()["result"]
    assert "pas été enregistrées" in reponse.json()["result"]
