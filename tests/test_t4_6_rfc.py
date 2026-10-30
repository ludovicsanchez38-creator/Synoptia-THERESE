"""Régression du tour 6, adaptée de la reproduction contradictoire du tour 5."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from app.models.database import get_sync_session
from app.models.entities import Message, Preference
from app.services.consentements import accord_valide, enregistrer_accord
from app.services.llm import LLMConfig, LLMProvider, LLMService
from app.services.providers.mistral import MistralProvider
from app.services.providers.openai import OpenAIProvider
from sqlmodel import select

from tests.test_t4_5_chemins_differes import texte_sse

EXTRAIT = "REFERENCE_CONTRAT_AMBRE"


@pytest.mark.parametrize("etape", ["faire", "capturer"])
@pytest.mark.parametrize("destination", ["openai", "mistral"])
@pytest.mark.parametrize("retrait", [False, True])
async def test_rfc_copie_document_apres_retrait(client, monkeypatch, destination, retrait, etape):
    from app.routers import chat
    from app.services import llm

    enregistrer_accord("llm", "openai", True, "3", [])
    enregistrer_accord("documents", "openai", True, "3", [])
    with get_sync_session() as s:
        s.merge(Preference(key="auto_extract_entities", value="false"))
        s.commit()
    envois = []

    async def transport(req):
        envois.append(
            {
                "body": req.content.decode(),
                "destination": svc.config.provider.value,
                "accord_documents": accord_valide("documents", svc.config.provider.value),
            }
        )
        texte = (
            f"Commande proposée à partir du contrat : {EXTRAIT}."
            if len(envois) == 1
            else json.dumps({"name": "devis", "prompt_template": "Prépare un devis."})
        )
        return httpx.Response(
            200, headers={"content-type": "text/event-stream"}, text=texte_sse(texte)
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as http:
        svc = LLMService(LLMConfig(LLMProvider.OPENAI, "gpt-4o", api_key="factice"))
        svc._provider = OpenAIProvider(svc.config, http)
        monkeypatch.setattr(chat, "get_llm_service", lambda: svc)
        monkeypatch.setattr(llm, "get_llm_service", lambda: svc)
        monkeypatch.setattr(
            chat,
            "get_qdrant_service",
            lambda: SimpleNamespace(
                async_search=AsyncMock(
                    return_value=[
                        {
                            "type": "file",
                            "text": EXTRAIT,
                            "metadata": {"name": "contrat.txt"},
                            "score": 0.99,
                        }
                    ]
                )
            ),
        )
        # Même payload que RFCChat : mémoire laissée à sa valeur par défaut,
        # outils désactivés et pas de reprise d'une conversation existante.
        question = "Propose une commande de devis en utilisant le contrat."
        premier = await client.post(
            "/api/chat/send", json={"message": question, "stream": True, "disable_tools": True}
        )
        assert premier.status_code == 200
        events = [
            json.loads(line[6:]) for line in premier.text.splitlines() if line.startswith("data: ")
        ]
        reponse = "".join(e.get("content", "") for e in events if e.get("type") == "text")
        assert EXTRAIT in reponse and EXTRAIT in envois[0]["body"]
        with get_sync_session() as s:
            msg = s.exec(select(Message).where(Message.role == "assistant")).all()[-1]
            assert json.loads(msg.extra_data)["provenance_documents"] == "documents"
        if retrait:
            enregistrer_accord("documents", "openai", False, "3", [])
        if destination != "openai":
            enregistrer_accord("llm", destination, True, "3", [])
            if not retrait:
                enregistrer_accord("documents", destination, True, "3", [])
            svc = LLMService(
                LLMConfig(LLMProvider.MISTRAL, "mistral-large-latest", api_key="factice")
            )
            svc._provider = MistralProvider(svc.config, http)
        # Copie exactement préparée par RFCWizard.goToCapture.
        messages = [
            {"role": "user", "content": question},
            {"role": "assistant", "content": reponse},
        ]
        if etape == "capturer":
            capture = await client.post(
                "/api/v3/commands/generate-template",
                json={
                    "brief": "\n".join(f"{m['role']}: {m['content']}" for m in messages),
                    "context": messages,
                    "rfc_source_ids": [msg.id],
                },
            )
        else:
            reprise = (
                "Voici le résumé de notre réflexion :\n\n"
                + "\n\n".join(
                    f"{('Moi' if m['role'] == 'user' else 'THÉRÈSE')}: {m['content']}"
                    for m in messages
                )
                + "\n\nMaintenant, génère-moi une ébauche de prompt template avec des {{placeholders}}."
            )
            capture = await client.post(
                "/api/chat/send",
                json={
                    "message": reprise,
                    "stream": True,
                    "disable_tools": True,
                    "rfc_source_ids": [msg.id],
                },
            )
        if retrait:
            assert len(envois) == 1, capture.text
            assert "accord" in capture.text.lower() or "documents" in capture.text.lower()
        else:
            assert capture.status_code == 200, capture.text
            assert len(envois) == 2
            assert EXTRAIT in envois[-1]["body"]
