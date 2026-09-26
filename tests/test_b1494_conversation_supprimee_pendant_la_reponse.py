"""B-1494 : supprimer une conversation pendant sa réponse laissait un message
orphelin.

Le tiroir permet de supprimer une conversation pendant qu'elle répond, et
le moteur supprime sans regarder les générations en cours. L'écriture de la
réponse (finale, d'erreur ou partielle) insérait ensuite un message dont la
conversation n'existe plus : invisible, mais conservé après la suppression.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel import select


async def _supprimer(conversation_id: str) -> None:
    from app.models.database import get_session_context
    from app.models.entities import Conversation

    async with get_session_context() as autre:
        conversation = await autre.get(Conversation, conversation_id)
        await autre.delete(conversation)
        await autre.commit()


async def _messages(conversation_id: str) -> list:
    from app.models.database import get_session_context
    from app.models.entities import Message

    async with get_session_context() as lecture:
        return list((await lecture.execute(
            select(Message).where(Message.conversation_id == conversation_id)
        )).scalars().all())


def _faux_modele(conversation_id: str, panne: bool):
    from app.services.providers.base import StreamEvent

    class _FauxLLM:
        config = SimpleNamespace(provider=SimpleNamespace(value="anthropic"), model="faux")

        def prepare_context(self, messages, memory_context=None):
            return SimpleNamespace(messages=[], system_prompt="")

        async def stream_response_with_tools(self, context, tools=None):
            yield StreamEvent(type="text", content="Voici où en est le devis.")
            await _supprimer(conversation_id)
            if panne:
                raise RuntimeError("fournisseur en panne")
            yield StreamEvent(type="done", stop_reason="end_turn")

    return _FauxLLM()


@pytest.mark.asyncio
@pytest.mark.parametrize("panne", [False, True], ids=["reponse-finale", "reponse-en-erreur"])
async def test_aucun_message_ne_survit_a_la_suppression(client, db_session, panne):
    from app.models.entities import Conversation
    from app.routers.chat import _do_stream_response

    conversation_id = f"conv-b1494-{panne}"
    db_session.add(Conversation(id=conversation_id, title="Devis Roux"))
    await db_session.commit()

    with patch("app.routers.chat.get_llm_service", return_value=_faux_modele(conversation_id, panne)), patch(
        "app.routers.chat._get_memory_context", AsyncMock(return_value=None)
    ):
        async for _ in _do_stream_response(conversation_id, "Où en est le devis ?", db_session, disable_tools=True):
            pass

    assert await _messages(conversation_id) == []


@pytest.mark.asyncio
async def test_par_la_route_diffusee_la_suppression_l_emporte(client):
    """Le parcours réel : envoi diffusé, suppression pendant la réponse."""
    creation = await client.post("/api/chat/conversations", json={"title": "Devis Roux"})
    assert creation.status_code == 200, creation.text
    conversation_id = creation.json()["id"]

    with patch("app.routers.chat.get_llm_service", return_value=_faux_modele(conversation_id, False)), patch(
        "app.routers.chat._get_memory_context", AsyncMock(return_value=None)
    ):
        reponse = await client.post("/api/chat/send", json={
            "message": "Où en est le devis ?", "conversation_id": conversation_id,
            "stream": True, "disable_tools": True,
        })

    assert reponse.status_code == 200, reponse.text[:300]
    assert await _messages(conversation_id) == []


@pytest.mark.asyncio
async def test_une_reponse_partielle_n_est_pas_ecrite_dans_une_conversation_disparue(client, db_session):
    from app.models.entities import Conversation
    from app.routers.chat import _persister_message_partiel

    conversation = Conversation(id="conv-b1494-partiel", title="Devis Roux")
    db_session.add(conversation)
    await db_session.commit()
    await _supprimer(conversation.id)

    llm = SimpleNamespace(config=SimpleNamespace(provider=SimpleNamespace(value="anthropic"), model="faux"))
    await _persister_message_partiel(conversation.id, "Début de réponse", llm)

    assert await _messages(conversation.id) == []
