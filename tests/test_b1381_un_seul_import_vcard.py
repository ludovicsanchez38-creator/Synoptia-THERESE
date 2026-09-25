"""B-1381 (persona Nathalie, cycle 13) : deux boutons « Importer (.vcf) », au
Pipeline et dans Contacts, appelaient deux routes aux règles différentes.

- doublon : e-mail seul au Pipeline (`/api/crm/import/vcf`), e-mail puis
  prénom et nom dans Contacts (`/api/memory/contacts/import`) ;
- messages : accentués d'un côté, « etre », « trouve » de l'autre ;
- nathalie-04 : réimporter le même fichier annonçait « 3 mis à jour » pour des
  fiches que rien n'avait changé.

Les deux routes délèguent désormais au même import : mêmes règles, mêmes
messages, et une fiche identique est dite « déjà à jour ».
"""

from __future__ import annotations

import pytest

ROUTES = ["/api/crm/import/vcf", "/api/memory/contacts/import"]

CARTES = (
    "BEGIN:VCARD\r\nVERSION:3.0\r\nN:Martin;Élodie;;;\r\nFN:Élodie Martin\r\n"
    "EMAIL:elodie@exemple.fr\r\nORG:Atelier Martin\r\nEND:VCARD\r\n"
    "BEGIN:VCARD\r\nVERSION:3.0\r\nN:Benali;Karim;;;\r\nFN:Karim Benali\r\n"
    "EMAIL:karim@exemple.fr\r\nEND:VCARD\r\n"
).encode()


async def _importer(client, route: str, contenu: bytes = CARTES, nom: str = "prospects.vcf"):
    return await client.post(route, files={"file": (nom, contenu, "text/vcard")})


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ROUTES)
async def test_un_homonyme_sans_e_mail_est_le_meme_contact_sur_les_deux_routes(client, route):
    cree = await client.post("/api/memory/contacts", json={"first_name": "Élodie", "last_name": "Martin"})
    assert cree.status_code == 200, cree.text

    resp = await _importer(client, route)

    assert resp.status_code == 200, resp.text
    corps = resp.json()
    assert (corps["created"], corps["updated"]) == (1, 1), corps
    fiches = (await client.get("/api/memory/contacts")).json()
    assert sum(1 for f in fiches if f["first_name"] == "Élodie") == 1, "doublon créé"


@pytest.mark.asyncio
async def test_les_deux_routes_rendent_le_meme_bilan(client):
    bilans = []
    for route in ROUTES:
        # Tables neuves entre les deux imports : même état de départ.
        for fiche in (await client.get("/api/memory/contacts")).json():
            await client.delete(f"/api/memory/contacts/{fiche['id']}")
        bilans.append((await _importer(client, route)).json())

    assert bilans[0] == bilans[1]
    assert bilans[0]["message"] == "2 contact(s) créé(s)"


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ROUTES)
async def test_un_fichier_d_un_autre_format_est_refuse_avec_accents(client, route):
    resp = await _importer(client, route, b"nom;email\nPaul;paul@exemple.fr\n", "prospects.csv")

    assert resp.status_code == 400
    corps = resp.json()
    assert (corps.get("detail") or corps.get("message")) == "Le fichier doit être au format .vcf"


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ROUTES)
async def test_reimporter_le_meme_fichier_ne_dit_pas_mis_a_jour(client, route):
    assert (await _importer(client, route)).status_code == 200

    corps = (await _importer(client, route)).json()

    assert (corps["created"], corps["updated"]) == (0, 0), corps
    assert corps["message"] == "0 contact(s) créé(s), 2 déjà à jour"


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ROUTES)
async def test_un_fichier_sans_carte_le_dit_avec_accents(client, route):
    corps = (await _importer(client, route, b"", "vide.vcf")).json()
    assert corps["message"] == "Aucun contact trouvé dans le fichier"
