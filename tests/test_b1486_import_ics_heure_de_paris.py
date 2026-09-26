"""B-1486 : un ICS importé à l'heure Z s'affichait à l'heure UTC.

L'agenda local range une heure murale de Paris sans fuseau (B-275). L'import
rendait l'instant de l'ICS avec son décalage, puis SQLite jetait le décalage :
une invitation Outlook à 08:00Z (10 h à Paris en juillet) se relisait 8 h.
Une heure flottante (sans fuseau, RFC 5545 : l'heure du lieu) reste telle
quelle.
"""

from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlmodel import select


def _ics(uid: str, debut: str, fin: str) -> bytes:
    return (
        "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Therese//Test//FR\r\n"
        "BEGIN:VTIMEZONE\r\nTZID:America/Martinique\r\n"
        "BEGIN:STANDARD\r\nDTSTART:19700101T000000\r\n"
        "TZOFFSETFROM:-0400\r\nTZOFFSETTO:-0400\r\nTZNAME:AST\r\nEND:STANDARD\r\n"
        "END:VTIMEZONE\r\n"
        f"BEGIN:VEVENT\r\nUID:{uid}\r\n{debut}\r\n{fin}\r\n"
        "SUMMARY:Point chantier\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"
    ).encode()


async def _importer_et_relire(client: AsyncClient, uid: str, debut: str, fin: str):
    from app.models import database as db_module
    from app.models.entities import CalendarEvent

    cal = await client.post(
        "/api/calendar/calendars", json={"summary": f"Agenda {uid}", "provider_type": "local"}
    )
    assert cal.status_code == 200, cal.text
    reponse = await client.post(
        f"/api/calendar/import-ics?calendar_id={cal.json()['id']}",
        files={"file": ("invitation.ics", _ics(uid, debut, fin), "text/calendar")},
    )
    assert reponse.status_code == 200, reponse.text
    async with db_module.AsyncSessionLocal() as session:
        return (await session.execute(
            select(CalendarEvent).where(CalendarEvent.calendar_id == cal.json()["id"])
        )).scalar_one()


@pytest.mark.asyncio
async def test_une_heure_z_se_range_en_heure_de_paris(client: AsyncClient):
    evenement = await _importer_et_relire(
        client, "b1486-z", "DTSTART:20260710T080000Z", "DTEND:20260710T090000Z"
    )
    assert evenement.start_datetime == datetime(2026, 7, 10, 10, 0)
    assert evenement.end_datetime == datetime(2026, 7, 10, 11, 0)


@pytest.mark.asyncio
async def test_une_heure_d_un_autre_fuseau_se_range_en_heure_de_paris(client: AsyncClient):
    evenement = await _importer_et_relire(
        client, "b1486-mq",
        "DTSTART;TZID=America/Martinique:20260710T100000",
        "DTEND;TZID=America/Martinique:20260710T110000",
    )
    assert evenement.start_datetime == datetime(2026, 7, 10, 16, 0)


@pytest.mark.asyncio
async def test_une_heure_flottante_ne_bouge_pas(client: AsyncClient):
    evenement = await _importer_et_relire(
        client, "b1486-flottante", "DTSTART:20260710T100000", "DTEND:20260710T110000"
    )
    assert evenement.start_datetime == datetime(2026, 7, 10, 10, 0)
