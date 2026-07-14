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
