"""Finding 2 (revue 30/08) : l'agenda du chat n'est pas celui de l'écran.

Un Gmail connecté pour le courrier masquait le local. Sans identifiant,
le chat lisait Google `primary` pendant que l'accueil montrait le local.
"""

from __future__ import annotations

from datetime import date, datetime, time

import pytest
from app.models.entities import Calendar, CalendarEvent, EmailAccount


async def _gmail_et_local(session):
    compte = EmailAccount(
        id="acc-gmail",
        email="a@gmail.com",
        provider="gmail",
        access_token="enc-a",
    )
    local = Calendar(
        id="cal-local",
        summary="Mon calendrier",
        provider="local",
        timezone="Europe/Paris",
    )
    session.add(compte)
    session.add(local)
    await session.commit()
    return compte, local


@pytest.mark.asyncio
async def test_gmail_plus_local_sans_id_prend_le_seul_agenda(db_session, monkeypatch):
    """Le local est le seul agenda en base : Gmail pour le courrier ne
    doit pas le voler. Avant : Google `primary` dès qu'un compte Gmail existait."""
    await _gmail_et_local(db_session)

    async def fake_ensure(account, session):
        raise AssertionError("Google ne doit pas être contacté : un seul agenda, local")

    monkeypatch.setattr("app.routers.email.ensure_valid_access_token", fake_ensure)

    from app.services.calendar.local_provider import LocalCalendarProvider
    from app.services.workspace_tools import _get_calendar_provider

    provider, cal_id, error = await _get_calendar_provider(db_session)
    assert error is None
    assert isinstance(provider, LocalCalendarProvider)
    assert cal_id == "cal-local"


@pytest.mark.asyncio
async def test_deux_agendas_sans_id_refuse(db_session, monkeypatch):
    """Local + Google en base, aucun choix d'écran : on refuse."""
    await _gmail_et_local(db_session)
    db_session.add(
        Calendar(
            id="cal-google",
            account_id="acc-gmail",
            summary="Gmail",
            provider="google",
            remote_id="primary",
        )
    )
    await db_session.commit()

    async def fake_ensure(account, session):
        raise AssertionError("plusieurs agendas : aucun jeton Google")

    monkeypatch.setattr("app.routers.email.ensure_valid_access_token", fake_ensure)

    from app.services.workspace_tools import _get_calendar_provider

    provider, cal_id, error = await _get_calendar_provider(db_session)
    assert provider is None
    assert cal_id is None
    assert error is not None
    assert "Gmail" in error
    assert "Mon calendrier" in error


@pytest.mark.asyncio
async def test_id_local_gagne_meme_si_gmail_existe(db_session, monkeypatch):
    """L'agenda de l'écran (local) gagne, Gmail reste pour le courrier."""
    await _gmail_et_local(db_session)

    async def fake_ensure(account, session):
        raise AssertionError("le local ne rafraîchit pas un jeton Google")

    monkeypatch.setattr("app.routers.email.ensure_valid_access_token", fake_ensure)

    from app.services.calendar.local_provider import LocalCalendarProvider
    from app.services.workspace_tools import _get_calendar_provider

    provider, cal_id, error = await _get_calendar_provider(
        db_session, calendar_id="cal-local"
    )
    assert error is None
    assert isinstance(provider, LocalCalendarProvider)
    assert cal_id == "cal-local"


@pytest.mark.asyncio
async def test_destination_de_confirmation_suit_l_agenda_de_l_ecran(db_session):
    await _gmail_et_local(db_session)
    from app.services.workspace_tools import get_calendar_confirmation_destination

    dest = await get_calendar_confirmation_destination(
        db_session, calendar_id="cal-local"
    )
    assert dest["calendar_id"] == "cal-local"
    assert dest["calendar_name"] == "Mon calendrier"
    assert dest["provider"] == "local"


@pytest.mark.asyncio
async def test_liste_gmail_n_efface_pas_le_calendrier_local(client, db_session, monkeypatch):
    """Choisir Gmail pour le courrier ne doit pas faire disparaître le local
    du menu Agenda."""
    await _gmail_et_local(db_session)

    async def fake_ensure(account, session):
        return "ya29.token"

    class FakeCalendarService:
        def __init__(self, _token):
            pass

        async def list_calendars(self):
            return [
                {
                    "id": "primary-google",
                    "summary": "Gmail",
                    "timeZone": "Europe/Paris",
                    "primary": True,
                }
            ]

    monkeypatch.setattr("app.routers.calendar.ensure_valid_access_token", fake_ensure)
    monkeypatch.setattr("app.routers.calendar.CalendarService", FakeCalendarService)

    reponse = await client.get("/api/calendar/calendars?account_id=acc-gmail")
    assert reponse.status_code == 200
    noms = {cal["summary"] for cal in reponse.json()}
    assert "Mon calendrier" in noms
    assert "Gmail" in noms


@pytest.mark.asyncio
async def test_brief_du_jour_nomme_l_agenda(client, db_session):
    """L'accueil mélangeait tous les événements sans dire de quel agenda."""
    local = Calendar(
        id="cal-local-brief",
        summary="Cabinet",
        provider="local",
        timezone="Europe/Paris",
    )
    db_session.add(local)
    db_session.add(
        CalendarEvent(
            id="evt-brief",
            calendar_id="cal-local-brief",
            summary="Point client",
            start_datetime=datetime.combine(date.today(), time(10, 0)),
            end_datetime=datetime.combine(date.today(), time(11, 0)),
            status="confirmed",
        )
    )
    await db_session.commit()

    reponse = await client.get("/api/dashboard/today")
    assert reponse.status_code == 200
    evenements = reponse.json()["events"]
    assert evenements
    point = next(e for e in evenements if e["id"] == "evt-brief")
    assert point["calendar_name"] == "Cabinet"
