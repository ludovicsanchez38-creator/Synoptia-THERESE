"""La recherche littérale ne doit jamais traverser les dossiers clients."""

from unittest.mock import AsyncMock

import pytest
from app.config import settings
from app.models.entities import Conversation, FileMetadata
from app.routers import memory
from app.services.qdrant import QdrantService
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


@pytest.fixture
def index():
    service = object.__new__(QdrantService)
    service._client = QdrantClient(location=":memory:")
    service._initialized = True
    service._client.create_collection(
        settings.qdrant_collection, vectors_config=VectorParams(size=1, distance=Distance.COSINE)
    )
    yield service
    service._client.close()


def test_index_restreint_les_fragments_au_dossier_et_a_la_conversation(index):
    index._client.upsert(settings.qdrant_collection, points=[
        PointStruct(id=i, vector=[1.0], payload={
            "type": "file", "entity_id": nom, "text": f"zéphyr {nom}",
            "scope": scope, "scope_id": identifiant,
        })
        for i, (nom, scope, identifiant) in enumerate([
            ("general", "global", None), ("client-a", "project", "a"),
            ("client-b", "project", "b"), ("conversation-a", "conversation", "ca"),
            ("conversation-b", "conversation", "cb"), ("orphelin", None, None),
        ])
    ])
    assert {r["entity_id"] for r in index.rechercher_contenu_fichiers("zéphyr")} == {"general"}
    resultats = index.rechercher_contenu_fichiers(
        "zéphyr", scope="project", scope_id="a", conversation_id="ca"
    )
    assert {r["entity_id"] for r in resultats} == {"general", "client-a", "conversation-a"}


@pytest.mark.asyncio
@pytest.mark.parametrize("semantique", [False, True])
async def test_route_ferme_tous_les_chemins_sans_perimetre(
    client, db_session, monkeypatch, index, semantique
):
    general = FileMetadata(path="/general/zéphyr.txt", name="zéphyr.txt", extension=".txt",
                           size=10, scope="global")
    prive = FileMetadata(path="/client-b/zéphyr.txt", name="zéphyr.txt", extension=".txt",
                         size=10, scope="project", scope_id="b")
    db_session.add_all([general, prive])
    await db_session.commit()
    index._client.upsert(settings.qdrant_collection, points=[
        PointStruct(id=i, vector=[1.0], payload={"type": "file", "entity_id": f.id,
                    "text": texte, "scope": f.scope, "scope_id": f.scope_id})
        for i, (f, texte) in enumerate([(general, "zéphyr général"), (prive, "zéphyr confidentiel")])
    ])
    index.async_search = AsyncMock(return_value=[
        {"entity_id": prive.id, "type": "file", "text": "zéphyr confidentiel", "score": 0.99}
    ])
    monkeypatch.setattr(memory, "get_qdrant_service", lambda: index)
    reponse = await client.post("/api/memory/search", json={
        "query": "zéphyr", "entity_types": ["file"], "include_semantic": semantique,
    })
    assert reponse.status_code == 200
    assert {r["id"] for r in reponse.json()["results"]} == {general.id}
    assert "confidentiel" not in reponse.text


@pytest.mark.asyncio
async def test_route_recherche_dans_le_dossier_demande_sans_ouvrir_un_autre(
    client, db_session, monkeypatch, index
):
    fichiers = [FileMetadata(path=f"/{p}/note.txt", name="note.txt", extension=".txt", size=10,
                            scope="project", scope_id=p) for p in ("a", "b")]
    db_session.add_all(fichiers)
    await db_session.commit()
    index._client.upsert(settings.qdrant_collection, points=[
        PointStruct(id=i, vector=[1.0], payload={"type": "file", "entity_id": f.id,
                    "text": f"zéphyr {f.scope_id}", "scope": f.scope, "scope_id": f.scope_id})
        for i, f in enumerate(fichiers)
    ])
    monkeypatch.setattr(memory, "get_qdrant_service", lambda: index)
    reponse = await client.post("/api/memory/search", json={
        "query": "zéphyr", "entity_types": ["file"], "include_semantic": False,
        "scope": "project", "scope_id": "a",
    })
    assert reponse.status_code == 200
    assert [r["id"] for r in reponse.json()["results"]] == [fichiers[0].id]


@pytest.mark.asyncio
async def test_route_refuse_un_vecteur_perime_et_une_conversation_d_un_autre_dossier(
    client, db_session, monkeypatch, index
):
    conversation = Conversation(id="conv-b", project_id="b")
    fichiers = [
        FileMetadata(path="/b/ancien.txt", name="ancien.txt", extension=".txt", size=10,
                     scope="project", scope_id="b"),
        FileMetadata(path="/b/piece.txt", name="piece.txt", extension=".txt", size=10,
                     scope="conversation", scope_id="conv-b"),
    ]
    db_session.add(conversation)
    db_session.add_all(fichiers)
    await db_session.commit()
    index._client.upsert(settings.qdrant_collection, points=[
        PointStruct(id=0, vector=[1.0], payload={"type": "file", "entity_id": fichiers[0].id,
                    "text": "zéphyr privé", "scope": "global"}),
        PointStruct(id=1, vector=[1.0], payload={"type": "file", "entity_id": fichiers[1].id,
                    "text": "zéphyr privé", "scope": "conversation", "scope_id": "conv-b"}),
    ])
    monkeypatch.setattr(memory, "get_qdrant_service", lambda: index)
    reponse = await client.post("/api/memory/search", json={
        "query": "zéphyr", "entity_types": ["file"], "include_semantic": False,
        "scope": "project", "scope_id": "a", "conversation_id": "conv-b",
    })
    assert reponse.status_code == 200
    assert reponse.json()["results"] == []
