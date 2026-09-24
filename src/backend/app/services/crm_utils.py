"""
THERESE v2 - CRM Utilities partagees

Fonctions utilitaires communes pour le CRM : upsert contact, upsert project,
upsert task, upsert deliverable, parsing de donnees, mappings de statuts.

Utilise par crm.py (router), crm_sync.py (service) et crm_import.py (service).
"""

import json
import logging
import math
import unicodedata
from datetime import UTC, datetime
from typing import get_args

from app.models.entities import Contact, Deliverable, Preference, Project, Task
from app.models.schemas import EtapePipeline, adresse_unique_valide
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

# B-1187 : une étape venue du tableur n'est retenue que si le pipeline la connaît.
ETAPES_PIPELINE = frozenset(get_args(EtapePipeline))

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
    # B-1108 : formes accentuées au féminin et anglaises (clés passées par
    # cle_de_statut : minuscules, sans accents, espaces en « _ »).
    "terminee": "completed",
    "livree": "completed",
    "annulee": "cancelled",
    "planifiee": "active",
    "actif": "active",
    "done": "completed",
    "finished": "completed",
    "paused": "on_hold",
    "canceled": "cancelled",
    "in_progress": "active",
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
    # B-1125 : priorités saisies en français dans le tableur
    "basse": "low",
    "faible": "low",
    "moyenne": "medium",
    "normale": "medium",
    "haute": "high",
    "elevee": "high",
    "urgente": "urgent",
}

VALID_TASK_STATUSES = {"todo", "in_progress", "done", "cancelled"}

# B-1125 : statuts de tâche en français ou en anglais (clés de cle_de_statut).
TASK_STATUS_MAP: dict[str, str] = {
    "todo": "todo", "a_faire": "todo",
    "in_progress": "in_progress", "en_cours": "in_progress",
    "done": "done", "fait": "done", "faite": "done", "termine": "done", "terminee": "done", "completed": "done",
    "cancelled": "cancelled", "canceled": "cancelled", "annule": "cancelled", "annulee": "cancelled",
}

# B-1109 : statuts des livrables ramenés au contrat de l'entité
# (a_faire, en_cours, en_revision, valide). L'ancienne liste (pending,
# in_progress, completed, blocked) réécrivait « valide » en « pending ».
# Même table que l'import de fichier (crm_import), plus les anciens alias.
DELIVERABLE_STATUS_MAP: dict[str, str] = {
    "a_faire": "a_faire", "a faire": "a_faire", "à faire": "a_faire", "todo": "a_faire", "pending": "a_faire",
    "en_cours": "en_cours", "en cours": "en_cours", "in_progress": "en_cours",
    "en_revision": "en_revision", "en revision": "en_revision", "en révision": "en_revision", "review": "en_revision",
    "valide": "valide", "validé": "valide", "done": "valide", "completed": "valide",
}




class LigneIncomplete(Exception):
    """B-1125 : ligne écartée avec un message, sans faire tomber la synchro.

    Pas une ValueError : les boucles de synchro ignorent celles-ci en silence
    (ID absent) ; celle-ci doit apparaître dans les erreurs rendues."""


def cle_de_statut(valeur: str | None) -> str:
    """B-1108 : « Terminé », « En cours » ou « On hold » deviennent « termine »,
    « en_cours » et « on_hold » : minuscules, sans accents, espaces et tirets
    ramenés à « _ ». Les tables de statuts sont cherchées avec cette clé."""
    texte = unicodedata.normalize("NFKD", (valeur or "").strip().lower())
    sans_accents = "".join(c for c in texte if not unicodedata.combining(c))
    return "_".join(sans_accents.replace("-", " ").split())


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


def score_du_tableur(valeur: object) -> int | None:
    """B-1213 : score lisible et compris entre 0 et 100, sinon None."""
    texte = str(valeur).strip() if valeur is not None else ""
    if not texte:
        return None
    try:
        nombre = float(texte)
    except ValueError:
        return None
    if not math.isfinite(nombre) or not 0 <= nombre <= 100:
        return None
    return int(nombre)


