"""La branche lit les objets sauvegardés localement, sans synchronisation."""
from datetime import UTC, datetime
import pytest
from app.models.entities import Contact, Document, EmailAccount, EmailMessage, Invoice


@pytest.mark.asyncio
async def test_liste_seulement_les_vrais_brouillons_locaux(client, db_session):
    contact = Contact(first_name='Fictive')
    compte = EmailAccount(email='fictif@example.test', provider='gmail')
    db_session.add_all([contact, compte])
    await db_session.commit()
    for statut in ('draft', 'sent', 'paid', 'overdue', 'cancelled'):
        db_session.add(Invoice(invoice_number='FACT-'+statut, contact_id=contact.id, due_date=datetime.now(UTC), status=statut))
    db_session.add(Invoice(invoice_number='DEV-draft', contact_id=contact.id, due_date=datetime.now(UTC), status='draft', document_type='devis'))
    for statut in ('en_cours', 'termine'):
        db_session.add(Document(title='Document '+statut, status=statut, brief='CORPS_NON_RECOPIE'))
    for draft in (True, False):
        db_session.add(EmailMessage(id='mail-'+str(draft), thread_id='fil', account_id=compte.id,
            from_email=compte.email, to_emails='[]', subject='Mail '+str(draft), labels='[]',
            date=datetime.now(UTC), internal_date=datetime.now(UTC), is_draft=draft, body_plain='CORPS_NON_RECOPIE'))
    await db_session.commit()
    rep = await client.get('/api/memory/drafts')
    assert rep.status_code == 200, rep.text
    data = rep.json()
    assert data['total'] == 4
    assert {d['kind'] for d in data['items']} == {'devis', 'facture', 'document', 'email'}
    assert 'CORPS_NON_RECOPIE' not in rep.text
    assert not (await client.get('/api/memory/drafts?offset=4')).json()['items']
    assert len((await client.get('/api/memory/drafts?limit=1')).json()['items']) == 1
    mail = await client.get('/api/memory/drafts/email/mail-True')
    assert mail.status_code == 200 and mail.json()['body_plain'] == 'CORPS_NON_RECOPIE'
    assert (await client.get('/api/memory/drafts/email/mail-False')).status_code == 404
