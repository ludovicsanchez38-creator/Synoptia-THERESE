"""B-1391 (persona Zoé, cycle 13, haute) : deux onglets sur la même fiche, le
second enregistrement effaçait le premier sans rien dire.

Le formulaire renvoie tous ses champs, périmés compris : l'onglet A, ouvert
avant que l'onglet B ne change l'entreprise, remettait l'ancienne entreprise en
enregistrant sa note. Même risque quand Thérèse modifie la fiche depuis le chat
pendant qu'elle est ouverte. Le formulaire envoie désormais la date de la
version qu'il a lue ; si la fiche a changé depuis, le moteur refuse (409) et
le dit, au lieu d'écraser.
"""

import pytest


async def _creer(client) -> dict:
    reponse = await client.post("/api/memory/contacts", json={
        "first_name": "Zoé", "last_name": "Doubleclic", "company": "Contradiction SARL",
    })
    assert reponse.status_code in (200, 201), reponse.text
    return reponse.json()


@pytest.mark.asyncio
async def test_une_version_perimee_est_refusee_sans_rien_ecraser(client):
    lue_par_a = await _creer(client)
    b = await client.patch(f"/api/memory/contacts/{lue_par_a['id']}", json={
        "company": "Version onglet B", "version_lue": lue_par_a["updated_at"],
    })
    assert b.status_code == 200, b.text

    a = await client.patch(f"/api/memory/contacts/{lue_par_a['id']}", json={
        "company": "Contradiction SARL", "notes": "Note saisie dans l'onglet A",
        "version_lue": lue_par_a["updated_at"],
    })
    assert a.status_code == 409, a.text
    corps = a.json()
    # L'interface lit `detail`, puis `message` (services/api/core.ts).
    assert "modifiée ailleurs" in (corps.get("detail") or corps.get("message") or ""), corps

    relue = (await client.get(f"/api/memory/contacts/{lue_par_a['id']}")).json()
    assert relue["company"] == "Version onglet B"
    assert not relue.get("notes")


@pytest.mark.asyncio
async def test_la_version_courante_passe(client):
    lue = await _creer(client)
    reponse = await client.patch(f"/api/memory/contacts/{lue['id']}", json={
        "notes": "À jour", "version_lue": lue["updated_at"],
    })
    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["notes"] == "À jour"


@pytest.mark.asyncio
async def test_sans_version_le_comportement_reste_le_meme(client):
    lue = await _creer(client)
    reponse = await client.patch(f"/api/memory/contacts/{lue['id']}", json={"notes": "Par le chat"})
    assert reponse.status_code == 200, reponse.text
