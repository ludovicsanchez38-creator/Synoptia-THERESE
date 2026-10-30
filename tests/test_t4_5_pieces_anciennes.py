"""Reproductions API du cinquième tour : transport en mémoire exclusivement."""

import json
from unittest.mock import AsyncMock

import httpx
import pytest
from app.models.database import get_sync_session
from app.models.entities import Message, Preference
from app.services.consentements import enregistrer_accord
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


@pytest.mark.parametrize("stream", [False, True])
@pytest.mark.parametrize("demande", ["ordinaire", "nouvelle_piece", "commande", "accord_maintenu"])
async def test_piece_ancienne_ecartee_question_ordinaire(
    client, monkeypatch, tmp_path, stream, demande
):
    from app.routers import chat

    for purpose in ("llm", "documents"):
        enregistrer_accord(purpose, "openai", True, "3", [])
    with get_sync_session() as s:
        s.merge(Preference(key="auto_extract_entities", value="false"))
        s.commit()
    doc = tmp_path / "temoin.txt"
    doc.write_text(EXTRAIT)
    monkeypatch.setattr(chat, "_get_file_context", AsyncMock(return_value=(EXTRAIT, None)))
    envois = []

    async def transport(req):
        envois.append(req.content.decode())
        return httpx.Response(
            200, headers={"content-type": "text/event-stream"}, text=texte_sse("Réponse au message")
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as http:
        svc = LLMService(LLMConfig(LLMProvider.OPENAI, "gpt-4o", api_key="factice"))
        svc._provider = OpenAIProvider(svc.config, http)
        monkeypatch.setattr(chat, "get_llm_service", lambda: svc)
        premier = await client.post(
            "/api/chat/send",
            json={
                "message": "Lis ce fichier",
                "file_paths": [str(doc)],
                "stream": stream,
                "include_memory": False,
                "disable_tools": True,
            },
        )
        assert premier.status_code == 200 and len(envois) == 1
        with get_sync_session() as s:
            conv = (
                s.exec(select(Message).where(Message.role == "assistant")).all()[-1].conversation_id
            )
        if demande != "accord_maintenu":
            enregistrer_accord("documents", "openai", False, "3", [])
        err = None
        status = None
        body = None
        try:
            second = await client.post(
                "/api/chat/send",
                json={
                    "message": "/fichier " + str(doc) if demande == "commande" else "Bonjour",
                    "file_paths": [str(doc)] if demande == "nouvelle_piece" else [],
                    "conversation_id": conv,
                    "stream": stream,
                    "include_memory": False,
                    "disable_tools": True,
                },
            )
            status = second.status_code
            body = second.text
        except Exception as exc:
            err = str(exc)
        if demande in ("nouvelle_piece", "commande"):
            assert len(envois) == 1
            assert "documents" in (err or body) and "accord" in (err or body)
            return
        assert status == 200, err or body
        assert len(envois) == 2, body
        assert (EXTRAIT in envois[-1]) == (demande == "accord_maintenu")
        if stream:
            body = " ".join(
                json.loads(line[6:]).get("content") or ""
                for line in body.splitlines()
                if line.startswith("data: ")
            )
        assert "Réponse au message" in body
        if demande != "accord_maintenu":
            assert "historique" in body and "accord" in body
