"""B-036 : un identifiant d'image ne désigne que lui-même.

`get_image` interpolait l'identifiant reçu de l'URL dans un motif glob
(`*_{image_id}.*`). Un identifiant portant des métacaractères sélectionnait
donc des fichiers que l'appelant n'avait pas nommés : `DELETE /api/images/*`
supprimait une image sans l'avoir désignée, et `GET /api/images/download/prive`
rendait le contenu d'un fichier hors nomenclature.
"""

import pytest
from app.services.image_generator import ImageGeneratorService
from httpx import AsyncClient

IMAGE_A = "therese_20260101_000001_aaaa1111.png"
IMAGE_B = "therese_20260101_000002_bbbb2222.png"
TRESOR = "tresor_prive.png"


@pytest.fixture
def dossier_images(tmp_path, monkeypatch):
    """Trois fichiers dans un dossier d'images jetable."""
    dossier = tmp_path / "images"
    dossier.mkdir()
    (dossier / IMAGE_A).write_bytes(b"AAA")
    (dossier / IMAGE_B).write_bytes(b"BBB")
    (dossier / TRESOR).write_bytes(b"SECRET")

    service = ImageGeneratorService(output_dir=dossier)
    monkeypatch.setattr("app.routers.images.get_image_service", lambda: service)
    return dossier


def _restants(dossier) -> set[str]:
    return {p.name for p in dossier.iterdir()}


@pytest.mark.asyncio
async def test_identifiant_image_refuse_les_metacaracteres(
    client: AsyncClient, dossier_images
):
    """Un joker ne supprime ni ne rend aucun fichier."""
    reponse = await client.delete("/api/images/%2A")
    assert reponse.status_code == 404, reponse.text
    assert _restants(dossier_images) == {IMAGE_A, IMAGE_B, TRESOR}, (
        "un identifiant portant un métacaractère a touché des fichiers "
        "que l'appelant n'a pas nommés"
    )

    reponse = await client.get("/api/images/download/%2A")
    assert reponse.status_code == 404
    assert b"SECRET" not in reponse.content


@pytest.mark.asyncio
async def test_identifiant_image_ne_designe_que_lui_meme(
    client: AsyncClient, dossier_images
):
    """Un identifiant partiel ne résout pas un fichier dont le nom le contient."""
    reponse = await client.get("/api/images/download/prive")
    assert reponse.status_code == 404, (
        "un fragment de nom de fichier a été accepté comme identifiant"
    )
    assert b"SECRET" not in reponse.content

    reponse = await client.delete("/api/images/prive")
    assert reponse.status_code == 404
    assert TRESOR in _restants(dossier_images)


@pytest.mark.asyncio
async def test_identifiant_legitime_fonctionne_toujours(
    client: AsyncClient, dossier_images
):
    """Contrôle positif : une image réellement nommée reste lisible et supprimable."""
    reponse = await client.get("/api/images/download/aaaa1111")
    assert reponse.status_code == 200, reponse.text
    assert reponse.content == b"AAA"

    reponse = await client.delete("/api/images/bbbb2222")
    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["deleted"] is True
    assert _restants(dossier_images) == {IMAGE_A, TRESOR}
