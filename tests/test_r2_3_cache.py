"""Migration du cache historique, entièrement dans la base chiffrée."""
import pytest
from app.models.entities import Conversation, Message
from sqlmodel import select


@pytest.mark.asyncio
async def test_reprise_cache_ancien_et_rejeu_sans_perte(client, db_session):
    charge = {'conversations': [{'id': 'cache-local', 'title': 'Échange non synchronisé', 'messages': [
        {'id': 'm-local', 'role': 'user', 'content': 'Tour accepté avant redémarrage', 'timestamp': '2026-10-21T06:00:00Z'},
        {'id': 'r-local', 'role': 'assistant', 'content': 'Réponse partielle', 'isStreaming': True,
         'timestamp': '2026-10-21T06:00:01Z', 'skillFiles': []}]}]}
    for _ in range(2):
        rep = await client.post('/api/chat/cache-migration', json=charge)
        assert rep.status_code == 200, rep.text
    db_session.expire_all()
    assert len((await db_session.execute(select(Conversation))).scalars().all()) == 1
    messages = (await db_session.execute(select(Message).order_by(Message.created_at))).scalars().all()
    assert [m.content for m in messages] == ['Tour accepté avant redémarrage', 'Réponse partielle']
    rep = await client.get('/api/chat/conversations/cache-local/messages')
    assert rep.status_code == 200, rep.text
    assert len(rep.json()) == 2
