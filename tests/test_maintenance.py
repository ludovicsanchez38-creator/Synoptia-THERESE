"""Mode maintenance exclusif utilisé pendant une restauration."""

import asyncio

import pytest
from app.services.maintenance import RequestAdmission, maintenance_mode


@pytest.mark.asyncio
async def test_maintenance_attend_les_requetes_deja_admises():
    maintenance_mode.end()
    admission = maintenance_mode.admit("POST", "/api/tasks")
    assert admission is RequestAdmission.TRACKED

    activation = asyncio.create_task(maintenance_mode.begin())
    await asyncio.sleep(0)

    assert maintenance_mode.active is True
    assert activation.done() is False

    maintenance_mode.release(admission)
    await activation
    maintenance_mode.end()


@pytest.mark.asyncio
async def test_maintenance_refuse_les_ecritures_api_avec_un_503(client):
    maintenance_mode.end()
    await maintenance_mode.begin()
    try:
        response = await client.post("/api/tasks", json={"title": "Ne doit pas passer"})
    finally:
        maintenance_mode.end()

    assert response.status_code == 503
    assert response.json()["code"] == "MAINTENANCE_MODE"
    assert "Aucune écriture API" in response.json()["message"]
