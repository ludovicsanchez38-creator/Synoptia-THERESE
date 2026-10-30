"""Copies différées : provenance manquante, transport et extraction."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.services.consentements import enregistrer_accord, verifier_envoi_llm
from app.services.context import ContextWindow
from app.services.error_handler import ErreurPourEcran
from app.services.llm import LLMConfig, LLMProvider, LLMService
from app.services.providers.base import Message, StreamEvent


def test_carte_possede_sa_copie_de_provenance():
    from app.services.tool_confirmations import pop_pending, register_pending

    arguments = {
        "_web_messages": [{"role": "assistant", "content": "EXTRAIT", "contient_documents": True}]
    }
    carte = register_pending("web_search", arguments)
    arguments["_web_messages"][0]["contient_documents"] = False
    assert pop_pending(carte)[1]["_web_messages"][0]["contient_documents"] is True


@pytest.mark.parametrize("copie", ["messages", "memory_original_messages"])
def test_garde_lit_provenance_des_copies(client, copie):
    enregistrer_accord("llm", "openai", True, "3", [])
    context = ContextWindow(messages=[])
    setattr(context, copie, [Message(role="user", content="EXTRAIT", contient_documents=True)])
    with pytest.raises(ErreurPourEcran, match="documents"):
        verifier_envoi_llm(LLMConfig(LLMProvider.OPENAI, "fictif"), context)


@pytest.mark.parametrize("trace", [True, None, "false"])
@pytest.mark.parametrize("retrait_tardif", [False, True])
async def test_copie_web_filtree_et_revalidee(client, monkeypatch, trace, retrait_tardif):
    from app.routers import chat
    from app.services.tool_confirmations import register_pending

    enregistrer_accord("llm", "openai", True, "3", [])
    enregistrer_accord("documents", "openai", retrait_tardif, "3", [])
    envois = []

    async def transport(*args, **kwargs):
        envois.append(str(args))
        yield StreamEvent(type="text", content="Réponse publique")

    svc = LLMService(LLMConfig(LLMProvider.OPENAI, "fictif", api_key="factice"))
    svc._provider = SimpleNamespace(continue_with_tool_results=transport)

    async def preparer():
        if retrait_tardif:
            enregistrer_accord("documents", "openai", False, "3", [])

    svc._ensure_provider = AsyncMock(side_effect=preparer)
    monkeypatch.setattr(chat, "get_llm_service", lambda: svc)
    monkeypatch.setattr(chat, "execute_web_search", AsyncMock(return_value="Source publique"))
    copie = {"role": "assistant", "content": "EXTRAIT_DIFFERE"}
    if trace is not None:
        copie["contient_documents"] = trace
    carte = register_pending(
        "web_search",
        {
            "query": "Question publique",
            "_provenance_documents": "sans_document",
            "_web_messages": [
                copie,
                {"role": "user", "content": "Question publique", "contient_documents": False},
            ],
        },
    )
    reponse = await client.post(
        "/api/chat/confirm-tool", json={"confirmation_id": carte, "approved": True}
    )
    assert reponse.status_code == 200
    assert "EXTRAIT_DIFFERE" not in str(envois)
    assert "accord" in reponse.text
    if retrait_tardif:
        assert not envois
    else:
        assert len(envois) == 1
        assert "historique" in reponse.text


async def test_extraction_differee_conserve_provenance(client, monkeypatch):
    from app.models.database import get_sync_session
    from app.models.entities import Conversation
    from app.models.entities import Message as DBMessage
    from app.routers import chat

    with get_sync_session() as session:
        conv = Conversation(title="Fictif")
        session.add(conv)
        session.flush()
        msg = DBMessage(
            conversation_id=conv.id,
            role="assistant",
            content="Réponse",
            extra_data=json.dumps({"provenance_documents": "documents"}),
        )
        session.add(msg)
        session.commit()
        conversation_id, message_id = conv.id, msg.id
    enregistrer_accord("llm", "openai", True, "3", [])
    envois = []

    async def transport(*args, **kwargs):
        envois.append(args)
        yield StreamEvent(type="text", content="{}")

    svc = LLMService(LLMConfig(LLMProvider.OPENAI, "fictif", api_key="factice"))
    svc._provider = SimpleNamespace(stream=transport)
    svc._ensure_provider = AsyncMock()
    await chat._extract_entities_background(
        "EXTRAIT_DOCUMENT_DIFFERE", conversation_id, message_id, svc
    )
    assert not envois
