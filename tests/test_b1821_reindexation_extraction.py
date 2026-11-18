"""B-1821 : une extraction en échec ne doit pas effacer l'index existant."""
from app.models.database import get_session_context
from app.models.entities import FileMetadata
from app.routers import files
from app.services import indexation
from sqlmodel import select


class FauxIndex:
    def __init__(self):
        self.retraits = []
        self.items = []

    async def async_add_memories(self, items):
        self.items.extend(items)

    async def async_delete_by_entity(self, entity_id):
        self.retraits.append(entity_id)
        self.items = [item for item in self.items if item["entity_id"] != entity_id]


async def test_reindexation_apres_extraction_none_preserve_anciens_vecteurs(client, tmp_path, monkeypatch):
    fichier = tmp_path / "rapport.txt"
    fichier.write_text("Texte initial suffisamment clair.", encoding="utf-8")
    faux = FauxIndex()
    monkeypatch.setattr(indexation, "get_qdrant_service", lambda: faux)
    premiere = await files.index_payload(path=str(fichier))
    assert premiere.chunk_count > 0 and faux.items
    anciens = faux.items.copy()
    monkeypatch.setattr(indexation, "extract_text", lambda _path: None)

    reponse = await client.post("/api/files/index", json={"path": str(fichier)})
    assert reponse.status_code == 422
    assert faux.retraits == []
    assert faux.items == anciens
    async with get_session_context() as session:
        ligne = (await session.execute(select(FileMetadata).where(FileMetadata.id == premiere.id))).scalar_one()
        assert ligne.chunk_count == premiere.chunk_count
        assert ligne.indexed_at.replace(tzinfo=None) == premiere.indexed_at.replace(tzinfo=None)
