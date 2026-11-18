"""Une annulation ne doit conserver que le texte relayé par le flux."""

import json

import pytest
from app.models.entities import Message
from sqlmodel import select

from tests.test_chat_traitement import _faux_service, _fin, _texte


@pytest.mark.asyncio
@pytest.mark.parametrize("debut", ["", "Début déjà affiché. "])
async def test_le_partiel_enregistre_correspond_au_texte_relaye(
    client, monkeypatch, debut
):
    from app.models.database import get_session_context
    from app.routers import chat

    conversation = (await client.post(
        "/api/chat/conversations", json={"title": "Annulation"}
    )).json()["id"]
    progression = []

    def evenements():
        if debut:
            yield _texte(debut)
        progression.append("arrêt demandé")
        assert chat._cancel_generation(conversation)
        yield _texte("Dernier morceau produit.")
        progression.append("après le dernier morceau")
        yield _fin()

    monkeypatch.setattr(chat, "get_llm_service", lambda: _faux_service(evenements))
    reponse = await client.post("/api/chat/send", json={
        "message": "Réponds brièvement.",
        "conversation_id": conversation,
        "stream": True,
        "disable_tools": True,
        "include_memory": False,
    })

    assert reponse.status_code == 200
    recus = [
        json.loads(ligne.removeprefix("data: "))
        for ligne in reponse.text.splitlines() if ligne.startswith("data: ")
    ]
    texte_relaye = "".join(e["content"] for e in recus if e["type"] == "text")
    assert progression == ["arrêt demandé"]
    assert recus[-1]["type"] == "cancelled"
    assert texte_relaye.startswith(debut)

    async with get_session_context() as session:
        resultat = await session.execute(select(Message).where(
            Message.conversation_id == conversation, Message.role == "assistant"
        ))
        textes_sauves = [message.content for message in resultat.scalars().all()]

    assert textes_sauves == ([texte_relaye] if texte_relaye.strip() else [])
