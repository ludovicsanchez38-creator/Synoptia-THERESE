"""
THÉRÈSE v2 - MCP Bridge Server

Serveur MCP (Model Context Protocol) qui expose les endpoints THÉRÈSE
comme des tools pour les agents OpenClaw.

14 tools exposés :
  CRM      : list_contacts, get_contact, create_activity
  Email    : list_emails, draft_email, send_email
  Factures : list_invoices, create_invoice
  Tâches   : list_tasks, create_task
  Calendrier : list_events, create_event
  Mémoire  : search_memory, get_project

Protocole : MCP stdio (stdin/stdout JSON-RPC).
Chaque tool fait un appel HTTP vers l API locale THÉRÈSE.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any

import httpx

logger = logging.getLogger(__name__)

THERESE_API_URL = os.environ.get("THERESE_API_URL", "http://127.0.0.1:17293")
THERESE_TOKEN = os.environ.get("THERESE_MCP_TOKEN", "")

# ============================================================
# Tools registry
# ============================================================

TOOLS: list[dict[str, Any]] = [
    # --- CRM ---
    {
        "name": "list_contacts",
        "description": "Liste les contacts CRM de THÉRÈSE avec filtrage optionnel.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Nombre max de résultats", "default": 50},
                "search": {"type": "string", "description": "Recherche par nom, email ou entreprise"},
            },
        },
    },
    {
        "name": "get_contact",
        "description": "Récupère les détails d un contact par son ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "contact_id": {"type": "string", "description": "ID du contact"},
            },
            "required": ["contact_id"],
        },
    },
    {
        "name": "create_activity",
        "description": "Crée une activité CRM (appel, email, rdv) liée à un contact.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "contact_id": {"type": "string", "description": "ID du contact"},
                "type": {"type": "string", "description": "Type : call, email, meeting, note"},
                "summary": {"type": "string", "description": "Résumé de l activité"},
            },
            "required": ["contact_id", "type", "summary"],
        },
    },
    # --- Email ---
    {
        "name": "list_emails",
        "description": "Liste les emails récents (boîte de réception).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Nombre max", "default": 20},
                "query": {"type": "string", "description": "Filtre de recherche Gmail"},
            },
        },
    },
    {
        "name": "draft_email",
        "description": "Crée un brouillon d email.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Destinataire"},
                "subject": {"type": "string", "description": "Objet"},
                "body": {"type": "string", "description": "Corps du message (texte ou HTML)"},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "send_email",
        "description": "Envoie un email directement.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Destinataire"},
                "subject": {"type": "string", "description": "Objet"},
                "body": {"type": "string", "description": "Corps du message"},
            },
            "required": ["to", "subject", "body"],
        },
    },
    # --- Factures ---
    {
        "name": "list_invoices",
        "description": "Liste les factures avec filtrage optionnel par statut.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Filtre : draft, sent, paid, overdue"},
                "limit": {"type": "integer", "default": 50},
            },
        },
    },
    {
        "name": "create_invoice",
        "description": "Crée une nouvelle facture pour un contact.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "contact_id": {"type": "string", "description": "ID du contact"},
                "lines": {
                    "type": "array",
                    "description": "Lignes de facture",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "quantity": {"type": "number"},
                            "unit_price": {"type": "number"},
                        },
                        "required": ["description", "quantity", "unit_price"],
                    },
                },
                "due_days": {"type": "integer", "description": "Délai de paiement en jours", "default": 30},
            },
            "required": ["contact_id", "lines"],
        },
    },
    # --- Tâches ---
    {
        "name": "list_tasks",
        "description": "Liste les tâches avec filtrage optionnel.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Filtre : pending, in_progress, done"},
                "limit": {"type": "integer", "default": 50},
            },
        },
    },
    {
        "name": "create_task",
        "description": "Crée une nouvelle tâche.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Titre de la tâche"},
                "description": {"type": "string", "description": "Description détaillée"},
                "due_date": {"type": "string", "description": "Date d échéance (ISO 8601)"},
                "priority": {"type": "string", "description": "Priorité : low, medium, high", "default": "medium"},
            },
            "required": ["title"],
        },
    },
    # --- Calendrier ---
    {
        "name": "list_events",
        "description": "Liste les événements du calendrier.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Nombre de jours à partir d aujourd hui", "default": 7},
                "limit": {"type": "integer", "default": 20},
            },
        },
    },
    {
        "name": "create_event",
        "description": "Crée un événement dans le calendrier.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Titre de l événement"},
                "start": {"type": "string", "description": "Date/heure de début (ISO 8601)"},
                "end": {"type": "string", "description": "Date/heure de fin (ISO 8601)"},
                "description": {"type": "string", "description": "Description"},
                "location": {"type": "string", "description": "Lieu"},
            },
            "required": ["title", "start", "end"],
        },
    },
    # --- Mémoire ---
    {
        "name": "search_memory",
        "description": "Recherche sémantique dans la mémoire THÉRÈSE (contacts, projets, notes).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Texte de recherche"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_project",
        "description": "Récupère les détails d un projet par son ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "ID du projet"},
            },
            "required": ["project_id"],
        },
    },
]

# ============================================================
# Tool → API mapping
# ============================================================

# Mapping tool_name → (method, path_template, body_builder)
# path_template peut contenir {arg_name} pour les paramètres de chemin.

TOOL_ROUTES: dict[str, tuple[str, str]] = {
    "list_contacts": ("GET", "/api/memory/contacts"),
    "get_contact": ("GET", "/api/memory/contacts/{contact_id}"),
    "create_activity": ("POST", "/api/crm/activities"),
    "list_emails": ("GET", "/api/email/messages"),
    "draft_email": ("POST", "/api/email/drafts"),
    "send_email": ("POST", "/api/email/send"),
    "list_invoices": ("GET", "/api/invoices"),
    "create_invoice": ("POST", "/api/invoices"),
    "list_tasks": ("GET", "/api/tasks"),
    "create_task": ("POST", "/api/tasks"),
    "list_events": ("GET", "/api/calendar/events"),
    "create_event": ("POST", "/api/calendar/events"),
    "search_memory": ("GET", "/api/memory/search"),
    "get_project": ("GET", "/api/memory/projects/{project_id}"),
}


async def _call_therese_api(
    method: str,
    path: str,
    params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Appelle l API THÉRÈSE locale."""
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if THERESE_TOKEN:
        headers["X-Therese-Token"] = THERESE_TOKEN

    url = f"{THERESE_API_URL}{path}"

    async with httpx.AsyncClient(timeout=20.0) as client:
        if method == "GET":
            resp = await client.get(url, params=params, headers=headers)
        elif method == "POST":
            resp = await client.post(url, json=body, headers=headers)
        elif method == "PUT":
            resp = await client.put(url, json=body, headers=headers)
        elif method == "DELETE":
            resp = await client.delete(url, headers=headers)
        else:
            return {"error": f"Méthode HTTP non supportée: {method}"}

        try:
            return resp.json()
        except Exception:
            return {"status": resp.status_code, "text": resp.text}


