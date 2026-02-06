"""
THERESE v2 - CRM Utilities partagees

Fonctions utilitaires communes pour le CRM : upsert contact, upsert project,
upsert task, upsert deliverable, parsing de donnees, mappings de statuts.

Utilise par crm.py (router), crm_sync.py (service) et crm_import.py (service).
"""

import json
import logging
from datetime import UTC, datetime

from app.models.entities import Contact, Deliverable, Preference, Project, Task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

logger = logging.getLogger(__name__)


# =============================================================================
# Constantes partagees
# =============================================================================

# Mapping des statuts de projet (francais -> interne)
PROJECT_STATUS_MAP: dict[str, str] = {
    "en_cours": "active",
    "en_pause": "on_hold",
    "termine": "completed",
    "annule": "cancelled",
    "en_attente": "on_hold",
    "livre": "completed",
    "planifie": "active",
    # Valeurs deja normalisees
    "active": "active",
    "completed": "completed",
    "on_hold": "on_hold",
    "cancelled": "cancelled",
}

VALID_PROJECT_STATUSES = {"active", "completed", "on_hold", "cancelled"}

# Mapping des priorites de tache
TASK_PRIORITY_MAP: dict[str, str] = {
    "normal": "medium",
    "urgent": "urgent",
    "low": "low",
    "high": "high",
    "medium": "medium",
}

VALID_TASK_STATUSES = {"todo", "in_progress", "done", "cancelled"}

# Statuts valides pour les livrables (endpoint import_crm_data)
VALID_DELIVERABLE_STATUSES_IMPORT = {"pending", "in_progress", "completed", "blocked"}


# =============================================================================
# Helpers de parsing
# =============================================================================


def parse_datetime(value: str | None) -> datetime | None:
    """
    Parse une date/heure depuis differents formats courants.

    Supporte ISO 8601, dates simples et format francais (dd/mm/yyyy).
    """
    if not value or not isinstance(value, str) or not value.strip():
        return None
    value = value.strip()
    for fmt in [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y",
    ]:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def split_name(full_name: str) -> tuple[str, str | None]:
    """Separe un nom complet en prenom et nom de famille."""
    parts = full_name.split(" ", 1)
    first_name = parts[0] if parts else ""
    last_name = parts[1] if len(parts) > 1 else None
    return first_name, last_name


