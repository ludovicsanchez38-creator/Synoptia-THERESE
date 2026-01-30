"""
THÉRÈSE v2 - CRM Sync Service

Synchronizes data from Google Sheets CRM to local SQLite database.
Google Sheets is the source of truth.

Sprint 2 - PERF-2.4: Migrated to AsyncSession for proper async DB operations.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.entities import Contact, Project, Deliverable, Task, Preference
from app.services.sheets_service import GoogleSheetsService

logger = logging.getLogger(__name__)


# ============================================================
# Sync Configuration
# ============================================================


CRM_SPREADSHEET_ID_KEY = "crm_spreadsheet_id"
CRM_SHEETS_TOKEN_KEY = "crm_sheets_access_token"
CRM_SHEETS_REFRESH_TOKEN_KEY = "crm_sheets_refresh_token"
CRM_LAST_SYNC_KEY = "crm_last_sync"


@dataclass
class SyncStats:
    """Statistics from a sync operation."""
    contacts_created: int = 0
    contacts_updated: int = 0
    projects_created: int = 0
    projects_updated: int = 0
    deliverables_created: int = 0
    deliverables_updated: int = 0
    tasks_created: int = 0
    tasks_updated: int = 0
    errors: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    def to_dict(self) -> dict:
        return {
            "contacts_created": self.contacts_created,
            "contacts_updated": self.contacts_updated,
            "projects_created": self.projects_created,
            "projects_updated": self.projects_updated,
            "deliverables_created": self.deliverables_created,
            "deliverables_updated": self.deliverables_updated,
            "tasks_created": self.tasks_created,
            "tasks_updated": self.tasks_updated,
            "errors": self.errors,
            "total_synced": (
                self.contacts_created + self.contacts_updated +
                self.projects_created + self.projects_updated +
                self.deliverables_created + self.deliverables_updated +
                self.tasks_created + self.tasks_updated
            ),
        }


# ============================================================
# CRM Sync Service
# ============================================================


class CRMSyncService:
    """
    Synchronizes CRM data from Google Sheets to THÉRÈSE.

    Google Sheets is the master data source.
    Sync is unidirectional: Sheets -> THÉRÈSE.

    Sprint 2 - PERF-2.4: Uses AsyncSession for non-blocking DB operations.
    """

    def __init__(self, session: AsyncSession, sheets_service: GoogleSheetsService):
        """
        Initialize sync service.

        Args:
            session: SQLAlchemy AsyncSession for database operations
            sheets_service: Authenticated Google Sheets service
        """
        self.session = session
        self.sheets = sheets_service

    async def sync_all(self, spreadsheet_id: str) -> SyncStats:
        """
        Sync all CRM data from Google Sheets.

        Syncs: Clients -> Projects -> Deliverables

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID

        Returns:
            SyncStats with counts and errors
        """
        stats = SyncStats()

        # Sync Clients -> Contacts
        try:
            clients_data = await self.sheets.get_all_data_as_dicts(spreadsheet_id, "Clients")
            logger.info(f"Found {len(clients_data)} clients in Google Sheets")
            await self._sync_contacts(clients_data, stats)
        except Exception as e:
            logger.error(f"Error syncing clients: {e}")
            stats.errors.append(f"Clients: {str(e)}")

        # Sync Projects
        try:
            projects_data = await self.sheets.get_all_data_as_dicts(spreadsheet_id, "Projects")
            logger.info(f"Found {len(projects_data)} projects in Google Sheets")
            await self._sync_projects(projects_data, stats)
        except Exception as e:
            logger.error(f"Error syncing projects: {e}")
            stats.errors.append(f"Projects: {str(e)}")

        # Sync Deliverables
        try:
            deliverables_data = await self.sheets.get_all_data_as_dicts(spreadsheet_id, "Deliverables")
            logger.info(f"Found {len(deliverables_data)} deliverables in Google Sheets")
            await self._sync_deliverables(deliverables_data, stats)
        except Exception as e:
            logger.error(f"Error syncing deliverables: {e}")
            stats.errors.append(f"Deliverables: {str(e)}")

        # Sync Tasks
        try:
            tasks_data = await self.sheets.get_all_data_as_dicts(spreadsheet_id, "Tasks")
            logger.info(f"Found {len(tasks_data)} tasks in Google Sheets")
            await self._sync_tasks(tasks_data, stats)
        except Exception as e:
            logger.error(f"Error syncing tasks: {e}")
            stats.errors.append(f"Tasks: {str(e)}")

        # Commit all changes (Sprint 2 - PERF-2.4: async commit)
        await self.session.commit()

        logger.info(f"CRM Sync completed: {stats.to_dict()}")
        return stats

    async def _sync_contacts(self, clients_data: list[dict], stats: SyncStats):
        """
        Sync clients from Sheets to Contact entities.

        Mapping:
            Sheets.ID -> Contact.id
            Sheets.Nom -> Contact.first_name + last_name (split)
            Sheets.Entreprise -> Contact.company
            Sheets.Email -> Contact.email
            Sheets.Tel -> Contact.phone
            Sheets.Source -> Contact.source
            Sheets.Stage -> Contact.stage
            Sheets.Score -> Contact.score
            Sheets.Tags -> Contact.tags (JSON)
            Sheets.LastInteraction -> Contact.last_interaction
        """
        for row in clients_data:
            try:
                crm_id = row.get("ID", "").strip()
                if not crm_id:
                    continue

                # Check if contact exists (Sprint 2 - PERF-2.4: async get)
                existing = await self.session.get(Contact, crm_id)

                # Parse name (split on first space)
                full_name = row.get("Nom", "").strip()
                first_name, last_name = self._split_name(full_name)

                # Parse score
                score_str = row.get("Score", "50").strip()
                try:
                    score = int(float(score_str)) if score_str else 50
                except ValueError:
                    score = 50

                # Parse tags
                tags_str = row.get("Tags", "").strip()
                tags_json = json.dumps(tags_str.split(",")) if tags_str else None

                # Parse last interaction
                last_interaction = self._parse_datetime(row.get("LastInteraction", ""))

                if existing:
                    # Update existing contact
                    existing.first_name = first_name
                    existing.last_name = last_name
                    existing.company = row.get("Entreprise", "").strip() or None
                    existing.email = row.get("Email", "").strip() or None
                    existing.phone = row.get("Tel", "").strip() or None
                    existing.source = row.get("Source", "").strip() or None
                    existing.stage = row.get("Stage", "contact").strip() or "contact"
                    existing.score = score
                    existing.tags = tags_json
                    existing.last_interaction = last_interaction
                    existing.updated_at = datetime.utcnow()
                    self.session.add(existing)
                    stats.contacts_updated += 1
                else:
                    # Create new contact
                    contact = Contact(
                        id=crm_id,
                        first_name=first_name,
                        last_name=last_name,
                        company=row.get("Entreprise", "").strip() or None,
                        email=row.get("Email", "").strip() or None,
                        phone=row.get("Tel", "").strip() or None,
                        source=row.get("Source", "").strip() or None,
                        stage=row.get("Stage", "contact").strip() or "contact",
                        score=score,
                        tags=tags_json,
                        last_interaction=last_interaction,
                        scope="global",
                    )
                    self.session.add(contact)
                    stats.contacts_created += 1

            except Exception as e:
                logger.error(f"Error syncing contact {row.get('ID', 'unknown')}: {e}")
                stats.errors.append(f"Contact {row.get('ID', 'unknown')}: {str(e)}")

    async def _sync_projects(self, projects_data: list[dict], stats: SyncStats):
        """
        Sync projects from Sheets to Project entities.

        Mapping:
            Sheets.ID -> Project.id
            Sheets.ClientID -> Project.contact_id
            Sheets.Name -> Project.name
            Sheets.Description -> Project.description
            Sheets.Status -> Project.status
            Sheets.Budget -> Project.budget
            Sheets.Notes -> Project.notes
        """
        # Map status values
        status_map = {
            "en_cours": "active",
            "en_pause": "on_hold",
            "termine": "completed",
            "annule": "cancelled",
        }

        for row in projects_data:
            try:
                project_id = row.get("ID", "").strip()
                if not project_id:
                    continue

                # Check if project exists (Sprint 2 - PERF-2.4: async get)
                existing = await self.session.get(Project, project_id)

                # Get contact ID
                client_id = row.get("ClientID", "").strip() or None

                # Verify contact exists if client_id provided (Sprint 2 - PERF-2.4: async get)
                if client_id:
                    contact = await self.session.get(Contact, client_id)
                    if not contact:
                        client_id = None  # Don't link to non-existent contact

                # Parse status
                raw_status = row.get("Status", "active").strip().lower()
                status = status_map.get(raw_status, raw_status)
                if status not in ["active", "completed", "on_hold", "cancelled"]:
                    status = "active"

                # Parse budget
                budget_str = row.get("Budget", "").strip()
                try:
                    budget = float(budget_str) if budget_str else None
                except ValueError:
                    budget = None

                if existing:
                    # Update existing project
                    existing.name = row.get("Name", "Sans nom").strip()
                    existing.description = row.get("Description", "").strip() or None
                    existing.contact_id = client_id
                    existing.status = status
                    existing.budget = budget
                    existing.notes = row.get("Notes", "").strip() or None
                    existing.updated_at = datetime.utcnow()
                    self.session.add(existing)
                    stats.projects_updated += 1
                else:
                    # Create new project
                    project = Project(
                        id=project_id,
                        name=row.get("Name", "Sans nom").strip(),
                        description=row.get("Description", "").strip() or None,
                        contact_id=client_id,
                        status=status,
                        budget=budget,
                        notes=row.get("Notes", "").strip() or None,
                        scope="global",
                    )
                    self.session.add(project)
                    stats.projects_created += 1

            except Exception as e:
                logger.error(f"Error syncing project {row.get('ID', 'unknown')}: {e}")
                stats.errors.append(f"Project {row.get('ID', 'unknown')}: {str(e)}")

    async def _sync_deliverables(self, deliverables_data: list[dict], stats: SyncStats):
        """
        Sync deliverables from Sheets to Deliverable entities.

        Mapping:
            Sheets.ID -> Deliverable.id
            Sheets.ProjectID -> Deliverable.project_id
            Sheets.Title -> Deliverable.title
            Sheets.Description -> Deliverable.description
            Sheets.Status -> Deliverable.status
            Sheets.DueDate -> Deliverable.due_date
            Sheets.DeliveredDate -> Deliverable.completed_at
        """
        # Map status values
        status_map = {
            "a_faire": "a_faire",
            "en_cours": "en_cours",
            "en_revision": "en_revision",
            "valide": "valide",
            "todo": "a_faire",
            "in_progress": "en_cours",
            "review": "en_revision",
            "done": "valide",
        }

        for row in deliverables_data:
            try:
                deliverable_id = row.get("ID", "").strip()
                if not deliverable_id:
                    continue

                # Check if deliverable exists (Sprint 2 - PERF-2.4: async get)
                existing = await self.session.get(Deliverable, deliverable_id)

                # Get project ID
                project_id = row.get("ProjectID", "").strip()
                if not project_id:
                    continue  # Skip deliverables without project

                # Verify project exists (Sprint 2 - PERF-2.4: async get)
                project = await self.session.get(Project, project_id)
                if not project:
                    logger.warning(f"Deliverable {deliverable_id} references unknown project {project_id}")
                    continue

                # Parse status
                raw_status = row.get("Status", "a_faire").strip().lower()
                status = status_map.get(raw_status, "a_faire")

                # Parse dates
                due_date = self._parse_datetime(row.get("DueDate", ""))
                completed_at = self._parse_datetime(row.get("DeliveredDate", ""))

                if existing:
                    # Update existing deliverable
                    existing.title = row.get("Title", "Sans titre").strip()
                    existing.description = row.get("Description", "").strip() or None
                    existing.project_id = project_id
                    existing.status = status
                    existing.due_date = due_date
                    existing.completed_at = completed_at
                    existing.updated_at = datetime.utcnow()
                    self.session.add(existing)
                    stats.deliverables_updated += 1
                else:
                    # Create new deliverable
                    deliverable = Deliverable(
                        id=deliverable_id,
                        title=row.get("Title", "Sans titre").strip(),
                        description=row.get("Description", "").strip() or None,
                        project_id=project_id,
                        status=status,
                        due_date=due_date,
                        completed_at=completed_at,
                    )
                    self.session.add(deliverable)
                    stats.deliverables_created += 1

            except Exception as e:
                logger.error(f"Error syncing deliverable {row.get('ID', 'unknown')}: {e}")
                stats.errors.append(f"Deliverable {row.get('ID', 'unknown')}: {str(e)}")

    async def _sync_tasks(self, tasks_data: list[dict], stats: SyncStats):
        """
        Sync tasks from Sheets to Task entities.

        Mapping:
            Sheets.ID -> Task.id
            Sheets.ClientID -> (ignored, no direct field)
            Sheets.Title -> Task.title
            Sheets.Description -> Task.description
            Sheets.DueDate -> Task.due_date
            Sheets.Priority -> Task.priority (normal->medium, urgent->urgent)
            Sheets.Status -> Task.status (todo/done)
            Sheets.CreatedAt -> Task.created_at
            Sheets.CompletedAt -> Task.completed_at
        """
        priority_map = {
            "normal": "medium",
            "urgent": "urgent",
            "low": "low",
            "high": "high",
            "medium": "medium",
        }

        for row in tasks_data:
            try:
                task_id = row.get("ID", "").strip()
                if not task_id:
                    continue

                existing = await self.session.get(Task, task_id)

                # Parse priority
                raw_priority = row.get("Priority", "medium").strip().lower()
                priority = priority_map.get(raw_priority, "medium")

                # Parse status
                raw_status = row.get("Status", "todo").strip().lower()
                if raw_status not in ("todo", "in_progress", "done", "cancelled"):
                    raw_status = "todo"

                # Parse dates
                due_date = self._parse_datetime(row.get("DueDate", ""))
                created_at = self._parse_datetime(row.get("CreatedAt", ""))
                completed_at = self._parse_datetime(row.get("CompletedAt", ""))

                if existing:
                    existing.title = row.get("Title", "Sans titre").strip()
                    existing.description = row.get("Description", "").strip() or None
                    existing.priority = priority
                    existing.status = raw_status
                    existing.due_date = due_date
                    existing.completed_at = completed_at
                    existing.updated_at = datetime.utcnow()
                    self.session.add(existing)
                    stats.tasks_updated += 1
                else:
                    task = Task(
                        id=task_id,
                        title=row.get("Title", "Sans titre").strip(),
                        description=row.get("Description", "").strip() or None,
                        priority=priority,
                        status=raw_status,
                        due_date=due_date,
                        completed_at=completed_at,
                        created_at=created_at or datetime.utcnow(),
                    )
                    self.session.add(task)
                    stats.tasks_created += 1

            except Exception as e:
                logger.error(f"Error syncing task {row.get('ID', 'unknown')}: {e}")
                stats.errors.append(f"Task {row.get('ID', 'unknown')}: {str(e)}")

    def _split_name(self, full_name: str) -> tuple[str, Optional[str]]:
        """Split full name into first and last name."""
        parts = full_name.split(" ", 1)
        first_name = parts[0] if parts else ""
        last_name = parts[1] if len(parts) > 1 else None
        return first_name, last_name

    def _parse_datetime(self, value: str) -> Optional[datetime]:
        """Parse datetime from various formats."""
        if not value or not value.strip():
            return None

        value = value.strip()

        # Try ISO format
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


# ============================================================
# Config Helpers (Sprint 2 - PERF-2.4: Async versions)
# ============================================================


async def get_crm_config(session: AsyncSession) -> dict:
    """Get CRM sync configuration from preferences."""
    spreadsheet_id = None
    last_sync = None
    has_token = False

    # Get spreadsheet ID (Sprint 2 - PERF-2.4: async execute)
    result = await session.execute(
        select(Preference).where(Preference.key == CRM_SPREADSHEET_ID_KEY)
    )
    pref = result.scalar_one_or_none()
    if pref:
        spreadsheet_id = pref.value

    # Get last sync time
    result = await session.execute(
        select(Preference).where(Preference.key == CRM_LAST_SYNC_KEY)
    )
    pref = result.scalar_one_or_none()
    if pref:
        last_sync = pref.value

    # Check if token exists
    result = await session.execute(
        select(Preference).where(Preference.key == CRM_SHEETS_TOKEN_KEY)
    )
    pref = result.scalar_one_or_none()
    has_token = pref is not None and bool(pref.value)

    return {
        "spreadsheet_id": spreadsheet_id,
        "last_sync": last_sync,
        "has_token": has_token,
        "configured": bool(spreadsheet_id and has_token),
    }


async def set_crm_spreadsheet_id(session: AsyncSession, spreadsheet_id: str):
    """Set CRM spreadsheet ID in preferences."""
    result = await session.execute(
        select(Preference).where(Preference.key == CRM_SPREADSHEET_ID_KEY)
    )
    pref = result.scalar_one_or_none()

    if pref:
        pref.value = spreadsheet_id
        pref.updated_at = datetime.utcnow()
    else:
        pref = Preference(
            key=CRM_SPREADSHEET_ID_KEY,
            value=spreadsheet_id,
            category="crm",
        )

    session.add(pref)
    await session.commit()


async def set_crm_tokens(session: AsyncSession, access_token: str, refresh_token: Optional[str] = None):
    """Store CRM Sheets tokens in preferences."""
    from app.services.encryption import encrypt_value

    # Store access token (encrypted)
    result = await session.execute(
        select(Preference).where(Preference.key == CRM_SHEETS_TOKEN_KEY)
    )
    pref = result.scalar_one_or_none()

    encrypted_token = encrypt_value(access_token)

    if pref:
        pref.value = encrypted_token
        pref.updated_at = datetime.utcnow()
    else:
        pref = Preference(
            key=CRM_SHEETS_TOKEN_KEY,
            value=encrypted_token,
            category="crm",
        )
    session.add(pref)

    # Store refresh token if provided
    if refresh_token:
        result = await session.execute(
            select(Preference).where(Preference.key == CRM_SHEETS_REFRESH_TOKEN_KEY)
        )
        pref = result.scalar_one_or_none()

        encrypted_refresh = encrypt_value(refresh_token)

        if pref:
            pref.value = encrypted_refresh
            pref.updated_at = datetime.utcnow()
        else:
            pref = Preference(
                key=CRM_SHEETS_REFRESH_TOKEN_KEY,
                value=encrypted_refresh,
                category="crm",
            )
        session.add(pref)

    await session.commit()


async def get_crm_access_token(session: AsyncSession) -> Optional[str]:
    """Get decrypted CRM Sheets access token."""
    from app.services.encryption import decrypt_value

    result = await session.execute(
        select(Preference).where(Preference.key == CRM_SHEETS_TOKEN_KEY)
    )
    pref = result.scalar_one_or_none()

    if not pref or not pref.value:
        return None

    try:
        return decrypt_value(pref.value)
    except Exception as e:
        logger.error(f"Failed to decrypt CRM token: {e}")
        return None


async def update_last_sync(session: AsyncSession):
    """Update last sync timestamp."""
    result = await session.execute(
        select(Preference).where(Preference.key == CRM_LAST_SYNC_KEY)
    )
    pref = result.scalar_one_or_none()

    now = datetime.utcnow().isoformat()

    if pref:
        pref.value = now
        pref.updated_at = datetime.utcnow()
    else:
        pref = Preference(
            key=CRM_LAST_SYNC_KEY,
            value=now,
            category="crm",
        )

    session.add(pref)
    await session.commit()
