"""B-1658 : une carte vCard retrouvée par le prénom et le nom perdait son
courriel sans rien dire.

L'import commun de B-1381 apparie d'abord par courriel, puis par prénom et
nom. Mais `email` ne figurait pas dans les champs repris : une fiche « Élodie
Martin » sans courriel restait sans courriel après l'import d'une carte qui
en portait un, et le bilan n'en disait rien.

Règle : un courriel absent de la fiche est repris ; un courriel différent
n'écrase pas celui de la fiche (il peut s'agir d'une autre adresse ou d'une
autre personne) et le bilan le signale.
"""

from __future__ import annotations

import pytest

ROUTES = ["/api/crm/import/vcf", "/api/memory/contacts/import"]

CARTE = (
    "BEGIN:VCARD\r\nVERSION:3.0\r\nN:Martin;Élodie;;;\r\nFN:Élodie Martin\r\n"
    "EMAIL:elodie@exemple.fr\r\nEND:VCARD\r\n"
).encode()


async def _importer(client, route: str):
    return await client.post(route, files={"file": ("carte.vcf", CARTE, "text/vcard")})


async def _fiche(client, identifiant: str) -> dict:
    return (await client.get(f"/api/memory/contacts/{identifiant}")).json()


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ROUTES)
async def test_le_courriel_absent_de_la_fiche_est_repris(client, route):
    cree = await client.post("/api/memory/contacts", json={"first_name": "Élodie", "last_name": "Martin"})
    assert cree.status_code == 200, cree.text

    corps = (await _importer(client, route)).json()

    assert corps["updated"] == 1, corps
    assert (await _fiche(client, cree.json()["id"]))["email"] == "elodie@exemple.fr"


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ROUTES)
async def test_un_courriel_different_est_garde_et_signale(client, route):
    cree = await client.post(
        "/api/memory/contacts",
        json={"first_name": "Élodie", "last_name": "Martin", "email": "e.martin@atelier.fr"},
    )
    assert cree.status_code == 200, cree.text

    corps = (await _importer(client, route)).json()

    assert (await _fiche(client, cree.json()["id"]))["email"] == "e.martin@atelier.fr"
    assert "courriel" in corps["message"], corps