def parse_budget(value: str | int | float | None) -> float | None:
    """Parse un budget depuis une valeur quelconque."""
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
    if value == "":
        return None
    try:
        nombre = float(value)
    except (ValueError, TypeError):
        return None
    # B-1219 : un budget infini ou NaN n'est pas un budget.
    return nombre if math.isfinite(nombre) else None


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
    return PROJECT_STATUS_MAP.get(cle_de_statut(raw_status)) or default


def normalize_task_priority(raw_priority: str | None, default: str = "medium") -> str:
    """Normalise une priorite de tache vers une valeur valide."""
    return TASK_PRIORITY_MAP.get(cle_de_statut(raw_priority), default)


def normalize_task_status(raw_status: str | None, default: str = "todo") -> str:
    """Normalise un statut de tache vers une valeur valide."""
    return TASK_STATUS_MAP.get(cle_de_statut(raw_status)) or default


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

    # B-1213 : un score illisible ou hors de 0 à 100 ne vaut rien (jumeau de
    # B-1165) ; il ne remplace pas le score enregistré.
    score_lu = score_du_tableur(row.get("Score"))

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

    # B-1081 : une adresse double ou douteuse venue du tableur n'est pas
    # recopiée (même règle que la fiche, B-1074) ; le reste de la ligne l'est.
    # B-1107 : sur une fiche existante, elle n'efface pas non plus l'adresse
    # valide déjà enregistrée. Une cellule vide garde son sens de miroir.
    courriel = _get("Email")
    courriel_refuse = bool(courriel) and not adresse_unique_valide(courriel)
    if courriel_refuse:
        courriel = existing.email if existing else None

    # B-1187 : même règle que B-1108/B-1125 (arbitrage du 24/09) : le tableur
    # fait foi pour ce qu'il dit, pas pour ce qu'il tait. Une cellule vide ou
    # une étape inconnue ne remplace pas la valeur enregistrée.
    etape_cellule = (_get("Stage") or "").lower()
    etape = etape_cellule if etape_cellule in ETAPES_PIPELINE else None

    if existing:
        if full_name:
            existing.first_name = first_name
            existing.last_name = last_name
        for attribut, colonne in (("company", "Entreprise"), ("phone", "Tel"), ("source", "Source")):
            valeur = _get(colonne)
            if valeur:
                setattr(existing, attribut, valeur)
        existing.email = courriel
        if etape:
            existing.stage = etape
        if score_lu is not None:
            existing.score = score_lu
        if tags_json is not None:
            existing.tags = tags_json
        existing.updated_at = datetime.now(UTC)
        return existing, False
    else:
        contact = Contact(
            id=crm_id,
            first_name=first_name,
            last_name=last_name,
            company=_get("Entreprise"),
            email=courriel,
            phone=_get("Tel"),
            source=_get("Source"),
            stage=etape or "contact",
            score=score_lu if score_lu is not None else 50,
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

    # B-1108 : le tableur fait foi pour ce qu'il dit, pas pour ce qu'il tait.
    # Une cellule ClientID vide ou un client inconnu ne délie pas le projet ;
    # un statut vide ou inconnu ne remplace pas le statut enregistré. La
    # requête (et non session.get) voit aussi un client créé plus tôt dans la
    # même synchro, pas encore validé en base.
    client_id = _get("ClientID")
    if client_id:
        connu = await session.execute(select(Contact.id).where(Contact.id == client_id))
        if connu.scalar_one_or_none() is None:
            client_id = None

    table_des_statuts = {cle_de_statut(cle): valeur for cle, valeur in effective_map.items()}
    status = table_des_statuts.get(cle_de_statut(_get("Status")))
    if status not in VALID_PROJECT_STATUSES:
        status = None

    budget_raw = row.get("Budget", "")
    if isinstance(budget_raw, str):
        budget_raw = budget_raw.strip() if budget_raw else ""
    budget = parse_budget(budget_raw)

    name = _get("Name", "Sans nom") or "Sans nom"
    description = _get("Description")
    notes = _get("Notes")

    if existing:
        # B-1188 : une cellule vide ne remplace ni le nom par « Sans nom »,
        # ni la description, le budget ou les notes (arbitrage du 24/09).
        if _get("Name"):
            existing.name = name
        if description:
            existing.description = description
        if client_id:
            existing.contact_id = client_id
        if status:
            existing.status = status
        if budget is not None and budget_raw:
            existing.budget = budget
        if notes:
            existing.notes = notes
        existing.updated_at = datetime.now(UTC)
        return existing, False
    else:
        project = Project(
            id=project_id,
            name=name,
            description=description,
            contact_id=client_id,
            status=status or "active",
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

    # B-1125 : une priorité ou un statut vide ou inconnu ne remplace pas
    # la valeur enregistrée ; une tâche neuve prend « medium » et « todo ».
    priority = TASK_PRIORITY_MAP.get(cle_de_statut(_get_str("Priority")))
    task_status = TASK_STATUS_MAP.get(cle_de_statut(_get_str("Status")))

    # Parser les dates
    due_date = parse_datetime(_get_str("DueDate"))
    created_at = parse_datetime(_get_str("CreatedAt"))
    completed_at = parse_datetime(_get_str("CompletedAt"))

    title = _get_str("Title", "Sans titre") or "Sans titre"
    description_val = _get_str("Description")

    if existing:
        # B-1188 : une cellule vide n'invente pas « Sans titre » et n'efface
        # ni la description ni les dates.
        if _get_str("Title"):
            existing.title = title
        if description_val:
            existing.description = description_val
        if priority:
            existing.priority = priority
        if task_status:
            existing.status = task_status
        if due_date is not None:
            existing.due_date = due_date
        if completed_at is not None:
            existing.completed_at = completed_at
        # B-1212 : même règle que la route des tâches, une tâche qui n'est plus
        # « done » n'a pas de date de fin (la cellule vide ne la protège pas).
        if existing.status != "done":
            existing.completed_at = None
        existing.updated_at = datetime.now(UTC)
        return existing, False
    else:
        task = Task(
            id=task_id,
            title=title,
            description=description_val or None,
            priority=priority or "medium",
            status=task_status or "todo",
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

    # B-1125 : un projet vide ou inconnu ne détache pas un livrable existant ;
    # un livrable neuf sans projet connu est écarté avec un message (la
    # colonne project_id est NOT NULL : l'échec éclatait au commit final et
    # faisait tomber toute la synchro en 500).
    project_id = _get("ProjectID")
    if project_id:
        connu = await session.execute(select(Project.id).where(Project.id == project_id))
        if connu.scalar_one_or_none() is None:
            project_id = None
    if not project_id and not existing:
        raise LigneIncomplete(f"livrable {deliv_id} écarté : aucun projet connu (colonne ProjectID vide ou inconnue)")
    # B-1109 : un statut absent, vide ou inconnu ne remplace pas celui d'un
    # livrable existant (même règle que B-1083 et B-1106).
    statut_reconnu = DELIVERABLE_STATUS_MAP.get(cle_de_statut(_get("Status")))

    title = _get("Title", "Sans titre") or "Sans titre"
    description = _get("Description")

    if existing:
        # B-1188 : ni titre inventé ni description effacée par une cellule vide.
        if _get("Title"):
            existing.title = title
        if description:
            existing.description = description
        if project_id:
            existing.project_id = project_id
        if statut_reconnu:
            existing.status = statut_reconnu
        existing.updated_at = datetime.now(UTC)
        return existing, False
    else:
        deliverable = Deliverable(
            id=deliv_id,
            title=title,
            description=description,
            project_id=project_id,
            status=statut_reconnu or "a_faire",
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
