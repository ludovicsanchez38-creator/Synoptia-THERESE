"""
THERESE v2 - Workspace Tools for LLM Tool Calling

Provides email and calendar tools that the LLM can call
during conversation to interact with user's connected accounts.
"""

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ============================================================
# Tool Definitions (OpenAI function calling format)
# ============================================================

READ_EMAILS_TOOL = {
    "type": "function",
    "function": {
        "name": "read_emails",
        "description": (
            "Lit les derniers emails de la boite mail connectee de l'utilisateur. "
            "Utilise cet outil quand l'utilisateur demande de lire, verifier, "
            "ou resumer ses emails."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "max_results": {
                    "type": "integer",
                    "description": "Nombre maximum d'emails a recuperer (defaut: 10, max: 30)",
                },
                "query": {
                    "type": "string",
                    "description": "Recherche dans les emails (ex: 'from:client@example.com', 'is:unread', 'sujet formation')",
                },
                "unread_only": {
                    "type": "boolean",
                    "description": "Si true, ne retourne que les emails non lus",
                },
            },
            "required": [],
        },
    },
}

SEND_EMAIL_TOOL = {
    "type": "function",
    "function": {
        "name": "send_email",
        "description": (
            "Envoie un email depuis le compte connecte de l'utilisateur. "
            "Utilise cet outil quand l'utilisateur demande d'envoyer un email."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Adresse email du destinataire",
                },
                "subject": {
                    "type": "string",
                    "description": "Sujet de l'email",
                },
                "body": {
                    "type": "string",
                    "description": "Corps de l'email (texte brut ou HTML)",
                },
                "cc": {
                    "type": "string",
                    "description": "Adresses en copie, separees par des virgules (optionnel)",
                },
                "is_html": {
                    "type": "boolean",
                    "description": "Si true, le body est du HTML (defaut: false)",
                },
            },
            "required": ["to", "subject", "body"],
        },
    },
}

SEARCH_EMAILS_TOOL = {
    "type": "function",
    "function": {
        "name": "search_emails",
        "description": (
            "Recherche dans les emails de l'utilisateur avec une requete. "
            "Utilise cet outil quand l'utilisateur cherche un email specifique."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Requete de recherche (ex: 'facture janvier', 'from:comptable', 'devis client')",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Nombre maximum de resultats (defaut: 10)",
                },
            },
            "required": ["query"],
        },
    },
}

LIST_CALENDAR_EVENTS_TOOL = {
    "type": "function",
    "function": {
        "name": "list_calendar_events",
        "description": (
            "Liste les evenements du calendrier de l'utilisateur. "
            "Utilise cet outil quand l'utilisateur demande ses prochains RDV, "
            "son agenda, ou son planning."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Nombre de jours a consulter (defaut: 7, max: 30)",
                },
            },
            "required": [],
        },
    },
}

CREATE_CALENDAR_EVENT_TOOL = {
    "type": "function",
    "function": {
        "name": "create_calendar_event",
        "description": (
            "Cree un evenement dans le calendrier de l'utilisateur. "
            "Utilise cet outil quand l'utilisateur demande de planifier "
            "un RDV, une reunion, ou un evenement."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Titre de l'evenement",
                },
                "start": {
                    "type": "string",
                    "description": "Date et heure de debut au format ISO 8601 (ex: 2026-03-26T14:00:00)",
                },
                "end": {
                    "type": "string",
                    "description": "Date et heure de fin au format ISO 8601 (ex: 2026-03-26T15:00:00)",
                },
                "description": {
                    "type": "string",
                    "description": "Description de l'evenement (optionnel)",
                },
                "location": {
                    "type": "string",
                    "description": "Lieu de l'evenement (optionnel)",
                },
                "attendees": {
                    "type": "string",
                    "description": "Emails des participants separes par des virgules (optionnel)",
                },
            },
            "required": ["summary", "start", "end"],
        },
    },
}


# All workspace tools
WORKSPACE_TOOLS = [
    READ_EMAILS_TOOL,
    SEND_EMAIL_TOOL,
    SEARCH_EMAILS_TOOL,
    LIST_CALENDAR_EVENTS_TOOL,
    CREATE_CALENDAR_EVENT_TOOL,
]

WORKSPACE_TOOL_NAMES = {t["function"]["name"] for t in WORKSPACE_TOOLS}


# ============================================================
# Tool Execution
# ============================================================

async def execute_workspace_tool(
    tool_name: str,
    arguments: dict[str, Any],
    session: AsyncSession,
) -> str:
    """Execute a workspace tool and return the result as string."""
    if tool_name == "read_emails":
        return await _read_emails(arguments, session)
    elif tool_name == "send_email":
        return await _send_email(arguments, session)
    elif tool_name == "search_emails":
        return await _search_emails(arguments, session)
    elif tool_name == "list_calendar_events":
        return await _list_calendar_events(arguments, session)
    elif tool_name == "create_calendar_event":
        return await _create_calendar_event(arguments, session)
    else:
        return f"Outil inconnu : {tool_name}"


