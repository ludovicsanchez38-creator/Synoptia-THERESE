"""P-134 (persona Nathalie, cycle 13) : « Relancer Karim Benali » à l'Accueil
ouvrait la liste des tâches, jamais la personne à rappeler. Le brief porte le
contact de la tâche pour que l'écran ouvre sa fiche."""

from datetime import date, datetime, time

import pytest
from app.models.entities import Contact, Task
from httpx import AsyncClient

JOUR_DU_BRIEF = date(2026, 9, 25)


@pytest.mark.asyncio
async def test_une_tache_du_brief_dit_la_personne_concernee(
    client: AsyncClient, db_session, monkeypatch
):
    monkeypatch.setattr("app.routers.dashboard.date_civile_paris", lambda *_a, **_k: JOUR_DU_BRIEF)
    db_session.add(Contact(id="c-karim", first_name="Karim", last_name="Benali"))
    db_session.add(Task(id="tk-relance", title="Relancer Karim Benali", status="todo",
                        due_date=datetime.combine(JOUR_DU_BRIEF, time(9, 0)), contact_id="c-karim"))
    db_session.add(Task(id="tk-seule", title="Ranger le bureau", status="todo",
                        due_date=datetime.combine(JOUR_DU_BRIEF, time(9, 0))))
    await db_session.commit()

    corps = (await client.get("/api/dashboard/today")).json()
    par_id = {t["id"]: t for t in corps["urgent_tasks"]}
    assert par_id["tk-relance"]["contact_id"] == "c-karim"
    assert par_id["tk-seule"]["contact_id"] is None
