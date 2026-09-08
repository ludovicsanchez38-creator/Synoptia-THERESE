"""P-048 (Sophie, c4 ; revue COCO 08/09) : la vue Livrables va créer et faire
évoluer un livrable. Le backend valide ce qu'il écrit (titre non blanc,
statut connu) et date honnêtement les validations (quitter « valide » efface
la date, revalider la repose)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _projet(client: AsyncClient) -> str:
    reponse = await client.post("/api/memory/projects", json={"name": "Site vitrine", "status": "active"})
    assert reponse.status_code == 200, reponse.text
    return reponse.json()["id"]


@pytest.mark.asyncio
async def test_un_titre_blanc_est_refuse_a_la_creation(client: AsyncClient):
    projet = await _projet(client)
    reponse = await client.post("/api/crm/deliverables", json={"project_id": projet, "title": "   "})
    assert reponse.status_code == 422, reponse.text


@pytest.mark.asyncio
async def test_un_statut_inconnu_est_refuse_a_la_creation_et_a_la_modification(client: AsyncClient):
    projet = await _projet(client)
    reponse = await client.post("/api/crm/deliverables", json={"project_id": projet, "title": "Maquette", "status": "termine"})
    assert reponse.status_code == 422, reponse.text
    cree = await client.post("/api/crm/deliverables", json={"project_id": projet, "title": "Maquette"})
    assert cree.status_code == 200, cree.text
    modif = await client.put(f"/api/crm/deliverables/{cree.json()['id']}", json={"status": "livre"})
    assert modif.status_code == 422, modif.text


@pytest.mark.asyncio
async def test_le_cycle_valide_en_cours_valide_redate_la_validation(client: AsyncClient):
    projet = await _projet(client)
    cree = await client.post("/api/crm/deliverables", json={"project_id": projet, "title": "Maquette"})
    identifiant = cree.json()["id"]
    premiere = await client.put(f"/api/crm/deliverables/{identifiant}", json={"status": "valide"})
    assert premiere.status_code == 200, premiere.text
    date_1 = premiere.json()["completed_at"]
    assert date_1 is not None
    reouvert = await client.put(f"/api/crm/deliverables/{identifiant}", json={"status": "en_cours"})
    assert reouvert.status_code == 200, reouvert.text
    assert reouvert.json()["completed_at"] is None, "quitter « valide » doit effacer la date de validation"
    seconde = await client.put(f"/api/crm/deliverables/{identifiant}", json={"status": "valide"})
    assert seconde.status_code == 200, seconde.text
    date_2 = seconde.json()["completed_at"]
    assert date_2 is not None and date_2 >= date_1, "revalider pose une nouvelle date, pas l'ancienne"
