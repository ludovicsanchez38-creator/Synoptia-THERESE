"""R3 : une correspondance Qdrant de fichier doit devenir un résultat HTTP."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.models.entities import FileMetadata
from app.routers import memory


@pytest.mark.asyncio
@pytest.mark.parametrize('types', [None, ['file']])
async def test_recherche_hydrate_fichiers_sans_perdre_les_extraits(client, db_session, monkeypatch, types):
    fichier = FileMetadata(path='/fictif/atelier.pdf', name='atelier.pdf', extension='.pdf', size=100, chunk_count=2)
    db_session.add(fichier)
    await db_session.commit()
    qdrant = MagicMock()
    qdrant.async_search = AsyncMock(return_value=[
        {'entity_id': fichier.id, 'type': 'file', 'text': 'La clause zéphyr.', 'score': .94},
        {'entity_id': fichier.id, 'type': 'file', 'text': 'Extrait moins pertinent.', 'score': .72},
        {'entity_id': 'orphelin', 'type': 'file', 'text': 'Supprimé.', 'score': .98},
    ])
    monkeypatch.setattr(memory, 'get_qdrant_service', lambda: qdrant)
    demande = {'query': 'zéphyr', 'entity_types': types}
    rep = await client.post('/api/memory/search', json=demande)
    assert rep.status_code == 200
    assert rep.json()['total'] == 1
    hit = rep.json()['results'][0]
    assert hit['id'] == fichier.id and hit['entity_type'] == 'file'
    assert hit['title'] == 'atelier.pdf' and hit['content'] == 'La clause zéphyr.'
    assert hit['score'] == .94
    assert qdrant.async_search.call_args.kwargs['memory_types'] == types


@pytest.mark.asyncio
@pytest.mark.parametrize('semantique', [True, False])
async def test_nom_de_fichier_retrouvable_sans_embeddings(client, db_session, monkeypatch, semantique):
    fichier = FileMetadata(path='/fictif/Orchidee.pdf', name='Orchidee.pdf', extension='.pdf', size=100)
    db_session.add(fichier)
    await db_session.commit()
    qdrant = MagicMock()
    qdrant.async_search = AsyncMock(side_effect=RuntimeError('Embeddings indisponibles, exemple fictif'))
    monkeypatch.setattr(memory, 'get_qdrant_service', lambda: qdrant)
    rep = await client.post('/api/memory/search', json={'query': 'Orchidee',
        'entity_types': ['file'], 'include_semantic': semantique})
    assert rep.status_code == 200
    assert [r['id'] for r in rep.json()['results']] == [fichier.id]
    assert qdrant.async_search.call_count == int(semantique)
    rep = await client.post('/api/memory/search', json={'query': 'Orchidee',
        'entity_types': ['contact'], 'include_semantic': False})
    assert rep.json()['total'] == 0


@pytest.mark.asyncio
async def test_indexation_filtre_qdrant_et_http_reels_sans_modele_en_ligne(client, db_session, tmp_path, monkeypatch):
    from app.config import settings
    from app.routers import files
    from app.services import indexation, qdrant
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams

    # Seul le calcul d'embeddings est factice. Indexation, stockage vectoriel,
    # filtre de type et hydratation SQL/HTTP sont les vrais chemins.
    service = object.__new__(qdrant.QdrantService)
    service._client = QdrantClient(location=':memory:')
    service._initialized = True
    service._client.create_collection(settings.qdrant_collection,
        vectors_config=VectorParams(size=4, distance=Distance.COSINE))
    monkeypatch.setattr(qdrant, 'embed_text', lambda texte: [1., 0., 0., 0.])
    monkeypatch.setattr(qdrant, 'embed_texts', lambda textes: [[1., 0., 0., 0.] for _ in textes])
    monkeypatch.setattr(indexation, 'get_qdrant_service', lambda: service)
    monkeypatch.setattr(memory, 'get_qdrant_service', lambda: service)
    chemin = tmp_path / 'atelier.txt'
    chemin.write_text('La clause zéphyr prévoit un acompte. ' * 40)
    try:
        indexe = await files.index_payload(path=str(chemin))
        assert indexe.chunk_count > 0
        hits = await service.async_search('zéphyr', memory_types=['file'])
        assert hits and hits[0]['entity_id'] == indexe.id
        rep = await client.post('/api/memory/search', json={'query': 'zéphyr', 'entity_types': ['file']})
        assert rep.status_code == 200
        assert [r['id'] for r in rep.json()['results']] == [indexe.id]
        assert 'zéphyr' in rep.json()['results'][0]['content']
        rep = await client.post('/api/memory/search', json={'query': 'zéphyr', 'entity_types': ['contact']})
        assert rep.json()['total'] == 0
    finally:
        service._client.close()
