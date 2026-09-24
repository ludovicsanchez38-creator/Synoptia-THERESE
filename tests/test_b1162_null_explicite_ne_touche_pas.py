"""B-1162 (cycle 13) : un null explicite sur un champ obligatoire ne fait plus 500.

`ContactUpdate` et `ProjectUpdate` disent « None = ne pas toucher », mais la
route applique `model_dump(exclude_unset=True)` : un `null` ENVOYÉ était
appliqué, et la colonne NOT NULL (scope, stage, score, rgpd_consentement ;
name, status, scope) refusait l'écriture en 500. Le null explicite sur ces
champs vaut désormais « ne pas toucher », comme le promet le schéma.
"""

import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize("champ", ["scope", "stage", "score", "rgpd_consentement"])
async def test_un_null_sur_un_champ_obligatoire_du_contact_ne_touche_rien(client, champ):
    creation = await client.post("/api/memory/contacts", json={"first_name": "Client", "last_name": "Null"})
    assert creation.status_code == 200, creation.text
    avant = creation.json()
    contact_id = avant["id"]
    fiche_avant = (await client.get(f"/api/memory/contacts/{contact_id}")).json()

    resp = await client.patch(f"/api/memory/contacts/{contact_id}", json={champ: None, "notes": "vu"})

    assert resp.status_code == 200, resp.text
    fiche = (await client.get(f"/api/memory/contacts/{contact_id}")).json()
    assert fiche.get(champ) == fiche_avant.get(champ)
    assert fiche["notes"] == "vu"


@pytest.mark.asyncio
@pytest.mark.parametrize("champ", ["name", "status", "scope"])
async def test_un_null_sur_un_champ_obligatoire_du_projet_ne_touche_rien(client, champ):
    creation = await client.post("/api/memory/projects", json={"name": "Projet null"})
    assert creation.status_code == 200, creation.text
    projet_id = creation.json()["id"]
    avant = (await client.get(f"/api/memory/projects/{projet_id}")).json()

    resp = await client.patch(f"/api/memory/projects/{projet_id}", json={champ: None, "notes": "vu"})

    assert resp.status_code == 200, resp.text
    apres = (await client.get(f"/api/memory/projects/{projet_id}")).json()
    assert apres.get(champ) == avant.get(champ)
    assert apres["notes"] == "vu"
