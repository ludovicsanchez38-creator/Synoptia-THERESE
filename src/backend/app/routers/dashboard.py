"""
THÉRÈSE v2 - Dashboard Router (US-005)

Endpoint agrégé "Ma journée" pour le tableau de bord à l'ouverture.
Données 100% locales SQLite, pas d'appel LLM.
"""

import json
import logging
import os
from datetime import date, datetime, timedelta

from app.models.database import get_session
from app.models.entities import (
    Calendar,
    CalendarEvent,
    Contact,
    EmailAccount,
    EmailFollowUp,
    EmailMessage,
    Invoice,
    Preference,
    Task,
)
from app.services.user_profile import get_cached_profile
from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

router = APIRouter()
logger = logging.getLogger(__name__)


def _attendee_emails(raw_attendees: str | None) -> list[str]:
    """Extrait les emails participants sans supposer le format du provider."""
    if not raw_attendees:
        return []
    try:
        values = json.loads(raw_attendees)
    except (TypeError, json.JSONDecodeError):
        return []
    if not isinstance(values, list):
        return []
    emails: list[str] = []
    for value in values:
        email = value.get("email") if isinstance(value, dict) else value
        if isinstance(email, str) and email.strip():
            emails.append(email.strip().lower())
    return emails

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
    """Au moins un LLM utilisable (clé cloud valide OU Ollama choisi/joignable) ?

    Revue adversariale US-012 - trois angles morts corrigés :
    - clé DB : vérifier le DÉCHIFFREMENT (une clé Fernet corrompue après
      réinitialisation du Keychain comptait comme configurée alors que le
      premier message échoue - exactement le cas que la checklist doit attraper) ;
    - env : pydantic-settings lit le .env sans peupler os.environ -> inclure
      settings.anthropic_api_key / settings.mistral_api_key ;
    - Ollama : le persona 100 % local n'a AUCUNE clé cloud ; sans cette
      détection, la carte « Configurer une clé IA (ou Ollama) » ne se masquait
      jamais pour lui.
    """
    from app.config import settings
    from app.routers.config import _check_key_decryptable

    for env_names, _ in _LLM_KEY_SOURCES:
        if any(os.environ.get(name) for name in env_names):
            return True
    # Fallback .env (pydantic-settings) pour les clés déclarées dans Settings
    if settings.anthropic_api_key or settings.mistral_api_key:
        return True

    try:
        for _, db_key in _LLM_KEY_SOURCES:
            has_key, _corrupted = await _check_key_decryptable(session, db_key)
            if has_key:
                return True
    except Exception as e:
        logger.warning(f"Erreur lecture clés LLM (setup-status): {e}")

    # Ollama : choisi comme provider (Preference) ou serveur local joignable
    try:
        result = await session.execute(
            select(Preference.value).where(Preference.key == "llm_provider").limit(1)
        )
        if result.scalar() == "ollama":
            return True
    except Exception as e:
        logger.debug(f"Erreur lecture provider (setup-status): {e}")
    try:
        from app.services.http_client import get_http_client

        client = await get_http_client()
        response = await client.get(f"{settings.ollama_base_url}/api/tags", timeout=1.0)
        if response.status_code == 200:
            return True
    except Exception:
        pass  # Ollama absent : attendu pour la plupart des installs cloud

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
        if profile is None:
            # Cache vide après un démarrage avec profil chiffré : lecture de
            # secours en session (déchiffre et répare le cache au passage).
            from app.services.user_profile import get_user_profile

            profile = await get_user_profile(session)
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

    Agrège : RDV du jour, tâches urgentes, relances email proches,
    factures impayées > 30j et prospects sans interaction > 15j.
    Conçu pour se charger en <500ms (SQLite local, pas d'appel réseau).
    """
    today = date.today()
    today_dt = datetime.combine(today, datetime.min.time())
    tomorrow_dt = datetime.combine(today + timedelta(days=1), datetime.min.time())
    thirty_days_ago = datetime.now() - timedelta(days=30)
    fifteen_days_ago = datetime.now() - timedelta(days=15)
    today_str = today.isoformat()  # "YYYY-MM-DD" pour all-day events
    follow_up_horizon = (today + timedelta(days=2)).isoformat() + "T23:59:59"

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

        attendee_emails_by_event = {
            ev.id: _attendee_emails(ev.attendees) for ev in [*timed_events, *allday_events]
        }
        attendee_emails = {
            email for emails in attendee_emails_by_event.values() for email in emails
        }
        contacts_by_email: dict[str, Contact] = {}
        if attendee_emails:
            contacts = (
                await session.execute(
                    select(Contact).where(func.lower(Contact.email).in_(attendee_emails))
                )
            ).scalars().all()
            contacts_by_email = {
                contact.email.strip().lower(): contact
                for contact in contacts
                if contact.email and contact.email.strip()
            }

        for ev in [*timed_events, *allday_events]:
            event_attendees = attendee_emails_by_event[ev.id]
            events_today.append({
                "id": ev.id,
                "summary": ev.summary,
                "start_datetime": ev.start_datetime.isoformat() if ev.start_datetime else None,
                "start_date": ev.start_date,
                "end_datetime": ev.end_datetime.isoformat() if ev.end_datetime else None,
                "location": ev.location,
                "all_day": ev.all_day,
                "attendees_count": len(event_attendees),
                "crm_contact_ids": [
                    contacts_by_email[email].id
                    for email in event_attendees
                    if email in contacts_by_email
                ],
            })
    except Exception as e:
        logger.warning(f"Erreur lecture événements calendrier: {e}")

    # --- Tâches urgentes (en retard ou dues aujourd'hui) ---
    urgent_tasks = []
    try:
        # BUG-125 : trier par échéance croissante (la plus en retard d'abord).
        # Sans ORDER BY, l'ordre était arbitraire (insertion) : avec plusieurs
        # tâches urgentes, une tâche en retard pouvait passer après les tâches
        # dues aujourd'hui et sortir du top-3 affiché par le tableau de bord -
        # elle semblait alors « invisible ».
        stmt_tasks = (
            select(Task)
            .where(
                and_(
                    # Borne STRICTE : une tâche due demain à 00:00 pile n'est
                    # pas urgente aujourd'hui (off-by-one relevé en revue).
                    Task.due_date < tomorrow_dt,
                    Task.status.notin_(["done", "cancelled"]),
                )
            )
            .order_by(Task.due_date.asc(), Task.id.asc())
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

    # --- Relances email échues ou proches (J+2 maximum) ---
    due_follow_ups = []
    try:
        follow_ups = (
            await session.execute(
                select(EmailFollowUp)
                .where(EmailFollowUp.status == "pending")
                .where(EmailFollowUp.due_date <= follow_up_horizon)
                .order_by(EmailFollowUp.due_date.asc(), EmailFollowUp.id.asc())
            )
        ).scalars().all()
        message_ids = {follow_up.email_message_id for follow_up in follow_ups}
        contact_ids = {follow_up.contact_id for follow_up in follow_ups if follow_up.contact_id}
        messages = (
            await session.execute(select(EmailMessage).where(EmailMessage.id.in_(message_ids)))
        ).scalars().all() if message_ids else []
        contacts = (
            await session.execute(select(Contact).where(Contact.id.in_(contact_ids)))
        ).scalars().all() if contact_ids else []
        messages_by_id = {message.id: message for message in messages}
        contacts_by_id = {contact.id: contact for contact in contacts}

        for follow_up in follow_ups:
            message = messages_by_id.get(follow_up.email_message_id)
            contact = contacts_by_id.get(follow_up.contact_id) if follow_up.contact_id else None
            due_follow_ups.append({
                "id": follow_up.id,
                "due_date": follow_up.due_date,
                "note": follow_up.note,
                "email_subject": message.subject if message else None,
                "email_from": (message.from_name or message.from_email) if message else None,
                "contact_id": follow_up.contact_id,
                "contact_name": contact.display_name if contact else None,
            })
    except Exception as e:
        logger.warning(f"Erreur lecture relances email: {e}")

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
        "due_follow_ups": due_follow_ups,
        "overdue_invoices": overdue_invoices,
        "stale_prospects": stale_prospects,
        "summary": {
            "events_count": len(events_today),
            "tasks_count": len(urgent_tasks),
            "follow_ups_count": len(due_follow_ups),
            "invoices_count": len(overdue_invoices),
            "prospects_count": len(stale_prospects),
        },
    }
