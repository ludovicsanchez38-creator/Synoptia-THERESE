"""Sauvegarde, retrait, restauration sur disque puis vraie garde d'envoi."""
from unittest.mock import AsyncMock

import pytest
from app.services.consentements import accord_valide, enregistrer_accord, historique
from app.services.error_handler import ErreurPourEcran
from app.services.llm import ContextWindow, LLMConfig, LLMProvider, LLMService, Message


@pytest.mark.parametrize('purpose', ['llm', 'documents', 'images', 'voice'])
async def test_une_sauvegarde_ne_ressuscite_pas_un_accord(client, purpose):
    enregistrer_accord('llm', 'openai', True, '3', [])
    enregistrer_accord(purpose, 'openai', True, '3', [])
    sauvegarde = await client.post('/api/data/backup', json={'password': 'Passphrase-Test-123'})
    assert sauvegarde.status_code == 200, sauvegarde.text
    enregistrer_accord(purpose, 'openai', False, '3', [], event_id='retrait-apres-sauvegarde')
    retrait = historique()[-1]
    response = await client.post(f"/api/data/restore/{sauvegarde.json()['backup_name']}?confirm=true",
                                 json={'password': 'Passphrase-Test-123'})
    assert response.status_code == 200, response.text
    assert not accord_valide(purpose, 'openai'), 'La restauration a ressuscité un accord retiré'
    assert any(r['event_id'] == retrait['event_id'] and r['occurred_at'] == retrait['occurred_at']
               and not r['granted'] for r in historique())
    # Réhydratation de l'interface et import v2 ne réactivent rien non plus.
    assert not any(g['purpose'] == purpose for g in (await client.get('/api/consents')).json()['grants'])
    if purpose in ('llm', 'documents'):
        service = LLMService(LLMConfig(LLMProvider.OPENAI, 'modele', api_key='factice'))
        service._ensure_provider = AsyncMock()
        context = ContextWindow(messages=[Message(role='user', content='Document fictif')],
                                contient_documents=purpose == 'documents')
        with pytest.raises(ErreurPourEcran, match=purpose):
            _ = [e async for e in service.stream_response_with_tools(context)]
        service._ensure_provider.assert_not_called()


async def test_accord_present_uniquement_dans_sauvegarde_demande_un_nouvel_accord(client):
    from app.models.database import get_sync_session
    from app.models.entities import CloudConsent
    from sqlmodel import delete

    enregistrer_accord('llm', 'openai', True, '3', [])
    sauvegarde = await client.post('/api/data/backup', json={'password': 'Passphrase-Test-123'})
    with get_sync_session() as session:
        session.exec(delete(CloudConsent))
        session.commit()
    response = await client.post(f"/api/data/restore/{sauvegarde.json()['backup_name']}?confirm=true",
                                 json={'password': 'Passphrase-Test-123'})
    assert response.status_code == 200, response.text
    assert not accord_valide('llm', 'openai')


async def test_restauration_interrompue_bloque_et_reprend_sans_perdre_le_retrait(client, monkeypatch):
    from app.services import consentements

    enregistrer_accord('llm', 'openai', True, '3', [])
    sauvegarde = await client.post('/api/data/backup', json={'password': 'Passphrase-Test-123'})
    enregistrer_accord('llm', 'openai', False, '3', [])
    terminer = consentements.terminer_restauration

    def disque_indisponible():
        raise OSError('Disque de test indisponible')

    monkeypatch.setattr(consentements, 'terminer_restauration', disque_indisponible)
    url = f"/api/data/restore/{sauvegarde.json()['backup_name']}?confirm=true"
    assert (await client.post(url, json={'password': 'Passphrase-Test-123'})).status_code == 500
    assert not accord_valide('llm', 'openai')
    assert consentements.accords_courants() == []
    monkeypatch.setattr(consentements, 'terminer_restauration', terminer)
    assert (await client.post(url, json={'password': 'Passphrase-Test-123'})).status_code == 200
    assert not accord_valide('llm', 'openai')
