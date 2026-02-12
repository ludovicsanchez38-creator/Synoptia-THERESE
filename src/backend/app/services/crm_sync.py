"""
THERESE v2 - CRM Sync Service

Synchronizes data from Google Sheets CRM to local SQLite database.
Google Sheets is the source of truth.

Sprint 2 - PERF-2.4: Migrated to AsyncSession for proper async DB operations.
Refactored: utilise crm_utils pour les upserts partages.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from app.models.entities import Contact, Deliverable, Preference, Project
from app.services.crm_utils import (
    parse_datetime,
    upsert_contact,
    upsert_project,
    upsert_task,
)
from app.services.sheets_service import GoogleSheetsService
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

logger = logging.getLogger(__name__)


# ============================================================
# Sync Configuration
# ============================================================


CRM_SPREADSHEET_ID_KEY = "crm_spreadsheet_id"
CRM_SHEETS_TOKEN_KEY = "crm_sheets_access_token"
CRM_SHEETS_REFRESH_TOKEN_KEY = "crm_sheets_refresh_token"
CRM_SHEETS_CLIENT_ID_KEY = "crm_sheets_client_id"
CRM_SHEETS_CLIENT_SECRET_KEY = "crm_sheets_client_secret"
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
    Synchronizes CRM data from Google Sheets to THERESE.

    Google Sheets is the master data source.
    Sync is unidirectional: Sheets -> THERESE.

    Sprint 2 - PERF-2.4: Uses AsyncSession for non-blocking DB operations.
    Refactored: delegue les upserts a crm_utils.
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

        Syncs: Clients -> Projects -> Deliverables -> Tasks

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

        Utilise upsert_contact() de crm_utils + gestion last_interaction specifique.
        """
        for row in clients_data:
            try:
                contact, created = await upsert_contact(self.session, row)
                # Champ specifique au sync service : last_interaction
                last_interaction = parse_datetime(row.get("LastInteraction", ""))
                contact.last_interaction = last_interaction
                if created:
                    stats.contacts_created += 1
                else:
                    stats.contacts_updated += 1
            except ValueError:
                continue  # ID manquant
            except Exception as e:
                logger.error(f"Error syncing contact {row.get('ID', 'unknown')}: {e}")
                stats.errors.append(f"Contact {row.get('ID', 'unknown')}: {str(e)}")

    async def _sync_projects(self, projects_data: list[dict], stats: SyncStats):
        """
        Sync projects from Sheets to Project entities.

        Utilise upsert_project() de crm_utils + verification contact existant.
        """
        for row in projects_data:
            try:
                project, created = await upsert_project(self.session, row)
                # Verification specifique : le contact lie existe-t-il ?
                if project.contact_id:
                    contact = await self.session.get(Contact, project.contact_id)
                    if not contact:
                        project.contact_id = None  # Ne pas lier a un contact inexistant
                if created:
                    stats.projects_created += 1
                else:
                    stats.projects_updated += 1
            except ValueError:
                continue
            except Exception as e:
                logger.error(f"Error syncing project {row.get('ID', 'unknown')}: {e}")
                stats.errors.append(f"Project {row.get('ID', 'unknown')}: {str(e)}")

    async def _sync_deliverables(self, deliverables_data: list[dict], stats: SyncStats):
        """
        Sync deliverables from Sheets to Deliverable entities.

        Ce mapping est specifique au service sync (statuts en francais, verification projet).
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

                existing = await self.session.get(Deliverable, deliverable_id)

                # Get project ID
                project_id = row.get("ProjectID", "").strip()
                if not project_id:
                    continue  # Skip deliverables without project

                # Verify project exists
                project = await self.session.get(Project, project_id)
                if not project:
                    logger.warning(f"Deliverable {deliverable_id} references unknown project {project_id}")
                    continue

                # Parse status
                raw_status = row.get("Status", "a_faire").strip().lower()
                status = status_map.get(raw_status, "a_faire")

                # Parse dates
                due_date = parse_datetime(row.get("DueDate", ""))
                completed_at = parse_datetime(row.get("DeliveredDate", ""))

                if existing:
                    existing.title = row.get("Title", "Sans titre").strip()
                    existing.description = row.get("Description", "").strip() or None
                    existing.project_id = project_id
                    existing.status = status
                    existing.due_date = due_date
                    existing.completed_at = completed_at
                    existing.updated_at = datetime.now(UTC)
                    self.session.add(existing)
                    stats.deliverables_updated += 1
                else:
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

        Utilise upsert_task() de crm_utils.
        """
        for row in tasks_data:
            try:
                _, created = await upsert_task(self.session, row)
                if created:
                    stats.tasks_created += 1
                else:
                    stats.tasks_updated += 1
            except ValueError:
                continue
            except Exception as e:
                logger.error(f"Error syncing task {row.get('ID', 'unknown')}: {e}")
                stats.errors.append(f"Task {row.get('ID', 'unknown')}: {str(e)}")


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
        pref.updated_at = datetime.now(UTC)
    else:
        pref = Preference(
            key=CRM_SPREADSHEET_ID_KEY,
            value=spreadsheet_id,
            category="crm",
        )

    session.add(pref)
    await session.commit()


