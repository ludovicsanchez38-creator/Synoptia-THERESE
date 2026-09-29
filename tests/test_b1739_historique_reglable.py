"""B-1739 : `max_history_messages` est enregistré et le chat l'ignore.

Le réglage vit dans la préférence `llm_behavior`. Le chat relit quand même
les 50 derniers messages, quoi qu'on ait posé. Un réglage à 10 doit n'en
transmettre que 10 (les plus récents), borné entre 1 et 200, 50 si rien
n'est posé.
"""

import json
from datetime import UTC, datetime, timedelta

import pytest
from app.models.entities import Conversation, Message, Preference
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class _Fournisseur:
    value = "anthropic"


class _Config:
    provider = _Fournisseur()
    model = "faux-modele"


class _FauxLLM:
    """Enregistre la liste réellement passée à prepare_context."""

    def __init__(self) -> None:
        self.messages: list = []

    config = _Config()

    def prepare_context(self, messages, memory_context=None):
        self.messages = list(messages)
        return type("Ctx", (), {"messages": list(messages), "system_prompt": ""})()

    async def stream_response(self, context, raise_on_error=False, usage_sink=None):
        if usage_sink is not None:
            usage_sink["input_tokens"] = 1
            usage_sink["output_tokens"] = 1
        yield "Réponse."


async def _fil(db_session: AsyncSession, nb: int) -> str:
    conv = Conversation(title="Fil long")
    db_session.add(conv)
    await db_session.commit()
    base = datetime(2026, 9, 29, 8, 0, tzinfo=UTC)
    for i in range(nb):
        db_session.add(
            Message(
                conversation_id=conv.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"passe-{i:03d}",
                created_at=base + timedelta(seconds=i),
            )
        )
    await db_session.commit()
    return conv.id


async def _poser(client: AsyncClient, valeur: int | None) -> None:
    if valeur is None:
        return
    reglage = await client.post(
        "/api/personalisation/llm-behavior",
        json={
            "custom_system_prompt": "",
            "use_custom_system_prompt": False,
            "response_style": "detailed",
            "include_memory_context": True,
            "max_history_messages": valeur,
        },
    )
    assert reglage.status_code == 200, reglage.text
    assert reglage.json()["max_history_messages"] == valeur


async def _messages_passes(
    client: AsyncClient, conv_id: str, llm: _FauxLLM
) -> list[str]:
    from unittest.mock import patch

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
    contenus = [m.content for m in llm.messages]
    assert contenus[-1] == "question-courante", contenus
    return [c for c in contenus if c.startswith("passe-")]


class TestPlafondHistorique:
    @pytest.mark.asyncio
    async def test_reglage_a_10_n_envoie_que_10_messages(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        conv_id = await _fil(db_session, 60)
        await _poser(client, 10)
        llm = _FauxLLM()
        passes = await _messages_passes(client, conv_id, llm)
        assert len(passes) == 10, (
            f"réglage à 10 : le modèle a reçu {len(passes)} messages passés"
        )
        assert passes == [f"passe-{i:03d}" for i in range(50, 60)]

    @pytest.mark.asyncio
    async def test_sans_reglage_reste_a_50(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        conv_id = await _fil(db_session, 60)
        passes = await _messages_passes(client, conv_id, _FauxLLM())
        assert len(passes) == 50
        assert passes[0] == "passe-010"
        assert passes[-1] == "passe-059"

    @pytest.mark.asyncio
    async def test_reglage_sous_1_est_borne_a_1(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        conv_id = await _fil(db_session, 60)
        await _poser(client, 0)
        passes = await _messages_passes(client, conv_id, _FauxLLM())
        assert passes == ["passe-059"]

    @pytest.mark.asyncio
    async def test_reglage_au_dessus_de_200_est_borne_a_200(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        conv_id = await _fil(db_session, 210)
        await _poser(client, 500)
        passes = await _messages_passes(client, conv_id, _FauxLLM())
        assert len(passes) == 200
        assert passes[0] == "passe-010"
        assert passes[-1] == "passe-209"

    @pytest.mark.asyncio
    async def test_valeur_illisible_retombe_sur_50(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        conv_id = await _fil(db_session, 60)
        db_session.add(
            Preference(
                key="llm_behavior",
                value=json.dumps({"max_history_messages": "beaucoup"}),
                category="llm",
            )
        )
        await db_session.commit()
        passes = await _messages_passes(client, conv_id, _FauxLLM())
        assert len(passes) == 50