def parse_score(value: str | int | float | None, default: int = 50) -> int:
    """Parse un score depuis une valeur string, int ou float."""
    if value is None:
        return default
    if isinstance(value, str):
        value = value.strip()
    if not value:
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def parse_budget(value: str | int | float | None) -> float | None:
    """Parse un budget depuis une valeur quelconque."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        value = value.strip()
    if not value:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def parse_tags_json(value: str | None) -> str | None:
    """Convertit une chaine de tags separee par des virgules en JSON array."""
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
    if not value:
        return None
    return json.dumps(value.split(","))


def safe_strip(value: str | None, default: str = "") -> str:
    """Strip une valeur en gerant les None et types mixtes."""
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def safe_strip_or_none(value: str | None) -> str | None:
    """Strip une valeur, retourne None si vide."""
    result = safe_strip(value)
    return result or None


def normalize_project_status(raw_status: str | None, default: str = "active") -> str:
    """Normalise un statut de projet vers une valeur valide."""
    if not raw_status:
        return default
    cleaned = raw_status.strip().lower()
    status = PROJECT_STATUS_MAP.get(cleaned, cleaned)
    if status not in VALID_PROJECT_STATUSES:
        return default
    return status


def normalize_task_priority(raw_priority: str | None, default: str = "medium") -> str:
    """Normalise une priorite de tache vers une valeur valide."""
    if not raw_priority:
        return default
    cleaned = raw_priority.strip().lower()
    return TASK_PRIORITY_MAP.get(cleaned, default)


def normalize_task_status(raw_status: str | None, default: str = "todo") -> str:
    """Normalise un statut de tache vers une valeur valide."""
    if not raw_status:
        return default
    cleaned = raw_status.strip().lower()
    if cleaned not in VALID_TASK_STATUSES:
        return default
    return cleaned


# =============================================================================
# Upsert Contact
# =============================================================================


async def upsert_contact(
    session: AsyncSession,
    row: dict,
    *,
    id_key: str = "ID",
    safe_get: bool = False,
) -> tuple[Contact, bool]:
    """
    Cree ou met a jour un contact depuis un dictionnaire de donnees.

    Le dictionnaire doit utiliser les cles Google Sheets :
    ID, Nom, Entreprise, Email, Tel, Source, Stage, Score, Tags.

    Args:
        session: Session de base de donnees async
        row: Dictionnaire avec les donnees du contact
        id_key: Cle pour l'ID dans le dictionnaire
        safe_get: Si True, utilise `(row.get(k, "") or "")` pour gerer les None

    Returns:
        Tuple (contact, created) - l'entite et un booleen True si cree, False si mis a jour

    Raises:
        ValueError: Si l'ID est vide ou absent
    """
    if safe_get:
        crm_id = (row.get(id_key, "") or "").strip()
    else:
        crm_id = row.get(id_key, "").strip()

    if not crm_id:
        raise ValueError(f"ID manquant (cle: {id_key})")

    # Verifier si le contact existe
    result = await session.execute(
        select(Contact).where(Contact.id == crm_id)
    )
    existing = result.scalar_one_or_none()

    # Parser le nom
    if safe_get:
        full_name = (row.get("Nom", "") or "").strip()
    else:
        full_name = row.get("Nom", "").strip()
    first_name, last_name = split_name(full_name)

    # Parser le score
    score_raw = row.get("Score", "50")
    if isinstance(score_raw, str):
        score_raw = score_raw.strip() if score_raw else "50"
    score = parse_score(score_raw)

    # Parser les tags
    tags_raw = row.get("Tags", "")
    if isinstance(tags_raw, str):
        tags_raw = tags_raw.strip() if tags_raw else ""
    tags_json = parse_tags_json(tags_raw) if tags_raw else None

    # Fonctions d'extraction de champs
    def _get(key: str, default: str = "") -> str | None:
        if safe_get:
            val = (row.get(key, default) or default).strip()
        else:
            val = row.get(key, default).strip()
        return val or None

    if existing:
        existing.first_name = first_name
        existing.last_name = last_name
        existing.company = _get("Entreprise")
        existing.email = _get("Email")
        existing.phone = _get("Tel")
        existing.source = _get("Source")
        existing.stage = _get("Stage", "contact") or "contact"
        existing.score = score
        existing.tags = tags_json
        existing.updated_at = datetime.now(UTC)
        return existing, False
    else:
        contact = Contact(
            id=crm_id,
            first_name=first_name,
            last_name=last_name,
            company=_get("Entreprise"),
            email=_get("Email"),
            phone=_get("Tel"),
            source=_get("Source"),
            stage=_get("Stage", "contact") or "contact",
            score=score,
            tags=tags_json,
            scope="global",
        )
        session.add(contact)
        return contact, True


# =============================================================================
# Upsert Project
# =============================================================================


async def upsert_project(
    session: AsyncSession,
    row: dict,
    *,
    id_key: str = "ID",
    safe_get: bool = False,
    status_map: dict[str, str] | None = None,
) -> tuple[Project, bool]:
    """
    Cree ou met a jour un projet depuis un dictionnaire de donnees.

    Le dictionnaire doit utiliser les cles Google Sheets :
    ID, ClientID, Name, Description, Status, Budget, Notes.

    Args:
        session: Session de base de donnees async
        row: Dictionnaire avec les donnees du projet
        id_key: Cle pour l'ID dans le dictionnaire
        safe_get: Si True, gere les valeurs None dans le dictionnaire
        status_map: Mapping de statuts additionnel (fusionne avec le defaut)

    Returns:
        Tuple (project, created) - l'entite et un booleen True si cree, False si mis a jour

    Raises:
        ValueError: Si l'ID est vide ou absent
    """
    effective_map = {**PROJECT_STATUS_MAP}
    if status_map:
        effective_map.update(status_map)

    if safe_get:
        project_id = (row.get(id_key, "") or "").strip()
    else:
        project_id = row.get(id_key, "").strip()

    if not project_id:
        raise ValueError(f"ID manquant (cle: {id_key})")

    # Verifier si le projet existe
    result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    existing = result.scalar_one_or_none()

    # Extraction de champs
    def _get(key: str, default: str = "") -> str | None:
        if safe_get:
            val = (row.get(key, default) or default).strip()
        else:
            val = row.get(key, default).strip()
        return val or None

    client_id = _get("ClientID")

    raw_status = _get("Status", "active") or "active"
    status = effective_map.get(raw_status.lower(), raw_status.lower())
    if status not in VALID_PROJECT_STATUSES:
        status = "active"

    budget_raw = row.get("Budget", "")
    if isinstance(budget_raw, str):
        budget_raw = budget_raw.strip() if budget_raw else ""
    budget = parse_budget(budget_raw)

    name = _get("Name", "Sans nom") or "Sans nom"
    description = _get("Description")
    notes = _get("Notes")

    if existing:
        existing.name = name
        existing.description = description
        existing.contact_id = client_id
        existing.status = status
        existing.budget = budget
        existing.notes = notes
        existing.updated_at = datetime.now(UTC)
        return existing, False
    else:
        project = Project(
            id=project_id,
            name=name,
            description=description,
            contact_id=client_id,
            status=status,
            budget=budget,
            notes=notes,
            scope="global",
        )
        session.add(project)
        return project, True


# =============================================================================
# Upsert Task
# =============================================================================


async def upsert_task(
    session: AsyncSession,
    row: dict,
    *,
    id_key: str = "ID",
    safe_get: bool = False,
) -> tuple[Task, bool]:
    """
    Cree ou met a jour une tache depuis un dictionnaire de donnees.

    Le dictionnaire doit utiliser les cles Google Sheets :
    ID, Title, Description, Priority, Status, DueDate, CreatedAt, CompletedAt.

    Args:
        session: Session de base de donnees async
        row: Dictionnaire avec les donnees de la tache
        id_key: Cle pour l'ID dans le dictionnaire
        safe_get: Si True, gere les valeurs None dans le dictionnaire

    Returns:
        Tuple (task, created) - l'entite et un booleen True si cree, False si mis a jour

    Raises:
        ValueError: Si l'ID est vide ou absent
    """
    if safe_get:
        task_id = (row.get(id_key, "") or "").strip()
    else:
        task_id = row.get(id_key, "").strip()

    if not task_id:
        raise ValueError(f"ID manquant (cle: {id_key})")

    existing = await session.get(Task, task_id)

    # Parser les champs
    def _get_str(key: str, default: str = "") -> str:
        if safe_get:
            return (row.get(key, default) or default).strip()
        return row.get(key, default).strip()

    raw_priority = _get_str("Priority", "medium")
    priority = normalize_task_priority(raw_priority)

    raw_status = _get_str("Status", "todo")
    task_status = normalize_task_status(raw_status)

    # Parser les dates
    due_date = parse_datetime(_get_str("DueDate"))
    created_at = parse_datetime(_get_str("CreatedAt"))
    completed_at = parse_datetime(_get_str("CompletedAt"))

    title = _get_str("Title", "Sans titre") or "Sans titre"
    description_val = _get_str("Description")

    if existing:
        existing.title = title
        existing.description = description_val or None
        existing.priority = priority
        existing.status = task_status
        existing.due_date = due_date
        existing.completed_at = completed_at
        existing.updated_at = datetime.now(UTC)
        return existing, False
    else:
        task = Task(
            id=task_id,
            title=title,
            description=description_val or None,
            priority=priority,
            status=task_status,
            due_date=due_date,
            completed_at=completed_at,
            created_at=created_at or datetime.now(UTC),
        )
        session.add(task)
        return task, True


# =============================================================================
# Upsert Deliverable (pour l'import direct via sync/import)
# =============================================================================


async def upsert_deliverable_from_import(
    session: AsyncSession,
    row: dict,
    *,
    id_key: str = "ID",
    safe_get: bool = False,
) -> tuple[Deliverable, bool]:
    """
    Cree ou met a jour un livrable depuis un dictionnaire de donnees (import direct).

    Le dictionnaire doit utiliser les cles :
    ID, ProjectID, Title, Description, Status.

    Args:
        session: Session de base de donnees async
        row: Dictionnaire avec les donnees du livrable
        id_key: Cle pour l'ID dans le dictionnaire
        safe_get: Si True, gere les valeurs None dans le dictionnaire

    Returns:
        Tuple (deliverable, created) - l'entite et un booleen

    Raises:
        ValueError: Si l'ID est vide ou absent
    """
    if safe_get:
        deliv_id = (row.get(id_key, "") or "").strip()
    else:
        deliv_id = row.get(id_key, "").strip()

    if not deliv_id:
        raise ValueError(f"ID manquant (cle: {id_key})")

    result = await session.execute(
        select(Deliverable).where(Deliverable.id == deliv_id)
    )
    existing = result.scalar_one_or_none()

    def _get(key: str, default: str = "") -> str | None:
        if safe_get:
            val = (row.get(key, default) or default).strip()
        else:
            val = row.get(key, default).strip()
        return val or None

    project_id = _get("ProjectID")
    raw_status = _get("Status", "pending") or "pending"
    status = raw_status.lower() if raw_status.lower() in VALID_DELIVERABLE_STATUSES_IMPORT else "pending"

    title = _get("Title", "Sans titre") or "Sans titre"
    description = _get("Description")

    if existing:
        existing.title = title
        existing.description = description
        existing.project_id = project_id
        existing.status = status
        existing.updated_at = datetime.now(UTC)
        return existing, False
    else:
        deliverable = Deliverable(
            id=deliv_id,
            title=title,
            description=description,
            project_id=project_id,
            status=status,
        )
        session.add(deliverable)
        return deliverable, True


# =============================================================================
# Helpers partages pour la synchronisation
# =============================================================================


async def update_last_sync_time(session: AsyncSession) -> str:
    """
    Met a jour le timestamp de derniere synchronisation dans les preferences.

    Returns:
        Le timestamp ISO au format string
    """
    result = await session.execute(
        select(Preference).where(Preference.key == "crm_last_sync")
    )
    last_sync_pref = result.scalar_one_or_none()
    now = datetime.now(UTC).isoformat()

    if last_sync_pref:
        last_sync_pref.value = now
        last_sync_pref.updated_at = datetime.now(UTC)
    else:
        last_sync_pref = Preference(key="crm_last_sync", value=now, category="crm")
        session.add(last_sync_pref)

    await session.commit()
    return now


def new_sync_stats() -> dict:
    """Cree un dictionnaire de statistiques de synchronisation vierge."""
    return {
        "contacts_created": 0,
        "contacts_updated": 0,
        "projects_created": 0,
        "projects_updated": 0,
        "deliverables_created": 0,
        "deliverables_updated": 0,
        "tasks_created": 0,
        "tasks_updated": 0,
        "errors": [],
    }


def compute_total_synced(stats: dict) -> int:
    """Calcule le total d'elements synchronises depuis un dict de stats."""
    return (
        stats["contacts_created"] + stats["contacts_updated"]
        + stats["projects_created"] + stats["projects_updated"]
        + stats["deliverables_created"] + stats["deliverables_updated"]
        + stats["tasks_created"] + stats["tasks_updated"]
    )
