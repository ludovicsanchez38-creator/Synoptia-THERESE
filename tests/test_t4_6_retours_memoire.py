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
async def test_refus_doublon_ne_retransmet_pas_titre(client, monkeypatch, retrait, destination):
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
        if len(envois) in (1, 3):
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
                                                "kind": "fait",
                                                "subject": "theme-isole",
                                                "title": f"Devis pour {EXTRAIT}"
                                                if len(envois) == 1
                                                else "Phrases simples",
                                                "content": "Je préfère des devis courts"
                                                if len(envois) == 1
                                                else "Je veux des phrases simples",
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
                "message": "Retiens : je veux des phrases simples.",
                "include_memory": True,
                "stream": True,
                "disable_tools": False,
            },
        )
        assert second.status_code == 200
        nouveaux = envois[avant:]
        assert nouveaux, second.text
        assert EXTRAIT not in nouveaux[0]["body"]
        assert "Une fiche correspond" in second.text, second.text
        if retrait:
            assert all(EXTRAIT not in e["body"] for e in nouveaux), second.text
        else:
            assert len(nouveaux) == 2


@pytest.mark.parametrize("origine", ["documents", "inconnue", "sans_document"])
@pytest.mark.parametrize("mode", ["correction", "negation"])
async def test_refus_ne_copie_pas_ancienne_fiche(db_session, origine, mode):
    from app.models.entities import Conversation, Message
    from app.services import memory_card_tools, memory_cards

    conversation = Conversation(title="Fictif")
    db_session.add(conversation)
    await db_session.flush()
    source = Message(
        conversation_id=conversation.id,
        role="user",
        content="Je préfère des devis courts",
        extra_data=json.dumps({"provenance_documents": "sans_document"}),
    )
    ancienne = MemoryCard(
        kind="fait",
        subject="theme-isole",
        title=EXTRAIT,
        content="Je ne contacte jamais Ambre.",
        provenance_documents=origine,
    )
    ancienne.dedup_key = memory_cards._cle(ancienne)
    db_session.add_all([source, ancienne])
    await db_session.commit()
    arguments = {
        "kind": "correction",
        "subject": "theme-isole",
        "title": "Devis courts",
        "content": source.content,
    }
    if mode == "negation":
        arguments.update(
            id=ancienne.id, version=ancienne.version, content=source.content + " immédiatement"
        )
    resultat = await memory_card_tools.executer_outil(
        arguments,
        scope="global",
        scope_id=None,
        conversation_id=conversation.id,
        contient_documents=False,
    )
    assert resultat["success"] is False
    if mode == "correction":
        assert "fiche existante" in resultat["message"]
        assert ancienne.id in resultat["detail"]
        assert "ambre" not in json.dumps(resultat).lower()
    else:
        assert "uniquement" in resultat["message"]
        if origine == "sans_document":
            assert "ambre" in resultat["detail"].lower()
        else:
            assert "detail" not in resultat
