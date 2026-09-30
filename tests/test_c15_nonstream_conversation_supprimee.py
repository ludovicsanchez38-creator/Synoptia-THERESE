"""Voie non diffusée de l'invariant B-1494 : aucun message après suppression.

Les données sont synthétiques et le fournisseur est un faux LLM. La suppression
se produit pendant stream_response, après une première portion de réponse.
"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from sqlmodel import select


async def _supprimer(conversation_id: str) -> None:
    from app.models.database import get_session_context
    from app.models.entities import Conversation

    async with get_session_context() as autre:
        conversation = await autre.get(Conversation, conversation_id)
        assert conversation is not None
        await autre.delete(conversation)
        await autre.commit()


async def _etat_persistant(conversation_id: str) -> tuple[object, list[dict]]:
    from app.models.database import get_session_context
    from app.models.entities import Conversation, Message

    async with get_session_context() as lecture:
        conversation = await lecture.get(Conversation, conversation_id)
        messages = list(
            (
                await lecture.execute(
                    select(Message).where(Message.conversation_id == conversation_id)
                )
            ).scalars().all()
        )
        return conversation, [
            {"role": message.role, "content": message.content}
            for message in messages
        ]


def _faux_llm(conversation_id: str, panne: bool):
    from app.services.context import ContextWindow

    class FauxLLM:
        config = SimpleNamespace(
            provider=SimpleNamespace(value="anthropic"), model="faux-suppression"
        )

        def prepare_context(self, messages, memory_context=None):
            return ContextWindow(
                messages=messages.copy(), system_prompt="Contexte de test", max_tokens=1000
            )

        async def stream_response(self, context, raise_on_error=False, usage_sink=None):
            yield "Réponse privée du dossier synthétique supprimé."
            await _supprimer(conversation_id)
            if panne:
                raise RuntimeError("Panne synthétique après suppression")

    return FauxLLM()


@pytest.mark.asyncio
@pytest.mark.parametrize("panne", [False, True], ids=["reponse-finale", "reponse-en-erreur"])
async def test_la_reponse_non_diffusee_ne_survit_pas_a_la_suppression(client, panne):
    creation = await client.post(
        "/api/chat/conversations", json={"title": "Dossier synthétique à supprimer"}
    )
    assert creation.status_code == 200, creation.text
    conversation_id = creation.json()["id"]

    with patch("app.routers.chat.get_llm_service", return_value=_faux_llm(conversation_id, panne)):
        reponse = await client.post(
            "/api/chat/send",
            json={
                "message": "Où en est ce dossier synthétique ?",
                "conversation_id": conversation_id,
                "stream": False,
                "disable_tools": True,
                "include_memory": False,
            },
        )

    assert reponse.status_code == 200, reponse.text
    conversation, messages = await _etat_persistant(conversation_id)
    assert conversation is None, "La suppression doit réellement avoir eu lieu"
    assert messages == [], f"Conversation absente, messages encore persistés : {messages!r}"
