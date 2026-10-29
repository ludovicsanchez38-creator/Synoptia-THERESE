"""Le moteur conserve les accords, leur retrait et leur origine héritée."""
import pytest
from sqlalchemy import inspect


@pytest.mark.asyncio
async def test_accord_retrait_et_reprise_idempotente(client, db_session):
    from app.services.consentements import (
        accord_valide,
        enregistrer_accord,
        historique,
        importer_accords,
    )

    ancien = {'purpose': 'documents', 'provider': 'openai', 'timestamp': '2026-01-02T03:04:05Z', 'dataCategories': ['documents']}
    importer_accords([ancien])
    assert accord_valide('documents', 'openai')
    importer_accords([ancien])
    assert len(historique()) == 1
    assert historique()[0]['text_version'] == '2'
    assert historique()[0]['occurred_at'] == ancien['timestamp']
    enregistrer_accord('documents', 'openai', False, '3', [])
    importer_accords([ancien])
    assert not accord_valide('documents', 'openai')
    assert len(historique()) == 2
    assert historique()[-1]['granted'] is False


@pytest.mark.asyncio
async def test_entete_de_requete_ne_remplace_pas_accord_local(client, db_session):
    from types import SimpleNamespace

    from app.services.memory_card_context import documents_autorises
    config = SimpleNamespace(provider=SimpleNamespace(value='openai'))
    assert not documents_autorises(config, ['documents:openai'])


@pytest.mark.asyncio
async def test_api_conserve_date_version_et_refuse_finalite_inconnue(client):
    response = await client.post('/api/consents', json={'purpose': 'llm', 'provider': 'openai', 'granted': True, 'text_version': '3', 'data_categories': ['messages']})
    assert response.status_code == 200
    body = (await client.get('/api/consents')).json()
    assert body['grants'][0]['provider'] == 'openai'
    assert body['history'][0]['recorded_at']
    assert body['history'][0]['text_version'] == '3'
    response = await client.post('/api/consents', json={'purpose': 'tout', 'provider': 'openai', 'granted': True, 'text_version': '3'})
    assert response.status_code == 422


def test_migration_cree_la_table_sans_perdre_les_preferences(tmp_path):
    from importlib.util import module_from_spec, spec_from_file_location
    from pathlib import Path

    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import create_engine, text
    path = Path('src/backend/alembic/versions/t4consent01_accords_cloud.py')
    assert path.exists()
    spec = spec_from_file_location('t4migration', path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    engine = create_engine(f'sqlite:///{tmp_path / "avant.db"}')
    with engine.begin() as conn:
        conn.execute(text('CREATE TABLE preferences (key TEXT, value TEXT)'))
        conn.execute(text("INSERT INTO preferences VALUES ('profil', 'existant')"))
        module.op = Operations(MigrationContext.configure(conn))
        module.upgrade()
        assert 'cloud_consents' in inspect(conn).get_table_names()
        assert conn.execute(text('SELECT value FROM preferences')).scalar() == 'existant'


@pytest.mark.asyncio
async def test_retrait_bloque_le_prochain_envoi_au_fournisseur(client, db_session):
    from unittest.mock import AsyncMock

    from app.services.consentements import enregistrer_accord
    from app.services.error_handler import ErreurPourEcran
    from app.services.llm import ContextWindow, LLMConfig, LLMProvider, LLMService, Message
    service = LLMService(LLMConfig(LLMProvider.OPENAI, 'modele', api_key='factice'))
    service._ensure_provider = AsyncMock()
    context = ContextWindow(messages=[Message(role='user', content='bonjour')])
    with pytest.raises(ErreurPourEcran, match='accord'):
        _ = [e async for e in service.stream_response_with_tools(context)]
    service._ensure_provider.assert_not_called()
    enregistrer_accord('llm', 'openai', True, '3', [])
    enregistrer_accord('llm', 'openai', False, '3', [])
    with pytest.raises(ErreurPourEcran, match='accord'):
        _ = [e async for e in service.stream_response_with_tools(context)]
    service._ensure_provider.assert_not_called()


@pytest.mark.asyncio
async def test_rejeu_de_decision_ne_duplique_pas_la_preuve(client):
    decision = {'purpose': 'images', 'provider': 'openai', 'granted': True, 'text_version': '3',
                'event_id': 'evenement-test-1'}
    assert (await client.post('/api/consents', json=decision)).status_code == 200
    assert (await client.post('/api/consents', json=decision)).status_code == 200
    assert len((await client.get('/api/consents')).json()['history']) == 1
