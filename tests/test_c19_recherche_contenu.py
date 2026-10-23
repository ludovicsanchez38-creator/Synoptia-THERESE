"""B-1040 : un mot exact dans l'index prime sur les noms approchants."""
from unittest.mock import AsyncMock

import pytest
from app.config import settings
from app.models.entities import Contact, FileMetadata
from app.models.schemas import MemorySearchRequest
from app.routers import memory
from app.services.qdrant import QdrantService
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


@pytest.mark.parametrize("mot", ["Lannion", "tarifs", "tellanmoine"])
@pytest.mark.parametrize("semantique", [True, False])
async def test_mot_exact_prime_sur_contact(db_session, monkeypatch, mot, semantique):
    fichier = FileMetadata(name="procedure.md", path="/documents/procedure.md", extension=".md", size=42)
    voisin = Contact(first_name="Nom voisin")
    db_session.add_all([fichier, voisin])
    await db_session.commit()
    qdrant = object.__new__(QdrantService)
    qdrant._client = QdrantClient(location=":memory:")
    qdrant._client.create_collection(settings.qdrant_collection, vectors_config=VectorParams(size=1, distance=Distance.COSINE))
    qdrant._client.upsert(settings.qdrant_collection, points=[
        PointStruct(id=i, vector=[1.0], payload={"type": "file", "entity_id": fichier.id,
                    "text": texte})
        for i, texte in enumerate([f"Texte préliminaire {mot}suffixe", f"Consigne : {mot.upper()}.", f"Encore {mot}."])
    ])
    qdrant.async_search = AsyncMock(return_value=[{"type": "contact", "entity_id": voisin.id, "score": 0.99}])
    monkeypatch.setattr(memory, "get_qdrant_service", lambda: qdrant)
    try:
        reponse = await memory.search_memory(MemorySearchRequest(query=mot, limit=1, include_semantic=semantique), db_session)
        assert reponse.results[0].id == fichier.id
        assert mot.lower() in reponse.results[0].content.lower()
        fichiers = await memory.search_memory(MemorySearchRequest(query=mot, entity_types=["file"]), db_session)
        assert [r.id for r in fichiers.results] == [fichier.id]
    finally:
        qdrant._client.close()


@pytest.mark.parametrize("mot", ["Quimper", "ponçage", "ébénisterie", "Trégastel", "vernissage",
                                  "Keravel", "délais", "Mélèze", "facturation", "assemblage"])
async def test_rejeu_mots(db_session, monkeypatch, mot):
    await test_mot_exact_prime_sur_contact(db_session, monkeypatch, mot, False)


def test_recherche_litterale_pagine_sans_sous_mot():
    qdrant = object.__new__(QdrantService)
    qdrant._client = QdrantClient(location=":memory:")
    qdrant._client.create_collection(settings.qdrant_collection, vectors_config=VectorParams(size=1, distance=Distance.COSINE))
    try:
        qdrant._client.upsert(settings.qdrant_collection, points=[
            PointStruct(id=i, vector=[1.0], payload={"type": "file", "entity_id": str(i),
                        "text": "tarifs" if i == 300 else "tarifsuffixe"}) for i in range(301)
        ])
        assert qdrant.rechercher_contenu_fichiers("tarifs") == [{"entity_id": "300", "text": "tarifs"}]
        assert qdrant.rechercher_contenu_fichiers("   ") == []
    finally:
        qdrant._client.close()


@pytest.mark.parametrize("texte,requete,attendu", [
    ("e\u0301be\u0301nisterie", "ébénisterie", True),
    ("ébénisterie", "e\u0301be\u0301nisterie", True),
    ("客户在北京工作。", "北京", True),
    ("tarifs", "tarif", False),
    ("STRASSE", "Straße", True),
])
def test_normalisation_et_frontieres(texte, requete, attendu):
    qdrant = object.__new__(QdrantService)
    qdrant._client = QdrantClient(location=":memory:")
    qdrant._client.create_collection(settings.qdrant_collection, vectors_config=VectorParams(size=1, distance=Distance.COSINE))
    try:
        qdrant._client.upsert(settings.qdrant_collection, points=[
            PointStruct(id=0, vector=[1.0], payload={"type": "file", "entity_id": "fiche", "text": texte})
        ])
        assert bool(qdrant.rechercher_contenu_fichiers(requete)) == attendu
    finally:
        qdrant._client.close()


def test_recherche_absente_16384_fragments_en_moins_d_une_seconde():
    from time import perf_counter
    from unittest.mock import patch

    qdrant = object.__new__(QdrantService)
    qdrant._client = QdrantClient(location=":memory:")
    qdrant._client.create_collection(settings.qdrant_collection, vectors_config=VectorParams(size=1, distance=Distance.COSINE))
    try:
        qdrant._client.upsert(settings.qdrant_collection, points=[
            PointStruct(id=i, vector=[1.0], payload={"type": "file", "entity_id": "document", "text": "Fragment ordinaire."})
            for i in range(16384)
        ])
        with patch.object(qdrant._client, "scroll", wraps=qdrant._client.scroll) as parcours:
            debut = perf_counter()
            assert qdrant.rechercher_contenu_fichiers("absent-du-corpus") == []
            duree = perf_counter() - debut
        print(f"16384 fragments, absent : {duree:.6f} s ; scroll={parcours.call_count}")
        assert duree < 1
        assert parcours.call_count == 1
    finally:
        qdrant._client.close()
