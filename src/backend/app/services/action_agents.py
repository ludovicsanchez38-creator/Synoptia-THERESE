"""
THERESE v2 - Action Agents

Systeme d'agents actionnables : chaque agent execute une sequence d'etapes
(appels LLM avec acces aux donnees locales) et produit un resultat structure.

Contrairement aux skills (generation textuelle one-shot), les action agents
executent des taches multi-etapes avec progression en temps reel.
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# Chemin du fichier de definition des agents
_AGENTS_JSON = Path(__file__).parent.parent / "agents" / "action_agents.json"


# ---------------------------------------------------------------------------
# Modeles
# ---------------------------------------------------------------------------


class TaskStatus(str, Enum):
    """Statut d'execution d'une tache."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class StepStatus(str, Enum):
    """Statut d'une etape individuelle."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class ActionAgentParam:
    """Parametre requis par un agent."""

    id: str
    label: str
    type: str = "text"
    required: bool = False
    placeholder: str = ""
    options: list[str] = field(default_factory=list)


@dataclass
class ActionAgentStep:
    """Definition d'une etape d'un agent."""

    id: str
    label: str
    prompt: str


@dataclass
class ActionAgentDef:
    """Definition d'un agent actionnable."""

    id: str
    name: str
    description: str
    icon: str
    category: str
    steps: list[ActionAgentStep]
    tools: list[str] = field(default_factory=list)
    params: list[ActionAgentParam] = field(default_factory=list)


@dataclass
class StepResult:
    """Resultat d'une etape executee."""

    step_id: str
    label: str
    status: StepStatus = StepStatus.PENDING
    content: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


