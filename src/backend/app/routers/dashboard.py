"""
THÉRÈSE v2 - Dashboard Router (US-005)

Endpoint agrégé "Ma journée" pour le tableau de bord à l'ouverture.
Données 100% locales SQLite, pas d'appel LLM.
"""

import logging
import os
from datetime import date, datetime, timedelta

from app.models.database import get_session
from app.models.entities import (
    Calendar,
    CalendarEvent,
    Contact,
    EmailAccount,
    Invoice,
    Preference,
    Task,
)
from app.services.user_profile import get_cached_profile
from fastapi import APIRouter, Depends
from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

router = APIRouter()
logger = logging.getLogger(__name__)

# US-012 : détection « au moins une clé LLM configurée » pour la checklist
# de mise en route. Mêmes providers que le router config (env OU Preference DB).
_LLM_KEY_SOURCES: list[tuple[list[str], str]] = [
    (["ANTHROPIC_API_KEY"], "anthropic_api_key"),
    (["MISTRAL_API_KEY"], "mistral_api_key"),
    (["OPENAI_API_KEY"], "openai_api_key"),
    (["GEMINI_API_KEY", "GOOGLE_API_KEY"], "gemini_api_key"),
    (["GROQ_API_KEY"], "groq_api_key"),
    (["XAI_API_KEY"], "grok_api_key"),
    (["OPENROUTER_API_KEY"], "openrouter_api_key"),
]


async def _has_any_llm_key(session: AsyncSession) -> bool:
    """Au moins une clé LLM cloud disponible (env ou DB) ?

    Sans aucune clé, le chat retombe sur Ollama local s'il est installé -
    la checklist Accueil doit rappeler cette étape au lieu de laisser
    l'utilisateur face à une erreur au premier message.
    """
    for env_names, _ in _LLM_KEY_SOURCES:
        if any(os.environ.get(name) for name in env_names):
            return True
    db_keys = [db_key for _, db_key in _LLM_KEY_SOURCES]
    try:
        result = await session.execute(
            select(Preference.key).where(Preference.key.in_(db_keys)).limit(1)
        )
        return result.scalar() is not None
    except Exception as e:
        logger.warning(f"Erreur lecture clés LLM (setup-status): {e}")
        return False


@router.get("/setup-status")
async def get_setup_status(session: AsyncSession = Depends(get_session)):
    """Retourne l'état de configuration initial pour la vue Accueil.

    Indique si l'utilisateur a déjà connecté un calendrier, un compte mail,
    et si son profil de facturation est complet.
    Permet d'afficher un guide de mise en route contextuel.
    """
    has_calendar = False
    try:
        result = await session.execute(select(Calendar.id).limit(1))
        has_calendar = result.scalar() is not None
    except Exception as e:
        logger.warning(f"Erreur lecture calendrier (setup-status): {e}")

    has_email = False
    try:
        result = await session.execute(select(EmailAccount.id).limit(1))
        has_email = result.scalar() is not None
    except Exception as e:
        logger.warning(f"Erreur lecture compte email (setup-status): {e}")

    billing_complete = False
    try:
        profile = get_cached_profile()
        if profile is not None:
            billing_complete = profile.is_billing_complete()
    except Exception as e:
        logger.warning(f"Erreur lecture profil facturation (setup-status): {e}")

    has_llm_key = await _has_any_llm_key(session)

    return {
        "has_calendar": has_calendar,
        "has_email": has_email,
        "billing_complete": billing_complete,
        "has_llm_key": has_llm_key,
    }


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
                "name": p.display_name,
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
