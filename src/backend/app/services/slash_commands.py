"""
THERESE v2 - Commandes slash deterministes (sans LLM).

Regression #bugs-21052026 : /contact, /projet, /rdv passaient par le LLM
(interpretation non deterministe), qui creait des entites EN MASSE et ne
respectait pas l'intention. On les execute desormais directement en CRUD,
sans appel LLM ni boucle d'outils, avec deduplication cote memory_tools.

Syntaxe :
  /contact Prenom Nom [email=... tel=... societe=... role=...]
  /projet Nom du projet [budget=1000 statut=active desc=...]
  /rdv Titre [date=2026-06-03T14:00]
"""

import json
import logging
import re
from datetime import datetime, timedelta

from app.services.memory_tools import execute_create_contact, execute_create_project
from app.services.workspace_tools import execute_workspace_tool
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

DETERMINISTIC_COMMANDS = {"contact", "projet", "rdv"}

# Alias de cles -> nom canonique d'argument
_KEY_ALIASES = {
    "email": "email", "mail": "email",
    "tel": "phone", "telephone": "phone", "téléphone": "phone", "phone": "phone",
    "societe": "company", "société": "company", "company": "company", "entreprise": "company",
    "role": "role", "rôle": "role", "poste": "role",
    "budget": "budget",
    "statut": "status", "status": "status",
    "desc": "description", "description": "description",
    "date": "date", "quand": "date",
}

# Detecte le premier token "cle=" (debut de la zone cle=valeur)
_KV_HEAD = re.compile(r"[A-Za-zÀ-ÿ]+=", re.UNICODE)
# Capture chaque paire cle=valeur (valeur jusqu'a la prochaine cle= ou la fin)
_KV_PAIR = re.compile(r"([A-Za-zÀ-ÿ]+)=(.*?)(?=\s+[A-Za-zÀ-ÿ]+=|$)", re.UNICODE | re.DOTALL)


def parse_slash_command(message: str) -> tuple[str, str] | None:
    """Detecte une commande deterministe en tete de message.

    Retourne (command, rest) si le message commence par une commande connue,
    sinon None (le message suit alors le flux LLM normal).
    """
    if not message:
        return None
    stripped = message.lstrip()
    if not stripped.startswith("/"):
        return None
    body = stripped[1:]
    name, _, rest = body.partition(" ")
    name = name.strip().lower()
    if name not in DETERMINISTIC_COMMANDS:
        return None
    return name, rest.strip()


def _split_positional_and_kwargs(rest: str) -> tuple[str, dict[str, str]]:
    """Separe le texte positionnel des paires cle=valeur."""
    head = _KV_HEAD.search(rest)
    if not head:
        return rest.strip(), {}
    positional = rest[: head.start()].strip()
    kv_part = rest[head.start():]
    kwargs: dict[str, str] = {}
    for m in _KV_PAIR.finditer(kv_part):
        key = m.group(1).strip().lower()
        val = m.group(2).strip()
        canon = _KEY_ALIASES.get(key)
        if canon and val:
            kwargs[canon] = val
    return positional, kwargs


async def _do_contact(rest: str, session: AsyncSession) -> str:
    positional, kw = _split_positional_and_kwargs(rest)
    tokens = positional.split()
    first_name = tokens[0] if tokens else ""
    last_name = " ".join(tokens[1:]) if len(tokens) > 1 else ""
    if not first_name and not kw.get("company"):
        return "Indique au moins un nom : `/contact Prénom Nom` (ou `/contact Prénom societe=...`)."

    args = {
        "first_name": first_name,
        "last_name": last_name,
        "email": kw.get("email"),
        "phone": kw.get("phone"),
        "company": kw.get("company"),
        "role": kw.get("role"),
    }
    result = json.loads(await execute_create_contact(args, session))
    if result.get("error"):
        return f"Impossible de créer le contact : {result['error']}"
    name = result.get("display_name", "contact")
    if result.get("already_existed"):
        return f"Contact **{name}** déjà en mémoire, je le réutilise (pas de doublon)."
    return f"Contact **{name}** créé en mémoire."


async def _do_projet(rest: str, session: AsyncSession) -> str:
    positional, kw = _split_positional_and_kwargs(rest)
    name = positional.strip()
    if not name:
        return "Indique un nom de projet : `/projet Nom du projet [budget=... statut=...]`."

    budget = None
    if kw.get("budget"):
        try:
            budget = float(kw["budget"].replace(",", ".").replace(" ", ""))
        except ValueError:
            budget = None

    args = {
        "name": name,
        "description": kw.get("description"),
        "status": kw.get("status", "active"),
        "budget": budget,
    }
    result = json.loads(await execute_create_project(args, session))
    if result.get("error"):
        return f"Impossible de créer le projet : {result['error']}"
    pname = result.get("name", "projet")
    if result.get("already_existed"):
        return f"Projet **{pname}** déjà en mémoire, je le réutilise (pas de doublon)."
    return f"Projet **{pname}** créé en mémoire."


async def _do_rdv(rest: str, session: AsyncSession) -> str:
    positional, kw = _split_positional_and_kwargs(rest)
    title = positional.strip()
    if not title:
        return "Indique un titre : `/rdv Titre date=2026-06-03T14:00`."
    date_str = kw.get("date")
    if not date_str:
        return (
            "Pour créer un rendez-vous, précise une date au format ISO : "
            "`/rdv " + title + " date=2026-06-03T14:00`."
        )
    try:
        start = datetime.fromisoformat(date_str)
    except ValueError:
        return f"Date invalide : '{date_str}'. Format attendu ISO 8601, ex : 2026-06-03T14:00."
    end = start + timedelta(hours=1)
    result = await execute_workspace_tool(
        "create_calendar_event",
        {
            "summary": title,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "description": kw.get("description"),
        },
        session,
    )
    return result


async def execute_slash_command(command: str, rest: str, session: AsyncSession) -> str:
    """Execute une commande deterministe et retourne le message de confirmation."""
    if command == "contact":
        return await _do_contact(rest, session)
    if command == "projet":
        return await _do_projet(rest, session)
    if command == "rdv":
        return await _do_rdv(rest, session)
    return f"Commande inconnue : /{command}"
