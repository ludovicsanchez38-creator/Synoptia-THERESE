"""Import JSON des contacts (US-BAK-02) : un champ « tags » vrai mais qui n'est
pas une liste de textes (« vip », un nombre, un objet) était stocké tel quel.
La fiche relue ne passait plus le schéma de réponse (tags: list[str]) : la
liste des contacts tombait en erreur. Lecteur V, cycle 13."""

import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize("etiquettes", [42, {"a": 1}, [3, None], " , "])
async def test_des_etiquettes_hors_forme_ne_cassent_pas_la_liste(client, etiquettes):
    resp = await client.post(
        "/api/data/import/contacts",
        json={"contacts": [{"id": "c-tags", "first_name": "Marie", "tags": etiquettes}]},
    )
    assert resp.status_code == 200, resp.text
    liste = await client.get("/api/memory/contacts")
    assert liste.status_code == 200, liste.text
    fiche = next(c for c in liste.json() if c["id"] == "c-tags")
    assert fiche.get("tags") in (None, []), fiche


@pytest.mark.asyncio
async def test_seuls_les_textes_d_une_liste_sont_gardes(client):
    resp = await client.post(
        "/api/data/import/contacts",
        json={"contacts": [{"id": "c-ok", "first_name": "Léa", "tags": ["vip", 3, "btp"]}]},
    )
    assert resp.status_code == 200, resp.text
    fiche = next(c for c in (await client.get("/api/memory/contacts")).json() if c["id"] == "c-ok")
    assert fiche["tags"] == ["vip", "btp"], fiche
