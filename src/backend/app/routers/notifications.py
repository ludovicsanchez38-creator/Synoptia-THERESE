"""
THERESE v2 - Notifications Router (US-004)

API endpoints pour les notifications push in-app.
"""

import logging

from app.models.database import get_session
from app.models.entities import Notification
from app.models.schemas import NotificationCountResponse, NotificationResponse
from app.services import notification_service
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
logger = logging.getLogger(__name__)


def _notification_to_response(notif: Notification) -> NotificationResponse:
    """Convertit un objet Notification en NotificationResponse."""
    return NotificationResponse(
        id=notif.id,
        title=notif.title,
        message=notif.message,
        type=notif.type,
        source=notif.source,
        action_url=notif.action_url,
        action_label=notif.action_label,
        is_read=notif.is_read,
        created_at=notif.created_at.isoformat() if notif.created_at else "",
        read_at=notif.read_at.isoformat() if notif.read_at else None,
    )


@router.get("/")
async def list_notifications(
    limit: int = Query(50, ge=1, le=200, description="Nombre max de notifications"),
    unread_only: bool = Query(False, description="Uniquement les non lues"),
    session: AsyncSession = Depends(get_session),
) -> list[NotificationResponse]:
    """Liste les notifications (les plus recentes en premier)."""
    notifications = await notification_service.get_notifications(
        session, limit=limit, unread_only=unread_only,
    )
    return [_notification_to_response(n) for n in notifications]


@router.get("/count")
async def get_unread_count(
    session: AsyncSession = Depends(get_session),
) -> NotificationCountResponse:
    """Retourne le nombre de notifications non lues."""
    count = await notification_service.get_unread_count(session)
    return NotificationCountResponse(unread_count=count)


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    session: AsyncSession = Depends(get_session),
) -> NotificationResponse:
    """Marque une notification comme lue."""
    notif = await notification_service.mark_as_read(session, notification_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification introuvable")
    return _notification_to_response(notif)


@router.post("/read-all")
async def mark_all_notifications_read(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Marque toutes les notifications comme lues."""
    count = await notification_service.mark_all_read(session)
    return {"marked_read": count}


@router.post("/generate")
async def generate_notifications() -> dict:
    """Declenche manuellement la generation de notifications (debug)."""
    results = await notification_service.generate_automatic_notifications()
    return {"generated": results, "total": sum(results.values())}
