"""
THERESE v2 - Actions déterministes du chat (tranche 1a, design 2026-07-10).

Un message composé UNIQUEMENT de `{action: ...}` est exécuté localement, sans
aucun appel LLM. Le registre ci-dessous est une ALLOWLIST stricte : pas
d'action générique `execute`, une action inconnue produit une réponse locale
listant les actions disponibles (jamais transmise au modèle).

Tranche 1a : navigation (`ouvrir <vue>`). Les cibles pointent vers les ids du
registre d'actions frontend (`lib/actionRegistry.ts`), exécutés côté client à
réception de l'événement `client_action`.
"""

import re
import unicodedata
from dataclasses import dataclass

# Message-action PUR uniquement (décision revue : l'inline cumulable est
# reporté - collisions avec [contact:], {{action: skill_id}} et les blocs de
# code montrant la syntaxe). Le lookahead négatif écarte {{action: ...}},
# syntaxe de forçage de skill existante (intent_detector).
_ACTION_MESSAGE = re.compile(r"^\{(?!\{)action:\s*(?P<body>[^{}]*?)\s*\}$", re.IGNORECASE)
_OUVRIR = re.compile(r"^ouvrir\s+(?P<cible>.+)$", re.IGNORECASE)

# cible normalisée (minuscules, sans accents) -> (action_id frontend, libellé)
NAVIGATION_TARGETS: dict[str, tuple[str, str]] = {
    "accueil": ("home.open", "l'Accueil"),
    "email": ("email.open", "l'Email"),
    "crm": ("crm.open", "le CRM"),
    "memoire": ("memory.open", "la Mémoire"),
    "documents": ("documents.open", "les Documents"),
    "taches": ("tasks.open", "les Tâches"),
    "calendrier": ("calendar.open", "le Calendrier"),
    "facturation": ("invoices.open", "la Facturation"),
    "factures": ("invoices.open", "la Facturation"),
    "projets": ("projects.open", "les Projets"),
    "parametres": ("settings.open", "les Paramètres"),
}


@dataclass
class ParsedChatAction:
    """Résultat du parsing d'un message-action."""

    kind: str  # "navigate" | "unknown"
    raw: str
    action_id: str | None = None
    target: str | None = None
    label: str | None = None


def _normalize(text: str) -> str:
    """Minuscules, sans accents, espaces réduits - tolérance de saisie."""
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", text).strip().lower()


def parse_action_message(text: str) -> ParsedChatAction | None:
    """Parse un message-action pur. None = pas un message-action (flux LLM
    habituel, strictement inchangé)."""
    match = _ACTION_MESSAGE.match(text.strip())
    if match is None:
        return None

    body = match.group("body").strip()
    ouvrir = _OUVRIR.match(body)
    if ouvrir:
        cible = _normalize(ouvrir.group("cible"))
        if cible in NAVIGATION_TARGETS:
            action_id, label = NAVIGATION_TARGETS[cible]
            return ParsedChatAction(
                kind="navigate", raw=body, action_id=action_id,
                target=cible, label=label,
            )
    return ParsedChatAction(kind="unknown", raw=body)


def available_actions_text() -> str:
    """Liste lisible des actions disponibles (réponse « action inconnue »)."""
    seen: dict[str, str] = {}
    for cible, (action_id, _label) in NAVIGATION_TARGETS.items():
        seen.setdefault(action_id, cible)
    lignes = [f"- {{action: ouvrir {cible}}}" for cible in sorted(seen.values())]
    return "\n".join(lignes)
