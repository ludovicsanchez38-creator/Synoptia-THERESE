"""B-1086 (cycle 12, réparé au cycle 13) : une mission d'Atelier restée
« en cours » après un arrêt brutal ne verrouille plus l'Atelier.

`recuperer_taches_orphelines` ne reprend que les ProcessingTask, alors que
le verrou de l'Atelier compte les AgentTask `pending` ou `in_progress`
(`routers/agents.py`, 409 sur /request et /spawn). Après un arrêt brutal,
l'Atelier restait bloqué à vie, et l'annulation rendait 409 faute de
processus. Au démarrage, une mission orpheline passe en erreur avec un
message qui le dit.
"""

import inspect

import pytest
from app.models.entities_agents import AgentTask
from sqlalchemy import func, select


@pytest.mark.asyncio
async def test_une_mission_orpheline_est_liberee_au_demarrage(db_session):
    from app.services.task_registry import recuperer_missions_orphelines

    db_session.add(AgentTask(id="mission-orpheline", title="Corriger", description="x", status="in_progress"))
    db_session.add(AgentTask(id="mission-attente", title="Attendre", description="x", status="pending"))
    db_session.add(AgentTask(id="mission-relue", title="Relue", description="x", status="review"))
    await db_session.commit()

    assert await recuperer_missions_orphelines(db_session) == 2

    actives = (await db_session.execute(
        select(func.count(AgentTask.id)).where(AgentTask.status.in_(["pending", "in_progress"]))
    )).scalar()
    assert actives == 0
    orpheline = await db_session.get(AgentTask, "mission-orpheline")
    assert orpheline.status == "error"
    assert "arrêt de l'application" in (orpheline.error or "")
    assert (await db_session.get(AgentTask, "mission-relue")).status == "review"


def test_le_demarrage_appelle_la_recuperation_des_missions():
    import app.main as module_main

    source = inspect.getsource(module_main)
    assert "recuperer_missions_orphelines(session)" in source
