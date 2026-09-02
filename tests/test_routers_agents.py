"""Le total d'une liste filtrée compte les lignes du filtre, pas la table.

B-102 : `GET /api/agents/tasks?status=merged` rendait 1 ligne et `total=3`.
Le `select(func.count(...))` du compte ne reprenait pas le `where` de la
requête de lignes, aux deux routes de listage du fichier.
"""

from datetime import UTC, datetime

import pytest
from app.models.entities_agents import AgentSession, AgentTask
from httpx import AsyncClient


async def _semer_taches(db_session) -> None:
    """Deux tâches `pending`, une `merged`."""
    db_session.add_all(
        [
            AgentTask(id="tache-pending-1", title="Une", status="pending"),
            AgentTask(id="tache-pending-2", title="Deux", status="pending"),
            AgentTask(id="tache-merged-1", title="Trois", status="merged"),
        ]
    )
    await db_session.commit()


async def _semer_sessions(db_session) -> None:
    """Deux sessions `running`, une `done`."""
    db_session.add_all(
        [
            AgentSession(id="session-running-1", instruction="Une", status="running"),
            AgentSession(id="session-running-2", instruction="Deux", status="running"),
            AgentSession(id="session-done-1", instruction="Trois", status="done"),
        ]
    )
    await db_session.commit()


@pytest.mark.asyncio
async def test_total_des_taches_suit_le_filtre_de_statut(client: AsyncClient, db_session):
    """Le total annoncé pour ?status=merged vaut le nombre de lignes rendues."""
    await _semer_taches(db_session)

    reponse = await client.get("/api/agents/tasks?status=merged")
    assert reponse.status_code == 200
    corps = reponse.json()

    assert len(corps["tasks"]) == 1
    assert corps["total"] == 1, (
        f"total={corps['total']} annonce des lignes que la liste ne montre pas "
        f"({len(corps['tasks'])} rendue(s))"
    )

    sans_filtre = (await client.get("/api/agents/tasks")).json()
    assert sans_filtre["total"] == 3


@pytest.mark.asyncio
async def test_total_des_sessions_suit_le_filtre_de_statut(client: AsyncClient, db_session):
    """Même invariant sur la seconde route de listage du fichier."""
    await _semer_sessions(db_session)

    reponse = await client.get("/api/agents/sessions?status=done")
    assert reponse.status_code == 200
    corps = reponse.json()

    assert len(corps["sessions"]) == 1
    assert corps["total"] == 1, (
        f"total={corps['total']} annonce des lignes que la liste ne montre pas "
        f"({len(corps['sessions'])} rendue(s))"
    )

    sans_filtre = (await client.get("/api/agents/sessions")).json()
    assert sans_filtre["total"] == 3


@pytest.mark.asyncio
async def test_total_des_taches_compte_le_filtre_pas_la_page(client: AsyncClient, db_session):
    """`total` n'est ni la taille de la page ni la taille de la table.

    Cinq tâches `pending`, une `merged`, une page de deux : le total doit
    valoir cinq (le filtre), jamais deux (la page) ni six (la table).
    """
    db_session.add_all(
        [AgentTask(id=f"tache-page-{i}", title=f"T{i}", status="pending") for i in range(5)]
        + [AgentTask(id="tache-page-merged", title="M", status="merged")]
    )
    await db_session.commit()

    corps = (await client.get("/api/agents/tasks?status=pending&limit=2")).json()

    assert len(corps["tasks"]) == 2
    assert corps["total"] == 5, (
        f"total={corps['total']} : attendu 5 (les lignes du filtre), "
        "ni 2 (la page) ni 6 (la table)"
    )


@pytest.mark.asyncio
async def test_total_des_sessions_compte_le_filtre_pas_la_page(client: AsyncClient, db_session):
    """Même verrou sur les sessions."""
    db_session.add_all(
        [
            AgentSession(id=f"session-page-{i}", instruction=f"S{i}", status="running")
            for i in range(5)
        ]
        + [
            AgentSession(
                id="session-page-done",
                instruction="D",
                status="done",
                finished_at=datetime.now(UTC),
            )
        ]
    )
    await db_session.commit()

    corps = (await client.get("/api/agents/sessions?status=running&limit=2")).json()

    assert len(corps["sessions"]) == 2
    assert corps["total"] == 5, (
        f"total={corps['total']} : attendu 5 (les lignes du filtre), "
        "ni 2 (la page) ni 6 (la table)"
    )
