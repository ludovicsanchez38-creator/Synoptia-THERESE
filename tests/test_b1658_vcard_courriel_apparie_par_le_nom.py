"""B-1658 : une carte vCard retrouvée par le prénom et le nom perdait son
courriel sans rien dire.

L'import commun de B-1381 apparie d'abord par courriel, puis par prénom et
nom. Mais `email` ne figurait pas dans les champs repris : une fiche « Élodie
Martin » sans courriel restait sans courriel après l'import d'une carte qui
en portait un, et le bilan n'en disait rien.

Règle : un courriel absent de la fiche est repris ; un courriel différent
n'écrase pas celui de la fiche (il peut s'agir d'une autre adresse ou d'une
autre personne) et le bilan le signale.

B-1706 : deux fiches « Élodie Martin » sans courriel. L'appariement par le
nom prenait la première (`limit(1)` sans ordre) et posait le courriel de la
carte sur l'une des deux, au hasard. Si plusieurs fiches portent ce prénom
et ce nom, on n'en modifie aucune, on n'en crée pas une de plus, et le bilan
le dit.
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


# Courriel, téléphone et société : si l'import choisit une fiche au hasard,
# ces trois champs bougent. Aucun ne doit bouger.
CARTE_HOMONYME = (
    "BEGIN:VCARD\r\nVERSION:3.0\r\nN:Martin;Élodie;;;\r\nFN:Élodie Martin\r\n"
    "EMAIL:elodie@exemple.fr\r\nTEL:0600000099\r\nORG:Atelier Nord\r\nEND:VCARD\r\n"
).encode()


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ROUTES)
async def test_un_nom_ambigu_ne_modifie_aucune_fiche(client, route):
    fiches = []
    for telephone, societe in (("0611111111", "Atelier Sud"), ("0622222222", "Atelier Est")):
        cree = await client.post(
            "/api/memory/contacts",
            json={"first_name": "Élodie", "last_name": "Martin", "phone": telephone, "company": societe},
        )
        assert cree.status_code == 200, cree.text
        fiches.append(cree.json())

    reponse = await client.post(
        route, files={"file": ("carte.vcf", CARTE_HOMONYME, "text/vcard")}
    )
    assert reponse.status_code == 200, reponse.text
    corps = reponse.json()

    for avant in fiches:
        fiche = await _fiche(client, avant["id"])
        assert fiche["email"] is None, fiche
        assert fiche["phone"] == avant["phone"], fiche
        assert fiche["company"] == avant["company"], fiche
        assert fiche["updated_at"] == avant["updated_at"], fiche

    homonymes = [
        fiche for fiche in (await client.get("/api/memory/contacts")).json()
        if fiche["first_name"] == "Élodie" and fiche["last_name"] == "Martin"
    ]
    assert len(homonymes) == 2, homonymes
    assert corps["created"] == 0, corps
    assert corps["updated"] == 0, corps
    assert corps.get("non_rapprochees") == 1, corps
    assert "1 carte non rapprochée : plusieurs fiches portent ce nom" in corps["message"], corps
