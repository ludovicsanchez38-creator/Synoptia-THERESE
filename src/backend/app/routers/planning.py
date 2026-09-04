"""API de calcul et de lecture du planning projet (P-039, lot A)."""

import json
import logging
from datetime import UTC, datetime

from app.models.database import get_session
from app.models.entities import (
    PlanningSnapshot,
    Project,
    Task,
    TaskDependency,
    TaskSchedule,
)
from app.models.planning_schemas import (
    CalculateScheduleRequest,
    ProjectScheduleResponse,
)
from app.services.planning import (
    ENGINE_VERSION,
    PlanningDependencyInput,
    PlanningTaskInput,
    calculate_schedule,
    fingerprint_inputs,
    planning_result_to_dict,
    planning_result_to_json,
)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

router = APIRouter()
logger = logging.getLogger(__name__)


def _utc_if_naive(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)


async def _project_inputs(
    session: AsyncSession, project_id: str
) -> tuple[list[PlanningTaskInput], list[PlanningDependencyInput]]:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projet non trouvé")

    tasks = (
        await session.execute(
            select(Task).where(Task.project_id == project_id).order_by(Task.id)
        )
    ).scalars().all()
    task_ids = [task.id for task in tasks]
    if not task_ids:
        return [], []

    schedules = (
        await session.execute(
            select(TaskSchedule).where(TaskSchedule.task_id.in_(task_ids))
        )
    ).scalars().all()
    schedule_by_task = {schedule.task_id: schedule for schedule in schedules}

    dependencies = (
        await session.execute(
            select(TaskDependency)
            .where(
                or_(
                    TaskDependency.predecessor_task_id.in_(task_ids),
                    TaskDependency.successor_task_id.in_(task_ids),
                )
            )
            .order_by(
                TaskDependency.predecessor_task_id,
                TaskDependency.successor_task_id,
                TaskDependency.kind,
            )
        )
    ).scalars().all()

    task_inputs = []
    for task in tasks:
        schedule = schedule_by_task.get(task.id)
        task_inputs.append(
            PlanningTaskInput(
                id=task.id,
                title=task.title,
                duration_optimistic_minutes=(
                    schedule.duration_optimistic_minutes if schedule else None
                ),
                duration_likely_minutes=(
                    schedule.duration_likely_minutes if schedule else None
                ),
                duration_pessimistic_minutes=(
                    schedule.duration_pessimistic_minutes if schedule else None
                ),
                constraint_type=schedule.constraint_type if schedule else None,
                constraint_at=(
                    _utc_if_naive(schedule.constraint_at) if schedule else None
                ),
                progress_percent=schedule.progress_percent if schedule else 0,
                is_milestone=schedule.is_milestone if schedule else False,
                billing_milestone=(
                    schedule.billing_milestone if schedule else False
                ),
            )
        )
    dependency_inputs = [
        PlanningDependencyInput(
            predecessor_task_id=dependency.predecessor_task_id,
            successor_task_id=dependency.successor_task_id,
            kind=dependency.kind,
            lag_minutes=dependency.lag_minutes,
        )
        for dependency in dependencies
    ]
    return task_inputs, dependency_inputs


def _snapshot_response(
    snapshot: PlanningSnapshot, *, reused: bool
) -> ProjectScheduleResponse:
    try:
        result = json.loads(snapshot.result_json)
    except (TypeError, json.JSONDecodeError) as exc:
        logger.error("Snapshot de planning %s illisible", snapshot.id, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Le résultat de planning enregistré est illisible",
        ) from exc
    return ProjectScheduleResponse.model_validate(
        {
            "snapshot_id": snapshot.id,
            "project_id": snapshot.project_id,
            "engine_version": snapshot.engine_version,
            "input_hash": snapshot.input_hash,
            "calculated_at": _utc_if_naive(snapshot.calculated_at),
            **result,
            "reused_snapshot": reused,
        }
    )


@router.get("/{project_id}/schedule", response_model=ProjectScheduleResponse)
async def get_project_schedule(
    project_id: str,
    session: AsyncSession = Depends(get_session),
) -> ProjectScheduleResponse:
    """Retourne le dernier snapshot sans recalcul ni mutation."""
    if await session.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    snapshot = (
        await session.execute(
            select(PlanningSnapshot)
            .where(PlanningSnapshot.project_id == project_id)
            .order_by(PlanningSnapshot.calculated_at.desc(), PlanningSnapshot.id.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Aucun planning calculé")
    return _snapshot_response(snapshot, reused=False)


@router.post(
    "/{project_id}/schedule/calculate",
    response_model=ProjectScheduleResponse,
)
async def calculate_project_schedule(
    project_id: str,
    request: CalculateScheduleRequest,
    session: AsyncSession = Depends(get_session),
) -> ProjectScheduleResponse:
    """Calcule un snapshot déterministe et réutilise l'identique."""
    tasks, dependencies = await _project_inputs(session, project_id)
    input_hash = fingerprint_inputs(
        tasks,
        dependencies,
        request.starts_at,
        request.timezone,
    )
    existing = (
        await session.execute(
            select(PlanningSnapshot).where(
                PlanningSnapshot.project_id == project_id,
                PlanningSnapshot.engine_version == ENGINE_VERSION,
                PlanningSnapshot.input_hash == input_hash,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return _snapshot_response(existing, reused=True)

    result = calculate_schedule(
        tasks,
        dependencies,
        starts_at=request.starts_at,
        timezone=request.timezone,
    )
    snapshot = PlanningSnapshot(
        project_id=project_id,
        engine_version=ENGINE_VERSION,
        input_hash=input_hash,
        calculated_at=datetime.now(UTC),
        state=result.state,
        warnings_json=json.dumps(result.warnings, ensure_ascii=False),
        missing_fields_json=json.dumps(result.missing_fields, ensure_ascii=False),
        result_json=planning_result_to_json(result),
    )
    session.add(snapshot)
    try:
        await session.commit()
        await session.refresh(snapshot)
    except IntegrityError:
        # Deux calculs identiques simultanés convergent vers le même snapshot.
        await session.rollback()
        existing = (
            await session.execute(
                select(PlanningSnapshot).where(
                    PlanningSnapshot.project_id == project_id,
                    PlanningSnapshot.engine_version == ENGINE_VERSION,
                    PlanningSnapshot.input_hash == input_hash,
                )
            )
        ).scalar_one()
        return _snapshot_response(existing, reused=True)
    return ProjectScheduleResponse.model_validate(
        {
            "snapshot_id": snapshot.id,
            "project_id": project_id,
            "input_hash": input_hash,
            "calculated_at": _utc_if_naive(snapshot.calculated_at),
            **planning_result_to_dict(result),
            "reused_snapshot": False,
        }
    )


@router.get(
    "/{project_id}/schedule/snapshots/{snapshot_id}",
    response_model=ProjectScheduleResponse,
)
async def get_project_schedule_snapshot(
    project_id: str,
    snapshot_id: str,
    session: AsyncSession = Depends(get_session),
) -> ProjectScheduleResponse:
    """Relit un snapshot précis, toujours sans recalcul."""
    snapshot = await session.get(PlanningSnapshot, snapshot_id)
    if snapshot is None or snapshot.project_id != project_id:
        raise HTTPException(status_code=404, detail="Snapshot de planning non trouvé")
    return _snapshot_response(snapshot, reused=False)
