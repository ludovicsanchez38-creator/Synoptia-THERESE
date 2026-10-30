"""Reproductions API du cinquième tour : transport en mémoire exclusivement."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from app.models.database import get_sync_session
from app.models.entities import Message, Preference
from app.services.consentements import accord_valide, enregistrer_accord
from app.services.llm import LLMConfig, LLMProvider, LLMService
from app.services.providers.openai import OpenAIProvider
from sqlmodel import select

EXTRAIT = "TEMOIN_DOCUMENTAIRE_RELECTURE_QUATRE"


def texte_sse(texte):
    return (
        "data: "
        + json.dumps(
            {"choices": [{"index": 0, "delta": {"content": texte}, "finish_reason": None}]}
        )
        + "\n\n"
        + "data: "
        + json.dumps({"choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]})
        + "\n\n"
        + "data: [DONE]\n\n"
    )


def appel_sse():
    return (
        "data: "
        + json.dumps(
            {
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "tool_calls": [
                                {
                                    "index": 0,
                                    "id": "web-fictif",
                                    "type": "function",
                                    "function": {
                                        "name": "web_search",
                                        "arguments": json.dumps(
                                            {"query": "source publique exemple"}
                                        ),
                                    },
                                }
                            ]
                        },
                        "finish_reason": None,
                    }
                ]
            }
        )
        + "\n\n"
        + "data: "
        + json.dumps({"choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls"}]})
        + "\n\n"
        + "data: [DONE]\n\n"
    )


@pytest.mark.parametrize("initial", ["openai", "mistral"])
@pytest.mark.parametrize("destination", ["openai", "mistral"])
@pytest.mark.parametrize("retrait", [False, True])
async def test_confirmation_filtre_documents_apres_retrait(
    client, monkeypatch, initial, destination, retrait
):
    from app.routers import chat

    for purpose in ("llm", "documents"):
        enregistrer_accord(purpose, initial, True, "3", [])
    with get_sync_session() as s:
        s.merge(Preference(key="auto_extract_entities", value="false"))
        s.commit()
    envois = []

    async def transport(req):
        envois.append(
            {
                "body": req.content.decode(),
                "accord_documents": accord_valide("documents", svc.config.provider.value),
            }
        )
        texte = (
            appel_sse()
            if len(envois) == 2
            else texte_sse(EXTRAIT if len(envois) == 1 else "Réponse rédigée")
        )
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=texte)

    http = httpx.AsyncClient(transport=httpx.MockTransport(transport))
    from app.services.providers.mistral import MistralProvider

    adaptateurs = {"openai": OpenAIProvider, "mistral": MistralProvider}
    svc = LLMService(
        LLMConfig(
            LLMProvider(initial),
            "gpt-4o" if initial == "openai" else "mistral-large-latest",
            api_key="factice",
        )
    )
    svc._provider = adaptateurs[initial](svc.config, http)
    monkeypatch.setattr(chat, "get_llm_service", lambda: svc)
    monkeypatch.setattr(
        chat,
        "get_qdrant_service",
        lambda: SimpleNamespace(
            async_search=AsyncMock(
                return_value=[
                    {
                        "type": "file",
                        "text": EXTRAIT,
                        "metadata": {"name": "temoin.txt"},
                        "score": 0.99,
                    }
                ]
            )
        ),
    )
    monkeypatch.setattr(
        chat, "get_mcp_service", lambda: SimpleNamespace(get_tools_for_llm=lambda: [])
    )
    recherche = AsyncMock(return_value="Source publique fictive")
    monkeypatch.setattr(chat, "execute_web_search", recherche)
    premier = await client.post(
        "/api/chat/send",
        json={
            "message": "Cite le fichier",
            "include_memory": True,
            "stream": True,
            "disable_tools": True,
        },
    )
    assert premier.status_code == 200 and EXTRAIT in premier.text
    with get_sync_session() as s:
        msg = s.exec(select(Message).where(Message.role == "assistant")).all()[-1]
        conv = msg.conversation_id
        assert json.loads(msg.extra_data)["provenance_documents"] == "documents"
    second = await client.post(
        "/api/chat/send",
        json={
            "message": "Cherche une source publique",
            "conversation_id": conv,
            "include_memory": False,
            "stream": True,
        },
    )
    events = [json.loads(x[6:]) for x in second.text.splitlines() if x.startswith("data: ")]
    carte = next(x["confirmation"] for x in events if x["type"] == "confirmation_required")
    assert EXTRAIT in str(carte["arguments"]["_web_messages"])
    assert any(m.get("contient_documents") is True for m in carte["arguments"]["_web_messages"])
    if retrait:
        enregistrer_accord("documents", initial, False, "3", [])
    if destination != initial:
        enregistrer_accord("llm", destination, True, "3", [])
        if not retrait:
            enregistrer_accord("documents", destination, True, "3", [])
        svc = LLMService(
            LLMConfig(
                LLMProvider(destination),
                "gpt-4o" if destination == "openai" else "mistral-large-latest",
                api_key="factice",
            )
        )
        svc._provider = adaptateurs[destination](svc.config, http)
    avant = len(envois)
    dernier = await client.post(
        "/api/chat/confirm-tool",
        json={"confirmation_id": carte["confirmation_id"], "approved": True},
    )
    assert dernier.status_code == 200
    if retrait:
        recherche.assert_not_called()
        assert len(envois) == avant
        assert "documents" in dernier.text and "accord" in dernier.text
        assert not accord_valide("documents", destination)
        assert EXTRAIT not in dernier.text
    else:
        recherche.assert_called_once()
        assert len(envois) == avant + 1
        assert EXTRAIT in envois[-1]["body"]
        with get_sync_session() as session:
            dernier_message = session.exec(
                select(Message).where(Message.role == "assistant")
            ).all()[-1]
            assert json.loads(dernier_message.extra_data)["provenance_documents"] == "documents"
    await http.aclose()
