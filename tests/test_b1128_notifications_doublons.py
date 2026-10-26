"""B-1128 : des doublons historiques ne doivent pas annuler le passage."""
from datetime import UTC, datetime, timedelta

import pytest
from app.models.entities import Calendar, CalendarEvent, Contact, Invoice, Notification, Task
from app.services import notification_service as service
from sqlmodel import select

RUBRIQUES = {"invoice": "factures_impayees", "crm": "prospects_inactifs",
             "task": "taches_en_retard", "calendar": "rdv_demain"}


async def verifier_passage(session, source, nombre=2, heures=1, lu=False, nom="initial"):
    maintenant = datetime.now(UTC)
    hier = maintenant - timedelta(days=45)
    demain = (maintenant + timedelta(days=1)).replace(hour=10, minute=0)
    calendrier = Calendar(summary=nom)
    session.add(calendrier)
    urls = {}
    for suffixe in ("ancien", "neuf"):
        contact = Contact(first_name=f"{nom}-{suffixe}", next_follow_up=hier)
        session.add(contact)
        await session.flush()
        facture = Invoice(invoice_number=f"{nom}-{suffixe}", contact_id=contact.id,
                          due_date=hier, status="sent")
        tache = Task(title=f"{nom}-{suffixe}", due_date=hier)
        rdv = CalendarEvent(id=f"{nom}-{suffixe}", calendar_id=calendrier.id,
                            summary=f"{nom}-{suffixe}", start_datetime=demain)
        session.add_all([facture, tache, rdv])
        urls[suffixe] = {"invoice": f"/invoices/{facture.id}", "crm": f"/crm/contacts/{contact.id}",
                         "task": f"/tasks/{tache.id}", "calendar": f"/calendar/events/{rdv.id}"}
    for _ in range(nombre):
        session.add(Notification(title=nom, message="Déjà signalé", source=source,
                                 action_url=urls["ancien"][source], is_read=lu,
                                 created_at=maintenant - timedelta(hours=heures)))
    await session.commit()
    fenetre = {"invoice": 168, "crm": 168, "task": 72, "calendar": 12}[source]
    attendus = {rubrique: 1 if s == source and heures < fenetre else 2
                for s, rubrique in RUBRIQUES.items()}
    assert await service.generate_automatic_notifications() == attendus
    # Vérifier le commit réel, y compris les notifications des étapes précédentes.
    notifs = (await session.execute(select(Notification))).scalars().all()
    assert len(notifs) == nombre + sum(attendus.values())
    for url in urls["neuf"].values():
        assert sum(n.action_url == url for n in notifs) == 1
    assert await service.generate_automatic_notifications() == dict.fromkeys(RUBRIQUES.values(), 0)


@pytest.mark.parametrize("source", RUBRIQUES)
async def test_un_doublon_ne_bloque_aucune_rubrique(db_session, source):
    await verifier_passage(db_session, source)


# Entrées inventées après le correctif : multiplicité, ancienneté et lecture.
@pytest.mark.parametrize("source,nombre,heures,lu,nom", [
    ("invoice", 4, 5, False, "kiwi"),
    ("invoice", 3, 166, True, "lierre"),
    ("invoice", 5, 172, False, "mousse"),
    ("crm", 6, 32, True, "nacre"),
    ("crm", 3, 180, False, "osier"),
    ("task", 4, 70, True, "pin"),
    ("task", 5, 74, False, "quartz"),
    ("calendar", 3, 10, False, "roseau"),
    ("calendar", 4, 14, True, "sauge"),
    ("calendar", 6, 4, True, "tilleul"),
])
async def test_rejeu_apres_correctif(db_session, source, nombre, heures, lu, nom):
    await verifier_passage(db_session, source, nombre, heures, lu, nom)
