"""US-002 - Confirmation humaine avant les outils sensibles.

Certains outils ont un effet de bord sortant et irréversible (envoi d'email).
Le LLM ne doit pas pouvoir les déclencher seul : l'action est mise en attente
ici, puis exécutée seulement après validation explicite de l'utilisateur via
l'endpoint /api/chat/confirm-tool.

Le stockage est volontairement en mémoire (durée de vie d'une confirmation =
quelques secondes/minutes). Une confirmation perdue à un redémarrage est sans
conséquence : l'action n'a tout simplement pas eu lieu (fail-safe).
"""
import uuid
from typing import Any

# Outils à effet de bord sortant/irréversible : exécution soumise à validation.
SENSITIVE_TOOL_NAMES: set[str] = {"send_email", "create_calendar_event"}

# confirmation_id -> (tool_name, arguments)
_pending: dict[str, tuple[str, dict[str, Any]]] = {}


def _base_tool_name(tool_name: str) -> str:
    """Nom d'outil sans le préfixe serveur MCP.

    Les outils exposés via un serveur MCP sont nommés '{server_id}__{tool}'
    (cf. mcp_service.get_tools_for_llm). On isole le nom réel de l'outil pour
    que le gate de confirmation s'applique quelle que soit sa provenance.
    """
    return tool_name.split("__", 1)[1] if "__" in tool_name else tool_name


def requires_confirmation(tool_name: str) -> bool:
    """True si l'outil ne doit jamais s'exécuter sans validation utilisateur.

    BUG-121 : couvre aussi un send_email exposé via MCP ('{server_id}__send_email').
    Sans ça, un tel outil échapperait au gate (nom préfixé) et s'exécuterait
    directement sans confirmation - violation de l'invariant US-002.
    """
    return _base_tool_name(tool_name) in SENSITIVE_TOOL_NAMES


def register_pending(tool_name: str, arguments: dict[str, Any]) -> str:
    """Enregistre une action en attente et renvoie son identifiant."""
    confirmation_id = uuid.uuid4().hex
    _pending[confirmation_id] = (tool_name, dict(arguments))
    return confirmation_id


def pop_pending(confirmation_id: str) -> tuple[str, dict[str, Any]] | None:
    """Retourne et consomme l'action en attente (None si inconnue/déjà consommée)."""
    return _pending.pop(confirmation_id, None)


# ---------------------------------------------------------------------------
# D1 : une même action ne doit produire qu'une carte de confirmation.
#
# Le garde BUG-121 (`sensitive_pending` côté boucle d'outils) ne couvre que la
# récursion. Un modèle qui répète send_email DANS un même tour empilait une
# carte par appel pour un unique envoi. On identifie donc l'action elle-même.
#
# Deux principes non négociables, dans cet ordre :
#   1. FAIL-OPEN — une empreinte incalculable renvoie None, donc la carte est
#      émise. Deux cartes de trop restent sûres ; une carte manquante serait un
#      envoi non confirmé.
#   2. Jamais fusionner deux envois distincts : l'empreinte porte sur tout ce
#      qui fait l'identité du message (destinataires, copie, objet, corps), pas
#      sur le seul nom d'outil.
# ---------------------------------------------------------------------------

# Alias observés pour un même champ : BUG-121 a vu le modèle halluciner
# `content` là où l'outil attend `body`. Ce n'est pas un second e-mail.
_ALIAS_CORPS = ("body", "content", "text", "message")


def _normaliser_adresses(valeur: Any) -> str | None:
    """Adresses en forme canonique, ou None si la valeur n'est pas exploitable."""
    if isinstance(valeur, str):
        brutes = [valeur]
    elif isinstance(valeur, (list, tuple)):
        brutes = [v for v in valeur if isinstance(v, str)]
        if len(brutes) != len(list(valeur)):
            return None
    elif valeur is None:
        return ""
    else:
        return None
    adresses = sorted({a.strip().lower() for a in brutes if a.strip()})
    return ",".join(adresses)


def empreinte_action(tool_name: str, arguments: dict[str, Any]) -> str | None:
    """Identité d'une action sensible, ou None si elle ne peut pas être établie.

    None = fail-open : l'appelant DOIT émettre la carte. On ne devine pas
    l'identité d'un envoi dont on ne comprend pas les arguments.
    """
    if _base_tool_name(tool_name) != "send_email":
        # Les autres outils sensibles n'ont pas d'identité normalisée à ce jour :
        # comportement inchangé, une carte par appel.
        return None

    destinataires = _normaliser_adresses(arguments.get("to"))
    if not destinataires:
        return None  # sans destinataire, aucune identité fiable : fail-open

    copies = _normaliser_adresses(arguments.get("cc"))
    if copies is None:
        return None

    objet = arguments.get("subject")
    if objet is not None and not isinstance(objet, str):
        return None

    corps: str | None = None
    for cle in _ALIAS_CORPS:
        valeur = arguments.get(cle)
        if isinstance(valeur, str):
            corps = valeur
            break
        if valeur is not None:
            return None

    return "|".join(
        (
            "send_email",
            destinataires,
            copies,
            (objet or "").strip(),
            (corps or "").strip(),
        )
    )
