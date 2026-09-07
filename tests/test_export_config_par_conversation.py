"""B-511 (cycle 4) : l'export de configuration recomposait chaque conversation par
un filtre imbriqué sur la liste complète des messages (coût quadratique). Une
passe range les messages par conversation ; l'export reste exact et ordonné."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest


@pytest.mark.asyncio
async def test_chaque_conversation_ne_porte_que_ses_messages_dans_l_ordre(client, db_session):
    from app.models.entities import Conversation, Message

    t0 = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    a = Conversation(id="conv-a", title="A")
    b = Conversation(id="conv-b", title="B")
    db_session.add_all([a, b])
    await db_session.flush()
    db_session.add_all([
        Message(conversation_id="conv-b", role="user", content="b1", created_at=t0),
        Message(conversation_id="conv-a", role="user", content="a1", created_at=t0 + timedelta(minutes=1)),
        Message(conversation_id="conv-a", role="assistant", content="a2", created_at=t0 + timedelta(minutes=2)),
        Message(conversation_id="conv-b", role="assistant", content="b2", created_at=t0 + timedelta(minutes=3)),
    ])
    await db_session.commit()

    reponse = await client.post("/api/config/export", json={})
    assert reponse.status_code == 200, reponse.text
    convs = {c["id"]: c for c in reponse.json()["conversations"]}
    assert [m["content"] for m in convs["conv-a"]["messages"]] == ["a1", "a2"]
    assert [m["content"] for m in convs["conv-b"]["messages"]] == ["b1", "b2"]
