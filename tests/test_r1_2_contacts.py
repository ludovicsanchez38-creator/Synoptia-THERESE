"""R1-2 : le carnet partagé et le choix explicite d'un projet."""
import json
from contextlib import closing
from unittest.mock import MagicMock

import pytest
from app.models.database import apply_adhoc_migrations, db_connect
from app.models.entities import Contact
from app.services.memory_tools import execute_create_contact, execute_read_contact
from sqlalchemy import select


@pytest.mark.asyncio
@pytest.mark.parametrize('scope,scope_id,attendu', [('global', None, 'global'), ('all', None, 'global'), ('project', 'dossier', 'project')])
async def test_contact_chat_visible_dans_les_lectures_du_carnet(
    client, db_session, scope, scope_id, attendu,
):
    resultat = json.loads(await execute_create_contact(
        {'first_name': 'Marie', 'last_name': 'Recette'}, db_session,
        scope=scope, scope_id=scope_id, conversation_id='fil-a',
    ))
    assert resultat['success'] is True
    contact = (await db_session.execute(select(Contact))).scalar_one()
    assert contact.scope == attendu
    assert contact.scope_id == (scope_id if attendu == 'project' else None)
    if attendu == 'global':
        # Le module, le store de Ctrl+K et le formulaire client partagent cette API.
        for suffixe in ('?scope=global', ''):
            liste = await client.get('/api/memory/contacts' + suffixe)
            assert contact.id in {c['id'] for c in liste.json()}
        lecture = json.loads(await execute_read_contact(
            {'query': 'Marie Recette'}, db_session,
            scope='global', conversation_id='fil-b',
        ))
        assert contact.id in json.dumps(lecture)


def test_migration_des_contacts_conversation_seulement(tmp_path):
    chemin = tmp_path / 'ancienne.db'
    with closing(db_connect(chemin)) as conn:
        conn.execute('CREATE TABLE contacts (id TEXT PRIMARY KEY, scope TEXT, scope_id TEXT)')
        conn.executemany('INSERT INTO contacts VALUES (?, ?, ?)', [
            ('ancien', 'conversation', 'fil'), ('client', 'project', 'dossier'), ('general', 'global', None),
        ])
        conn.commit()
    apply_adhoc_migrations(chemin)
    apply_adhoc_migrations(chemin)
    with closing(db_connect(chemin)) as conn:
        lignes = dict((r[0], r[1:]) for r in conn.execute('SELECT id, scope, scope_id FROM contacts'))
    assert lignes['ancien'] == ('global', None)
    assert lignes['client'] == ('project', 'dossier')


def test_migration_des_vecteurs_sans_reencoder(monkeypatch):
    from app.services import qdrant
    from app.services.qdrant import QdrantService
    monkeypatch.setattr(qdrant, '_projets_des_contacts', lambda: {}, raising=False)
    service = QdrantService()
    client = MagicMock()
    service._client = client
    service.promouvoir_contacts_conversation()
    appel = client.set_payload.call_args.kwargs
    assert appel['payload'] == {'scope': 'global', 'scope_id': None}
    filtre = appel['points'].model_dump()
    assert 'conversation' in json.dumps(filtre)
    assert 'contact' in json.dumps(filtre)


def test_un_helper_de_facture_ne_migre_pas_le_carnet(tmp_path):
    from app.models.database import ensure_invoice_legacy_columns
    chemin = tmp_path / 'ancienne.db'
    with closing(db_connect(chemin)) as conn:
        conn.execute('CREATE TABLE contacts (id TEXT, scope TEXT, scope_id TEXT)')
        conn.execute("INSERT INTO contacts VALUES ('ancien', 'conversation', 'fil')")
        conn.commit()
    ensure_invoice_legacy_columns(chemin)
    with closing(db_connect(chemin)) as conn:
        assert conn.execute('SELECT scope FROM contacts').fetchone()[0] == 'conversation'


def test_migration_conserve_le_projet_choisi_dans_une_ancienne_conversation(tmp_path):
    chemin = tmp_path / 'ancienne.db'
    with closing(db_connect(chemin)) as conn:
        conn.execute('CREATE TABLE contacts (id TEXT PRIMARY KEY, scope TEXT, scope_id TEXT)')
        conn.execute('CREATE TABLE conversations (id TEXT PRIMARY KEY, memory_scope TEXT, project_id TEXT)')
        conn.execute("INSERT INTO conversations VALUES ('fil-projet', 'project', 'projet-a')")
        conn.execute("INSERT INTO contacts VALUES ('ancien', 'conversation', 'fil-projet')")
        conn.commit()
    apply_adhoc_migrations(chemin)
    apply_adhoc_migrations(chemin)
    with closing(db_connect(chemin)) as conn:
        assert conn.execute('SELECT scope, scope_id FROM contacts').fetchone() == ('project', 'projet-a')


def test_vecteurs_legacy_conservent_aussi_le_projet(monkeypatch):
    from app.services.qdrant import QdrantService, settings
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, PointStruct, VectorParams
    client = QdrantClient(':memory:')
    client.create_collection(settings.qdrant_collection, vectors_config=VectorParams(size=2, distance=Distance.COSINE))
    client.upsert(settings.qdrant_collection, points=[
        PointStruct(id=1, vector=[1., 0.], payload={'type': 'contact', 'entity_id': 'c-projet', 'scope': 'conversation', 'scope_id': 'fil-projet'}),
        PointStruct(id=2, vector=[1., 0.], payload={'type': 'contact', 'entity_id': 'c-libre', 'scope': 'conversation', 'scope_id': 'fil-libre'}),
        PointStruct(id=3, vector=[1., 0.], payload={'type': 'file', 'entity_id': 'document', 'scope': 'conversation', 'scope_id': 'fil-libre'}),
    ])
    from app.services import qdrant
    monkeypatch.setattr(qdrant, '_projets_des_contacts', lambda: {'projet-a': ['c-projet']}, raising=False)
    service = QdrantService()
    service._client = client
    try:
        service.promouvoir_contacts_conversation()
        points, _ = client.scroll(settings.qdrant_collection)
        payloads = {p.payload['entity_id']: p.payload for p in points}
        assert payloads['c-projet']['scope'] == 'project'
        assert payloads['c-projet']['scope_id'] == 'projet-a'
        assert payloads['c-libre']['scope'] == 'global'
        assert payloads['document']['scope'] == 'conversation'
    finally:
        client.close()
