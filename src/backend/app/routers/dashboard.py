"""
THÉRÈSE v2 - Dashboard Router (US-005)

Endpoint agrégé "Ma journée" pour le tableau de bord à l'ouverture.
Données 100% locales SQLite, pas d'appel LLM.
"""

import logging
from datetime import date, datetime, timedelta

from app.models.database import get_session
from app.models.entities import CalendarEvent, Contact, Invoice, Task
from fastapi import APIRouter, Depends
from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/today")
async def get_today_dashboard(session: AsyncSession = Depends(get_session)):
    """Retourne les données du jour pour le tableau de bord.

    Agrège : RDV du jour, tâches urgentes, factures impayées > 30j,
    prospects à relancer (sans interaction > 15j).
    Conçu pour se charger en <500ms (SQLite local, pas d'appel réseau).
    """
    today = date.today()
    today_dt = datetime.combine(today, datetime.min.time())
    tomorrow_dt = datetime.combine(today + timedelta(days=1), datetime.min.time())
    thirty_days_ago = datetime.now() - timedelta(days=30)
    fifteen_days_ago = datetime.now() - timedelta(days=15)
    today_str = today.isoformat()  # "YYYY-MM-DD" pour all-day events

    # --- RDV du jour (CalendarEvent) ---
    events_today = []
    try:
        # Events avec heure (start_datetime dans la journée)
        stmt_timed = select(CalendarEvent).where(
            and_(
                CalendarEvent.start_datetime >= today_dt,
                CalendarEvent.start_datetime < tomorrow_dt,
                CalendarEvent.status != "cancelled",
            )
        )
        result_timed = await session.execute(stmt_timed)
        timed_events = result_timed.scalars().all()

        # Events all-day (start_date == today)
        stmt_allday = select(CalendarEvent).where(
            and_(
                CalendarEvent.all_day == True,  # noqa: E712
                CalendarEvent.start_date == today_str,
                CalendarEvent.status != "cancelled",
            )
        )
        result_allday = await session.execute(stmt_allday)
        allday_events = result_allday.scalars().all()

        for ev in [*timed_events, *allday_events]:
            events_today.append({
                "id": ev.id,
                "summary": ev.summary,
                "start_datetime": ev.start_datetime.isoformat() if ev.start_datetime else None,
                "start_date": ev.start_date,
                "end_datetime": ev.end_datetime.isoformat() if ev.end_datetime else None,
                "location": ev.location,
                "all_day": ev.all_day,
            })
    except Exception as e:
        logger.warning(f"Erreur lecture événements calendrier: {e}")

    # --- Tâches urgentes (en retard ou dues aujourd'hui) ---
    urgent_tasks = []
    try:
        stmt_tasks = select(Task).where(
            and_(
                Task.due_date <= tomorrow_dt,
                Task.status.notin_(["done", "cancelled"]),
            )
        )
        result_tasks = await session.execute(stmt_tasks)
        tasks = result_tasks.scalars().all()

        for t in tasks:
            urgent_tasks.append({
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "priority": t.priority,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "project_id": t.project_id,
            })
    except Exception as e:
        logger.warning(f"Erreur lecture tâches: {e}")

    # --- Factures impayées > 30 jours ---
    overdue_invoices = []
    try:
        stmt_invoices = select(Invoice).where(
            and_(
                Invoice.status.in_(["sent", "overdue"]),
                Invoice.due_date <= thirty_days_ago,
            )
        )
        result_invoices = await session.execute(stmt_invoices)
        invoices = result_invoices.scalars().all()

        for inv in invoices:
            overdue_invoices.append({
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "contact_id": inv.contact_id,
                "total_ttc": inv.total_ttc,
                "currency": inv.currency,
                "due_date": inv.due_date.isoformat() if inv.due_date else None,
                "status": inv.status,
            })
    except Exception as e:
        logger.warning(f"Erreur lecture factures: {e}")

    # --- Prospects à relancer (sans interaction > 15 jours) ---
    stale_prospects = []
    try:
        stmt_prospects = select(Contact).where(
            and_(
                Contact.stage.in_(["contact", "discovery"]),
                or_(
                    Contact.last_interaction == None,  # noqa: E711
                    Contact.last_interaction < fifteen_days_ago,
                ),
            )
        )
        result_prospects = await session.execute(stmt_prospects)
        prospects = result_prospects.scalars().all()

        for p in prospects:
            stale_prospects.append({
                "id": p.id,
                "name": p.name,
                "company": p.company,
                "stage": p.stage,
                "email": p.email,
                "last_interaction": p.last_interaction.isoformat() if p.last_interaction else None,
            })
    except Exception as e:
        logger.warning(f"Erreur lecture prospects: {e}")

    return {
        "date": today.isoformat(),
        "events": events_today,
        "urgent_tasks": urgent_tasks,
        "overdue_invoices": overdue_invoices,
        "stale_prospects": stale_prospects,
        "summary": {
            "events_count": len(events_today),
            "tasks_count": len(urgent_tasks),
            "invoices_count": len(overdue_invoices),
            "prospects_count": len(stale_prospects),
        },
    }