async def set_crm_tokens(
    session: AsyncSession,
    access_token: str,
    refresh_token: str | None = None,
    client_id: str | None = None,
    client_secret: str | None = None,
):
    """Store CRM Sheets tokens and credentials in preferences."""
    from app.services.encryption import encrypt_value

    # Store access token (encrypted)
    result = await session.execute(
        select(Preference).where(Preference.key == CRM_SHEETS_TOKEN_KEY)
    )
    pref = result.scalar_one_or_none()

    encrypted_token = encrypt_value(access_token)

    if pref:
        pref.value = encrypted_token
        pref.updated_at = datetime.now(UTC)
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
            pref.updated_at = datetime.now(UTC)
        else:
            pref = Preference(
                key=CRM_SHEETS_REFRESH_TOKEN_KEY,
                value=encrypted_refresh,
                category="crm",
            )
        session.add(pref)

    # Store client credentials for token refresh
    for key, value in [
        (CRM_SHEETS_CLIENT_ID_KEY, client_id),
        (CRM_SHEETS_CLIENT_SECRET_KEY, client_secret),
    ]:
        if value:
            result = await session.execute(
                select(Preference).where(Preference.key == key)
            )
            pref = result.scalar_one_or_none()
            encrypted = encrypt_value(value)
            if pref:
                pref.value = encrypted
                pref.updated_at = datetime.now(UTC)
            else:
                pref = Preference(key=key, value=encrypted, category="crm")
            session.add(pref)

    await session.commit()


async def get_crm_access_token(session: AsyncSession) -> str | None:
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


async def ensure_valid_crm_token(session: AsyncSession) -> str | None:
    """
    Ensure the CRM Sheets access token is valid, refreshing if needed.

    Tente de refresh le token via le refresh_token stocké.
    Si pas de refresh_token ou échec du refresh, retourne le token actuel
    (qui sera peut-être expiré - le 401 sera géré par l'appelant).

    Returns:
        Access token valide (ou None si aucun token).
    """
    from app.services.encryption import decrypt_value, encrypt_value
    from app.services.oauth import (
        GOOGLE_TOKEN_URL,
        GSHEETS_SCOPES,
        RUNTIME_PORT,
        OAuthConfig,
        get_oauth_service,
    )

    # Get current access token
    access_token = await get_crm_access_token(session)
    if not access_token:
        return None

    # Get refresh token
    result = await session.execute(
        select(Preference).where(Preference.key == CRM_SHEETS_REFRESH_TOKEN_KEY)
    )
    refresh_pref = result.scalar_one_or_none()
    if not refresh_pref or not refresh_pref.value:
        logger.warning("Pas de refresh token CRM, impossible de rafraîchir")
        return access_token

    try:
        refresh_token = decrypt_value(refresh_pref.value)
    except Exception:
        logger.error("Impossible de déchiffrer le refresh token CRM")
        return access_token

    # Get client credentials (stored or from EmailAccount/MCP)
    client_id = None
    client_secret = None

    # 1. Try stored CRM credentials
    for key, attr in [
        (CRM_SHEETS_CLIENT_ID_KEY, "client_id"),
        (CRM_SHEETS_CLIENT_SECRET_KEY, "client_secret"),
    ]:
        result = await session.execute(
            select(Preference).where(Preference.key == key)
        )
        pref = result.scalar_one_or_none()
        if pref and pref.value:
            try:
                val = decrypt_value(pref.value)
                if attr == "client_id":
                    client_id = val
                else:
                    client_secret = val
            except Exception:
                pass

    # 2. Fallback: EmailAccount Gmail credentials
    if not client_id or not client_secret:
        from app.models.entities import EmailAccount

        email_result = await session.execute(
            select(EmailAccount).where(
                EmailAccount.provider == "gmail",
                EmailAccount.client_id.isnot(None),
                EmailAccount.client_secret.isnot(None),
            )
        )
        email_account = email_result.scalar_one_or_none()
        if email_account and email_account.client_id and email_account.client_secret:
            try:
                client_id = decrypt_value(email_account.client_id)
                client_secret = decrypt_value(email_account.client_secret)
            except Exception:
                pass

    if not client_id or not client_secret:
        logger.warning("Pas de credentials OAuth pour refresh CRM token")
        return access_token

    # Refresh the token
    try:
        oauth_service = get_oauth_service()
        config = OAuthConfig(
            client_id=client_id,
            client_secret=client_secret,
            auth_url="",  # Non utilisé pour le refresh
            token_url=GOOGLE_TOKEN_URL,
            scopes=GSHEETS_SCOPES,
            redirect_uri=f"http://localhost:{RUNTIME_PORT}/api/crm/sync/callback",
        )

        new_tokens = await oauth_service.refresh_access_token(refresh_token, config)
        new_access_token = new_tokens["access_token"]

        # Update stored access token
        result = await session.execute(
            select(Preference).where(Preference.key == CRM_SHEETS_TOKEN_KEY)
        )
        pref = result.scalar_one_or_none()
        if pref:
            pref.value = encrypt_value(new_access_token)
            pref.updated_at = datetime.now(UTC)
            session.add(pref)
            await session.commit()

        logger.info("CRM Sheets access token rafraîchi avec succès")
        return new_access_token

    except Exception as e:
        logger.warning(f"Échec du refresh CRM token: {e} - utilisation du token actuel")
        return access_token


async def update_last_sync(session: AsyncSession):
    """Update last sync timestamp."""
    result = await session.execute(
        select(Preference).where(Preference.key == CRM_LAST_SYNC_KEY)
    )
    pref = result.scalar_one_or_none()

    now = datetime.now(UTC).isoformat()

    if pref:
        pref.value = now
        pref.updated_at = datetime.now(UTC)
    else:
        pref = Preference(
            key=CRM_LAST_SYNC_KEY,
            value=now,
            category="crm",
        )

    session.add(pref)
    await session.commit()