@dataclass
class TaskState:
    """Etat d'execution d'une tache."""

    task_id: str
    agent_id: str
    agent_name: str
    status: TaskStatus = TaskStatus.PENDING
    params: dict[str, str] = field(default_factory=dict)
    steps: list[StepResult] = field(default_factory=list)
    result: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    _cancel_event: asyncio.Event = field(
        default_factory=asyncio.Event, repr=False
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialise l'etat pour l'API."""
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "status": self.status.value,
            "params": self.params,
            "steps": [
                {
                    "step_id": s.step_id,
                    "label": s.label,
                    "status": s.status.value,
                    "content": s.content,
                    "started_at": s.started_at,
                    "completed_at": s.completed_at,
                    "error": s.error,
                }
                for s in self.steps
            ],
            "result": self.result,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "progress": self._progress(),
        }

    def _progress(self) -> float:
        """Pourcentage de progression (0.0 - 1.0)."""
        if not self.steps:
            return 0.0
        completed = sum(
            1
            for s in self.steps
            if s.status in (StepStatus.COMPLETED, StepStatus.SKIPPED)
        )
        return completed / len(self.steps)


# ---------------------------------------------------------------------------
# Chargement des definitions
# ---------------------------------------------------------------------------


def _load_agent_definitions() -> dict[str, ActionAgentDef]:
    """Charge les definitions d'agents depuis le JSON."""
    if not _AGENTS_JSON.exists():
        logger.warning("Fichier action_agents.json introuvable : %s", _AGENTS_JSON)
        return {}

    try:
        with open(_AGENTS_JSON, encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as e:
        logger.error("Erreur lecture action_agents.json : %s", e)
        return {}

    agents: dict[str, ActionAgentDef] = {}
    for entry in raw:
        steps = [
            ActionAgentStep(
                id=s["id"],
                label=s["label"],
                prompt=s["prompt"],
            )
            for s in entry.get("steps", [])
        ]
        params = [
            ActionAgentParam(
                id=p["id"],
                label=p["label"],
                type=p.get("type", "text"),
                required=p.get("required", False),
                placeholder=p.get("placeholder", ""),
                options=p.get("options", []),
            )
            for p in entry.get("params", [])
        ]
        agent = ActionAgentDef(
            id=entry["id"],
            name=entry["name"],
            description=entry["description"],
            icon=entry.get("icon", "Zap"),
            category=entry.get("category", "general"),
            steps=steps,
            tools=entry.get("tools", []),
            params=params,
        )
        agents[agent.id] = agent

    logger.info("Charge %d action agents", len(agents))
    return agents


# Cache global des definitions
_agent_defs: dict[str, ActionAgentDef] | None = None


def get_agent_definitions() -> dict[str, ActionAgentDef]:
    """Retourne les definitions d'agents (avec cache)."""
    global _agent_defs
    if _agent_defs is None:
        _agent_defs = _load_agent_definitions()
    return _agent_defs


def reload_agent_definitions() -> None:
    """Force le rechargement des definitions."""
    global _agent_defs
    _agent_defs = None


# ---------------------------------------------------------------------------
# Contexte local (donnees de l'utilisateur)
# ---------------------------------------------------------------------------


async def _gather_local_context(tools: list[str]) -> str:
    """
    Rassemble le contexte local disponible selon les outils declares.

    Chaque outil correspond a un domaine de donnees de THERESE.
    On fournit un resume au LLM pour qu'il puisse raisonner.
    """
    context_parts: list[str] = []

    if "email" in tools:
        try:
            from app.models.database import get_session_context
            from app.models.entities import Email

            async with get_session_context() as session:
                from sqlalchemy import select

                stmt = (
                    select(Email)
                    .order_by(Email.date.desc())
                    .limit(20)
                )
                result = await session.execute(stmt)
                emails = result.scalars().all()
                if emails:
                    lines = []
                    for e in emails:
                        date_str = e.date.strftime("%d/%m") if e.date else "?"
                        lines.append(
                            f"- [{date_str}] {e.sender or '?'} -> {e.subject or '(sans objet)'}"
                        )
                    context_parts.append(
                        "## Emails recents\n" + "\n".join(lines)
                    )
        except Exception as e:
            logger.debug("Contexte email indisponible : %s", e)

    if "crm" in tools:
        try:
            from app.models.database import get_session_context
            from app.models.entities import Contact

            async with get_session_context() as session:
                from sqlalchemy import func, select

                count_stmt = select(func.count()).select_from(Contact)
                total = (await session.execute(count_stmt)).scalar() or 0
                stmt = (
                    select(Contact)
                    .order_by(Contact.updated_at.desc())
                    .limit(15)
                )
                result = await session.execute(stmt)
                contacts = result.scalars().all()
                if contacts:
                    lines = [f"Total contacts : {total}"]
                    for c in contacts:
                        name = f"{c.first_name or ''} {c.last_name or ''}".strip() or c.email or "?"
                        company = f" ({c.company})" if c.company else ""
                        lines.append(f"- {name}{company}")
                    context_parts.append(
                        "## CRM - Contacts recents\n" + "\n".join(lines)
                    )
        except Exception as e:
            logger.debug("Contexte CRM indisponible : %s", e)

    if "calendar" in tools:
        try:
            from app.services.calendar_service import CalendarService

            cal_svc = CalendarService()
            events = await cal_svc.get_upcoming_events(limit=10)
            if events:
                lines = []
                for ev in events:
                    lines.append(
                        f"- {ev.get('start', '?')} : {ev.get('summary', '(sans titre)')}"
                    )
                context_parts.append(
                    "## Calendrier - Evenements a venir\n" + "\n".join(lines)
                )
        except Exception as e:
            logger.debug("Contexte calendrier indisponible : %s", e)

    if "tasks" in tools:
        try:
            from app.models.database import get_session_context
            from app.models.entities import Task

            async with get_session_context() as session:
                from sqlalchemy import select

                stmt = (
                    select(Task)
                    .order_by(Task.due_date.asc().nullslast())
                    .limit(15)
                )
                result = await session.execute(stmt)
                tasks = result.scalars().all()
                if tasks:
                    lines = []
                    for t in tasks:
                        status = getattr(t, "status", "?")
                        due = ""
                        if t.due_date:
                            due = f" (echeance : {t.due_date.strftime('%d/%m')})"
                        lines.append(f"- [{status}] {t.title}{due}")
                    context_parts.append(
                        "## Taches\n" + "\n".join(lines)
                    )
        except Exception as e:
            logger.debug("Contexte taches indisponible : %s", e)

    if "invoices" in tools:
        try:
            from app.models.database import get_session_context
            from app.models.entities import Invoice

            async with get_session_context() as session:
                from sqlalchemy import select

                stmt = (
                    select(Invoice)
                    .order_by(Invoice.created_at.desc())
                    .limit(15)
                )
                result = await session.execute(stmt)
                invoices = result.scalars().all()
                if invoices:
                    lines = []
                    for inv in invoices:
                        status = getattr(inv, "status", "?")
                        amount = getattr(inv, "total_ttc", getattr(inv, "total", "?"))
                        client = getattr(inv, "client_name", "?")
                        lines.append(
                            f"- {inv.number or '?'} | {client} | {amount} EUR | {status}"
                        )
                    context_parts.append(
                        "## Factures\n" + "\n".join(lines)
                    )
        except Exception as e:
            logger.debug("Contexte factures indisponible : %s", e)

    if not context_parts:
        return "(Aucune donnee locale disponible pour cette action.)"

    return "\n\n".join(context_parts)


# ---------------------------------------------------------------------------
# ActionRunner
# ---------------------------------------------------------------------------


ProgressCallback = Callable[[TaskState], None]


class ActionRunner:
    """Execute un agent actionnable etape par etape."""

    # Stockage en memoire des taches en cours / terminees
    _tasks: dict[str, TaskState] = {}

    @classmethod
    def get_task(cls, task_id: str) -> TaskState | None:
        """Recupere l'etat d'une tache."""
        return cls._tasks.get(task_id)

    @classmethod
    def list_tasks(cls) -> list[TaskState]:
        """Liste toutes les taches."""
        return list(cls._tasks.values())

    @classmethod
    def cancel_task(cls, task_id: str) -> bool:
        """Annule une tache en cours."""
        task = cls._tasks.get(task_id)
        if not task:
            return False
        if task.status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
            return False
        task._cancel_event.set()
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now(UTC).isoformat()
        return True

    @classmethod
    async def run(
        cls,
        agent_id: str,
        params: dict[str, str] | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> TaskState:
        """
        Lance l'execution d'un agent.

        Args:
            agent_id: Identifiant de l'agent a executer
            params: Parametres fournis par l'utilisateur
            on_progress: Callback appele a chaque changement d'etat

        Returns:
            TaskState final
        """
        defs = get_agent_definitions()
        agent_def = defs.get(agent_id)
        if not agent_def:
            raise ValueError(f"Agent inconnu : {agent_id}")

        # Valider les parametres requis
        params = params or {}
        for p in agent_def.params:
            if p.required and p.id not in params:
                raise ValueError(
                    f"Parametre requis manquant : {p.label} ({p.id})"
                )

        # Creer la tache
        task_id = str(uuid.uuid4())
        task = TaskState(
            task_id=task_id,
            agent_id=agent_id,
            agent_name=agent_def.name,
            params=params,
            steps=[
                StepResult(step_id=s.id, label=s.label)
                for s in agent_def.steps
            ],
        )
        cls._tasks[task_id] = task

        # Lancer l'execution en tache de fond
        asyncio.create_task(
            cls._execute(task, agent_def, params, on_progress)
        )

        return task

    @classmethod
    async def _execute(
        cls,
        task: TaskState,
        agent_def: ActionAgentDef,
        params: dict[str, str],
        on_progress: ProgressCallback | None,
    ) -> None:
        """Execution interne sequentielle des etapes."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(UTC).isoformat()
        if on_progress:
            on_progress(task)

        # Rassembler le contexte local
        local_context = await _gather_local_context(agent_def.tools)

        # Obtenir le service LLM
        try:
            from app.services.llm import get_llm_service

            llm = get_llm_service()
            if not llm:
                task.status = TaskStatus.ERROR
                task.error = "Aucun service LLM configure."
                task.completed_at = datetime.now(UTC).isoformat()
                if on_progress:
                    on_progress(task)
                return
        except Exception as e:
            task.status = TaskStatus.ERROR
            task.error = f"Erreur LLM : {e}"
            task.completed_at = datetime.now(UTC).isoformat()
            if on_progress:
                on_progress(task)
            return

        # Historique accumule entre les etapes
        accumulated_results: list[str] = []

        for i, step_def in enumerate(agent_def.steps):
            # Verifier annulation
            if task._cancel_event.is_set():
                for remaining in task.steps[i:]:
                    remaining.status = StepStatus.SKIPPED
                break

            step_result = task.steps[i]
            step_result.status = StepStatus.RUNNING
            step_result.started_at = datetime.now(UTC).isoformat()
            if on_progress:
                on_progress(task)

            # Preparer le prompt de l'etape
            step_prompt = step_def.prompt
            for key, value in params.items():
                step_prompt = step_prompt.replace(f"{{{{{key}}}}}", value)

            # System prompt
            system_prompt = (
                f"Tu es un assistant professionnel qui execute l'action '{agent_def.name}'.\n"
                f"Etape actuelle : {step_def.label} ({i + 1}/{len(agent_def.steps)}).\n\n"
                f"## Donnees locales disponibles\n{local_context}\n\n"
            )
            if accumulated_results:
                system_prompt += (
                    "## Resultats des etapes precedentes\n"
                    + "\n\n---\n\n".join(accumulated_results)
                    + "\n\n"
                )
            system_prompt += (
                "Reponds de maniere structuree en markdown. "
                "Sois factuel et actionnable. "
                "Si des donnees manquent, dis-le clairement sans inventer."
            )

            try:
                from app.services.providers import Message

                messages = [Message(role="user", content=step_prompt)]
                context = llm.prepare_context(
                    messages, system_prompt=system_prompt
                )

                # Streaming : on accumule la reponse complete
                content = ""
                async for chunk in llm.stream_response(context):
                    content += chunk
                    step_result.content = content
                    # Notifier regulierement (tous les 50 caracteres)
                    if len(content) % 50 < len(chunk) and on_progress:
                        on_progress(task)

                step_result.content = content
                step_result.status = StepStatus.COMPLETED
                step_result.completed_at = datetime.now(UTC).isoformat()

                # Ajouter au contexte accumule
                accumulated_results.append(
                    f"### {step_def.label}\n{content}"
                )

            except Exception as e:
                logger.error(
                    "Erreur etape %s de l'agent %s : %s",
                    step_def.id,
                    agent_def.id,
                    e,
                    exc_info=True,
                )
                step_result.status = StepStatus.ERROR
                step_result.error = str(e)
                step_result.completed_at = datetime.now(UTC).isoformat()
                # On continue les etapes suivantes malgre l'erreur

            if on_progress:
                on_progress(task)

        # Generer le resultat final (synthese de toutes les etapes)
        if not task._cancel_event.is_set():
            completed_steps = [
                s for s in task.steps if s.status == StepStatus.COMPLETED
            ]
            if completed_steps:
                result_parts = [
                    f"# {agent_def.name}\n",
                    f"*Execute le {datetime.now(UTC).strftime('%d/%m/%Y a %H:%M')} UTC*\n",
                ]
                for s in completed_steps:
                    result_parts.append(f"## {s.label}\n\n{s.content}\n")
                task.result = "\n".join(result_parts)

            task.status = TaskStatus.COMPLETED
        else:
            task.status = TaskStatus.CANCELLED

        task.completed_at = datetime.now(UTC).isoformat()
        if on_progress:
            on_progress(task)

        # Nettoyage : garder max 20 taches en memoire
        if len(cls._tasks) > 20:
            sorted_tasks = sorted(
                cls._tasks.values(),
                key=lambda t: t.created_at,
            )
            for old_task in sorted_tasks[:-20]:
                if old_task.status not in (
                    TaskStatus.PENDING,
                    TaskStatus.RUNNING,
                ):
                    del cls._tasks[old_task.task_id]