async def _get_email_provider(session: AsyncSession):
    """Retrieve the first configured email account and return a provider."""
    from app.models.entities import EmailAccount
    from app.routers.email import ensure_valid_access_token
    from app.services.email.provider_factory import get_email_provider
    from app.services.encryption import decrypt_value

    result = await session.execute(select(EmailAccount).limit(1))
    account = result.scalar_one_or_none()
    if not account:
        return None, "Aucun compte email connecte. Configure ton email dans les parametres."

    if account.provider == "gmail":
        account = await ensure_valid_access_token(account, session)
        access_token = decrypt_value(account.access_token)
        provider = get_email_provider("gmail", access_token=access_token)
    elif account.provider == "imap":
        provider = get_email_provider(
            "imap",
            email_address=account.email,
            password=decrypt_value(account.imap_password) if account.imap_password else "",
            imap_host=account.imap_host or "",
            imap_port=account.imap_port or 993,
            smtp_host=account.smtp_host or "",
            smtp_port=account.smtp_port or 587,
            smtp_use_tls=account.smtp_use_tls if account.smtp_use_tls is not None else True,
        )
    else:
        return None, f"Provider email non supporte : {account.provider}"

    return provider, None


async def _get_calendar_provider(session: AsyncSession):
    """Retrieve Google Calendar provider using the email account token."""
    from app.models.entities import EmailAccount
    from app.routers.email import ensure_valid_access_token
    from app.services.calendar.google_provider import GoogleCalendarProvider
    from app.services.encryption import decrypt_value

    result = await session.execute(
        select(EmailAccount).where(EmailAccount.provider == "gmail").limit(1)
    )
    account = result.scalar_one_or_none()
    if not account:
        return None, "Aucun compte Google connecte. Le calendrier necessite un compte Gmail."

    account = await ensure_valid_access_token(account, session)
    access_token = decrypt_value(account.access_token)
    return GoogleCalendarProvider(access_token=access_token), None


async def _read_emails(args: dict, session: AsyncSession) -> str:
    """Read recent emails."""
    provider, error = await _get_email_provider(session)
    if error:
        return error

    max_results = min(args.get("max_results", 10), 30)
    query = args.get("query")
    unread_only = args.get("unread_only", False)

    try:
        messages, _ = await provider.list_messages(
            max_results=max_results,
            query=query,
            unread_only=unread_only,
        )

        if not messages:
            return "Aucun email trouve."

        lines = [f"**{len(messages)} email(s) trouves :**\n"]
        for msg in messages:
            read_marker = "" if msg.is_read else "🔵 "
            star_marker = "⭐ " if msg.is_starred else ""
            date_str = msg.date.strftime("%d/%m %H:%M") if msg.date else ""
            lines.append(
                f"- {read_marker}{star_marker}**{msg.subject or '(sans sujet)'}** "
                f"— de {msg.from_name or msg.from_email} ({date_str})"
            )
            if msg.snippet:
                lines.append(f"  _{msg.snippet[:120]}..._" if len(msg.snippet or "") > 120 else f"  _{msg.snippet}_")

        return "\n".join(lines)
    except Exception as e:
        logger.exception("Erreur lecture emails")
        return f"Erreur lors de la lecture des emails : {e}"


async def _send_email(args: dict, session: AsyncSession) -> str:
    """Send an email.

    BUG-085 : Validation rapide des parametres et du provider AVANT
    de tenter l'envoi, pour eviter un spinner long suivi d'une erreur.
    """
    import asyncio
    import re

    from app.services.email.base_provider import SendEmailRequest

    to_addr = args.get("to", "").strip()
    subject = args.get("subject", "").strip()
    body = args.get("body", "")
    cc = [addr.strip() for addr in args.get("cc", "").split(",") if addr.strip()] if args.get("cc") else []
    is_html = args.get("is_html", False)

    # Validation rapide des parametres (pas d'appel reseau)
    if not to_addr:
        return "Erreur : le destinataire est obligatoire."
    if not subject:
        return "Erreur : le sujet est obligatoire."

    # Validation basique du format email
    email_pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    if not email_pattern.match(to_addr):
        return f"Erreur : l'adresse '{to_addr}' ne semble pas etre un email valide."

    # Recuperer le provider (verifie la config, le token, etc.)
    provider, error = await _get_email_provider(session)
    if error:
        return error

    try:
        request = SendEmailRequest(
            to=[to_addr],
            subject=subject,
            body=body,
            cc=cc,
            is_html=is_html,
        )
        # BUG-085 : timeout de 30s pour l'envoi (evite les spinners infinis)
        await asyncio.wait_for(provider.send_message(request), timeout=30.0)
        return f"Email envoye avec succes a {to_addr} (sujet: {subject})"
    except asyncio.TimeoutError:
        logger.error("Timeout envoi email a %s", to_addr)
        return (
            f"Erreur : l'envoi de l'email a {to_addr} a expiré après 30 secondes. "
            "Vérifie la configuration de ton compte email (serveur SMTP, identifiants)."
        )
    except Exception as e:
        logger.exception("Erreur envoi email")
        error_msg = str(e)
        # Messages d'erreur plus clairs pour les cas courants
        if "authentication" in error_msg.lower() or "login" in error_msg.lower():
            return (
                f"Erreur d'authentification lors de l'envoi a {to_addr}. "
                "Vérifie tes identifiants email dans les parametres."
            )
        if "connection" in error_msg.lower() or "connect" in error_msg.lower():
            return (
                f"Impossible de se connecter au serveur d'envoi pour {to_addr}. "
                "Vérifie ta connexion internet et la configuration SMTP."
            )
        return f"Erreur lors de l'envoi de l'email : {e}"


