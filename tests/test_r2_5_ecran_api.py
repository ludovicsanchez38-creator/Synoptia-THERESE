"""Noyau exposé ensemble : lecture locale, correction, effacement et accord tardif."""

import pytest
from app.models.entities import Message
from app.services import llm, memory_cards
from app.services.providers.base import LLMProvider
from sqlmodel import select

from tests.test_p159_contexte_transmis import _evenements
from tests.test_r2_3_outil import action, fournisseur  # noqa: F401


@pytest.mark.asyncio
async def test_lecture_correction_archive_effacement(client, db_session):
    fiche = await memory_cards.ecrire(action())
    rep = await client.get('/api/memory/cards')
    assert rep.status_code == 200
    assert rep.json()['items'][0]['id'] == fiche['id']
    assert rep.json()['items'][0]['updated_at'].endswith(('Z', '+00:00'))
    rep = await client.patch(f"/api/memory/cards/{fiche['id']}", json={'version': 1, 'content': 'Préfère les listes.'})
    assert rep.status_code == 200 and rep.json()['protected']
    assert (await client.patch(f"/api/memory/cards/{fiche['id']}", json={'version': 1, 'title': 'Périmé'})).status_code == 409
    rep = await client.post(f"/api/memory/cards/{fiche['id']}/release", json={'version': 2})
    assert rep.status_code == 200 and not rep.json()['protected']
    rep = await client.patch(f"/api/memory/cards/{fiche['id']}", json={'version': 3, 'state': 'archivee'})
    assert rep.status_code == 200 and rep.json()['protected']
    assert (await client.get('/api/memory/cards')).json()['total'] == 0
    assert (await client.get('/api/memory/cards?state=archivee')).json()['total'] == 1
    assert (await client.delete(f"/api/memory/cards/{fiche['id']}?version=4")).status_code == 200
    assert (await client.get(f"/api/memory/cards/{fiche['id']}")).status_code == 404
    assert (await client.post('/api/memory/cards', json=action())).status_code == 405  # écriture autonome seulement


@pytest.mark.asyncio
async def test_accord_apres_payload_et_reprise_sans_dupliquer_la_source(client, db_session, fournisseur):  # noqa: F811
    await memory_cards.ecrire(action())
    fournisseur[0].config = llm.LLMConfig(LLMProvider.OPENAI, 'factice', context_window=128000)
    rep = await client.post('/api/chat/send', json={'message': 'Aide-moi à rédiger.', 'stream': True})
    accord = next(e for e in _evenements(rep.text) if e['type'] == 'memory_consent_required')
    assert accord['provider'] == 'openai' and accord['purpose'] == 'llm'
    assert not fournisseur[2]
    rep = await client.post('/api/chat/send', json={'message': 'Aide-moi à rédiger.', 'stream': True,
        'conversation_id': accord['conversation_id'], 'resume_message_id': accord['message_id'],
        'memory_card_grants': ['llm:openai']})
    assert rep.status_code == 200 and len(fournisseur[2]) == 1
    messages = (await db_session.execute(select(Message).where(Message.role == 'user'))).scalars().all()
    assert len(messages) == 1
