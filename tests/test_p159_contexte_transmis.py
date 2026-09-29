"""P-159 : la réponse dit combien de messages passés ont été transmis.

Le chat relit un historique, ajoute le tour courant, puis `trim_to_fit`
peut en retirer pour tenir dans le modèle. Ces deux comptes doivent
voyager avec la réponse, hors flux et dans l'événement `done`.
"""

import json
from datetime import UTC, datetime, timedelta

import pytest
from app.models.entities import Conversation, Message
from app.services.context import ContextWindow
from app.services.providers.base import StreamEvent
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class _Fournisseur:
    value = "anthropic"


class _Config:
    provider = _Fournisseur()
    model = "faux-modele"


class _FauxLLM:
    def __init__(self, max_tokens: int | None = None) -> None:
        self.max_tokens = max_tokens

    config = _Config()

    def prepare_context(self, messages, memory_context=None):
        if self.max_tokens is None:
            return type("Ctx", (), {"messages": list(messages), "system_prompt": ""})()
        return ContextWindow(
            messages=list(messages),
            system_prompt="systeme",
            max_tokens=self.max_tokens,
        ).trim_to_fit()

    async def stream_response(self, context, raise_on_error=False, usage_sink=None):
        if usage_sink is not None:
            usage_sink["input_tokens"] = 3
            usage_sink["output_tokens"] = 2
        yield "Réponse courte."

    async def stream_response_with_tools(self, context, tools=None):
        yield StreamEvent(type="text", content="Réponse courte.")
        yield StreamEvent(type="done", stop_reason="end_turn")


def _attendu(messages: list, max_tokens: int | None) -> dict[str, int]:
    """Même coupe que le faux service : le test ne recopie pas la formule."""
    if max_tokens is None:
        fenetre = list(messages)
    else:
        fenetre = ContextWindow(
            messages=list(messages),
            system_prompt="systeme",
            max_tokens=max_tokens,
        ).trim_to_fit().messages
    relus = max(0, len(messages) - 1)
    transmis = max(0, len(fenetre) - 1)
    if transmis > relus:
        transmis = relus
    return {"messages_relus": relus, "messages_transmis": transmis}


async def _fil(db_session: AsyncSession, nb: int, taille: int = 12) -> str:
    conv = Conversation(title="Contexte")
    db_session.add(conv)
    await db_session.commit()
    base = datetime(2026, 9, 29, 9, 0, tzinfo=UTC)
    for i in range(nb):
        db_session.add(
            Message(
                conversation_id=conv.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"passe-{i:02d}-" + ("x" * taille),
                created_at=base + timedelta(seconds=i),
            )
        )
    await db_session.commit()
    return conv.id


def _evenements(texte: str) -> list[dict]:
    return [
        json.loads(ligne.removeprefix("data: "))
        for ligne in texte.splitlines()
        if ligne.startswith("data: ")
    ]


class TestContexteTransmis:
    @pytest.mark.asyncio
    async def test_reponse_hors_flux_donne_les_messages_relus(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        from unittest.mock import patch

        conv_id = await _fil(db_session, 3)
        llm = _FauxLLM()
        with patch("app.routers.chat.get_llm_service", return_value=llm):
            reponse = await client.post(
                "/api/chat/send",
                json={
                    "message": "question-courante",
                    "conversation_id": conv_id,
                    "stream": False,
                    "include_memory": False,
                },
            )
        assert reponse.status_code == 200, reponse.text
        corps = reponse.json()
        assert corps["contexte"] == {"messages_relus": 3, "messages_transmis": 3}, corps
        assert "content" in corps and "conversation_id" in corps

    @pytest.mark.asyncio
    async def test_coupe_du_modele_diminue_les_messages_transmis(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        from unittest.mock import patch

        conv_id = await _fil(db_session, 8, taille=400)
        llm = _FauxLLM(max_tokens=80)
        with patch("app.routers.chat.get_llm_service", return_value=llm):
            reponse = await client.post(
                "/api/chat/send",
                json={
                    "message": "question-courante",
                    "conversation_id": conv_id,
                    "stream": False,
                    "include_memory": False,
                },
            )
        assert reponse.status_code == 200, reponse.text
        # Le faux service coupe vraiment : 8 messages longs ne tiennent pas.
        attendu = _attendu(
            [type("M", (), {"content": "x" * 400, "role": "user"})() for _ in range(8)]
            + [type("M", (), {"content": "question-courante", "role": "user"})()],
            80,
        )
        assert attendu["messages_transmis"] < attendu["messages_relus"]
        assert reponse.json()["contexte"]["messages_relus"] == 8
        assert reponse.json()["contexte"]["messages_transmis"] == attendu["messages_transmis"]
        historique = await client.get(f"/api/chat/conversations/{conv_id}/messages")
        assistant = [m for m in historique.json() if m["role"] == "assistant"][-1]
        extra = json.loads(assistant["extra_data"])
        assert extra["contexte"] == reponse.json()["contexte"]

    @pytest.mark.asyncio
    async def test_flux_porte_le_contexte_sur_done(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        from unittest.mock import patch

        conv_id = await _fil(db_session, 2)
        with patch("app.routers.chat.get_llm_service", return_value=_FauxLLM()):
            reponse = await client.post(
                "/api/chat/send",
                json={
                    "message": "question-courante",
                    "conversation_id": conv_id,
                    "stream": True,
                    "include_memory": False,
                },
            )
        assert reponse.status_code == 200, reponse.text
        done = next(e for e in _evenements(reponse.text) if e.get("type") == "done")
        assert done["contexte"] == {"messages_relus": 2, "messages_transmis": 2}
        assert "usage" in done

    @pytest.mark.asyncio
    async def test_action_locale_ne_porte_pas_de_contexte(
        self, client: AsyncClient
    ) -> None:
        reponse = await client.post(
            "/api/chat/send",
            json={"message": "{action: ouvrir crm}", "stream": False},
        )
        assert reponse.status_code == 200, reponse.text
        assert reponse.json().get("contexte") is None
