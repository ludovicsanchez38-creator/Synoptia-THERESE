"""
THÉRÈSE v2 - Tasks Router

API endpoints pour la gestion des tâches locales.
Phase 3 - Tasks/Todos
"""

import json
import logging
from datetime import UTC, datetime

from app.models.database import get_session
from app.models.entities import Contact, Project, Task
from app.models.schemas import CreateTaskRequest, TaskResponse, UpdateTaskRequest
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

# B-346 : rangs métier des colonnes texte, pour un tri qui ne dépende pas de
# l'alphabet (voir list_tasks).
_RANG_DE_PRIORITE = case(
    (Task.priority == "urgent", 4),
    (Task.priority == "high", 3),
    (Task.priority == "medium", 2),
    (Task.priority == "low", 1),
    else_=0,
)
_RANG_DE_STATUT = case(
    (Task.status == "in_progress", 4),
    (Task.status == "todo", 3),
    (Task.status == "done", 2),
    (Task.status == "cancelled", 1),
    else_=0,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# =============================================================================
# CRUD TASKS
# =============================================================================


async def _verifier_rattachements(
    session: AsyncSession, project_id: str | None, contact_id: str | None
) -> None:
    """B-186 : une tâche ne s'accroche qu'à un dossier ou une personne qui existe.

    Sans ce contrôle, `project_id="projet-fantome"` était recopié tel quel :
    la tâche ne remontait dans aucun filtre par projet réel et survivait à la
    suppression de tous les projets. `POST /api/files/upload` rend 404
    « Projet non trouvé » avant d'écrire ; c'est le même devoir ici.
    """
    if project_id is not None and await session.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    if contact_id is not None and await session.get(Contact, contact_id) is None:
        raise HTTPException(status_code=404, detail="Contact non trouvé")


# Collection exposee avec ET sans slash final (anti-redirection 307).
@router.get("", include_in_schema=False)
@router.get("/")
async def list_tasks(
    status: str | None = Query(None, description="Filter by status"),
    priority: str | None = Query(None, description="Filter by priority"),
    project_id: str | None = Query(None, description="Filter by project"),
    contact_id: str | None = Query(None, description="Filtrer par contact"),
    limit: int = Query(200, ge=1, le=1000, description="Nombre max de tâches"),
    offset: int = Query(0, ge=0, description="Décalage de pagination"),
    session: AsyncSession = Depends(get_session),
) -> list[TaskResponse]:
    """
    Liste toutes les tâches avec filtres optionnels.

    Filters:
        - status: todo, in_progress, done, cancelled
        - priority: low, medium, high, urgent
        - project_id: UUID du projet lié
        - contact_id: UUID du contact concerné

    US-016 : paginé (limit/offset, défaut 200) - la réponse était non bornée,
    des centaines de tâches terminées étaient sérialisées à chaque ouverture.
    """
    stmt = select(Task)

    if status:
        stmt = stmt.where(Task.status == status)
    if priority:
        stmt = stmt.where(Task.priority == priority)
    if project_id:
        stmt = stmt.where(Task.project_id == project_id)
    if contact_id:
        stmt = stmt.where(Task.contact_id == contact_id)

    # Order by: uncompleted first, then by priority, then by due date.
    # B-346 (05/09/2026) : `Task.priority.desc()` comparait du TEXTE, et
    # rendait « urgent, medium, low, high » : une tâche haute sortait
    # dernière. Un ordre métier se donne par une table de rang, pas par
    # l'alphabet ; le statut tenait par chance (t > i > d > c), il reçoit
    # la sienne aussi.
    stmt = stmt.order_by(
        _RANG_DE_STATUT.desc(),  # todo/in_progress avant done/cancelled
        _RANG_DE_PRIORITE.desc(),
        Task.due_date.asc(),
        Task.id.asc(),  # ordre TOTAL : pagination déterministe
    )
    stmt = stmt.limit(limit).offset(offset)

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
            contact_id=task.contact_id,
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
        raise HTTPException(status_code=404, detail="Tâche introuvable.")

    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date.isoformat() if task.due_date else None,
        project_id=task.project_id,
        contact_id=task.contact_id,
        tags=json.loads(task.tags) if task.tags else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )


@router.post("", include_in_schema=False)
@router.post("/")
async def create_task(
    request: CreateTaskRequest,
    session: AsyncSession = Depends(get_session),
) -> TaskResponse:
    """Crée une nouvelle tâche."""
    await _verifier_rattachements(session, request.project_id, request.contact_id)

    # Parse due_date
    due_date = None
    if request.due_date:
        try:
            due_date = datetime.fromisoformat(request.due_date.replace("Z", ""))
        except ValueError:
            raise HTTPException(status_code=400, detail="Format de date d'échéance invalide (attendu : ISO 8601).")

    # Create task
    task = Task(
        title=request.title,
        description=request.description,
        status=request.status,
        priority=request.priority,
        due_date=due_date,
        project_id=request.project_id,
        contact_id=request.contact_id,
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
        contact_id=task.contact_id,
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
        raise HTTPException(status_code=404, detail="Tâche introuvable.")

    # B-032 : le contact était contrôlé à la création et ignoré ici. Même
    # devoir des deux côtés, sinon la porte de service reste ouverte.
    await _verifier_rattachements(session, request.project_id, request.contact_id)

    # Update fields.
    # B-423 (05/09/2026) : les champs facultatifs sont déclarés `str | None =
    # None`, donc « absent » et « null » se confondaient sur `is not None` :
    # impossible d'effacer une description, une échéance ou un rattachement
    # par PUT. Un champ ENVOYÉ à null efface ; un champ absent ne touche à rien.
    envoyes = request.model_fields_set
    if request.title is not None:
        task.title = request.title
    if "description" in envoyes:
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
    if "due_date" in envoyes:
        if request.due_date is None:
            task.due_date = None
        else:
            try:
                task.due_date = datetime.fromisoformat(request.due_date.replace("Z", ""))
            except ValueError:
                raise HTTPException(status_code=400, detail="Format de date d'échéance invalide (attendu : ISO 8601).")
    if "project_id" in envoyes:
        task.project_id = request.project_id
    # B-032 : champ déclaré au schéma, accepté en 200, puis jeté - la réponse
    # comme la relecture rendaient l'ancien contact, sans un avertissement.
    if "contact_id" in envoyes:
        task.contact_id = request.contact_id
    if "tags" in envoyes:
        task.tags = json.dumps(request.tags) if request.tags is not None else None

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
        contact_id=task.contact_id,
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
        raise HTTPException(status_code=404, detail="Tâche introuvable.")

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
        raise HTTPException(status_code=404, detail="Tâche introuvable.")

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
        contact_id=task.contact_id,
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
        raise HTTPException(status_code=404, detail="Tâche introuvable.")

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
        contact_id=task.contact_id,
        tags=json.loads(task.tags) if task.tags else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )
