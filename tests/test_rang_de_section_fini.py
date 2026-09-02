"""B-184 (RB2-014) — ni l'infini ni NaN ne sont des rangs de section.

`order` est déclaré `float` nu dans les trois schémas qui le portent. Pydantic
accepte donc « Infinity » et « NaN » en mode lax :

- « Infinity » passe en HTTP 200 et la relecture rend `order: null`, sur un
  champ que `SectionResponse` déclare `number` ET requis. La clé de tri de la
  trame est perdue ;
- « NaN » est écrit NULL par le pilote sur une colonne NOT NULL : 500
  « une erreur inattendue s'est produite, réessaie », alors qu'aucun essai ne
  peut aboutir.
"""

import pytest
from httpx import AsyncClient


async def _document_avec_deux_sections(client: AsyncClient) -> tuple[str, list[dict]]:
    doc = await client.post(
        "/api/documents", json={"title": "Trame des rangs", "brief": "Deux sections"}
    )
    assert doc.status_code == 200, doc.text
    document_id = doc.json()["id"]

    sections = []
    for rang, titre in ((1.0, "Section A"), (2.0, "Section B")):
        reponse = await client.post(
            f"/api/documents/{document_id}/sections",
            json={"title": titre, "brief": "", "order": rang, "depth": 0},
        )
        assert reponse.status_code == 200, reponse.text
        sections.append(reponse.json())

    return document_id, sections


class TestB184RangDeSectionFini:
    @pytest.mark.asyncio
    async def test_rang_ordinaire_toujours_accepte(self, client: AsyncClient) -> None:
        """Contrôle de l'instrument : un rang fini reste écrit et relu."""
        document_id, sections = await _document_avec_deux_sections(client)

        reponse = await client.patch(
            f"/api/documents/sections/{sections[1]['id']}", json={"order": 3.5}
        )
        assert reponse.status_code == 200, reponse.text
        assert reponse.json()["order"] == 3.5

        relu = await client.get(f"/api/documents/{document_id}")
        rangs = {s["title"]: s["order"] for s in relu.json()["sections"]}
        assert rangs == {"Section A": 1.0, "Section B": 3.5}

    @pytest.mark.asyncio
    async def test_patch_infini_refuse(self, client: AsyncClient) -> None:
        document_id, sections = await _document_avec_deux_sections(client)

        reponse = await client.patch(
            f"/api/documents/sections/{sections[1]['id']}", json={"order": "Infinity"}
        )

        assert reponse.status_code == 422, (
            f"Infinity accepte : {reponse.status_code} -> {reponse.text[:200]}"
        )
        assert "order" in reponse.text

        # Et la trame n'a pas bougé : personne n'a perdu sa clé de tri.
        relu = await client.get(f"/api/documents/{document_id}")
        rangs = [(s["title"], s["order"]) for s in relu.json()["sections"]]
        assert rangs == [("Section A", 1.0), ("Section B", 2.0)], rangs

    @pytest.mark.asyncio
    async def test_patch_nan_refuse_sans_500(self, client: AsyncClient) -> None:
        _, sections = await _document_avec_deux_sections(client)

        reponse = await client.patch(
            f"/api/documents/sections/{sections[1]['id']}", json={"order": "NaN"}
        )

        assert reponse.status_code == 422, (
            f"NaN rend {reponse.status_code} -> {reponse.text[:200]}"
        )

    @pytest.mark.asyncio
    async def test_creation_avec_rang_non_fini_refusee(self, client: AsyncClient) -> None:
        document_id, _ = await _document_avec_deux_sections(client)

        for valeur in ("NaN", "Infinity", "-Infinity"):
            reponse = await client.post(
                f"/api/documents/{document_id}/sections",
                json={"title": "Section fantome", "brief": "", "order": valeur},
            )
            assert reponse.status_code == 422, (
                f"order={valeur} a la creation : {reponse.status_code} -> {reponse.text[:200]}"
            )

    @pytest.mark.asyncio
    async def test_reorganisation_avec_rang_non_fini_refusee(self, client: AsyncClient) -> None:
        """Même ligne de cause dans le troisième schéma qui porte `order`."""
        document_id, sections = await _document_avec_deux_sections(client)

        reponse = await client.post(
            f"/api/documents/{document_id}/sections/reorder",
            json={
                "items": [
                    {"id": sections[0]["id"], "order": 1.0, "depth": 0},
                    {"id": sections[1]["id"], "order": "Infinity", "depth": 0},
                ]
            },
        )

        assert reponse.status_code == 422, (
            f"reorder Infinity : {reponse.status_code} -> {reponse.text[:200]}"
        )

        relu = await client.get(f"/api/documents/{document_id}")
        rangs = [(s["title"], s["order"]) for s in relu.json()["sections"]]
        assert rangs == [("Section A", 1.0), ("Section B", 2.0)], rangs
