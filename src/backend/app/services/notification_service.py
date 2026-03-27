"""
THERESE v2 - Notification Service (US-004)

Gestion des notifications push in-app avec rappels automatiques.
Un solo oublie. Pas de notifications = pas de relances,
factures impayees oubliees, RDV rates.
"""

import logging
from datetime import UTC, datetime, timedelta

from app.models.database import get_session_context
from app.models.entities import (
    CalendarEvent,
    Contact,
    Invoice,
    Notification,
    Task,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

logger = logging.getLogger(__name__)


async def create_notification(
    session: AsyncSession,
    *,
    title: str,
    message: str,
    type: str = "info",
    source: str = "system",
    action_url: str | None = None,
    action_label: str | None = None,
) -> Notification:
    """Cree une nouvelle notification."""
    notif = Notification(
        title=title,
        message=message,
        type=type,
        source=source,
        action_url=action_url,
        action_label=action_label,
    )
    session.add(notif)
    await session.flush()
    logger.info(f"Notification creee: [{type}] {title}")
    return notif


async def get_unread_count(session: AsyncSession) -> int:
    """Retourne le nombre de notifications non lues."""
    result = await session.execute(
        select(func.count(Notification.id)).where(Notification.is_read == False)  # noqa: E712
    )
    return result.scalar_one()


async def get_notifications(
    session: AsyncSession,
    *,
    limit: int = 50,
    unread_only: bool = False,
) -> list[Notification]:
    """Retourne la liste des notifications (les plus recentes en premier)."""
    stmt = select(Notification).order_by(Notification.created_at.desc()).limit(limit)
    if unread_only:
        stmt = stmt.where(Notification.is_read == False)  # noqa: E712
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def mark_as_read(session: AsyncSession, notification_id: str) -> Notification | None:
    """Marque une notification comme lue."""
    result = await session.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notif = result.scalar_one_or_none()
    if notif:
        notif.is_read = True
        notif.read_at = datetime.now(UTC)
        session.add(notif)
        await session.flush()
    return notif


async def mark_all_read(session: AsyncSession) -> int:
    """Marque toutes les notifications comme lues. Retourne le nombre modifie."""
    from sqlalchemy import update

    now = datetime.now(UTC)
    result = await session.execute(
        update(Notification)
        .where(Notification.is_read == False)  # noqa: E712
        .values(is_read=True, read_at=now)
    )
    await session.flush()
    count = result.rowcount
    if count > 0:
        logger.info(f"{count} notifications marquees comme lues")
    return count


# =========================================================================
# Generation automatique de notifications (logique metier)
# =========================================================================


async def _check_overdue_invoices(session: AsyncSession) -> int:
    """Genere des notifications pour les factures impayees > 30 jours."""
    count = 0
    threshold = datetime.now(UTC) - timedelta(days=30)

    result = await session.execute(
        select(Invoice).where(
            Invoice.status.in_(["sent", "overdue"]),
            Invoice.due_date < threshold,
        )
    )
    invoices = result.scalars().all()

    for inv in invoices:
        days_overdue = (datetime.now(UTC) - inv.due_date).days
        # Verifier quon na pas deja une notif recente pour cette facture
        existing = await session.execute(
            select(Notification).where(
                Notification.source == "invoice",
                Notification.action_url == f"/invoices/{inv.id}",
                Notification.created_at > datetime.now(UTC) - timedelta(days=7),
            )
        )
        if existing.scalar_one_or_none():
            continue

        await create_notification(
            session,
            title="Facture impayee",
            message=f"Facture {inv.invoice_number} impayee depuis {days_overdue} jours",
            type="warning",
            source="invoice",
            action_url=f"/invoices/{inv.id}",
            action_label="Relancer",
        )
        count += 1

    return count


async def _check_inactive_prospects(session: AsyncSession) -> int:
    """Genere des notifications pour les prospects sans interaction > 15 jours."""
    count = 0
    threshold = datetime.now(UTC) - timedelta(days=15)

    result = await session.execute(
        select(Contact).where(
            Contact.stage.in_(["contact", "discovery", "proposition"]),
            Contact.last_interaction != None,  # noqa: E711
            Contact.last_interaction < threshold,
        )
    )
    contacts = result.scalars().all()

    for contact in contacts:
        days_inactive = (datetime.now(UTC) - contact.last_interaction).days
        # Verifier quon na pas deja une notif recente pour ce contact
        existing = await session.execute(
            select(Notification).where(
                Notification.source == "crm",
                Notification.action_url == f"/crm/contacts/{contact.id}",
                Notification.created_at > datetime.now(UTC) - timedelta(days=7),
            )
        )
        if existing.scalar_one_or_none():
            continue

        await create_notification(
            session,
            title="Prospect inactif",
            message=f"{contact.display_name} n'a pas repondu depuis {days_inactive} jours",
            type="action",
            source="crm",
            action_url=f"/crm/contacts/{contact.id}",
            action_label="Relancer",
        )
        count += 1

    return count


async def _check_overdue_tasks(session: AsyncSession) -> int:
    """Genere des notifications pour les taches en retard."""
    count = 0
    now = datetime.now(UTC)

    result = await session.execute(
        select(Task).where(
            Task.status.in_(["todo", "in_progress"]),
            Task.due_date != None,  # noqa: E711
            Task.due_date < now,
        )
    )
    tasks = result.scalars().all()

    for task in tasks:
        days_overdue = (now - task.due_date).days
        # Verifier quon na pas deja une notif recente pour cette tache
        existing = await session.execute(
            select(Notification).where(
                Notification.source == "task",
                Notification.action_url == f"/tasks/{task.id}",
                Notification.created_at > now - timedelta(days=3),
            )
        )
        if existing.scalar_one_or_none():
            continue

        await create_notification(
            session,
            title="Tache en retard",
            message=f"Tache '{task.title}' en retard de {days_overdue} jour" + ("s" if days_overdue > 1 else ""),
            type="warning",
            source="task",
            action_url=f"/tasks/{task.id}",
            action_label="Voir",
        )
        count += 1

    return count


async def _check_upcoming_events(session: AsyncSession) -> int:
    """Genere des notifications pour les RDV du lendemain."""
    count = 0
    now = datetime.now(UTC)
    tomorrow_start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_end = tomorrow_start + timedelta(days=1)

    result = await session.execute(
        select(CalendarEvent).where(
            CalendarEvent.start_datetime != None,  # noqa: E711
            CalendarEvent.start_datetime >= tomorrow_start,
            CalendarEvent.start_datetime < tomorrow_end,
            CalendarEvent.status == "confirmed",
        )
    )
    events = result.scalars().all()

    for event in events:
        # Verifier quon na pas deja une notif pour cet evenement
        existing = await session.execute(
            select(Notification).where(
                Notification.source == "calendar",
                Notification.action_url == f"/calendar/events/{event.id}",
                Notification.created_at > now - timedelta(hours=12),
            )
        )
        if existing.scalar_one_or_none():
            continue

        time_str = event.start_datetime.strftime("%Hh%M") if event.start_datetime else ""
        await create_notification(
            session,
            title="RDV demain",
            message=f"RDV demain a {time_str} : {event.summary}",
            type="reminder",
            source="calendar",
            action_url=f"/calendar/events/{event.id}",
            action_label="Voir",
        )
        count += 1

    return count


async def generate_automatic_notifications() -> dict[str, int]:
    """
    Genere toutes les notifications automatiques.
    Appele par le scheduler toutes les heures et au demarrage.
    """
    results: dict[str, int] = {}

    try:
        async with get_session_context() as session:
            results["factures_impayees"] = await _check_overdue_invoices(session)
            results["prospects_inactifs"] = await _check_inactive_prospects(session)
            results["taches_en_retard"] = await _check_overdue_tasks(session)
            results["rdv_demain"] = await _check_upcoming_events(session)

        total = sum(results.values())
        if total > 0:
            logger.info(f"Notifications generees: {results} (total: {total})")
        else:
            logger.debug("Aucune nouvelle notification generee")

    except Exception as e:
        logger.error(f"Erreur generation notifications: {e}")

    return results
