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


def _poser_un_point(service) -> None:
    from qdrant_client.models import PointStruct

    service.client.upsert(
        collection_name=settings.qdrant_collection,
        points=[PointStruct(id=1, vector=[0.1] * settings.embedding_dimensions,
                            payload={"entity_id": "contact-x", "type": "contact"})],
    )
    assert service.client.count(settings.qdrant_collection).count == 1


@pytest.mark.asyncio
async def test_la_collection_existe_toujours_apres_la_purge(client, vrai_qdrant):
    assert settings.qdrant_collection in _collections(vrai_qdrant)
    # B-1186 : sans point posé, le compte final valait 0 même quand la purge
    # n'effaçait plus rien ; le test ne prouvait pas l'effacement.
    _poser_un_point(vrai_qdrant)

    resp = await client.delete("/api/data/all?confirm=true")

    assert resp.status_code == 200, resp.text
    assert settings.qdrant_collection in _collections(vrai_qdrant), "la purge laisse le service sur une collection absente"
    assert vrai_qdrant.client.count(settings.qdrant_collection).count == 0


@pytest.mark.asyncio
async def test_les_vecteurs_partent_meme_si_la_collection_ne_peut_pas_etre_supprimee(
    client, vrai_qdrant, monkeypatch
):
    """B-1199 : sous Windows, supprimer la collection du stockage local échoue
    (fichier verrouillé) ; l'exception était avalée et les vecteurs restaient,
    alors que la réponse annonçait « toutes mes données » effacées."""
    _poser_un_point(vrai_qdrant)

    def verrouille(*_a, **_k):
        raise PermissionError("[WinError 32] fichier utilisé par un autre processus")

    monkeypatch.setattr(vrai_qdrant.client, "delete_collection", verrouille)

    resp = await client.delete("/api/data/all?confirm=true")

    assert resp.status_code == 200, resp.text
    assert vrai_qdrant.client.count(settings.qdrant_collection).count == 0


@pytest.mark.asyncio
async def test_les_vecteurs_partent_meme_si_la_suppression_de_collection_n_agit_pas(
    client, vrai_qdrant, monkeypatch
):
    """B-1199, second volet (CI Windows run 36070072718) : la suppression de la
    collection ne lève rien mais laisse le stockage local en place ; la
    collection recréée rechargeait les anciens points."""
    _poser_un_point(vrai_qdrant)
    monkeypatch.setattr(vrai_qdrant.client, "delete_collection", lambda *_a, **_k: True)

    resp = await client.delete("/api/data/all?confirm=true")

    assert resp.status_code == 200, resp.text
    assert vrai_qdrant.client.count(settings.qdrant_collection).count == 0


@pytest.mark.asyncio
async def test_la_purge_recree_la_collection_meme_si_elle_manquait(client, vrai_qdrant):
    """B-1224 : régression de B-1199 (revue du diff, n° 4). Retirer les points
    d'une collection absente lève ValueError ; l'exception sautait la
    recréation et le service restait sur une collection absente (B-1130)."""
    vrai_qdrant.client.delete_collection(settings.qdrant_collection)
    assert settings.qdrant_collection not in _collections(vrai_qdrant)

    resp = await client.delete("/api/data/all?confirm=true")

    assert resp.status_code == 200, resp.text
    assert settings.qdrant_collection in _collections(vrai_qdrant)
