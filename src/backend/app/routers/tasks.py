"""
THÉRÈSE v2 - Tasks Router

API endpoints pour la gestion des tâches locales.
Phase 3 - Tasks/Todos
"""

import logging
import json
from datetime import UTC, datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Task
from app.models.schemas import TaskResponse, CreateTaskRequest, UpdateTaskRequest
from app.models.database import get_session

router = APIRouter()
logger = logging.getLogger(__name__)


# =============================================================================
# CRUD TASKS
# =============================================================================


@router.get("/")
async def list_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    project_id: Optional[str] = Query(None, description="Filter by project"),
    session: AsyncSession = Depends(get_session),
) -> List[TaskResponse]:
    """
    Liste toutes les tâches avec filtres optionnels.

    Filters:
        - status: todo, in_progress, done, cancelled
        - priority: low, medium, high, urgent
        - project_id: UUID du projet lié
    """
    stmt = select(Task)

    if status:
        stmt = stmt.where(Task.status == status)
    if priority:
        stmt = stmt.where(Task.priority == priority)
    if project_id:
        stmt = stmt.where(Task.project_id == project_id)

    # Order by: uncompleted first, then by priority, then by due date
    stmt = stmt.order_by(
        Task.status.desc(),  # todo/in_progress avant done/cancelled
        Task.priority.desc(),
        Task.due_date.asc(),
    )

    result = await session.execute(stmt)
    tasks = result.scalars().all()

    return [
        TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            priority=task.priority,
            due_date=task.due_date.isoformat() if task.due_date else None,
            project_id=task.project_id,
            tags=json.loads(task.tags) if task.tags else None,
            completed_at=task.completed_at.isoformat() if task.completed_at else None,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
        )
        for task in tasks
    ]


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
) -> TaskResponse:
    """Récupère une tâche spécifique."""
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date.isoformat() if task.due_date else None,
        project_id=task.project_id,
        tags=json.loads(task.tags) if task.tags else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )


@router.post("/")
async def create_task(
    request: CreateTaskRequest,
    session: AsyncSession = Depends(get_session),
) -> TaskResponse:
    """Crée une nouvelle tâche."""
    # Parse due_date
    due_date = None
    if request.due_date:
        try:
            due_date = datetime.fromisoformat(request.due_date.replace("Z", ""))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid due_date format")

    # Create task
    task = Task(
        title=request.title,
        description=request.description,
        status=request.status,
        priority=request.priority,
        due_date=due_date,
        project_id=request.project_id,
        tags=json.dumps(request.tags or []),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    session.add(task)
    await session.commit()
    await session.refresh(task)

    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date.isoformat() if task.due_date else None,
        project_id=task.project_id,
        tags=json.loads(task.tags) if task.tags else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )


@router.put("/{task_id}")
async def update_task(
    task_id: str,
    request: UpdateTaskRequest,
    session: AsyncSession = Depends(get_session),
) -> TaskResponse:
    """Met à jour une tâche existante."""
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Update fields
    if request.title is not None:
        task.title = request.title
    if request.description is not None:
        task.description = request.description
    if request.status is not None:
        task.status = request.status
        # Auto-set completed_at when status becomes "done"
        if request.status == "done" and not task.completed_at:
            task.completed_at = datetime.now(UTC)
        elif request.status != "done":
            task.completed_at = None
    if request.priority is not None:
        task.priority = request.priority
    if request.due_date is not None:
        try:
            task.due_date = datetime.fromisoformat(request.due_date.replace("Z", ""))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid due_date format")
    if request.project_id is not None:
        task.project_id = request.project_id
    if request.tags is not None:
        task.tags = json.dumps(request.tags)

    task.updated_at = datetime.now(UTC)

    session.add(task)
    await session.commit()
    await session.refresh(task)

    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date.isoformat() if task.due_date else None,
        project_id=task.project_id,
        tags=json.loads(task.tags) if task.tags else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Supprime une tâche."""
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await session.delete(task)
    await session.commit()

    return {"success": True, "message": "Task deleted"}


# =============================================================================
# ACTIONS
# =============================================================================


@router.patch("/{task_id}/complete")
async def complete_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
) -> TaskResponse:
    """Marque une tâche comme complétée."""
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = "done"
    task.completed_at = datetime.now(UTC)
    task.updated_at = datetime.now(UTC)

    session.add(task)
    await session.commit()
    await session.refresh(task)

    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date.isoformat() if task.due_date else None,
        project_id=task.project_id,
        tags=json.loads(task.tags) if task.tags else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )


@router.patch("/{task_id}/uncomplete")
async def uncomplete_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
) -> TaskResponse:
    """Marque une tâche comme non complétée."""
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = "todo"
    task.completed_at = None
    task.updated_at = datetime.now(UTC)

    session.add(task)
    await session.commit()
    await session.refresh(task)

    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date.isoformat() if task.due_date else None,
        project_id=task.project_id,
        tags=json.loads(task.tags) if task.tags else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )
