"""B-1150 : demain désigne une date civile à Paris, même au changement d'heure."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from app.models import entities
from app.models.entities import Calendar, CalendarEvent, Contact, Notification, Task
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
    maintenant = datetime.fromisoformat(date_locale).replace(tzinfo=PARIS)
    figer(monkeypatch, maintenant)
    calendrier = Calendar(summary="Agenda local")
    db_session.add(calendrier)
    await db_session.flush()
    demain = (maintenant + timedelta(days=1)).replace(hour=0, minute=0)
    heures = [demain - timedelta(seconds=1), demain, demain.replace(hour=9, minute=15),
              demain + timedelta(days=1) - timedelta(seconds=1), demain + timedelta(days=1)]
    for i, heure in enumerate(heures):
        db_session.add(CalendarEvent(
            id=f"rdv-{i}", calendar_id=calendrier.id, summary=f"Rendez-vous {i}",
            start_datetime=heure.astimezone(UTC).replace(tzinfo=None),
        ))
    await db_session.flush()
    assert await module._check_upcoming_events(db_session) == 3
    notifications = (await db_session.execute(select(Notification))).scalars().all()
    assert {n.action_url for n in notifications} == {f"/calendar/events/rdv-{i}" for i in (1, 2, 3)}
    assert next(n.message for n in notifications if n.action_url.endswith("rdv-2")) == "RDV demain à 09h15 : Rendez-vous 2"


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
