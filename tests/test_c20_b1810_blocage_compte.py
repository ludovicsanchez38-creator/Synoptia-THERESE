"""Un compte étranger ne peut pas modifier le blocage d'un événement."""

import pytest
from app.models.entities import Calendar, CalendarEvent


@pytest.mark.asyncio
async def test_blocage_refuse_le_compte_etranger(client, db_session):
    db_session.add(Calendar(id="cal-a", account_id="compte-a", summary="Agenda A"))
    db_session.add(CalendarEvent(id="ev-a", calendar_id="cal-a", summary="Séance"))
    await db_session.commit()

    lecture = await client.get(
        "/api/calendar/events/ev-a", params={"account_id": "compte-b"}
    )
    assert lecture.status_code == 404

    modification = await client.patch(
        "/api/calendar/events/ev-a/blocage",
        params={"account_id": "compte-b"},
        json={"blocage": "Motif étranger"},
    )
    assert modification.status_code == 404

    evenement = await client.get(
        "/api/calendar/events/ev-a", params={"account_id": "compte-a"}
    )
    assert evenement.status_code == 200
    assert evenement.json()["blocage"] is None


@pytest.mark.asyncio
async def test_blocage_exige_un_calendrier_rattachable(client, db_session):
    db_session.add(CalendarEvent(id="ev-orphelin", calendar_id="absent", summary="Séance"))
    await db_session.commit()

    reponse = await client.patch(
        "/api/calendar/events/ev-orphelin/blocage", json={"blocage": "Motif"}
    )
    assert reponse.status_code == 404
    lecture = await client.get(
        "/api/calendar/events/ev-orphelin", params={"account_id": "compte-a"}
    )
    assert lecture.status_code == 404


@pytest.mark.asyncio
async def test_blocage_autorise_le_compte_proprietaire_et_le_calendrier_local(client, db_session):
    db_session.add(Calendar(id="cal-a", account_id="compte-a", summary="Agenda A"))
    db_session.add(Calendar(id="cal-local", summary="Agenda local"))
    db_session.add(CalendarEvent(id="ev-a", calendar_id="cal-a", summary="Séance A"))
    db_session.add(CalendarEvent(id="ev-local", calendar_id="cal-local", summary="Séance locale"))
    await db_session.commit()

    assert (await client.patch(
        "/api/calendar/events/ev-a/blocage", json={"blocage": "Motif"}
    )).status_code == 404
    assert (await client.patch(
        "/api/calendar/events/ev-a/blocage", params={"account_id": "compte-a"},
        json={"blocage": "Motif"},
    )).status_code == 200
    assert (await client.patch(
        "/api/calendar/events/ev-local/blocage", json={"blocage": "Motif"}
    )).status_code == 200


@pytest.mark.asyncio
async def test_blocage_refuse_un_calendrier_externe_sans_compte(client, db_session):
    db_session.add(Calendar(id="cal-sans-compte", summary="Agenda", provider="google"))
    db_session.add(CalendarEvent(id="ev-sans-compte", calendar_id="cal-sans-compte", summary="Séance"))
    await db_session.commit()

    reponse = await client.patch(
        "/api/calendar/events/ev-sans-compte/blocage", json={"blocage": "Motif"}
    )
    assert reponse.status_code == 404
    assert (await client.get("/api/calendar/events/ev-sans-compte")).status_code == 404
