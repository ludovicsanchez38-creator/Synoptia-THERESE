"""B-1113 : une consignation en échec ne laisse aucun vecteur interrogeable.

Campagne du 22/10 (02h36) : « Indexed 1 chunks » puis `database is locked` en
consignant le résultat. L'API a répondu 500, la fiche est restée à 0 fragment,
et les vecteurs, jamais retirés, ont nourri la recherche et le chat des
exécutions suivantes.
"""
import pytest
from app.services import indexation
from sqlalchemy.exc import OperationalError


class QdrantFactice:
    def __init__(self):
        self.ajouts: list[str] = []
        self.retraits: list[str] = []

    async def async_add_memories(self, items):
        self.ajouts.extend(item["entity_id"] for item in items)

    async def async_delete_by_entity(self, entity_id):
        self.retraits.append(entity_id)
        return 1


def _verrouillee(consignations):
    async def consigner(file_id, chunk_count, indexed_at, figer_perimetre=False):
        consignations.append(chunk_count)
        if chunk_count:
            raise OperationalError("UPDATE file_metadata", {}, Exception("database is locked"))
    return consigner


@pytest.mark.parametrize("reindexation", [False, True])
async def test_consignation_en_echec_retire_les_vecteurs(monkeypatch, reindexation):
    qdrant, consignations = QdrantFactice(), []
    monkeypatch.setattr(indexation, "get_qdrant_service", lambda: qdrant)
    monkeypatch.setattr(indexation, "_consigner_resultat", _verrouillee(consignations))
    monkeypatch.setattr(indexation, "_DELAIS_CONSIGNATION", (0, 0))

    with pytest.raises(OperationalError):
        await indexation._ecrire_et_consigner(
            "f1", "procedure-finition.md", [{"entity_id": "f1", "text": "chiffon"}], reindexation, False)

    assert qdrant.ajouts == ["f1"]
    assert qdrant.retraits[-1] == "f1"
    # Trois essais du résultat, puis la base ne promet plus de fragments.
    assert consignations == [1, 1, 1, 0]


async def test_verrou_passager_garde_l_indexation(monkeypatch):
    # Astra c19e v1 (réserve) : un verrou court ne doit pas coûter l'indexation.
    qdrant, consignations = QdrantFactice(), []

    async def consigner(file_id, chunk_count, indexed_at, figer_perimetre=False):
        consignations.append(chunk_count)
        if len(consignations) == 1:
            raise OperationalError("UPDATE file_metadata", {}, Exception("database is locked"))

    monkeypatch.setattr(indexation, "get_qdrant_service", lambda: qdrant)
    monkeypatch.setattr(indexation, "_consigner_resultat", consigner)
    monkeypatch.setattr(indexation, "_DELAIS_CONSIGNATION", (0, 0))

    assert (await indexation._ecrire_et_consigner(
        "f1", "doc.md", [{"entity_id": "f1", "text": "x"}], True, False))[0] == 1
    assert consignations == [1, 1]
    assert qdrant.retraits == ["f1"]  # le seul retrait est celui de la réindexation


async def test_consignation_reussie_garde_les_vecteurs(monkeypatch):
    qdrant, consignations = QdrantFactice(), []

    async def consigner(file_id, chunk_count, indexed_at, figer_perimetre=False):
        consignations.append(chunk_count)

    monkeypatch.setattr(indexation, "get_qdrant_service", lambda: qdrant)
    monkeypatch.setattr(indexation, "_consigner_resultat", consigner)

    assert (await indexation._ecrire_et_consigner(
        "f1", "doc.md", [{"entity_id": "f1", "text": "x"}], False, False))[0] == 1
    assert qdrant.retraits == []
    assert consignations == [1]


async def test_fichier_supprime_pendant_l_indexation_reste_un_409(monkeypatch):
    from fastapi import HTTPException

    qdrant = QdrantFactice()

    async def consigner(file_id, chunk_count, indexed_at, figer_perimetre=False):
        await qdrant.async_delete_by_entity(file_id)
        raise HTTPException(status_code=409, detail="Le fichier a été supprimé pendant son indexation.")

    monkeypatch.setattr(indexation, "get_qdrant_service", lambda: qdrant)
    monkeypatch.setattr(indexation, "_consigner_resultat", consigner)

    with pytest.raises(HTTPException) as erreur:
        await indexation._ecrire_et_consigner("f1", "doc.md", [{"entity_id": "f1", "text": "x"}], False, False)
    assert erreur.value.status_code == 409
    assert qdrant.retraits == ["f1"]