async def execute_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Exécute un tool MCP en appelant l API THÉRÈSE correspondante.

    Args:
        tool_name: Nom du tool (ex: "list_contacts").
        arguments: Arguments passés par l agent.

    Returns:
        Résultat de l appel API.
    """
    route = TOOL_ROUTES.get(tool_name)
    if not route:
        return {"error": f"Tool inconnu: {tool_name}"}

    method, path_template = route

    # Résoudre les paramètres de chemin ({contact_id}, {project_id}, etc.)
    path = path_template
    path_params: list[str] = []
    for key, value in list(arguments.items()):
        placeholder = "{" + key + "}"
        if placeholder in path:
            path = path.replace(placeholder, str(value))
            path_params.append(key)

    # Séparer query params et body
    remaining = {k: v for k, v in arguments.items() if k not in path_params}

    if method == "GET":
        return await _call_therese_api(method, path, params=remaining)
    else:
        return await _call_therese_api(method, path, body=remaining)


# ============================================================
# MCP JSON-RPC handler (stdio)
# ============================================================


async def handle_request(request: dict[str, Any]) -> dict[str, Any]:
    """Traite une requête MCP JSON-RPC.

    Supporte :
      - initialize : handshake MCP
      - tools/list : retourne les 14 tools avec schemas
      - tools/call : exécute un tool

    Args:
        request: Requête JSON-RPC.

    Returns:
        Réponse JSON-RPC.
    """
    method = request.get("method", "")
    req_id = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "therese-mcp-bridge",
                    "version": "1.0.0",
                },
            },
        }

    if method == "notifications/initialized":
        # Notification, pas de réponse requise
        return {}

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": TOOLS},
        }

    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        try:
            result = await execute_tool(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, default=str),
                        }
                    ],
                },
            }
        except Exception as e:
            logger.error("Erreur execute_tool %s: %s", tool_name, e)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({"error": str(e)}, ensure_ascii=False),
                        }
                    ],
                    "isError": True,
                },
            }

    # Méthode inconnue
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": -32601,
            "message": f"Méthode inconnue: {method}",
        },
    }


async def run_stdio_server() -> None:
    """Boucle principale du serveur MCP stdio.

    Lit les requêtes JSON-RPC sur stdin, envoie les réponses sur stdout.
    """
    logger.info("MCP THÉRÈSE Bridge démarré (stdio)")

    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin.buffer)

    buffer = ""
    while True:
        try:
            data = await reader.read(4096)
            if not data:
                break

            buffer += data.decode("utf-8")

            # Traiter chaque ligne JSON complète
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue

                try:
                    request = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning("JSON invalide: %s", line[:200])
                    continue

                response = await handle_request(request)

                # Les notifications n ont pas de réponse
                if response:
                    output = json.dumps(response, ensure_ascii=False) + "\n"
                    sys.stdout.write(output)
                    sys.stdout.flush()

        except Exception as e:
            logger.error("Erreur serveur MCP: %s", e)
            break

    logger.info("MCP THÉRÈSE Bridge arrêté")


# Point d entrée direct : python -m app.services.mcp_therese_server
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_stdio_server())
