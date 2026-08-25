"""
THERESE v2 - Actions Router

Endpoints pour le systeme d'agents actionnables.
Routes les demandes vers des agents multi-etapes avec suivi de progression.
"""

import logging

from app.services.action_agents import (
    ActionRunner,
    get_agent_definitions,
)
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas de requete / reponse
# ---------------------------------------------------------------------------


class RunActionRequest(BaseModel):
    """Requete de lancement d'une action."""

    params: dict[str, str] = Field(
        default_factory=dict,
        description="Parametres fournis par l'utilisateur",
    )


class ActionAgentResponse(BaseModel):
    """Description d'un agent actionnable pour l'UI."""

    id: str
    name: str
    description: str
    icon: str
    category: str
    steps_count: int
    tools: list[str]
    params: list[dict]


class TaskResponse(BaseModel):
    """Etat d'une tache."""

    task_id: str
    agent_id: str
    agent_name: str
    status: str
    params: dict[str, str]
    steps: list[dict]
    result: str
    created_at: str
    started_at: str | None
    completed_at: str | None
    error: str | None
    progress: float


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=list[ActionAgentResponse])
async def list_actions():
    """Liste les agents actions disponibles."""
    defs = get_agent_definitions()
    return [
        ActionAgentResponse(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            icon=agent.icon,
            category=agent.category,
            steps_count=len(agent.steps),
            tools=agent.tools,
            params=[
                {
                    "id": p.id,
                    "label": p.label,
                    "type": p.type,
                    "required": p.required,
                    "placeholder": p.placeholder,
                    "options": p.options,
                }
                for p in agent.params
            ],
        )
        for agent in defs.values()
    ]


@router.get("/{agent_id}", response_model=ActionAgentResponse)
async def get_action(agent_id: str):
    """Recupere les details d'un agent action."""
    defs = get_agent_definitions()
    agent = defs.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' introuvable")
    return ActionAgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        icon=agent.icon,
        category=agent.category,
        steps_count=len(agent.steps),
        tools=agent.tools,
        params=[
            {
                "id": p.id,
                "label": p.label,
                "type": p.type,
                "required": p.required,
                "placeholder": p.placeholder,
                "options": p.options,
            }
            for p in agent.params
        ],
    )


@router.post("/{agent_id}/run", response_model=TaskResponse)
async def run_action(agent_id: str, request: RunActionRequest):
    """Lance l'execution d'un agent action."""
    try:
        task = await ActionRunner.run(
            agent_id=agent_id,
            params=request.params,
        )
        return TaskResponse(**task.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Erreur lancement action %s : %s", agent_id, e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du lancement de l'action : {e}",
        )


@router.get("/tasks/list", response_model=list[TaskResponse])
async def list_tasks():
    """Liste toutes les taches (en cours et terminees)."""
    tasks = ActionRunner.list_tasks()
    return [TaskResponse(**t.to_dict()) for t in tasks]


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Recupere le statut d'une tache."""
    task = ActionRunner.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Tache '{task_id}' introuvable")
    return TaskResponse(**task.to_dict())


@router.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """Demande l'arret d'une tache en cours.

    0.47 : la route historique passe par le service canonique quand le
    traitement durable existe - meme transition cancel_requested, meme
    adaptateur, un seul chemin d'annulation. Repli sur la primitive
    in-memory si le suivi n'a pas pu naitre (fail-open de `run`).
    """
    task = ActionRunner.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Tache '{task_id}' introuvable")

    from app.models.database import get_session_context
    from app.models.processing import EtatTache, ProcessingTask
    from app.services import traitements
    from sqlmodel import select

    async with get_session_context() as session:
        resultat = await session.execute(
            select(ProcessingTask).where(
                ProcessingTask.type == "action",
                ProcessingTask.entity_id == task_id,
                ProcessingTask.state.in_(tuple(EtatTache.actifs())),
            )
        )
        traitement = resultat.scalars().first()

    if traitement is not None:
        arret = await traitements.demander_arret(traitement.id)
        # Revue jalon (F9) : « unavailable » dans la fenêtre d'enrôlement
        # n'est PAS un refus - la demande est posée durablement et rejouée
        # par lier_adaptateur. Seul un état déjà terminal refuse.
        transmise = arret is not None and arret.state in (
            EtatTache.CANCEL_REQUESTED, EtatTache.CANCELLED
        )
    else:
        transmise = ActionRunner.cancel_task(task_id)

    if not transmise:
        raise HTTPException(
            status_code=400,
            detail=f"Impossible d'annuler (statut : {task.status.value})",
        )
    return {"message": f"Arret demande pour la tache '{task_id}'"}
