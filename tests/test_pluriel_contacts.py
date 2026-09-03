"""Finding 6 (revue 30/08) : deux fiches, la même adresse, le CRM en prenait une.

`limit(1)` global : « Générer une réponse » injectait notes, score et
téléphone de l'autre fiche. Un échec franc : on n'en prend aucune.
"""

from __future__ import annotations

from datetime import date, datetime, time

import pytest
from app.models.entities import Calendar, CalendarEvent, Contact

#: Jour du brief posé par le test, jamais lu sur le runner (B-261).
JOUR_DU_BRIEF = date(2026, 6, 15)


@pytest.mark.asyncio
async def test_deux_fiches_meme_email_n_en_prend_aucune(db_session):
    db_session.add_all([
        Contact(first_name="Jean", last_name="A", email="jean@x.fr", notes="notes A", score=10),
        Contact(first_name="Jean", last_name="B", email="jean@x.fr", notes="notes B", score=90),
    ])
    await db_session.commit()
    from app.routers.email import get_crm_contact_by_email

    contact = await get_crm_contact_by_email(db_session, "jean@x.fr")
    assert contact is None


@pytest.mark.asyncio
async def test_une_fiche_est_retrouvee(db_session):
    unique = Contact(first_name="Lea", last_name="Seul", email="lea@x.fr", notes="ok")
    db_session.add(unique)
    await db_session.commit()
    from app.routers.email import get_crm_contact_by_email

    contact = await get_crm_contact_by_email(db_session, "LEA@x.fr")
    assert contact is not None
    assert contact.notes == "ok"


@pytest.mark.asyncio
async def test_brief_n_attache_pas_un_contact_ambigu(client, db_session, monkeypatch):
    """B-261 : le brief compte en jour civil de PARIS, pas en jour du runner.

    `date.today()` posait le rendez-vous sur la date locale du runner ; sous
    `TZ=UTC` après 22 h, le brief ne le voyait plus et `next(...)` levait une
    StopIteration, que la boucle asyncio rendait en RuntimeError illisible.
    On pose l'horloge du brief, et l'absence est nommée.
    """
    monkeypatch.setattr(
        "app.routers.dashboard.date_civile_paris", lambda *_a, **_k: JOUR_DU_BRIEF
    )
    db_session.add_all([
        Contact(id="c-a", first_name="Jean", last_name="A", email="jean@x.fr"),
        Contact(id="c-b", first_name="Jean", last_name="B", email="jean@x.fr"),
        Calendar(id="cal-amb", summary="Agenda", provider="local"),
        CalendarEvent(
            id="evt-amb",
            calendar_id="cal-amb",
            summary="Point",
            start_datetime=datetime.combine(JOUR_DU_BRIEF, time(10, 0)),
            end_datetime=datetime.combine(JOUR_DU_BRIEF, time(11, 0)),
            attendees='[{"email":"jean@x.fr"}]',
        ),
    ])
    await db_session.commit()

    reponse = await client.get("/api/dashboard/today")
    assert reponse.status_code == 200
    point = next(
        (e for e in reponse.json()["events"] if e["id"] == "evt-amb"), None
    )
    assert point is not None, "le rendez-vous du jour doit être au brief"
    assert point["crm_contact_ids"] == []
