"""Références RFC incertaines, anciennes copies et retrait au transport."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from app.models.database import get_sync_session
from app.models.entities import Conversation, Message
from app.services.consentements import enregistrer_accord
from app.services.llm import LLMConfig, LLMProvider, LLMService
from app.services.providers.mistral import MistralProvider
from app.services.providers.openai import OpenAIProvider


def source_rfc():
    with get_sync_session() as s:
        conv = Conversation(title="RFC fictif")
        s.add(conv)
        s.flush()
        msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content="REFERENCE_AMBRE",
            extra_data=json.dumps({"provenance_documents": "documents"}),
        )
        s.add(msg)
        s.commit()
        return msg.id


@pytest.mark.parametrize("destination", ["openai", "mistral"])
@pytest.mark.parametrize(
    "copies",
    [
        dict(brief="REFERENCE_AMBRE"),
        dict(brief="Génère", context=[{"role": "assistant", "content": "REFERENCE_AMBRE"}]),
    ],
)
async def test_copies_anciennes_brief_ou_context_sans_reference(
    client, monkeypatch, destination, copies
):
    from app.services import llm

    enregistrer_accord("llm", destination, True, "3", [])
    svc = LLMService(LLMConfig(LLMProvider(destination), "fictif", api_key="factice"))
    monkeypatch.setattr(llm, "get_llm_service", lambda: svc)
    transport = AsyncMock()
    svc._provider = SimpleNamespace(stream=transport)
    response = await client.post("/api/v3/commands/generate-template", json=copies)
    assert "documents" in response.text and "accord" in response.text
    transport.assert_not_called()


@pytest.mark.parametrize("etape", ["faire", "capturer"])
@pytest.mark.parametrize("destination", ["openai", "mistral"])
async def test_retrait_tardif_rfc_avant_transport(client, monkeypatch, destination, etape):
    from app.routers import chat
    from app.services import llm

    for purpose in ("llm", "documents"):
        enregistrer_accord(purpose, destination, True, "3", [])
    envois = []

    async def transport(req):
        envois.append(req.content)
        return httpx.Response(500)

    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as http:
        svc = LLMService(LLMConfig(LLMProvider(destination), "fictif", api_key="factice"))
        svc._provider = (OpenAIProvider if destination == "openai" else MistralProvider)(
            svc.config, http
        )

        async def retirer():
            enregistrer_accord("documents", destination, False, "3", [])

        monkeypatch.setattr(svc, "_ensure_provider", retirer)
        monkeypatch.setattr(llm, "get_llm_service", lambda: svc)
        monkeypatch.setattr(chat, "get_llm_service", lambda: svc)
        ids = [source_rfc()]
        path = "/api/chat/send" if etape == "faire" else "/api/v3/commands/generate-template"
        payload = (
            {"message": "Génère une ébauche", "include_memory": False, "disable_tools": True}
            if etape == "faire"
            else {"brief": "Génère"}
        )
        response = await client.post(path, json=payload | {"rfc_source_ids": ids})
        assert not envois
        assert "documents" in response.text and "accord" in response.text


@pytest.mark.parametrize("ids", [[], ["introuvable"]])
async def test_capture_source_inconnue_refusee(client, ids):
    response = await client.post(
        "/api/v3/commands/generate-template", json={"brief": "Fictif", "rfc_source_ids": ids}
    )
    assert response.status_code == 409
    assert "Renvoie ton message" in response.text


@pytest.mark.parametrize("modifier", [False, True])
async def test_commande_persistante_ne_perd_pas_origine(client, monkeypatch, modifier):
    from app.routers import commands_v3

    registre = SimpleNamespace(create_user_command=AsyncMock(), update_user_command=AsyncMock())
    monkeypatch.setattr(commands_v3, "get_command_registry", lambda: registre)
    methode, path = (
        (client.put, "/api/v3/commands/user/user-fictive")
        if modifier
        else (client.post, "/api/v3/commands/user")
    )
    response = await methode(
        path,
        json={
            "name": "fictive",
            "prompt_template": "REFERENCE_AMBRE",
            "rfc_source_ids": [source_rfc()],
        },
    )
    assert response.status_code == 409
    assert "document" in response.text
    registre.create_user_command.assert_not_called()
    registre.update_user_command.assert_not_called()
