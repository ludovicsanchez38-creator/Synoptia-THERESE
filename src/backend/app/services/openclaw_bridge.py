"""
THÉRÈSE v2 - OpenClaw Bridge

Client HTTP asynchrone vers l API OpenClaw externe (port 18789).
Permet de piloter les agents OpenClaw (Katia, Zézette) depuis THÉRÈSE.
"""

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

OPENCLAW_API_URL = os.environ.get("OPENCLAW_API_URL", "http://localhost:18789")
OPENCLAW_TIMEOUT = 30.0


def _base_url() -> str:
    """URL de base de l API OpenClaw."""
    return OPENCLAW_API_URL.rstrip("/")


def _client() -> httpx.AsyncClient:
    """Crée un client HTTP asynchrone avec timeout."""
    return httpx.AsyncClient(
        base_url=_base_url(),
        timeout=httpx.Timeout(OPENCLAW_TIMEOUT),
        headers={"Content-Type": "application/json"},
    )


async def check_connection() -> bool:
    """Vérifie que l API OpenClaw est accessible.

    Returns:
        True si OpenClaw répond, False sinon.
    """
    try:
        async with _client() as client:
            resp = await client.get("/api/health")
            return resp.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException, OSError) as e:
        logger.debug("OpenClaw inaccessible: %s", e)
        return False


async def list_agents() -> list[dict[str, Any]]:
    """Récupère la liste des agents configurés dans OpenClaw.

    Returns:
        Liste de dicts avec id, name, status pour chaque agent.
    """
    try:
        async with _client() as client:
            resp = await client.get("/api/agents")
            resp.raise_for_status()
            data = resp.json()
            # OpenClaw retourne soit une liste, soit un dict avec clé "agents"
            if isinstance(data, list):
                return data
            return data.get("agents", [])
    except (httpx.HTTPError, OSError) as e:
        logger.error("Erreur list_agents OpenClaw: %s", e)
        return []


async def spawn_session(
    agent_name: str,
    instruction: str,
    mcp_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Crée une session OpenClaw avec un prompt initial.

    Args:
        agent_name: Nom de l agent OpenClaw (ex: "katia", "zezette").
        instruction: Prompt initial / instruction pour l agent.
        mcp_config: Configuration MCP optionnelle (serveurs à connecter).

    Returns:
        Dict avec session_id, status, etc. ou {"error": "..."} en cas d échec.
    """
    body: dict[str, Any] = {
        "agent": agent_name,
        "prompt": instruction,
    }
    if mcp_config:
        body["mcp_servers"] = mcp_config

    try:
        async with _client() as client:
            resp = await client.post("/api/sessions", json=body)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        detail = ""
        try:
            detail = e.response.json().get("detail", e.response.text)
        except Exception:
            detail = e.response.text
        logger.error("Erreur spawn_session OpenClaw (%s): %s", e.response.status_code, detail)
        return {"error": f"OpenClaw {e.response.status_code}: {detail}"}
    except (httpx.HTTPError, OSError) as e:
        logger.error("Erreur spawn_session OpenClaw: %s", e)
        return {"error": str(e)}


async def get_session_status(session_id: str) -> dict[str, Any]:
    """Récupère l état d une session OpenClaw.

    Args:
        session_id: Identifiant de la session.

    Returns:
        Dict avec status (running/done/error), created_at, etc.
    """
    try:
        async with _client() as client:
            resp = await client.get(f"/api/sessions/{session_id}")
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        logger.error("Erreur get_session_status (%s): %s", session_id, e.response.status_code)
        return {"error": f"Session introuvable ou erreur {e.response.status_code}"}
    except (httpx.HTTPError, OSError) as e:
        logger.error("Erreur get_session_status: %s", e)
        return {"error": str(e)}


async def get_session_messages(session_id: str) -> list[dict[str, Any]]:
    """Récupère l historique des messages d une session OpenClaw.

    Args:
        session_id: Identifiant de la session.

    Returns:
        Liste de messages (role, content, timestamp).
    """
    try:
        async with _client() as client:
            resp = await client.get(f"/api/sessions/{session_id}/messages")
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                return data
            return data.get("messages", [])
    except (httpx.HTTPError, OSError) as e:
        logger.error("Erreur get_session_messages: %s", e)
        return []


async def send_message(session_id: str, message: str) -> dict[str, Any]:
    """Envoie un message à un agent dans une session en cours.

    Args:
        session_id: Identifiant de la session.
        message: Contenu du message à envoyer.

    Returns:
        Réponse de l agent ou {"error": "..."}.
    """
    try:
        async with _client() as client:
            resp = await client.post(
                f"/api/sessions/{session_id}/messages",
                json={"content": message},
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        detail = ""
        try:
            detail = e.response.json().get("detail", e.response.text)
        except Exception:
            detail = e.response.text
        logger.error("Erreur send_message: %s", detail)
        return {"error": f"OpenClaw {e.response.status_code}: {detail}"}
    except (httpx.HTTPError, OSError) as e:
        logger.error("Erreur send_message: %s", e)
        return {"error": str(e)}


async def cancel_session(session_id: str) -> bool:
    """Annule une session OpenClaw en cours.

    Args:
        session_id: Identifiant de la session à annuler.

    Returns:
        True si annulée avec succès, False sinon.
    """
    try:
        async with _client() as client:
            resp = await client.delete(f"/api/sessions/{session_id}")
            return resp.status_code in (200, 204)
    except (httpx.HTTPError, OSError) as e:
        logger.error("Erreur cancel_session: %s", e)
        return False
