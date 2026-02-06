"""
THERESE v2 - Service d'Audit

Logging des activites utilisateur pour tracabilite et securite.

US-SEC-05: Logs d'activite
"""

import logging
from datetime import UTC, datetime
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field, SQLModel, select

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """Types d'actions auditees."""

    # Authentification / Cles API
    API_KEY_SET = "api_key_set"
    API_KEY_DELETED = "api_key_deleted"
    API_KEY_ROTATED = "api_key_rotated"

    # Profil utilisateur
    PROFILE_UPDATED = "profile_updated"
    PROFILE_DELETED = "profile_deleted"

    # Donnees
    CONTACT_CREATED = "contact_created"
    CONTACT_UPDATED = "contact_updated"
    CONTACT_DELETED = "contact_deleted"
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_DELETED = "project_deleted"

    # Conversations
    CONVERSATION_CREATED = "conversation_created"
    CONVERSATION_DELETED = "conversation_deleted"

    # Fichiers
    FILE_INDEXED = "file_indexed"
    FILE_DELETED = "file_deleted"

    # Export / RGPD
    DATA_EXPORTED = "data_exported"
    DATA_DELETED_ALL = "data_deleted_all"

    # Configuration
    CONFIG_CHANGED = "config_changed"
    LLM_PROVIDER_CHANGED = "llm_provider_changed"

    # Board
    BOARD_DECISION = "board_decision"

    # Erreurs
    AUTH_FAILED = "auth_failed"
    ENCRYPTION_ERROR = "encryption_error"


class ActivityLog(SQLModel, table=True):
    """Log d'activite utilisateur."""

    __tablename__ = "activity_logs"

    id: int | None = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
    action: str = Field(index=True)  # AuditAction value
    resource_type: str | None = None  # contact, project, conversation, etc.
    resource_id: str | None = None
    details: str | None = None  # JSON serialized details
    ip_address: str | None = None
    user_agent: str | None = None

    class Config:
        """Pydantic config."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class AuditService:
    """Service de logging d'activite."""

    def __init__(self, session: AsyncSession):
        """Initialise avec une session de base de donnees."""
        self.session = session

    async def log(
        self,
        action: AuditAction,
        resource_type: str | None = None,
        resource_id: str | None = None,
        details: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> ActivityLog:
        """
        Enregistre une action dans les logs.

        Args:
            action: Type d'action
            resource_type: Type de ressource (contact, project, etc.)
            resource_id: ID de la ressource
            details: Details supplementaires (JSON)
            ip_address: Adresse IP du client
            user_agent: User-Agent du client

        Returns:
            L'entree de log creee
        """
        log_entry = ActivityLog(
            action=action.value,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.session.add(log_entry)
        await self.session.commit()
        await self.session.refresh(log_entry)

        logger.debug(f"Audit: {action.value} - {resource_type}:{resource_id}")

        return log_entry

    async def get_logs(
        self,
        action: AuditAction | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ActivityLog]:
        """
        Recupere les logs d'activite avec filtres.

        Args:
            action: Filtrer par type d'action
            resource_type: Filtrer par type de ressource
            resource_id: Filtrer par ID de ressource
            start_date: Date de debut
            end_date: Date de fin
            limit: Nombre max de resultats
            offset: Offset pour pagination

        Returns:
            Liste des logs correspondants
        """
        query = select(ActivityLog).order_by(ActivityLog.timestamp.desc())

        if action:
            query = query.where(ActivityLog.action == action.value)

        if resource_type:
            query = query.where(ActivityLog.resource_type == resource_type)

        if resource_id:
            query = query.where(ActivityLog.resource_id == resource_id)

        if start_date:
            query = query.where(ActivityLog.timestamp >= start_date)

        if end_date:
            query = query.where(ActivityLog.timestamp <= end_date)

        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_logs_count(
        self,
        action: AuditAction | None = None,
        resource_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> int:
        """Compte le nombre de logs correspondant aux filtres."""
        from sqlalchemy import func

        query = select(func.count(ActivityLog.id))

        if action:
            query = query.where(ActivityLog.action == action.value)

        if resource_type:
            query = query.where(ActivityLog.resource_type == resource_type)

        if start_date:
            query = query.where(ActivityLog.timestamp >= start_date)

        if end_date:
            query = query.where(ActivityLog.timestamp <= end_date)

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def cleanup_old_logs(self, days: int = 90) -> int:
        """
        Supprime les logs de plus de N jours.

        Args:
            days: Nombre de jours de retention

        Returns:
            Nombre de logs supprimes
        """
        from datetime import timedelta

        from sqlalchemy import delete

        cutoff_date = datetime.now(UTC) - timedelta(days=days)

        query = delete(ActivityLog).where(ActivityLog.timestamp < cutoff_date)
        result = await self.session.execute(query)
        await self.session.commit()

        deleted_count = result.rowcount
        logger.info(f"Supprime {deleted_count} logs de plus de {days} jours")

        return deleted_count


# Helper pour logging rapide sans session
async def log_activity(
    session: AsyncSession,
    action: AuditAction,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: str | None = None,
) -> ActivityLog:
    """Helper pour logger une activite."""
    service = AuditService(session)
    return await service.log(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )
