"""US-002 - Confirmation humaine avant les outils sensibles.

Un outil qui n'est pas une lecture classée ne s'exécute pas tout seul :
l'action est mise en attente ici, puis exécutée seulement après validation
explicite via /api/chat/confirm-tool.

Passe 4 (30/08) : le portillon était une liste de deux noms. Tout le reste
partait. La décision suit désormais la classe d'effet (`classe_de`).

Le stockage est volontairement en mémoire (durée de vie d'une confirmation =
quelques secondes/minutes). Une confirmation perdue à un redémarrage est sans
conséquence : l'action n'a tout simplement pas eu lieu (fail-safe).
"""
import uuid
from typing import Any

from app.services.contexte_execution import LECTURE_SEULE, classe_de

# confirmation_id -> (tool_name, arguments)
_pending: dict[str, tuple[str, dict[str, Any], str | None]] = {}


def _base_tool_name(tool_name: str) -> str:
    """Nom d'outil sans le préfixe serveur MCP.

    Les outils exposés via un serveur MCP sont nommés '{server_id}__{tool}'
    (cf. mcp_service.get_tools_for_llm). On isole le nom réel de l'outil pour
    que le gate de confirmation s'applique quelle que soit sa provenance.
    """
    return tool_name.split("__", 1)[1] if "__" in tool_name else tool_name


def requires_confirmation(tool_name: str) -> bool:
    """True si l'outil ne doit jamais s'exécuter sans validation utilisateur.

    Passe 4 (frontière de confiance, 30/08) : le portillon comptait deux
    noms (`send_email`, `create_calendar_event`). Tout le reste s'exécutait :
    `web_search` chez Brave avec le contexte, `browser_navigate` vers
    l'API locale, `create_contact`, et n'importe quel preset MCP (Slack,
    WhatsApp, Stripe, filesystem). `classe_de()` savait déjà qu'un outil
    inconnu est une mutation externe ; on s'en sert enfin.

    Fail-closed : seule la lecture classée passe sans carte. Un nom que
    le registre ne connaît pas (MCP y compris un préfixe collé sur un
    nom de lecture native) est traité comme sortant. On ne dépouille
    PAS le préfixe MCP avant de classer : `filesystem__read_file` n'est
    pas l'outil local `read_file`.
    """
    return bool(classe_de(tool_name) != LECTURE_SEULE)


def register_pending(
    tool_name: str, arguments: dict[str, Any], conversation_id: str | None = None
) -> str:
    """Enregistre une action en attente et renvoie son identifiant.

    `conversation_id` voyage avec l'action : c'est le CHEMIN d'Ines. Elle a
    confirme la creation de « Seance Martin » depuis le dossier Martin ; sans
    cette information, l'evenement se creait sans dossier et reapparaissait
    chez Ruiz. Cloisonner le flux sans cloisonner la confirmation ne couvrirait
    pas le cas qui a produit le constat.
    """
    confirmation_id = uuid.uuid4().hex
    _pending[confirmation_id] = (tool_name, dict(arguments), conversation_id)
    return confirmation_id


def pop_pending(
    confirmation_id: str,
) -> tuple[str, dict[str, Any], str | None] | None:
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


def canoniser_arguments(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Ramène les alias d'un outil sensible sur les noms qu'il lit vraiment.

    Relevé par la relecture adversariale : `_send_email` ne lit que `body`. Un
    modèle qui écrit `content` produisait donc un e-mail au corps VIDE — et la
    déduplication aggravait le cas, puisque la carte conserve les arguments du
    premier appel reçu. Ce qui est montré à l'utilisateur doit être exactement
    ce qui partira.

    Un `body` déjà présent fait autorité : on ne l'écrase jamais.
    """
    if _base_tool_name(tool_name) != "send_email":
        return arguments

    canonises = dict(arguments)
    if not isinstance(canonises.get("body"), str) or not canonises["body"]:
        for alias in _ALIAS_CORPS[1:]:
            valeur = canonises.get(alias)
            if isinstance(valeur, str) and valeur:
                canonises["body"] = valeur
                break
    return canonises
