"""Un compte étranger ne peut pas modifier le blocage d'un événement."""

from unittest.mock import AsyncMock

import pytest
from app.models.entities import Calendar, CalendarEvent
from app.services.calendar.base_provider import CalendarEventDTO


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
@pytest.mark.parametrize("compte", [None, ""])
async def test_blocage_refuse_un_calendrier_externe_sans_compte(client, db_session, compte):
    db_session.add(Calendar(id="cal-sans-compte", summary="Agenda", provider="google"))
    db_session.add(CalendarEvent(id="ev-sans-compte", calendar_id="cal-sans-compte", summary="Séance"))
    await db_session.commit()

    reponse = await client.patch(
        "/api/calendar/events/ev-sans-compte/blocage",
        params={} if compte is None else {"account_id": compte},
        json={"blocage": "Motif"},
    )
    assert reponse.status_code == 404
    assert (await client.get(
        "/api/calendar/events/ev-sans-compte",
        params={} if compte is None else {"account_id": compte},
    )).status_code == 404


@pytest.mark.asyncio
@pytest.mark.parametrize("fournisseur", ["caldav", "local"])
@pytest.mark.parametrize("compte", [None, ""])
@pytest.mark.parametrize("operation", ["lecture", "blocage"])
async def test_evenement_sans_compte_autorise_lecture_et_blocage(
    client, db_session, fournisseur, compte, operation
):
    db_session.add(Calendar(id="cal-sans-compte", summary="Agenda", provider=fournisseur))
    db_session.add(CalendarEvent(id="ev-sans-compte", calendar_id="cal-sans-compte", summary="Séance"))
    await db_session.commit()
    url = "/api/calendar/events/ev-sans-compte"

    if operation == "lecture":
        assert (await client.get(url, params={"account_id": "etranger"})).status_code == 404
        reponse = await client.get(url, params={} if compte is None else {"account_id": compte})
        assert reponse.status_code == 200
        assert reponse.json()["summary"] == "Séance"
    else:
        assert (await client.patch(
            f"{url}/blocage", params={"account_id": "etranger"}, json={"blocage": "Étranger"},
        )).status_code == 404
        reponse = await client.patch(
            f"{url}/blocage", params={} if compte is None else {"account_id": compte},
            json={"blocage": "Pièce manquante"},
        )
        assert reponse.status_code == 200
        assert reponse.json()["blocage"] == "Pièce manquante"


@pytest.mark.asyncio
async def test_caldav_sans_compte_autorise_modification_et_suppression(
    client, db_session, monkeypatch
):
    from app.routers import calendar

    db_session.add(Calendar(
        id="cal-caldav", summary="Agenda", provider="caldav", remote_id="agenda-distant",
    ))
    db_session.add(CalendarEvent(id="ev-caldav", calendar_id="cal-caldav", summary="Séance"))
    await db_session.commit()
    fournisseur = AsyncMock()
    fournisseur.update_event.return_value = CalendarEventDTO(
        id="ev-caldav", calendar_id="agenda-distant", summary="Séance modifiée",
    )
    monkeypatch.setattr(calendar, "_get_provider_for_calendar", AsyncMock(return_value=fournisseur))

    modification = await client.put(
        "/api/calendar/events/ev-caldav", params={"calendar_id": "cal-caldav"},
        json={"summary": "Séance modifiée"},
    )
    assert modification.status_code == 200
    assert modification.json()["summary"] == "Séance modifiée"
    assert fournisseur.update_event.await_args.args[:2] == ("agenda-distant", "ev-caldav")

    suppression = await client.delete(
        "/api/calendar/events/ev-caldav", params={"calendar_id": "cal-caldav"},
    )
    assert suppression.status_code == 200
    assert suppression.json()["success"] is True
    fournisseur.delete_event.assert_awaited_once_with("agenda-distant", "ev-caldav")
