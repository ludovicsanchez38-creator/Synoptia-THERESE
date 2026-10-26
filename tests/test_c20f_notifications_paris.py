"""B-1150 : demain désigne une date civile à Paris, même au changement d'heure."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from zoneinfo import ZoneInfo

import httpx
import pytest
from app.main import app
from app.models import entities
from app.models.entities import CalendarEvent, Contact, Notification, Task
from app.services import notification_service as module
from app.services import relances
from sqlmodel import select

PARIS = ZoneInfo("Europe/Paris")


def figer(monkeypatch, maintenant):
    class Horloge(datetime):
        @classmethod
        def now(cls, tz=None):
            return maintenant.astimezone(tz) if tz else maintenant.replace(tzinfo=None)

    monkeypatch.setattr(module, "datetime", Horloge)


async def verifier_jour(db_session, monkeypatch, date_locale):
    maintenant = datetime.fromisoformat(date_locale)
    maintenant = maintenant.replace(tzinfo=PARIS) if maintenant.tzinfo is None else maintenant.astimezone(PARIS)
    figer(monkeypatch, maintenant)
    monkeypatch.setattr(entities, "datetime", module.datetime)
    demain = (maintenant + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=None,
    )
    # Charge utile d'EventForm : heure saisie sans décalage + fuseau du poste.
    # L'API et le provider local décident seuls de la valeur stockée en base.
    entrees = [
        (demain - timedelta(minutes=30), "Ce soir", None),
        (demain - timedelta(seconds=1), "Dernière seconde ce soir", None),
        (demain, "Minuit demain", "00h00"),
        (demain.replace(hour=9, minute=15), "Demain matin", "09h15"),
        (demain.replace(hour=23, minute=30), "Demain soir", "23h30"),
        (demain + timedelta(days=1) - timedelta(seconds=1), "Dernière seconde demain", "23h59"),
        (demain + timedelta(days=1), "Après-demain", None),
    ]
    attendues = {}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test",
    ) as client:
        calendrier = await client.post("/api/calendar/calendars", json={
            "summary": "Agenda local", "provider_type": "local", "timezone": "Europe/Paris",
        })
        assert calendrier.status_code == 200, calendrier.text
        for heure, titre, affichage in entrees:
            reponse = await client.post("/api/calendar/events", json={
                "calendar_id": calendrier.json()["id"], "summary": titre,
                "start_datetime": heure.isoformat(),
                "end_datetime": (heure + timedelta(minutes=15)).isoformat(),
                "timezone": "Europe/Paris",
            })
            assert reponse.status_code == 200, reponse.text
            identifiant = reponse.json()["id"]
            stocke = await db_session.get(CalendarEvent, identifiant)
            assert stocke.start_datetime.tzinfo is None
            assert stocke.start_datetime == heure
            if affichage is not None:
                attendues[f"/calendar/events/{identifiant}"] = f"RDV demain à {affichage} : {titre}"

        generation = await client.post("/api/notifications/generate")
        assert generation.status_code == 200, generation.text
        reponse = await client.get("/api/notifications/")
        assert reponse.status_code == 200, reponse.text
        notifications = [n for n in reponse.json() if n["source"] == "calendar"]
        messages = {n["message"] for n in notifications}
        print(f"Agenda API {date_locale} : {sorted(messages)}")
        assert messages == set(attendues.values())
        assert {n["action_url"]: n["message"] for n in notifications} == attendues
        assert len(notifications) == generation.json()["generated"]["rdv_demain"] == len(attendues)
        seconde_generation = await client.post("/api/notifications/generate")
        assert seconde_generation.status_code == 200, seconde_generation.text
        assert seconde_generation.json()["generated"]["rdv_demain"] == 0


@pytest.mark.parametrize("jour", ["2026-03-28", "2026-10-24", "2026-10-26"])
@pytest.mark.parametrize("heure", ["12:00", "00:30"])
async def test_regression_astra_v2_par_api(db_session, monkeypatch, jour, heure):
    await verifier_jour(db_session, monkeypatch, f"{jour}T{heure}")


@pytest.mark.parametrize("date_locale", [
    "2026-10-23T23:58", "2026-10-24T23:59",
    "2026-10-25T02:30+02:00", "2026-10-25T02:30+01:00", "2026-10-26T23:59",
    "2027-03-26T23:58", "2027-03-27T00:30",
    "2027-03-28T01:59+01:00", "2027-03-28T03:00+02:00", "2027-03-29T00:01",
])
async def test_dix_rejeux_agenda_apres_astra_v2(db_session, monkeypatch, date_locale):
    await verifier_jour(db_session, monkeypatch, date_locale)


@pytest.mark.parametrize("date_locale", ["2026-10-24T00:30", "2026-10-26T00:30"])
async def test_minuit_trente_avant_et_apres_heure_hiver(db_session, monkeypatch, date_locale):
    await verifier_jour(db_session, monkeypatch, date_locale)


async def test_tache_retard_inferieur_a_un_jour(db_session, monkeypatch):
    maintenant = datetime(2026, 10, 26, 0, 30, tzinfo=PARIS)
    figer(monkeypatch, maintenant)
    db_session.add(Task(title="Contrat", due_date=(maintenant - timedelta(hours=2)).astimezone(UTC)))
    await db_session.flush()
    assert await module._check_overdue_tasks(db_session) == 1
    notif = (await db_session.execute(select(Notification))).scalar_one()
    assert notif.message == "Tâche 'Contrat' en retard de moins d'un jour"


@pytest.mark.parametrize("date_locale", [
    "2026-03-28T00:30", "2026-03-29T00:30", "2026-03-30T00:30",
    "2026-10-25T00:30", "2026-10-25T23:30", "2026-12-31T23:30",
])
async def test_six_rejeux_agenda(db_session, monkeypatch, date_locale):
    await verifier_jour(db_session, monkeypatch, date_locale)


@pytest.mark.parametrize("minutes,retard", [
    (1, "moins d'un jour"), (1439, "moins d'un jour"),
    (1440, "1 jour"), (2940, "2 jours"),
])
async def test_quatre_rejeux_taches(db_session, monkeypatch, minutes, retard):
    maintenant = datetime(2026, 11, 5, 12, tzinfo=UTC)
    figer(monkeypatch, maintenant)
    db_session.add(Task(title="Livraison", due_date=(maintenant - timedelta(minutes=minutes)).replace(tzinfo=None)))
    await db_session.flush()
    assert await module._check_overdue_tasks(db_session) == 1
    notif = (await db_session.execute(select(Notification))).scalar_one()
    assert notif.message == f"Tâche 'Livraison' en retard de {retard}"


async def verifier_relance(db_session, monkeypatch, date_locale, echeance, retard, rappel=False):
    maintenant = datetime.fromisoformat(date_locale).replace(tzinfo=PARIS)
    figer(monkeypatch, maintenant)
    monkeypatch.setattr(relances, "datetime", module.datetime)
    monkeypatch.setattr(entities, "datetime", module.datetime)
    contact = Contact(first_name="Camille", next_follow_up=datetime.fromisoformat(echeance))
    db_session.add(contact)
    db_session.add(Contact(first_name="Demain", next_follow_up=(
        maintenant + timedelta(days=1)
    ).replace(hour=9, tzinfo=None)))
    await db_session.flush()
    await db_session.refresh(contact)
    assert contact.next_follow_up.tzinfo is None  # Heure murale relue depuis SQLite.
    if rappel:
        db_session.add(Notification(
            title="Ancien rappel", message="Relance précédente", source="crm",
            action_url=f"/crm/contacts/{contact.id}",
            created_at=(maintenant - timedelta(days=8)).astimezone(UTC).replace(tzinfo=None),
        ))
        await db_session.flush()
    assert await module._check_inactive_prospects(db_session) == 1
    notifications = (await db_session.execute(select(Notification).where(
        Notification.title == "Relance échue",
    ))).scalars().all()
    assert len(notifications) == 1
    attendu = "aujourd'hui" if retard == 0 else f"il y a {retard} jour{'s' if retard > 1 else ''}"
    assert notifications[0].message == f"Relance de Camille prévue {attendu}"
    assert await module._check_inactive_prospects(db_session) == 0


@pytest.mark.parametrize("maintenant,retard", [
    ("2026-10-24T10:30", 1), ("2026-10-26T08:00", 3),
])
async def test_relance_retard_en_jours_civils(db_session, monkeypatch, maintenant, retard):
    await verifier_relance(db_session, monkeypatch, maintenant, "2026-10-23T09:00", retard)


@pytest.mark.parametrize("maintenant,echeance,retard,rappel", [
    ("2026-10-24T00:01", "2026-10-23T09:00", 1, False),
    ("2026-11-06T08:00", "2026-11-05T09:00", 1, False),
    ("2026-07-14T08:00", "2026-07-13T09:00", 1, False),
    ("2026-03-29T08:00", "2026-03-28T09:00", 1, False),
    ("2026-03-30T00:30", "2026-03-28T09:00", 2, False),
    ("2026-10-25T08:00", "2026-10-24T09:00", 1, False),
    ("2026-11-01T00:30", "2026-10-31T09:00", 1, False),
    ("2027-01-01T00:01", "2026-12-31T09:00", 1, False),
    ("2026-11-06T00:01", "2026-11-06T09:00", 0, False),
    ("2026-11-06T08:00", "2026-10-23T09:00", 14, True),
])
async def test_dix_rejeux_relances_apres_astra(
    db_session, monkeypatch, maintenant, echeance, retard, rappel,
):
    await verifier_relance(db_session, monkeypatch, maintenant, echeance, retard, rappel)


@pytest.mark.parametrize("maintenant,saisie,stockage", [
    ("2026-10-24T00:30", "2026-10-22T22:30:00Z", "2026-10-23T09:00"),
    ("2026-10-26T00:30", "2026-10-24T22:30:00Z", "2026-10-25T09:00"),
    ("2027-03-27T00:30", "2027-03-25T23:30:00Z", "2027-03-26T09:00"),
    ("2027-03-29T00:30", "2027-03-27T23:30:00Z", "2027-03-28T09:00"),
])
async def test_relance_api_garde_le_jour_civil_apres_astra_v2(
    db_session, monkeypatch, maintenant, saisie, stockage,
):
    """B-1166 : vérifier l'écriture normalisée avant le calcul du retard."""
    figer(monkeypatch, datetime.fromisoformat(maintenant).replace(tzinfo=PARIS))
    monkeypatch.setattr(relances, "datetime", module.datetime)
    monkeypatch.setattr(entities, "datetime", module.datetime)
    # Seule l'indexation sémantique est simulée ; validation et SQL restent réels.
    monkeypatch.setattr("app.routers.memory._embed_contact", AsyncMock())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test",
    ) as client:
        reponse = await client.post("/api/memory/contacts", json={
            "first_name": "Camille", "next_follow_up": saisie,
        })
    assert reponse.status_code == 200, reponse.text
    contact = await db_session.get(Contact, reponse.json()["id"])
    assert contact.next_follow_up.tzinfo is None
    assert contact.next_follow_up == datetime.fromisoformat(stockage)
    assert await module._check_inactive_prospects(db_session) == 1
    notification = (await db_session.execute(select(Notification))).scalar_one()
    assert notification.message == "Relance de Camille prévue il y a 1 jour"
    assert await module._check_inactive_prospects(db_session) == 0
