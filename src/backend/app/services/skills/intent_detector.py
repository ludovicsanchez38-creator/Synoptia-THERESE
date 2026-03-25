"""
THÉRÈSE v2 - Skill Intent Detector

Détecte automatiquement quel skill déclencher à partir du message utilisateur.
Supporte aussi la syntaxe explicite {{action: skill_id}}.

BUG-093 : les skills ne se déclenchaient que via l'UI guidée.
"""

import logging
import re

logger = logging.getLogger(__name__)

# Mapping mots-clés → skill_id
# Chaque entrée : (patterns_regex, skill_id, format_fichier)
SKILL_PATTERNS: list[tuple[list[str], str, str]] = [
    # PPTX - Présentations
    (
        [
            r"\b(?:power\s*point|pptx|présentation|diaporama|slides?)\b",
            r"\b(?:créer?|génér?er?|fai[st]|produi[st]|prépare)\b.*\b(?:présentation|slides?|diapo)\b",
            r"\b(?:présentation|slides?|diapo)\b.*\b(?:créer?|génér?er?|fai[st]|produi[st])\b",
        ],
        "pptx-pro",
        "pptx",
    ),
    # DOCX - Documents Word
    (
        [
            r"\b(?:document\s+word|docx|\.docx)\b",
            r"\b(?:créer?|génér?er?|fai[st]|produi[st]|rédige)\b.*\b(?:document|rapport|guide|procédure|compte.rendu)\b",
            r"\b(?:document|rapport|guide|procédure|compte.rendu)\b.*\b(?:créer?|génér?er?|fai[st]|produi[st]|rédige)\b",
        ],
        "docx-pro",
        "docx",
    ),
    # XLSX - Tableurs Excel
    (
        [
            r"\b(?:excel|xlsx|tableur|spreadsheet|\.xlsx)\b",
            r"\b(?:créer?|génér?er?|fai[st]|produi[st])\b.*\b(?:tableur|feuille\s+de\s+calcul|excel)\b",
        ],
        "xlsx-pro",
        "xlsx",
    ),
    # HTML - Pages web
    (
        [
            r"\b(?:page\s+web|html|site\s+web|landing\s+page)\b.*\b(?:créer?|génér?er?|fai[st])\b",
            r"\b(?:créer?|génér?er?|fai[st])\b.*\b(?:page\s+web|html|site|landing)\b",
        ],
        "html-pro",
        "html",
    ),
    # Email pro
    (
        [
            r"\b(?:rédige|écris|compose)\b.*\b(?:e-?mail|mail|courriel)\b",
            r"\b(?:e-?mail|mail|courriel)\b.*\b(?:professionnel|pro|formel)\b",
        ],
        "email-pro",
        "text",
    ),
    # Post LinkedIn
    (
        [
            r"\b(?:linkedin|post\s+linkedin)\b",
            r"\b(?:rédige|écris|compose|génère)\b.*\blinkedin\b",
        ],
        "linkedin-post",
        "text",
    ),
    # Proposition commerciale
    (
        [
            r"\b(?:proposition\s+commerciale|devis|offre\s+commerciale|propale)\b",
        ],
        "proposal-pro",
        "text",
    ),
]

# Syntaxe explicite {{action: skill_id}}
ACTION_PATTERN = re.compile(
    r"\{\{action\s*:\s*([a-zA-Z0-9_-]+)\s*\}\}",
    re.IGNORECASE,
)


def parse_action_syntax(message: str) -> tuple[str | None, str]:
    """
    Parse la syntaxe {{action: skill_id}} dans le message.

    Returns:
        Tuple (skill_id ou None, message nettoyé sans le tag {{action}})
    """
    match = ACTION_PATTERN.search(message)
    if match:
        skill_id = match.group(1).strip()
        # Retirer le tag du message
        clean_message = ACTION_PATTERN.sub("", message).strip()
        logger.info(f"Action explicite détectée : {{{{action: {skill_id}}}}}")
        return skill_id, clean_message
    return None, message


def detect_skill_intent(message: str) -> tuple[str | None, str | None]:
    """
    Détecte automatiquement le skill à déclencher depuis le message.

    Returns:
        Tuple (skill_id ou None, format_fichier ou None)
    """
    message_lower = message.lower()

    for patterns, skill_id, file_format in SKILL_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, message_lower):
                logger.info(f"Skill auto-détecté : {skill_id} (pattern: {pattern})")
                return skill_id, file_format

    return None, None


def resolve_skill_from_message(
    message: str,
    explicit_skill_id: str | None = None,
) -> tuple[str | None, str | None, str]:
    """
    Résout le skill à utiliser, avec priorité :
    1. skill_id explicite (passé par l'UI)
    2. syntaxe {{action: skill_id}}
    3. détection automatique par mots-clés

    Returns:
        Tuple (skill_id, file_format, message nettoyé)
    """
    # 1. Explicite (depuis l'UI guided prompts)
    if explicit_skill_id:
        return explicit_skill_id, None, message

    # 2. Syntaxe {{action: ...}}
    action_skill_id, clean_message = parse_action_syntax(message)
    if action_skill_id:
        return action_skill_id, None, clean_message

    # 3. Détection automatique
    detected_skill_id, file_format = detect_skill_intent(message)
    if detected_skill_id:
        return detected_skill_id, file_format, message

    return None, None, message
