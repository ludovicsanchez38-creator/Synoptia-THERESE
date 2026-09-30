"""B-1743 à B-1745 : émission unique et avoir avec référence explicite."""
from datetime import UTC, datetime, timedelta

import pytest
from app.models import database as db
from app.models.entities import Invoice
from app.routers.invoices import _facture_d_origine_pour_le_pdf
from httpx import AsyncClient


async def _contact(client: AsyncClient) -> str:
    response = await client.post('/api/memory/contacts', json={'first_name': 'Client', 'last_name': 'Jetable'})
    assert response.status_code == 200, response.text
    return response.json()['id']


async def _historique(client: AsyncClient, document_type: str = 'facture') -> dict:
    contact_id = await _contact(client)
    now = datetime.now(UTC)
    prefix = 'FACT' if document_type == 'facture' else 'AV'
    async with db.AsyncSessionLocal() as session:
        old = Invoice(
            contact_id=contact_id, document_type=document_type,
            invoice_number=f'{prefix}-{now.year}-007', status='cancelled',
            issue_date=now - timedelta(days=60), due_date=now - timedelta(days=30),
            sent_at=now - timedelta(days=60),
        )
        session.add(old)
        session.add(Invoice(
            contact_id=contact_id, document_type=document_type,
            invoice_number=f'{prefix}-{now.year}-008', status='sent',
            due_date=now + timedelta(days=30), sent_at=now,
        ))
        await session.commit()
        identifiant = old.id
    response = await client.get(f'/api/invoices/{identifiant}')
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.asyncio
@pytest.mark.parametrize('document_type', ['facture', 'avoir'])
@pytest.mark.parametrize('transition', ['sent', 'paid', 'mark-paid'])
async def test_piece_historiquement_emise_garde_numero_et_dates(client: AsyncClient, document_type: str, transition: str):
    old = await _historique(client, document_type)
    if transition == 'mark-paid':
        response = await client.patch(f"/api/invoices/{old['id']}/mark-paid", json={})
    else:
        response = await client.put(f"/api/invoices/{old['id']}", json={'status': transition})
    assert response.status_code == 200, response.text
    after = response.json()
    for field in ['invoice_number', 'issue_date', 'due_date', 'sent_at']:
        assert after[field] == old[field], (field, old[field], after[field])


@pytest.mark.asyncio
async def test_avoir_peut_referencer_facture_emise_historiquement_annulee(client: AsyncClient):
    old = await _historique(client)
    response = await client.post('/api/invoices/', json={
        'contact_id': old['contact_id'], 'document_type': 'avoir',
        'converted_from_id': old['id'],
        'lines': [{'description': 'Rectification', 'quantity': 1, 'unit_price_ht': 10}],
    })
    assert response.status_code == 200, response.text
    async with db.AsyncSessionLocal() as session:
        credit = await session.get(Invoice, response.json()['id'])
        reference = await _facture_d_origine_pour_le_pdf(session, credit)
    assert reference == {
        'numero': old['invoice_number'],
        'date': datetime.fromisoformat(old['issue_date'].replace('Z', '+00:00')).strftime('%d/%m/%Y'),
    }


@pytest.mark.asyncio
@pytest.mark.parametrize('operation', ['draft', 'notes', 'delete'])
async def test_brouillon_provisoire_annule_reste_modifiable_et_supprimable(client: AsyncClient, operation: str):
    contact_id = await _contact(client)
    created = await client.post('/api/invoices/', json={
        'contact_id': contact_id, 'document_type': 'facture',
        'lines': [{'description': 'Brouillon', 'quantity': 1, 'unit_price_ht': 10}],
    })
    piece = created.json()
    cancelled = await client.put(f"/api/invoices/{piece['id']}", json={'status': 'cancelled'})
    assert cancelled.status_code == 200, cancelled.text
    if operation == 'delete':
        response = await client.delete(f"/api/invoices/{piece['id']}")
    else:
        fields = {'status': 'draft'} if operation == 'draft' else {'notes': 'Corrigé avant émission'}
        response = await client.put(f"/api/invoices/{piece['id']}", json=fields)
    assert response.status_code == 200, response.text


