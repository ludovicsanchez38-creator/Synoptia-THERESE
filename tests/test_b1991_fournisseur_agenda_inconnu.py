"""B-1991 : un fournisseur inconnu ne doit pas être présenté comme Google."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import httpx
import pytest
from app.models.entities import Calendar, CalendarEvent, EmailAccount
from app.services import calendar_service
from sqlmodel import select


async def test_b1991_creer_sur_un_fournisseur_inconnu_explique_le_refus(client, db_session):
    agenda = Calendar(summary="Agenda de test", provider="inconnu")
    db_session.add(agenda)
    await db_session.commit()
    debut = datetime.now(UTC) + timedelta(days=1)

    reponse = await client.post(
        "/api/calendar/events",
        json={
            "calendar_id": agenda.id,
            "summary": "Rendez-vous de test",
            "start_datetime": debut.isoformat(),
            "end_datetime": (debut + timedelta(hours=1)).isoformat(),
        },
    )

    assert reponse.status_code == 400
    assert reponse.json()["message"] == "Ce fournisseur d’agenda n’est pas pris en charge."


@pytest.fixture
async def collision_primary(client, db_session, monkeypatch):
    compte = EmailAccount(id="compte-r1", email="agenda@example.test", provider="gmail")
    autre = EmailAccount(id="autre-r1", email="autre@example.test", provider="gmail")
    inconnu = Calendar(id="primary", summary="Historique", provider="inconnu", account_id=compte.id)
    voisin = Calendar(id=autre.email, summary="Voisin", provider="google", account_id=autre.id, primary=True)
    db_session.add_all([compte, autre, inconnu, voisin])
    await db_session.commit()
    appels = []

    def google_simule(requete: httpx.Request) -> httpx.Response:
        appels.append((requete.method, requete.url.path))
        if requete.method == "GET" and requete.url.path.endswith("/calendars/primary"):
            return httpx.Response(200, json={
                "id": compte.email, "summary": "Principal Google", "timeZone": "Europe/Paris",
            })
        if requete.method == "POST" and requete.url.path.endswith(f"/calendars/{compte.email}/events"):
            return httpx.Response(200, json={
                "id": "evenement-r1", "summary": "Rendez-vous de test",
                "start": {"date": "2026-12-01"}, "end": {"date": "2026-12-02"},
                "status": "confirmed",
            })
        if requete.method == "GET" and requete.url.path in (
            "/calendar/v3/calendars/primary/events",
            f"/calendar/v3/calendars/{compte.email}/events",
        ):
            return httpx.Response(200, json={"items": [{
                "id": "evenement-r1", "summary": "Rendez-vous de test",
                "start": {"date": "2026-12-01"}, "end": {"date": "2026-12-02"},
                "status": "confirmed",
            }]})
        raise AssertionError(f"Appel inattendu : {requete.method} {requete.url.path}")

    async with httpx.AsyncClient(transport=httpx.MockTransport(google_simule)) as transport:
        monkeypatch.setattr(calendar_service, "get_http_client", AsyncMock(return_value=transport))
        yield compte, inconnu, voisin, appels


@pytest.mark.parametrize("deja_en_cache", [False, True])
async def test_relecture_r1_primary_implicite_resout_le_compte_sans_detourner_la_ligne(
    client, db_session, collision_primary, deja_en_cache: bool,
):
    compte, inconnu, voisin, appels = collision_primary
    if deja_en_cache:
        db_session.add(Calendar(
            id=compte.email, account_id=compte.id, provider="google", primary=True,
            summary="Principal Google", remote_id=compte.email,
        ))
        await db_session.commit()
    reponse = await client.post(
        "/api/calendar/events", params={"account_id": compte.id},
        json={"summary": "Rendez-vous de test", "start_date": "2026-12-01", "end_date": "2026-12-01"},
    )

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["calendar_id"] == compte.email
    evenement = await db_session.get(CalendarEvent, "evenement-r1")
    assert evenement.calendar_id == compte.email
    principal = await db_session.get(Calendar, evenement.calendar_id)
    assert (principal.provider, principal.account_id, principal.primary) == ("google", compte.id, True)
    await db_session.refresh(inconnu)
    await db_session.refresh(voisin)
    assert (inconnu.provider, inconnu.summary, inconnu.account_id) == ("inconnu", "Historique", compte.id)
    assert (voisin.summary, voisin.account_id) == ("Voisin", "autre-r1")
    assert appels == [
        ("GET", "/calendar/v3/calendars/primary"),
        ("POST", f"/calendar/v3/calendars/{compte.email}/events"),
    ]
    for destination in ({}, {"calendar_id": "primary"}, {"calendar_id": compte.email}):
        lecture = await client.get(
            "/api/calendar/events", params={"account_id": compte.id, **destination},
        )
        assert lecture.status_code == 200, lecture.text
        assert [evt["id"] for evt in lecture.json()] == ["evenement-r1"]
        assert lecture.json()[0]["calendar_id"] == compte.email
    assert len((await db_session.execute(select(CalendarEvent))).scalars().all()) == 1
    await db_session.refresh(inconnu)
    await db_session.refresh(voisin)
    assert (inconnu.provider, inconnu.summary, inconnu.account_id) == ("inconnu", "Historique", compte.id)
    assert (voisin.summary, voisin.account_id) == ("Voisin", "autre-r1")


@pytest.mark.parametrize("avec_compte", [False, True])
async def test_relecture_r1_primary_explicite_inconnu_reste_refuse(
    client, db_session, collision_primary, avec_compte: bool,
):
    compte, _, _, appels = collision_primary
    reponse = await client.post(
        "/api/calendar/events", params={"account_id": compte.id} if avec_compte else {},
        json={
            "calendar_id": "primary", "calendar_id_is_stored": True,
            "summary": "Rendez-vous de test",
            "start_date": "2026-12-01", "end_date": "2026-12-01",
        },
    )

    assert reponse.status_code == 400
    assert reponse.json()["message"] == "Ce fournisseur d’agenda n’est pas pris en charge."
    assert appels == []
    assert (await db_session.execute(select(CalendarEvent))).scalars().all() == []


async def test_relecture_r2_primary_explicite_google_cree_et_relit(
    client, db_session, collision_primary,
):
    compte, inconnu, voisin, _ = collision_primary
    creation = await client.post(
        "/api/calendar/events", params={"account_id": compte.id},
        json={
            "calendar_id": "primary", "summary": "Rendez-vous de test",
            "start_date": "2026-12-01", "end_date": "2026-12-01",
        },
    )
    assert creation.status_code == 200, creation.text
    assert creation.json()["calendar_id"] == compte.email
    lecture = await client.get(
        "/api/calendar/events", params={"account_id": compte.id, "calendar_id": "primary"},
    )
    assert lecture.status_code == 200, lecture.text
    assert [evt["id"] for evt in lecture.json()] == [creation.json()["id"]]
    assert lecture.json()[0]["calendar_id"] == compte.email
    await db_session.refresh(inconnu)
    await db_session.refresh(voisin)
    assert (inconnu.provider, inconnu.summary, inconnu.account_id) == ("inconnu", "Historique", compte.id)
    assert (voisin.summary, voisin.account_id) == ("Voisin", "autre-r1")


async def test_relecture_r2_un_agenda_selectionne_absent_ne_devient_pas_un_alias(
    client, collision_primary,
):
    compte, _, _, appels = collision_primary
    reponse = await client.post(
        "/api/calendar/events", params={"account_id": compte.id},
        json={
            "calendar_id": "agenda-absent", "calendar_id_is_stored": True,
            "summary": "Rendez-vous de test",
            "start_date": "2026-12-01", "end_date": "2026-12-01",
        },
    )
    assert reponse.status_code == 404, reponse.text
    assert appels == []


@pytest.mark.parametrize("identifiant_distant", ["primary", "autre@example.test"])
async def test_relecture_r1_la_resolution_google_ne_reaffecte_pas_un_agenda_existant(
    client, db_session, collision_primary, monkeypatch, identifiant_distant: str,
):
    compte, inconnu, voisin, appels = collision_primary
    monkeypatch.setattr(calendar_service.CalendarService, "get_calendar", AsyncMock(return_value={
        "id": identifiant_distant, "summary": "Principal distant",
    }))

    reponse = await client.post(
        "/api/calendar/events", params={"account_id": compte.id},
        json={"summary": "Rendez-vous de test", "start_date": "2026-12-01", "end_date": "2026-12-01"},
    )

    assert reponse.status_code == 409, reponse.text
    assert "autre agenda" in reponse.json()["message"]
    assert appels == []
    assert (await db_session.execute(select(CalendarEvent))).scalars().all() == []
    await db_session.refresh(inconnu)
    await db_session.refresh(voisin)
    assert (inconnu.provider, inconnu.summary, inconnu.account_id) == ("inconnu", "Historique", compte.id)
    assert (voisin.provider, voisin.summary, voisin.account_id) == ("google", "Voisin", "autre-r1")
