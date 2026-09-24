"""B-1130 (cycle 12, réparé au cycle 13) : après « Effacer toutes mes
données », la mémoire vectorielle repart d'une collection vide.

La purge supprimait la collection Qdrant, mais le service restait initialisé
sur elle : jusqu'au redémarrage, chaque ajout en mémoire visait une
collection absente et l'embedding (best-effort) se perdait en silence.
Qdrant est simulé dans la suite ; ce test pose un vrai service sur un
dossier jetable.
"""

import pytest
from app.config import settings
from app.services import qdrant as module_qdrant


@pytest.fixture
def vrai_qdrant(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "qdrant_path", str(tmp_path / "qdrant"))
    service = module_qdrant.QdrantService()
    _ = service.client
    monkeypatch.setattr(module_qdrant, "_qdrant_service", service)
    # conftest remplace aussi la fonction par une lambda qui rend le simulacre.
    monkeypatch.setattr(module_qdrant, "get_qdrant_service", lambda: service)
    yield service
    service.close()


def _collections(service) -> set[str]:
    return {c.name for c in service.client.get_collections().collections}


@pytest.mark.asyncio
async def test_la_collection_existe_toujours_apres_la_purge(client, vrai_qdrant):
    assert settings.qdrant_collection in _collections(vrai_qdrant)

    resp = await client.delete("/api/data/all?confirm=true")

    assert resp.status_code == 200, resp.text
    assert settings.qdrant_collection in _collections(vrai_qdrant), "la purge laisse le service sur une collection absente"
    assert vrai_qdrant.client.count(settings.qdrant_collection).count == 0