@pytest.mark.asyncio
@pytest.mark.parametrize('transition', ['sent', 'mark-paid'])
async def test_un_avoir_sans_reference_reste_brouillon_a_lemission(client: AsyncClient, transition: str):
    contact_id = await _contact(client)
    created = await client.post('/api/invoices/', json={
        'contact_id': contact_id, 'document_type': 'avoir',
        'lines': [{'description': 'Rectification à compléter', 'quantity': 1, 'unit_price_ht': 10}],
    })
    assert created.status_code == 200, created.text
    piece = created.json()
    if transition == 'mark-paid':
        response = await client.patch(f"/api/invoices/{piece['id']}/mark-paid", json={})
    else:
        response = await client.put(f"/api/invoices/{piece['id']}", json={'status': transition})
    assert response.status_code == 409, response.text
    assert "facture d'origine" in response.json()['message']
    unchanged = (await client.get(f"/api/invoices/{piece['id']}")).json()
    assert unchanged['status'] == 'draft'
    assert unchanged['invoice_number'] == piece['invoice_number']


@pytest.mark.asyncio
@pytest.mark.parametrize('document_type', ['facture', 'avoir'])
async def test_emission_initiale_prov_annule_accepte_le_formulaire_complet(client: AsyncClient, document_type: str):
    contact_id = await _contact(client)
    origine_id = None
    if document_type == 'avoir':
        origine = await client.post('/api/invoices/', json={
            'contact_id': contact_id, 'document_type': 'facture',
            'lines': [{'description': 'Origine', 'quantity': 1, 'unit_price_ht': 20}],
        })
        origine_id = origine.json()['id']
        emise = await client.put(f'/api/invoices/{origine_id}', json={'status': 'sent'})
        assert emise.status_code == 200, emise.text
    created = await client.post('/api/invoices/', json={
        'contact_id': contact_id, 'document_type': document_type,
        'lines': [{'description': 'Brouillon', 'quantity': 1, 'unit_price_ht': 10}],
    })
    assert created.status_code == 200, created.text
    piece = created.json()
    cancelled = await client.put(f"/api/invoices/{piece['id']}", json={'status': 'cancelled'})
    assert cancelled.status_code == 200, cancelled.text
    fields = {
        'status': 'sent', 'contact_id': contact_id, 'currency': 'EUR',
        'issue_date': piece['issue_date'], 'due_date': piece['due_date'],
        'notes': 'Dernière correction avant émission',
        'lines': [{'description': 'Version finale', 'quantity': 2, 'unit_price_ht': 10}],
    }
    if origine_id:
        fields['converted_from_id'] = origine_id
    response = await client.put(f"/api/invoices/{piece['id']}", json=fields)
    assert response.status_code == 200, response.text
    assert response.json()['status'] == 'sent'
    assert not response.json()['invoice_number'].startswith('PROV-')
    assert response.json()['notes'] == fields['notes']
    assert response.json()['lines'][0]['description'] == 'Version finale'
    assert response.json()['converted_from_id'] == origine_id
    relue = (await client.get(f"/api/invoices/{piece['id']}")).json()
    assert relue['invoice_number'] == response.json()['invoice_number']
    assert relue['sent_at'] is not None


@pytest.mark.asyncio
@pytest.mark.parametrize('operation', ['draft', 'notes', 'delete'])
async def test_refus_avoir_emis_explique_la_correction_effectivement_disponible(client: AsyncClient, operation: str):
    piece = await _historique(client, 'avoir')
    if operation == 'delete':
        response = await client.delete(f"/api/invoices/{piece['id']}")
    else:
        fields = {'status': 'draft'} if operation == 'draft' else {'notes': 'Modification interdite'}
        response = await client.put(f"/api/invoices/{piece['id']}", json=fields)
    assert response.status_code == 409, response.text
    assert 'expert-comptable' in response.json()['message']
    assert 'émets un avoir' not in response.json()['message']
