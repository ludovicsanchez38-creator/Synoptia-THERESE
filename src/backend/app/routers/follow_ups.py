"""
THERESE v2 - Follow-Ups Router

Endpoints CRUD pour les suivis métier liés aux emails.
Email Backlog.
"""

import logging
from datetime import UTC, datetime

from app.models.database import get_session
from app.models.entities import Contact, EmailFollowUp, EmailMessage
from app.models.schemas_email import (
    CreateFollowUpRequest,
    FollowUpResponse,
    UpdateFollowUpRequest,
)
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

logger = logging.getLogger(__name__)

router = APIRouter()


def _follow_up_to_response(fu: EmailFollowUp) -> FollowUpResponse:
    """Convertit un EmailFollowUp en FollowUpResponse."""
    return FollowUpResponse(
        id=fu.id,
        email_message_id=fu.email_message_id,
        contact_id=fu.contact_id,
        due_date=fu.due_date,
        note=fu.note,
        status=fu.status,
        created_at=fu.created_at,
    )


@router.post("", response_model=FollowUpResponse)
async def create_follow_up(
    request: CreateFollowUpRequest,
    session: AsyncSession = Depends(get_session),
) -> FollowUpResponse:
    """
    Crée un suivi métier lié à un email.
    """
    # Vérifier que le message existe
    message = await session.get(EmailMessage, request.email_message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Email message not found")

    # Vérifier le contact si fourni
    if request.contact_id:
        contact = await session.get(Contact, request.contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")

    follow_up = EmailFollowUp(
        email_message_id=request.email_message_id,
        contact_id=request.contact_id,
        due_date=request.due_date,
        note=request.note,
    )
    session.add(follow_up)
    await session.commit()
    await session.refresh(follow_up)

    logger.info("Follow-up créé : %s (échéance %s)", follow_up.id, follow_up.due_date)

    return _follow_up_to_response(follow_up)


@router.get("", response_model=list[FollowUpResponse])
async def list_follow_ups(
    status: str | None = Query(None, description="Filtrer par status (pending, done, cancelled)"),
    due_date: str | None = Query(None, description="Filtrer par date d'échéance (ISO 8601, ex: 2026-03-29)"),
    session: AsyncSession = Depends(get_session),
) -> list[FollowUpResponse]:
    """
    Liste les suivis métier avec filtres optionnels.
    """
    statement = select(EmailFollowUp)

    if status:
        statement = statement.where(EmailFollowUp.status == status)
    if due_date:
        # Filtre par préfixe de date (ex: "2026-03-29" matche "2026-03-29T...")
        statement = statement.where(EmailFollowUp.due_date.startswith(due_date))

    statement = statement.order_by(EmailFollowUp.due_date.asc())

    result = await session.execute(statement)
    follow_ups = result.scalars().all()

    return [_follow_up_to_response(fu) for fu in follow_ups]


@router.get("/due", response_model=list[FollowUpResponse])
async def list_due_follow_ups(
    session: AsyncSession = Depends(get_session),
) -> list[FollowUpResponse]:
    """
    Liste les suivis échus ou du jour (status=pending, due_date <= aujourd'hui).
    """
    today = datetime.now(UTC).strftime("%Y-%m-%d")

    statement = (
        select(EmailFollowUp)
        .where(EmailFollowUp.status == "pending")
        .where(EmailFollowUp.due_date <= today + "T23:59:59")
        .order_by(EmailFollowUp.due_date.asc())
    )

    result = await session.execute(statement)
    follow_ups = result.scalars().all()

    return [_follow_up_to_response(fu) for fu in follow_ups]


@router.put("/{follow_up_id}", response_model=FollowUpResponse)
async def update_follow_up(
    follow_up_id: str,
    request: UpdateFollowUpRequest,
    session: AsyncSession = Depends(get_session),
) -> FollowUpResponse:
    """
    Met à jour un suivi métier.
    """
    follow_up = await session.get(EmailFollowUp, follow_up_id)
    if not follow_up:
        raise HTTPException(status_code=404, detail="Follow-up not found")

    if request.due_date is not None:
        follow_up.due_date = request.due_date
    if request.note is not None:
        follow_up.note = request.note
    if request.status is not None:
        if request.status not in ("pending", "done", "cancelled"):
            raise HTTPException(
                status_code=400,
                detail="Invalid status. Must be 'pending', 'done', or 'cancelled'.",
            )
        follow_up.status = request.status
    if request.contact_id is not None:
        # Vérifier que le contact existe
        contact = await session.get(Contact, request.contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        follow_up.contact_id = request.contact_id

    session.add(follow_up)
    await session.commit()
    await session.refresh(follow_up)

    return _follow_up_to_response(follow_up)


@router.delete("/{follow_up_id}")
async def delete_follow_up(
    follow_up_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Supprime un suivi métier.
    """
    follow_up = await session.get(EmailFollowUp, follow_up_id)
    if not follow_up:
        raise HTTPException(status_code=404, detail="Follow-up not found")

    await session.delete(follow_up)
    await session.commit()

    return {"deleted": True, "id": follow_up_id}