async def _search_emails(args: dict, session: AsyncSession) -> str:
    """Search emails."""
    provider, error = await _get_email_provider(session)
    if error:
        return error

    query = args.get("query", "")
    max_results = min(args.get("max_results", 10), 30)

    if not query:
        return "Erreur : une requete de recherche est necessaire."

    try:
        messages, _ = await provider.list_messages(
            max_results=max_results,
            query=query,
        )

        if not messages:
            return f"Aucun email trouve pour la recherche '{query}'."

        lines = [f"**{len(messages)} resultat(s) pour '{query}' :**\n"]
        for msg in messages:
            date_str = msg.date.strftime("%d/%m %H:%M") if msg.date else ""
            lines.append(
                f"- **{msg.subject or '(sans sujet)'}** "
                f"— de {msg.from_name or msg.from_email} ({date_str})"
            )
            if msg.snippet:
                lines.append(f"  _{msg.snippet[:120]}_")

        return "\n".join(lines)
    except Exception as e:
        logger.exception("Erreur recherche emails")
        return f"Erreur lors de la recherche : {e}"


async def _list_calendar_events(args: dict, session: AsyncSession) -> str:
    """List upcoming calendar events."""
    from datetime import datetime, timedelta, timezone

    provider, error = await _get_calendar_provider(session)
    if error:
        return error

    days = min(args.get("days", 7), 30)
    now = datetime.now(timezone.utc)
    time_max = now + timedelta(days=days)

    try:
        events, _ = await provider.list_events(
            calendar_id="primary",
            time_min=now,
            time_max=time_max,
            max_results=50,
        )

        if not events:
            return f"Aucun evenement dans les {days} prochains jours."

        lines = [f"**{len(events)} evenement(s) dans les {days} prochains jours :**\n"]
        for event in events:
            if event.all_day:
                date_str = event.start.strftime("%d/%m") if event.start else ""
                time_str = "(journee)"
            else:
                date_str = event.start.strftime("%d/%m") if event.start else ""
                time_str = event.start.strftime("%H:%M") if event.start else ""
                if event.end:
                    time_str += f"-{event.end.strftime('%H:%M')}"

            location_str = f" 📍 {event.location}" if event.location else ""
            attendees_str = f" ({len(event.attendees)} participants)" if event.attendees else ""

            lines.append(
                f"- **{date_str} {time_str}** — {event.summary}{location_str}{attendees_str}"
            )

        return "\n".join(lines)
    except Exception as e:
        logger.exception("Erreur lecture calendrier")
        return f"Erreur lors de la lecture du calendrier : {e}"


async def _create_calendar_event(args: dict, session: AsyncSession) -> str:
    """Create a calendar event."""
    from datetime import datetime

    from app.services.calendar.base_provider import CreateEventRequest

    provider, error = await _get_calendar_provider(session)
    if error:
        return error

    summary = args.get("summary", "")
    start_str = args.get("start", "")
    end_str = args.get("end", "")

    if not summary or not start_str or not end_str:
        return "Erreur : titre, debut et fin sont obligatoires."

    try:
        start = datetime.fromisoformat(start_str)
        end = datetime.fromisoformat(end_str)
    except ValueError as e:
        return f"Erreur de format de date : {e}. Utilise le format ISO 8601 (ex: 2026-03-26T14:00:00)."

    attendees = [
        addr.strip() for addr in args.get("attendees", "").split(",") if addr.strip()
    ] if args.get("attendees") else None

    try:
        request = CreateEventRequest(
            calendar_id="primary",
            summary=summary,
            start=start,
            end=end,
            description=args.get("description"),
            location=args.get("location"),
            attendees=attendees,
            timezone="Europe/Paris",
        )
        event = await provider.create_event(request)
        return (
            f"Evenement cree : **{event.summary}** "
            f"le {event.start.strftime('%d/%m/%Y %H:%M') if event.start else ''}"
        )
    except Exception as e:
        logger.exception("Erreur creation evenement")
        return f"Erreur lors de la creation de l'evenement : {e}"
