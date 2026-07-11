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
# code montrant la syntaxe). Durcissement 0a (design Variables V4, finding
# Codex 5 VÉRIFIÉ : 5,6 s de CPU sur 3000 espaces) : l'enveloppe est extraite
# en temps linéaire SANS regex (_extract_action_body), et une enveloppe
# reconnue mais malformée répond localement au lieu de retomber dans le LLM.
_MAX_ACTION_LENGTH = 2000
# Corps d'action : caractères hors accolades OU tokens {nom} simples
# (préparation tranche 3 substitution). Alternance non ambiguë ([^{}] exclut
# `{`, l'autre branche commence par `{`) = pas de backtracking.
_BODY_TOKENS = re.compile(r"(?:[^{}]|\{[a-z0-9_]{1,32}\})*\Z")
_OUVRIR = re.compile(r"^ouvrir\s+(?P<cible>.+)$", re.IGNORECASE)
# Tranche 1b : produire <format> "<sujet>" (guillemets droits ou français).
# Le sujet est validé non-blanc APRÈS strip (un `"   "` était accepté).
_PRODUIRE = re.compile(
    r'^produire\s+(?P<fmt>[a-z]+)\s+(?:"(?P<sujet_d>[^"]*)"|«(?P<sujet_f>[^»]*)»)$',
    re.IGNORECASE,
)

# format -> skill de génération (allowlist stricte, ids du registre skills)
PRODUCE_SKILLS: dict[str, str] = {
    "docx": "docx-pro",
    "xlsx": "xlsx-pro",
    "pptx": "pptx-pro",
}

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

    kind: str  # "navigate" | "produce" | "variable" | "help" | "unknown"
    raw: str
    action_id: str | None = None
    target: str | None = None
    label: str | None = None
    skill_id: str | None = None  # kind == "produce"
    subject: str | None = None  # kind == "produce"
    var_op: str | None = None  # kind == "variable" : creer|remplacer|ajouter|supprimer|afficher|lister|erreur
    var_name: str | None = None
    var_value: str | None = None
    var_is_list: bool = False
    var_message: str | None = None  # var_op == "erreur"


# Tranche 2 Variables V4 : verbes du chat (zéro LLM). Valeurs de mutation
# entre guillemets droits ou français, SANS accolades ni retour ligne (tue la
# récursion et les ambiguïtés d'échappement à la source - design V4).
_VARIABLE_CMD = re.compile(
    r"^variable\s+(?P<verbe>[a-zéA-ZÉ]+)\s+(?P<reste>.+)$", re.IGNORECASE
)
_VAR_ARG = re.compile(
    r'^(?P<nom>[a-z0-9_]{1,32})(?:\s+(?:(?P<liste>liste)|"(?P<val_d>[^"]*)"|«\s*(?P<val_f>[^»]*?)\s*»))?$',
    re.IGNORECASE,
)
_VARIABLE_VERBS = {
    "creer": "creer",
    "remplacer": "remplacer",
    "ajouter": "ajouter",
    "supprimer": "supprimer",
    "afficher": "afficher",
}


def _variable_erreur(body: str, message: str) -> "ParsedChatAction":
    return ParsedChatAction(
        kind="variable", raw=body, var_op="erreur", var_message=message
    )


