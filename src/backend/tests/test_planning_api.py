"""P-039 : API locale de calcul et snapshots de planning."""

from datetime import UTC, datetime

import pytest
from app.main import app
from app.models.entities import (
    PlanningResource,
    PlanningSnapshot,
    Project,
    Task,
    TaskAllocation,
    TaskDependency,
    TaskSchedule,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select


async def _project_with_chain(session: AsyncSession) -> Project:
    project = Project(name="Déploiement")
    first = Task(id="task-a", title="Préparer", project_id=project.id)
    second = Task(id="task-b", title="Livrer", project_id=project.id)
    session.add(project)
    session.add(first)
    session.add(second)
    session.add(
        TaskSchedule(
            task_id=first.id,
            duration_optimistic_minutes=60,
            duration_likely_minutes=60,
            duration_pessimistic_minutes=60,
        )
    )
    session.add(
        TaskSchedule(
            task_id=second.id,
            duration_optimistic_minutes=120,
            duration_likely_minutes=120,
            duration_pessimistic_minutes=120,
        )
    )
    session.add(
        TaskDependency(
            predecessor_task_id=first.id,
            successor_task_id=second.id,
        )
    )
    await session.commit()
    return project


@pytest.mark.asyncio
async def test_calcul_snapshot_lecture_et_reutilisation(async_client, db_session):
    project = await _project_with_chain(db_session)
    payload = {"starts_at": "2026-09-07T09:00:00+02:00"}

    calculated = await async_client.post(
        f"/api/projects/{project.id}/schedule/calculate", json=payload
    )
    assert calculated.status_code == 200, calculated.text
    body = calculated.json()
    assert body["state"] == "complete"
    assert body["critical_path"] == ["task-a", "task-b"]
    assert body["project_duration_minutes"] == 180
    assert body["finishes_at"] == "2026-09-07T12:00:00+02:00"
    assert body["reused_snapshot"] is False

    latest = await async_client.get(f"/api/projects/{project.id}/schedule")
    assert latest.status_code == 200
    assert latest.json()["snapshot_id"] == body["snapshot_id"]

    reused = await async_client.post(
        f"/api/projects/{project.id}/schedule/calculate", json=payload
    )
    assert reused.status_code == 200
    assert reused.json()["snapshot_id"] == body["snapshot_id"]
    assert reused.json()["reused_snapshot"] is True

    archived = await async_client.get(
        f"/api/projects/{project.id}/schedule/snapshots/{body['snapshot_id']}"
    )
    assert archived.status_code == 200
    snapshots = (
        await db_session.execute(
            select(PlanningSnapshot).where(
                PlanningSnapshot.project_id == project.id
            )
        )
    ).scalars().all()
    assert len(snapshots) == 1


@pytest.mark.asyncio
async def test_projet_incomplet_n_invente_aucune_duree(async_client, db_session):
    project = Project(name="Projet incomplet")
    db_session.add(project)
    db_session.add(Task(id="task-empty", title="À estimer", project_id=project.id))
    await db_session.commit()

    response = await async_client.post(
        f"/api/projects/{project.id}/schedule/calculate",
        json={"starts_at": "2026-09-07T09:00:00+02:00"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "incomplete"
    assert body["project_duration_minutes"] is None
    assert body["tasks"][0]["expected_duration_minutes"] is None
    assert body["missing_fields"] == [
        "tasks.task-empty.duration_likely_minutes",
        "tasks.task-empty.duration_optimistic_minutes",
        "tasks.task-empty.duration_pessimistic_minutes",
    ]


@pytest.mark.asyncio
async def test_dependance_hors_projet_rend_le_planning_invalide(
    async_client, db_session
):
    first_project = Project(name="Projet A")
    second_project = Project(name="Projet B")
    first = Task(id="task-a", title="A", project_id=first_project.id)
    second = Task(id="task-b", title="B", project_id=second_project.id)
    db_session.add(first_project)
    db_session.add(second_project)
    db_session.add(first)
    db_session.add(second)
    db_session.add(
        TaskSchedule(
            task_id=first.id,
            duration_optimistic_minutes=30,
            duration_likely_minutes=30,
            duration_pessimistic_minutes=30,
        )
    )
    db_session.add(
        TaskDependency(
            predecessor_task_id=first.id,
            successor_task_id=second.id,
        )
    )
    await db_session.commit()

    response = await async_client.post(
        f"/api/projects/{first_project.id}/schedule/calculate",
        json={"starts_at": "2026-09-07T09:00:00+02:00"},
    )

    assert response.status_code == 200
    assert response.json()["state"] == "invalid"
    assert "tâche absente ou hors projet" in response.json()["errors"][0]


@pytest.mark.asyncio
async def test_projet_et_snapshot_absents_rendent_404(async_client):
    calculation = await async_client.post(
        "/api/projects/absent/schedule/calculate",
        json={"starts_at": "2026-09-07T09:00:00+02:00"},
    )
    latest = await async_client.get("/api/projects/absent/schedule")
    snapshot = await async_client.get(
        "/api/projects/absent/schedule/snapshots/absent"
    )

    assert calculation.status_code == 404
    assert latest.status_code == 404
    assert snapshot.status_code == 404


@pytest.mark.asyncio
async def test_date_de_depart_sans_fuseau_est_refusee(async_client, db_session):
    project = Project(name="Fuseau")
    db_session.add(project)
    await db_session.commit()

    response = await async_client.post(
        f"/api/projects/{project.id}/schedule/calculate",
        json={"starts_at": "2026-09-07T09:00:00"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_supprimer_une_tache_purge_son_planning(async_client, db_session):
    await _project_with_chain(db_session)

    response = await async_client.delete("/api/tasks/task-a")
    assert response.status_code == 200, response.text

    schedule = await db_session.get(TaskSchedule, "task-a")
    dependencies = (
        await db_session.execute(
            select(TaskDependency).where(
                TaskDependency.predecessor_task_id == "task-a"
            )
        )
    ).scalars().all()
    assert schedule is None
    assert dependencies == []


@pytest.mark.asyncio
async def test_supprimer_un_projet_purge_tout_son_perimetre_planning(
    async_client, db_session
):
    project = await _project_with_chain(db_session)
    resource = PlanningResource(project_id=project.id, name="Ludo")
    db_session.add(resource)
    db_session.add(
        TaskAllocation(task_id="task-a", resource_id=resource.id)
    )
    await db_session.commit()
    calculated = await async_client.post(
        f"/api/projects/{project.id}/schedule/calculate",
        json={"starts_at": "2026-09-07T09:00:00+02:00"},
    )
    assert calculated.status_code == 200

    await db_session.delete(project)
    await db_session.commit()

    assert await db_session.get(PlanningResource, resource.id) is None
    assert await db_session.get(TaskSchedule, "task-a") is None
    snapshots = (
        await db_session.execute(
            select(PlanningSnapshot).where(
                PlanningSnapshot.project_id == project.id
            )
        )
    ).scalars().all()
    assert snapshots == []


def test_snapshot_conserve_un_horodatage_utc():
    snapshot = PlanningSnapshot(
        project_id="project",
        engine_version="test",
        input_hash="0" * 64,
        calculated_at=datetime.now(UTC),
        state="complete",
        result_json="{}",
    )
    assert snapshot.calculated_at.tzinfo is UTC


def test_lot_a_n_expose_aucune_mutation_de_planning():
    paths = {
        path: set(methods)
        for path, methods in app.openapi()["paths"].items()
        if "/schedule" in path
    }

    assert paths == {
        "/api/projects/{project_id}/schedule": {"get"},
        "/api/projects/{project_id}/schedule/calculate": {"post"},
        "/api/projects/{project_id}/schedule/snapshots/{snapshot_id}": {"get"},
    }
