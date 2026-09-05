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

from app.models.processing import EtatTache
from app.services import task_registry
from app.services import traitements as traitements_service
from app.services.error_handler import message_pour_ecran

logger = logging.getLogger(__name__)

# Chemin du fichier de definition des agents
_AGENTS_JSON = Path(__file__).parent.parent / "agents" / "action_agents.json"


# ---------------------------------------------------------------------------
# Modeles
# ---------------------------------------------------------------------------


class TaskStatus(str, Enum):
    """Statut d'execution d'une tache.

    `CANCEL_REQUESTED` est distinct de `CANCELLED` (0.47) : demander l'arret
    n'est pas l'obtenir - le flux LLM de l'etape en cours tourne encore.
    Seul le chemin de boucle de `_execute` pose `CANCELLED`.
    """

    PENDING = "pending"
    RUNNING = "running"
    CANCEL_REQUESTED = "cancel_requested"
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
    # Traitement durable (panneau Traitements) - None si le suivi n'a pas
    # pu naitre : l'action s'execute quand meme (fail-open).
    _handle: Optional["traitements_service.TraitementHandle"] = field(
        default=None, repr=False
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


async def _gather_local_context(
    tools: list[str], params: dict[str, str] | None = None
) -> str:
    """
    Rassemble le contexte local disponible selon les outils declares.

    Chaque outil correspond a un domaine de donnees de THERESE.
    On fournit un resume au LLM pour qu'il puisse raisonner.
    """
    context_parts: list[str] = []

    if "email" in tools:
        try:
            # B-342 (05/09/2026) : l'entité s'appelle EmailMessage ; l'import
            # d'un `Email` inexistant tombait dans le rattrapage ci-dessous,
            # journalisé en debug, et l'agent raisonnait sans courriels.
            from app.models.database import get_session_context
            from app.models.entities import EmailMessage

            async with get_session_context() as session:
                from sqlalchemy import select

                stmt = (
                    select(EmailMessage)
                    .order_by(EmailMessage.date.desc())
                    .limit(20)
                )
                result = await session.execute(stmt)
                emails = result.scalars().all()
                if emails:
                    lines = []
                    for e in emails:
                        date_str = e.date.strftime("%d/%m") if e.date else "?"
                        expediteur = e.from_name or e.from_email or "?"
                        lines.append(
                            f"- [{date_str}] {expediteur} -> {e.subject or '(sans objet)'}"
                        )
                    context_parts.append(
                        "## Emails recents\n" + "\n".join(lines)
                    )
        except Exception as e:
            logger.debug("Contexte email indisponible : %s", e)

    if "crm" in tools:
        try:
            from app.models.database import get_session_context
            from app.models.entities import Activity, Contact, Invoice

            async with get_session_context() as session:
                from collections import defaultdict

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
                    contact_ids = [contact.id for contact in contacts]
                    activites = (
                        await session.execute(
                            select(Activity)
                            .where(
                                Activity.contact_id.in_(contact_ids),
                                Activity.statut == "en_vigueur",
                            )
                            .order_by(Activity.created_at.desc())
                        )
                    ).scalars().all()
                    pieces = (
                        await session.execute(
                            select(Invoice)
                            .where(Invoice.contact_id.in_(contact_ids))
                            .order_by(Invoice.created_at.desc())
                        )
                    ).scalars().all()
                    activites_par_contact: dict[str, list[Activity]] = defaultdict(list)
                    pieces_par_contact: dict[str, list[Invoice]] = defaultdict(list)
                    for activite in activites:
                        if len(activites_par_contact[activite.contact_id]) < 3:
                            activites_par_contact[activite.contact_id].append(activite)
                    for piece in pieces:
                        if len(pieces_par_contact[piece.contact_id]) < 5:
                            pieces_par_contact[piece.contact_id].append(piece)

                    lines = [f"Total contacts : {total}"]
                    for c in contacts:
                        name = f"{c.first_name or ''} {c.last_name or ''}".strip() or c.email or "?"
                        company = f" ({c.company})" if c.company else ""
                        derniere_interaction = (
                            c.last_interaction.strftime("%d/%m/%Y")
                            if c.last_interaction else "non renseignée"
                        )
                        prochaine_relance = (
                            c.next_follow_up.strftime("%d/%m/%Y")
                            if c.next_follow_up else "aucune"
                        )
                        lines.append(
                            f"- {name}{company} | étape : {c.stage} | "
                            f"dernière interaction : {derniere_interaction} | "
                            f"prochaine relance : {prochaine_relance}"
                        )
                        for activite in activites_par_contact[c.id]:
                            date_activite = activite.created_at.strftime("%d/%m/%Y")
                            lines.append(
                                f"  - activité [{date_activite}] {activite.type} : "
                                f"{activite.title}"
                            )
                        for piece in pieces_par_contact[c.id]:
                            lines.append(
                                f"  - {piece.document_type} {piece.invoice_number} | "
                                f"{piece.status} | {piece.total_ttc} {piece.currency} | "
                                f"échéance {piece.due_date.strftime('%d/%m/%Y')}"
                            )
                    context_parts.append(
                        "## CRM - Contacts recents\n" + "\n".join(lines)
                    )
        except Exception as e:
            logger.debug("Contexte CRM indisponible : %s", e)

    if "calendar" in tools:
        try:
            # B-343 (05/09/2026) : CalendarService exige un jeton Google et
            # n'a jamais eu de get_upcoming_events ; la branche échouait en
            # silence. L'agenda local est en base : on le lit là.
            from app.models.database import get_session_context
            from app.models.entities import CalendarEvent

            async with get_session_context() as session:
                from sqlalchemy import or_, select

                maintenant = datetime.now(UTC)
                aujourd_hui = maintenant.date().isoformat()
                stmt = (
                    select(CalendarEvent)
                    .where(
                        or_(
                            CalendarEvent.start_datetime >= maintenant,
                            CalendarEvent.start_date >= aujourd_hui,
                        )
                    )
                    .order_by(CalendarEvent.start_datetime.asc(), CalendarEvent.start_date.asc())
                    .limit(10)
                )
                result = await session.execute(stmt)
                events = result.scalars().all()
            if events:
                lines = []
                for ev in events:
                    debut = (
                        ev.start_datetime.strftime("%d/%m %H:%M")
                        if ev.start_datetime
                        else (ev.start_date or "?")
                    )
                    lines.append(f"- {debut} : {ev.summary or '(sans titre)'}")
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
                from sqlalchemy.orm import selectinload

                # B-572 (05/09/2026) : les quinze pièces les plus récemment
                # CRÉÉES pouvaient exclure une facture en retard plus ancienne,
                # que « Relance clients » ne voyait alors jamais. Les créances
                # ouvertes passent d'abord, par échéance ; les pièces récentes
                # complètent, sans doublon.
                creances = (
                    select(Invoice)
                    .options(selectinload(Invoice.contact))
                    .where(Invoice.status.in_(("overdue", "sent")))
                    .order_by(Invoice.due_date.asc())
                    .limit(30)
                )
                recentes = (
                    select(Invoice)
                    .options(selectinload(Invoice.contact))
                    .order_by(Invoice.created_at.desc())
                    .limit(15)
                )
                invoices = list((await session.execute(creances)).scalars().all())
                vus = {inv.id for inv in invoices}
                for inv in (await session.execute(recentes)).scalars().all():
                    if inv.id not in vus:
                        invoices.append(inv)
                        vus.add(inv.id)
                if invoices:
                    lines = []
                    for inv in invoices:
                        # Finding 8 (30/08) : `number` / `client_name` n'existent
                        # pas, et EUR était en dur. Une facture USD sortait
                        # « ? | ? | 1000 EUR ».
                        status = getattr(inv, "status", "?")
                        amount = getattr(inv, "total_ttc", "?")
                        devise = getattr(inv, "currency", None) or "EUR"
                        numero = getattr(inv, "invoice_number", None) or "?"
                        fiche = getattr(inv, "contact", None)
                        client = fiche.display_name if fiche is not None else "?"
                        echeance = getattr(inv, "due_date", None)
                        quand = echeance.strftime("%d/%m/%Y") if echeance else "?"
                        lines.append(
                            f"- {numero} | {client} | {amount} {devise} | {status}"
                            f" | échéance {quand}"
                        )
                    context_parts.append(
                        "## Factures\n" + "\n".join(lines)
                    )
        except Exception as e:
            logger.debug("Contexte factures indisponible : %s", e)

    if "web_search" in tools:
        # B-331 (05/09/2026) : l'outil était déclaré côté données sans être
        # servi côté exécution. On cherche avec les paramètres de l'action
        # quand la recherche est autorisée ; sinon on le dit, pour que le
        # modèle ne comble pas le vide.
        try:
            from app.services.web_search import (
                formater_resultats_pour_llm,
                get_web_search_service,
                recherche_web_autorisee,
            )

            requete = " ".join(
                v.strip() for v in (params or {}).values() if isinstance(v, str) and v.strip()
            )[:200]
            if not recherche_web_autorisee():
                context_parts.append(
                    "## Recherche web\n(non autorisée dans les réglages : aucune recherche "
                    "effectuée, ne rien inventer à ce sujet)"
                )
            elif not requete:
                context_parts.append(
                    "## Recherche web\n(aucun sujet fourni : aucune recherche effectuée)"
                )
            else:
                reponse = await get_web_search_service().search(requete, max_results=5)
                context_parts.append("## Recherche web\n" + formater_resultats_pour_llm(reponse))
        except Exception as e:
            logger.warning("Contexte recherche web indisponible : %s", e)
            context_parts.append(
                "## Recherche web\n(indisponible : aucune recherche effectuée, ne rien inventer)"
            )

    if not context_parts:
        return "(Aucune donnee locale disponible pour cette action.)"

    return "\n\n".join(context_parts)


# ---------------------------------------------------------------------------
# ActionRunner
# ---------------------------------------------------------------------------


ProgressCallback = Callable[[TaskState], None]

# Etats en memoire ou plus rien ne bouge.
_STATUTS_TERMINAUX = (
    TaskStatus.COMPLETED,
    TaskStatus.CANCELLED,
    TaskStatus.ERROR,
)

# Mapping vers l'etat durable du ProcessingTask (design 0.47).
_ETAT_DURABLE = {
    TaskStatus.COMPLETED: EtatTache.DONE,
    TaskStatus.ERROR: EtatTache.FAILED,
    TaskStatus.CANCELLED: EtatTache.CANCELLED,
}


class ActionRunner:
    """Execute un agent actionnable etape par etape."""

    # Stockage en memoire des taches en cours / terminees
    _tasks: dict[str, TaskState] = {}
    # References fortes sur les executions de fond (lecon 0.43.4).
    _taches_de_fond: set["asyncio.Task[None]"] = set()

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
        """Demande l'arret d'une tache (primitive unique, jamais terminal)."""
        return demander_arret_action(task_id)

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

        # Enrolement 0.47 : chaque run est un ProcessingTask visible au
        # panneau Traitements. Fail-open : le suivi en panne ne doit pas
        # empecher l'action elle-meme.
        try:
            task._handle = await traitements_service.creer_traitement(
                type="action",
                label=agent_def.name,
                entity_id=task_id,
            )
        except Exception:
            logger.warning(
                "Suivi indisponible pour l'action %s : elle s'execute sans "
                "apparaitre au panneau Traitements",
                agent_id,
                exc_info=True,
            )

        # Lancer l'execution en tache de fond. Reference forte obligatoire
        # (lecon 0.43.4) : sans elle le GC peut avaler la tache en plein vol.
        tache = asyncio.create_task(
            cls._execute(task, agent_def, params, on_progress)
        )
        cls._taches_de_fond.add(tache)
        tache.add_done_callback(cls._taches_de_fond.discard)

        return task

    @classmethod
    async def _execute(
        cls,
        task: TaskState,
        agent_def: ActionAgentDef,
        params: dict[str, str],
        on_progress: ProgressCallback | None,
    ) -> None:
        """Enveloppe terminale (0.47) : AUCUN chemin ne laisse la tache
        running - ni en memoire, ni au panneau Traitements."""
        try:
            await cls._derouler(task, agent_def, params, on_progress)
        except Exception as e:
            logger.error(
                "Echec de l'action %s : %s", agent_def.id, e, exc_info=True
            )
            if task.status not in _STATUTS_TERMINAUX:
                task.status = TaskStatus.ERROR
                # Revue 0.48 (F4) : task.error part à l'écran (panneau
                # Actions, suivi durable) - le brut reste aux logs.
                task.error = message_pour_ecran(e, ou="pendant l'action")
                task.completed_at = datetime.now(UTC).isoformat()
                if on_progress:
                    on_progress(task)
        finally:
            if task._handle is not None:
                try:
                    await task._handle.terminer(
                        _ETAT_DURABLE.get(task.status, EtatTache.FAILED),
                        error=task.error,
                    )
                except Exception:
                    logger.warning(
                        "Cloture du traitement de l'action %s impossible",
                        task.task_id,
                        exc_info=True,
                    )
            cls._purger_vieilles_taches()

    @classmethod
    def _clore_annulee(
        cls, task: TaskState, on_progress: ProgressCallback | None
    ) -> None:
        """Annulation gagnee avant toute production : clore sans RUNNING."""
        for step in task.steps:
            if step.status == StepStatus.PENDING:
                step.status = StepStatus.SKIPPED
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now(UTC).isoformat()
        if on_progress:
            on_progress(task)

    @classmethod
    async def _derouler(
        cls,
        task: TaskState,
        agent_def: ActionAgentDef,
        params: dict[str, str],
        on_progress: ProgressCallback | None,
    ) -> None:
        """Execution interne sequentielle des etapes."""
        handle = task._handle

        # La course (0.47) : une annulation posee avant ce point a gagne -
        # RUNNING n'est jamais reecrit, aucune etape ne tourne.
        if (
            task._cancel_event.is_set()
            or task.status == TaskStatus.CANCEL_REQUESTED
        ):
            cls._clore_annulee(task, on_progress)
            return

        if handle is not None:
            try:
                await handle.demarrer()
            except traitements_service.AnnuleAvantDemarrage:
                # demander_arret a deja pose CANCELLED durable.
                cls._clore_annulee(task, on_progress)
                return
            await handle.lier_adaptateur(
                task_registry.AnnulationCooperative(
                    lambda: demander_arret_action(task.task_id)
                )
            )
            # L'enrolement peut avoir rejoue une demande durable : la course
            # se rejoue ici, avant d'ecrire RUNNING.
            if task._cancel_event.is_set():
                cls._clore_annulee(task, on_progress)
                return

        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(UTC).isoformat()
        if on_progress:
            on_progress(task)

        # Rassembler le contexte local
        local_context = await _gather_local_context(agent_def.tools, params)

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
            logger.error("Action : échec d'accès au service LLM : %s", e, exc_info=True)
            task.error = message_pour_ecran(e, ou="au démarrage de l'action")
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
            if handle is not None:
                await handle.progresser(
                    step=step_def.label,
                    progress=i / len(agent_def.steps),
                )

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
                step_result.error = message_pour_ecran(
                    e, ou=f"à l'étape « {step_def.label} »"
                )
                step_result.completed_at = datetime.now(UTC).isoformat()
                # On continue les etapes suivantes malgre l'erreur

            if on_progress:
                on_progress(task)

        # Generer le resultat final (synthese de toutes les etapes)
        if not task._cancel_event.is_set():
            completed_steps = [
                s for s in task.steps if s.status == StepStatus.COMPLETED
            ]
            failed_steps = [
                s for s in task.steps if s.status == StepStatus.ERROR
            ]
            if completed_steps:
                result_parts = [
                    f"# {agent_def.name}\n",
                    f"*Exécuté le {datetime.now(UTC).strftime('%d/%m/%Y à %H:%M')} UTC*\n",
                ]
                for s in completed_steps:
                    result_parts.append(f"## {s.label}\n\n{s.content}\n")
                task.result = "\n".join(result_parts)

            # Revue 30/08 : une étape en échec laissait le statut
            # `completed`. L'utilisateur recevait un rapport amputé
            # présenté comme terminé.
            if failed_steps:
                task.status = TaskStatus.ERROR
                task.error = (
                    f"{len(failed_steps)} étape"
                    f"{'s ont' if len(failed_steps) > 1 else ' a'} échoué"
                    f" ({', '.join(s.label for s in failed_steps)})"
                )
            elif completed_steps:
                task.status = TaskStatus.COMPLETED
            else:
                task.status = TaskStatus.ERROR
                task.error = "Aucune étape n'a produit de résultat."
            if handle is not None:
                await handle.progresser(progress=1.0)
        else:
            task.status = TaskStatus.CANCELLED

        task.completed_at = datetime.now(UTC).isoformat()
        if on_progress:
            on_progress(task)

    @classmethod
    def _purger_vieilles_taches(cls) -> None:
        """Garder au plus 20 taches en memoire (jamais une vivante)."""
        if len(cls._tasks) <= 20:
            return
        sorted_tasks = sorted(
            cls._tasks.values(),
            key=lambda t: t.created_at,
        )
        for old_task in sorted_tasks[:-20]:
            if old_task.status in _STATUTS_TERMINAUX:
                del cls._tasks[old_task.task_id]


def demander_arret_action(task_id: str) -> bool:
    """LA primitive d'arret des actions (0.47) : poser la demande, jamais
    l'etat terminal.

    L'evenement coupe la boucle entre deux etapes ; le statut passe a
    CANCEL_REQUESTED pour que l'interface dise la verite (le flux LLM de
    l'etape en cours tourne encore). Utilisee par `cancel_task` ET par
    l'adaptateur du traitement durable - un seul chemin d'annulation.
    """
    task = ActionRunner._tasks.get(task_id)
    if not task:
        return False
    if task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
        task._cancel_event.set()
        task.status = TaskStatus.CANCEL_REQUESTED
        return True
    if task.status == TaskStatus.CANCEL_REQUESTED:
        # Idempotent : la demande tient toujours.
        task._cancel_event.set()
        return True
    return False
