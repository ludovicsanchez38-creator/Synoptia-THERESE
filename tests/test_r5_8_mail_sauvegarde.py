"""Un message Gmail synchronisé n'est pas un identifiant de brouillon."""
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from app.models.entities import Contact, EmailAccount, EmailMessage


@pytest.mark.asyncio
@pytest.mark.parametrize('effacement', ['contact', 'anonymisation', 'purge'])
async def test_correction_mail_resout_le_brouillon_et_actualise_la_seule_copie_locale(client, db_session, monkeypatch, effacement):
    from app.routers import email
    contact = Contact(first_name='Fictive')
    compte = EmailAccount(email='fictif@example.test', provider='gmail')
    db_session.add_all([contact, compte])
    await db_session.commit()
    db_session.add(EmailMessage(id='message-ancien', account_id=compte.id, thread_id='fil', from_email=compte.email,
        to_emails='[]', date=datetime.now(UTC), internal_date=datetime.now(UTC), labels='["DRAFT"]', is_draft=True, contact_id=contact.id, body_plain='Ancien texte'))
    await db_session.commit()
    gmail = AsyncMock()
    gmail._request.return_value = {'drafts': [{'id': 'brouillon-reel', 'message': {'id': 'message-ancien'}}]}
    gmail.update_draft.return_value = {'id': 'brouillon-reel', 'message': {'id': 'message-nouveau', 'threadId': 'fil'}}
    monkeypatch.setattr(email, 'get_gmail_service_for_account', AsyncMock(return_value=gmail))
    rep = await client.post('/api/email/messages/draft', params={'account_id': compte.id, 'source_message_id': 'message-ancien'},
        json={'to': ['fictif@example.test'], 'subject': 'Objet corrigé', 'body': 'Texte corrigé'})
    assert rep.status_code == 200, rep.text
    gmail.create_draft.assert_not_called()
    assert gmail.update_draft.call_args.args[0] == 'brouillon-reel'
    liste = (await client.get('/api/memory/drafts')).json()['items']
    assert [d['id'] for d in liste] == ['message-nouveau']
    mail = (await client.get('/api/memory/drafts/email/message-nouveau')).json()
    assert mail['body_plain'] == 'Texte corrigé' and mail['subject'] == 'Objet corrigé'
    assert (await client.get('/api/memory/drafts/email/message-ancien')).status_code == 404
    export = (await client.get(f'/api/rgpd/export/{contact.id}')).json()
    assert [m['id'] for m in export['email_messages']] == ['message-nouveau']
    if effacement == 'contact':
        rep = await client.delete(f'/api/memory/contacts/{contact.id}')
    elif effacement == 'anonymisation':
        rep = await client.post(f'/api/rgpd/anonymize/{contact.id}', json={})
    else:
        rep = await client.delete('/api/data/all', params={'confirm': True})
    assert rep.status_code == 200
    assert not (await client.get('/api/memory/drafts')).json()['items']
    from pathlib import Path

    from app.config import settings
    for fichier in Path(settings.data_dir).rglob('*'):
        if fichier.is_file():
            assert b'Texte corrig' not in fichier.read_bytes(), fichier.name


@pytest.mark.asyncio
async def test_message_non_brouillon_refuse_avant_appel_distant(client, db_session, monkeypatch):
    from app.routers import email
    compte = EmailAccount(email='fictif@example.test', provider='gmail')
    db_session.add(compte)
    await db_session.commit()
    fournisseur = AsyncMock()
    monkeypatch.setattr(email, 'get_gmail_service_for_account', fournisseur)
    rep = await client.post('/api/email/messages/draft', params={'account_id': compte.id, 'source_message_id': 'inconnu'},
        json={'to': ['fictif@example.test'], 'subject': 'Objet', 'body': 'Texte'})
    assert rep.status_code == 404
    fournisseur.assert_not_called()


@pytest.mark.asyncio
async def test_cache_brouillon_ne_reecrit_pas_apres_purge(db_session):
    from app.routers.email import SendEmailRequest
    from app.services.local_drafts import actualiser_cache
    from app.services.memory_tools import creations_du_chat_suspendues, generation_des_donnees
    from sqlmodel import select
    compte = EmailAccount(email='fictif@example.test', provider='gmail')
    db_session.add(compte)
    await db_session.commit()
    generation = generation_des_donnees()
    async with creations_du_chat_suspendues():
        pass
    await actualiser_cache(db_session, compte, SendEmailRequest(to=['fictif@example.test'], subject='Objet', body='Texte'),
        'nouveau', generation_attendue=generation)
    assert not (await db_session.execute(select(EmailMessage))).scalars().all()