def _parse_variable_body(body: str) -> "ParsedChatAction | None":
    """Verbes variable du chat. None = pas une commande variable."""
    if _normalize(body) == "variables":
        return ParsedChatAction(kind="variable", raw=body, var_op="lister")
    cmd = _VARIABLE_CMD.match(body)
    if cmd is None:
        if _normalize(body).startswith("variable"):
            return _variable_erreur(
                body,
                "Syntaxe : {action: variable "
                'creer|remplacer|ajouter|supprimer|afficher nom ["valeur"|liste]}',
            )
        return None
    verbe = _VARIABLE_VERBS.get(_normalize(cmd.group("verbe")))
    if verbe is None:
        return _variable_erreur(
            body,
            f"Verbe inconnu : « {cmd.group('verbe')} ». Verbes disponibles : "
            "creer, remplacer, ajouter, supprimer, afficher.",
        )
    arg = _VAR_ARG.match(cmd.group("reste").strip())
    if arg is None:
        return _variable_erreur(
            body,
            "Argument invalide : nom en minuscules/chiffres/_ (32 c. max), "
            'valeur entre guillemets sans accolades ni retour ligne.',
        )
    nom = arg.group("nom").lower()
    est_liste = arg.group("liste") is not None
    valeur = arg.group("val_d") if arg.group("val_d") is not None else arg.group("val_f")
    if valeur is not None:
        valeur = valeur.strip()
        if not valeur:
            return _variable_erreur(body, "La valeur ne peut pas être vide.")
        if "{" in valeur or "}" in valeur or "\n" in valeur or "\r" in valeur:
            return _variable_erreur(
                body,
                "Une valeur de variable ne peut pas contenir d'accolades ni de "
                "retour ligne (design V1).",
            )
    if verbe in ("creer",) and not est_liste and valeur is None:
        return _variable_erreur(
            body, 'Syntaxe : {action: variable creer nom "valeur"} ou '
            "{action: variable creer nom liste}",
        )
    if verbe in ("remplacer", "ajouter") and valeur is None:
        return _variable_erreur(
            body, f'Syntaxe : {{action: variable {verbe} nom "valeur"}}'
        )
    if verbe in ("supprimer", "afficher") and (est_liste or valeur is not None):
        return _variable_erreur(
            body, f"Syntaxe : {{action: variable {verbe} nom}}"
        )
    return ParsedChatAction(
        kind="variable", raw=body, var_op=verbe, var_name=nom,
        var_value=valeur, var_is_list=est_liste,
    )


def _normalize(text: str) -> str:
    """Minuscules, sans accents, espaces réduits - tolérance de saisie."""
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", text).strip().lower()


def _extract_action_body(text: str) -> str | None:
    """Extrait le corps d'une enveloppe `{action: ...}` en temps linéaire.

    None = pas une enveloppe action (flux LLM). `{{action:` (forçage de skill
    existant) et les objets JSON collés (clé entre guillemets) restent None.
    """
    if not text.startswith("{") or text.startswith("{{") or not text.endswith("}"):
        return None
    head, sep, body = text[1:-1].partition(":")
    if not sep or head.strip().lower() != "action":
        return None
    return body.strip()


def parse_action_message(text: str) -> ParsedChatAction | None:
    """Parse un message-action pur. None = pas un message-action (flux LLM
    habituel, strictement inchangé). Une enveloppe action reconnue répond
    TOUJOURS localement, même malformée (jamais le LLM)."""
    text = text.strip()
    body = _extract_action_body(text)
    if body is None:
        return None
    if len(text) > _MAX_ACTION_LENGTH:
        return ParsedChatAction(kind="unknown", raw=body[:200])
    if _BODY_TOKENS.fullmatch(body) is None:
        # Accolades parasites (corps non conforme) : réponse locale bornée.
        return ParsedChatAction(kind="unknown", raw=body[:200])

    if _normalize(body) == "aide":
        return ParsedChatAction(kind="help", raw=body)
    ouvrir = _OUVRIR.match(body)
    if ouvrir:
        cible = _normalize(ouvrir.group("cible"))
        if cible in NAVIGATION_TARGETS:
            action_id, label = NAVIGATION_TARGETS[cible]
            return ParsedChatAction(
                kind="navigate", raw=body, action_id=action_id,
                target=cible, label=label,
            )
    variable = _parse_variable_body(body)
    if variable is not None:
        return variable
    produire = _PRODUIRE.match(body)
    if produire:
        fmt = produire.group("fmt").lower()
        sujet = (produire.group("sujet_d") or produire.group("sujet_f") or "").strip()
        if fmt in PRODUCE_SKILLS and sujet:
            return ParsedChatAction(
                kind="produce", raw=body,
                skill_id=PRODUCE_SKILLS[fmt], subject=sujet,
            )
    return ParsedChatAction(kind="unknown", raw=body)


def available_actions_text() -> str:
    """Liste lisible des actions disponibles (réponse « action inconnue »)."""
    seen: dict[str, str] = {}
    for cible, (action_id, _label) in NAVIGATION_TARGETS.items():
        seen.setdefault(action_id, cible)
    lignes = [f"- {{action: ouvrir {cible}}}" for cible in sorted(seen.values())]
    lignes += [
        f'- {{action: produire {fmt} "sujet du document"}}'
        for fmt in sorted(PRODUCE_SKILLS)
    ]
    lignes += [
        '- {action: variable creer nom "valeur"} (ou : creer nom liste)',
        '- {action: variable remplacer|ajouter nom "valeur"}',
        "- {action: variable afficher|supprimer nom}",
        "- {action: variables}",
    ]
    return "\n".join(lignes)
