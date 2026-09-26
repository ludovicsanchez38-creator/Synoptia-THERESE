"""B-1503 : supprimer un projet laissait ses contacts rangés dans un projet
disparu.

La suppression détache les conversations, documents et événements du
projet, mais pas les contacts ni les sous-projets qui y étaient rangés
(scope « project »). Ils restaient cloisonnés sur un identifiant mort :
invisibles pour l'assistante dans toute conversation, et leur vecteur
effacé avec ceux du projet.
"""

import pytest


@pytest.mark.asyncio
async def test_les_contacts_et_sous_projets_du_projet_repassent_au_general(client):
    from app.models import database as db_module
    from app.models.entities import Contact, Project

    projet = await client.post("/api/memory/projects", json={"name": "Cuisine Roux"})
    assert projet.status_code == 200, projet.text
    projet_id = projet.json()["id"]
    contact = await client.post("/api/memory/contacts", json={
        "first_name": "Julien", "last_name": "Garnier", "scope": "project", "scope_id": projet_id,
    })
    assert contact.status_code == 200, contact.text
    sous_projet = await client.post("/api/memory/projects", json={
        "name": "Plans de la cuisine", "scope": "project", "scope_id": projet_id,
    })
    assert sous_projet.status_code == 200, sous_projet.text

    suppression = await client.delete(f"/api/memory/projects/{projet_id}")
    assert suppression.status_code == 200, suppression.text

    async with db_module.AsyncSessionLocal() as session:
        fiche = await session.get(Contact, contact.json()["id"])
        dossier = await session.get(Project, sous_projet.json()["id"])
    assert (fiche.scope, fiche.scope_id) == ("global", None)
    assert (dossier.scope, dossier.scope_id) == ("global", None)
