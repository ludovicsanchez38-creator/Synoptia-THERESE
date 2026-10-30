"""Régression du tour 6, adaptée de la reproduction contradictoire du tour 5."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from app.models.database import get_sync_session
from app.models.entities import MemoryCard, Preference
from app.services.consentements import accord_valide, enregistrer_accord
from app.services.llm import LLMConfig, LLMProvider, LLMService
from app.services.providers.mistral import MistralProvider
from app.services.providers.openai import OpenAIProvider
from sqlmodel import select

from tests.test_t4_5_chemins_differes import texte_sse

EXTRAIT = "Maison Ambre"


@pytest.mark.parametrize("destination", ["openai", "mistral"])
@pytest.mark.parametrize("retrait", [False, True])
@pytest.mark.parametrize("memoire", [False, True])
@pytest.mark.parametrize("flux", [False, True])
async def test_fiche_issue_document(client, monkeypatch, retrait, memoire, flux, destination):
    from app.routers import chat

    enregistrer_accord("llm", "openai", True, "3", ["memory_cards_r2_v1"])
    enregistrer_accord("documents", "openai", True, "3", ["memory_cards_r2_v1"])
    with get_sync_session() as s:
        s.merge(Preference(key="auto_extract_entities", value="false"))
        s.commit()
    envois = []

    async def transport(req):
        envois.append(
            {"body": req.content.decode(), "accord_documents": accord_valide("documents", "openai")}
        )
        if len(envois) == 1:
            data = {
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "tool_calls": [
                                {
                                    "index": 0,
                                    "id": "memoire-fictive",
                                    "type": "function",
                                    "function": {
                                        "name": "upsert_memory_card",
                                        "arguments": json.dumps(
                                            {
                                                "kind": "preference",
                                                "subject": "devis",
                                                "title": f"Devis pour {EXTRAIT}",
                                                "content": "Je préfère des devis courts",
                                            }
                                        ),
                                    },
                                }
                            ]
                        },
                        "finish_reason": None,
                    }
                ]
            }
            fin = {"choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls"}]}
            texte = (
                "data: "
                + json.dumps(data)
                + "\n\n"
                + "data: "
                + json.dumps(fin)
                + "\n\ndata: [DONE]\n\n"
            )
        else:
            texte = texte_sse("Réponse au message")
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=texte)

    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as http:
        svc = LLMService(LLMConfig(LLMProvider.OPENAI, "gpt-4o", api_key="factice"))
        svc._provider = OpenAIProvider(svc.config, http)
        monkeypatch.setattr(chat, "get_llm_service", lambda: svc)
        recherche = AsyncMock(
            return_value=[
                {
                    "type": "file",
                    "text": f"Client du contrat : {EXTRAIT}",
                    "metadata": {"name": "contrat.txt"},
                    "score": 0.99,
                }
            ]
        )
        monkeypatch.setattr(
            chat, "get_qdrant_service", lambda: SimpleNamespace(async_search=recherche)
        )
        monkeypatch.setattr(
            chat, "get_mcp_service", lambda: SimpleNamespace(get_tools_for_llm=lambda: [])
        )
        premier = await client.post(
            "/api/chat/send",
            json={
                "message": "Consulte le contrat et retiens ma préférence : je préfère des devis courts.",
                "include_memory": True,
                "stream": True,
            },
        )
        assert premier.status_code == 200
        with get_sync_session() as s:
            cartes = s.exec(select(MemoryCard)).all()
            assert len(cartes) == 1, premier.text
            assert EXTRAIT in cartes[0].title
            conv = cartes[0].conversation_id
        assert EXTRAIT in envois[0]["body"]
        if retrait:
            enregistrer_accord("documents", "openai", False, "3", [])
        if destination == "mistral":
            enregistrer_accord("llm", "mistral", True, "3", ["memory_cards_r2_v1"])
            enregistrer_accord("documents", "mistral", not retrait, "3", ["memory_cards_r2_v1"])
            svc = LLMService(
                LLMConfig(LLMProvider.MISTRAL, "mistral-large-latest", api_key="factice")
            )
            svc._provider = MistralProvider(svc.config, http)
        recherche.return_value = []
        avant = len(envois)
        second = await client.post(
            "/api/chat/send",
            json={
                "message": "Bonjour, préparons un devis.",
                "conversation_id": conv,
                "include_memory": memoire,
                "stream": flux,
                "disable_tools": True,
            },
        )
        assert second.status_code == 200
        if memoire and retrait:
            assert len(envois) == avant, second.text
            assert "documents" in second.text and "accord" in second.text
        else:
            assert len(envois) == avant + 1, second.text
            assert (EXTRAIT in envois[-1]["body"]) == memoire
