"""B-1150 : demain désigne une date civile à Paris, même au changement d'heure."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from app.models.entities import Calendar, CalendarEvent, Notification, Task
from app.services import notification_service as module
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
