"""B-1163 (cycle 13) : une fiche contact garde toujours une identité.

B-171 (décision de Ludo, P-005) exige à la création au moins un prénom, un
nom, une société ou une adresse e-mail. Deux portes l'ignoraient : le PATCH,
qui vidait les quatre et rendait 200 avec une fiche vide, et la création CRM
(`POST /api/crm/contacts`), qui acceptait un prénom fait d'espaces.
"""

import pytest

VIDE = {"first_name": "", "last_name": "", "company": "", "email": ""}


async def _contact(client, **champs) -> str:
    corps = {"first_name": "Client", "last_name": "Identite"} | champs
    resp = await client.post("/api/memory/contacts", json=corps)
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_le_patch_ne_vide_pas_toute_l_identite(client):
    contact_id = await _contact(client, email="client@example.invalid")

    resp = await client.patch(f"/api/memory/contacts/{contact_id}", json=VIDE)

    assert resp.status_code == 422, resp.text
    fiche = (await client.get(f"/api/memory/contacts/{contact_id}")).json()
    assert (fiche["first_name"], fiche["email"]) == ("Client", "client@example.invalid")


@pytest.mark.asyncio
async def test_le_patch_peut_vider_un_champ_si_un_autre_reste(client):
    contact_id = await _contact(client, company="Brasserie Lumière")

    resp = await client.patch(f"/api/memory/contacts/{contact_id}", json={"first_name": "", "last_name": ""})

    assert resp.status_code == 200, resp.text
    assert (await client.get(f"/api/memory/contacts/{contact_id}")).json()["company"] == "Brasserie Lumière"


@pytest.mark.asyncio
async def test_la_creation_crm_refuse_une_fiche_sans_identite(client):
    resp = await client.post("/api/crm/contacts", json={"first_name": "   "})
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_la_creation_crm_accepte_une_societe_seule(client):
    resp = await client.post("/api/crm/contacts", json={"first_name": " ", "company": "Brasserie Lumière"})
    assert resp.status_code == 200, resp.text
