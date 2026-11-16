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


@pytest.mark.asyncio
async def test_parcours_caldav_depuis_la_liste_garde_le_blocage_et_le_bon_agenda(
    client, db_session, monkeypatch,
):
    from app.routers import calendar

    for identifiant in ("cal-dav-a", "cal-dav-b"):
        db_session.add(Calendar(
            id=identifiant, summary=identifiant, provider="caldav", remote_id=identifiant,
        ))
    await db_session.commit()
    evenement = CalendarEventDTO(id="uid-partage", calendar_id="distant", summary="Séance")
    fournisseur = AsyncMock()
    fournisseur.list_events.return_value = ([evenement], None)
    fournisseur.update_event.return_value = CalendarEventDTO(
        id="uid-partage", calendar_id="distant", summary="Modifiée",
    )
    monkeypatch.setattr(calendar, "_get_provider_for_calendar", AsyncMock(return_value=fournisseur))

    async def liste(calendrier):
        reponse = await client.get("/api/calendar/events", params={"calendar_id": calendrier})
        assert reponse.status_code == 200
        return reponse.json()[0]

    a = await liste("cal-dav-a")
    b = await liste("cal-dav-b")
    assert a["id"] == b["id"] == "uid-partage"
    url = f"/api/calendar/events/{a['id']}"
    assert (await client.get(url)).status_code == 404
    assert (await client.patch(f"{url}/blocage", json={"blocage": "Ambigu"})).status_code == 404
    lecture = await client.get(url, params={"calendar_id": a["calendar_id"]})
    assert lecture.status_code == 200
    assert lecture.json()["id"] == a["id"]
    pose = await client.patch(
        f"{url}/blocage", params={"calendar_id": a["calendar_id"]},
        json={"blocage": "Attestation manquante"},
    )
    assert pose.status_code == 200
    assert pose.json()["id"] == a["id"]
    assert (await liste("cal-dav-a"))["blocage"] == "Attestation manquante"
    assert (await liste("cal-dav-b"))["blocage"] is None
    modification = await client.put(url, params={"calendar_id": a["calendar_id"]}, json={"summary": "Modifiée"})
    assert modification.status_code == 200
    assert modification.json()["blocage"] == "Attestation manquante"
    relu = await client.get(url, params={"calendar_id": a["calendar_id"]})
    assert relu.json()["summary"] == "Modifiée"
    assert relu.json()["blocage"] == "Attestation manquante"
    fournisseur.update_event.assert_awaited_once()
    assert fournisseur.update_event.await_args.args[:2] == ("cal-dav-a", "uid-partage")
    suppression = await client.delete(url, params={"calendar_id": a["calendar_id"]})
    assert suppression.status_code == 200
    fournisseur.delete_event.assert_awaited_once_with("cal-dav-a", "uid-partage")
    assert (await client.get(url, params={"calendar_id": "cal-dav-a"})).status_code == 404
    assert (await client.get(url, params={"calendar_id": "cal-dav-b"})).status_code == 200
    assert (await client.get(url)).json()["calendar_id"] == "cal-dav-b"


@pytest.mark.asyncio
@pytest.mark.parametrize("fournisseur", ["local", "caldav"])
@pytest.mark.parametrize("proprietaire", [None, "compte-a"])
async def test_compte_etranger_refuse_toutes_les_operations_avant_le_fournisseur(
    client, db_session, monkeypatch, fournisseur, proprietaire,
):
    from app.routers import calendar

    db_session.add(Calendar(
        id="cal-controle", summary="Agenda", provider=fournisseur, account_id=proprietaire,
    ))
    db_session.add(CalendarEvent(id="ev-controle", calendar_id="cal-controle", summary="Séance"))
    await db_session.commit()
    provider = AsyncMock()
    provider.update_event.return_value = CalendarEventDTO(
        id="ev-controle", calendar_id="cal-controle", summary="Modifiée",
    )
    obtenir = AsyncMock(return_value=provider)
    monkeypatch.setattr(calendar, "_get_provider_for_calendar", obtenir)
    params = {"calendar_id": "cal-controle", "account_id": "compte-b"}
    url = "/api/calendar/events/ev-controle"

    reponses = [
        await client.get(url, params=params),
        await client.patch(f"{url}/blocage", params=params, json={"blocage": "Motif"}),
        await client.put(url, params=params, json={"summary": "Modifiée"}),
        await client.delete(url, params=params),
    ]
    assert [reponse.status_code for reponse in reponses] == [404, 404, 404, 404]
    obtenir.assert_not_awaited()
    db_session.expire_all()
    assert (await db_session.get(CalendarEvent, "ev-controle")).summary == "Séance"
