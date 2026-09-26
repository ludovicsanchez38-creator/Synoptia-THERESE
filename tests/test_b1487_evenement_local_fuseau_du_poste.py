"""B-1487 : créer ou déplacer un événement local ignorait le fuseau du poste.

L'écran envoie l'heure saisie sans fuseau et, à côté, le fuseau réel du
poste (EventForm). L'agenda local range une heure murale de Paris (B-275) et
la relit comme telle. Le routeur jetait le fuseau : un rendez-vous saisi à
10 h en Martinique était rangé à 10 h de Paris, puis réaffiché à 4 h.
"""

from datetime import datetime

import pytest
from httpx import AsyncClient


async def _agenda(client: AsyncClient) -> str:
    reponse = await client.post(
        "/api/calendar/calendars", json={"summary": "Agenda local", "provider_type": "local"}
    )
    assert reponse.status_code == 200, reponse.text
    return reponse.json()["id"]


async def _stocke(event_id: str):
    from app.models import database as db_module
    from app.models.entities import CalendarEvent

    async with db_module.AsyncSessionLocal() as session:
        return await session.get(CalendarEvent, event_id)


async def _creer(client: AsyncClient, cal: str, debut: str, fin: str, fuseau: str):
    reponse = await client.post("/api/calendar/events", json={
        "calendar_id": cal, "summary": "Point chantier",
        "start_datetime": debut, "end_datetime": fin, "timezone": fuseau,
    })
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


@pytest.mark.asyncio
async def test_un_rendez_vous_saisi_en_martinique_se_range_en_heure_de_paris(client: AsyncClient):
    cal = await _agenda(client)
    cree = await _creer(client, cal, "2026-07-10T10:00:00", "2026-07-10T11:00:00", "America/Martinique")

    stocke = await _stocke(cree["id"])
    assert stocke.start_datetime == datetime(2026, 7, 10, 16, 0)
    assert stocke.end_datetime == datetime(2026, 7, 10, 17, 0)
    # La réponse, ajoutée telle quelle à l'écran, désigne le même instant.
    assert datetime.fromisoformat(cree["start_datetime"]) == datetime.fromisoformat("2026-07-10T10:00:00-04:00")


@pytest.mark.asyncio
async def test_un_rendez_vous_saisi_a_paris_ne_bouge_pas(client: AsyncClient):
    cal = await _agenda(client)
    cree = await _creer(client, cal, "2026-07-10T10:00:00", "2026-07-10T11:00:00", "Europe/Paris")
    assert (await _stocke(cree["id"])).start_datetime == datetime(2026, 7, 10, 10, 0)


@pytest.mark.asyncio
async def test_deplacer_un_rendez_vous_en_martinique_suit_le_fuseau(client: AsyncClient):
    cal = await _agenda(client)
    cree = await _creer(client, cal, "2026-07-10T10:00:00", "2026-07-10T11:00:00", "Europe/Paris")

    reponse = await client.put(
        f"/api/calendar/events/{cree['id']}?calendar_id={cal}",
        json={
            "start_datetime": "2026-07-10T11:00:00", "end_datetime": "2026-07-10T12:00:00",
            "timezone": "America/Martinique",
        },
    )
    assert reponse.status_code == 200, reponse.text
    stocke = await _stocke(cree["id"])
    assert stocke.start_datetime == datetime(2026, 7, 10, 17, 0)
    assert stocke.end_datetime == datetime(2026, 7, 10, 18, 0)
