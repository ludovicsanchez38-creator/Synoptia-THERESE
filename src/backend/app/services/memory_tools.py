"""
THERESE v2 - Memory Tools for LLM Tool Calling

Provides create_contact and create_project tools that the LLM can call
to directly add entities to the memory system during conversation.
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Contact, Project
from app.services.qdrant import get_qdrant_service

logger = logging.getLogger(__name__)


# ============================================================
# Tool Definitions (OpenAI function calling format)
# ============================================================

CREATE_CONTACT_TOOL = {
    "type": "function",
    "function": {
        "name": "create_contact",
        "description": (
            "Cree un nouveau contact dans la memoire de THERESE. "
            "Utilise cet outil quand l'utilisateur mentionne une nouvelle personne "
            "et souhaite l'enregistrer comme contact."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "first_name": {
                    "type": "string",
                    "description": "Prenom du contact",
                },
                "last_name": {
                    "type": "string",
                    "description": "Nom de famille du contact",
                },
                "company": {
                    "type": "string",
                    "description": "Entreprise du contact (optionnel)",
                },
                "email": {
                    "type": "string",
                    "description": "Adresse email du contact (optionnel)",
                },
                "phone": {
                    "type": "string",
                    "description": "Numero de telephone du contact (optionnel)",
                },
                "role": {
                    "type": "string",
                    "description": "Role ou poste du contact (optionnel)",
                },
                "notes": {
                    "type": "string",
                    "description": "Notes supplementaires sur le contact (optionnel)",
                },
            },
            "required": ["first_name", "last_name"],
        },
    },
}

CREATE_PROJECT_TOOL = {
    "type": "function",
    "function": {
        "name": "create_project",
        "description": (
            "Cree un nouveau projet dans la memoire de THERESE. "
            "Utilise cet outil quand l'utilisateur mentionne un nouveau projet "
            "et souhaite l'enregistrer."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Nom du projet",
                },
                "description": {
                    "type": "string",
                    "description": "Description du projet (optionnel)",
                },
                "status": {
                    "type": "string",
                    "enum": ["active", "on_hold", "completed", "cancelled"],
                    "description": "Statut du projet (defaut: active)",
                },
                "budget": {
                    "type": "number",
                    "description": "Budget du projet en euros (optionnel)",
                },
            },
            "required": ["name"],
        },
    },
}

MEMORY_TOOLS = [CREATE_CONTACT_TOOL, CREATE_PROJECT_TOOL]


# ============================================================
# Tool Execution
# ============================================================

async def execute_create_contact(
    arguments: dict[str, Any],
    session: AsyncSession,
) -> str:
    """
    Execute the create_contact tool.

    Creates a contact in SQLite and indexes it in Qdrant.

    Returns:
        JSON string with the result for the LLM.
    """
    first_name = arguments.get("first_name", "").strip()
    last_name = arguments.get("last_name", "").strip()

    if not first_name or not last_name:
        return json.dumps({"error": "Prenom et nom requis"}, ensure_ascii=False)

    try:
        contact = Contact(
            first_name=first_name,
            last_name=last_name,
            display_name=f"{first_name} {last_name}",
            company=arguments.get("company"),
            email=arguments.get("email"),
            phone=arguments.get("phone"),
            role=arguments.get("role"),
            notes=arguments.get("notes"),
            last_interaction=datetime.now(UTC),
        )
        session.add(contact)
        await session.flush()

        # Index in Qdrant
        try:
            qdrant = get_qdrant_service()
            text_parts = [f"Contact: {contact.display_name}"]
            if contact.company:
                text_parts.append(f"Entreprise: {contact.company}")
            if contact.role:
                text_parts.append(f"Role: {contact.role}")
            if contact.email:
                text_parts.append(f"Email: {contact.email}")
            if contact.phone:
                text_parts.append(f"Tel: {contact.phone}")
            if contact.notes:
                text_parts.append(f"Notes: {contact.notes}")

            await qdrant.async_add_memory(
                text="\n".join(text_parts),
                memory_type="contact",
                entity_id=contact.id,
                metadata={
                    "name": contact.display_name,
                    "company": contact.company,
                    "email": contact.email,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to embed new contact in Qdrant: {e}")

        await session.commit()

        logger.info(f"Created contact via tool: {contact.display_name} ({contact.id})")
        return json.dumps({
            "success": True,
            "contact_id": contact.id,
            "display_name": contact.display_name,
            "message": f"Contact '{contact.display_name}' cree avec succes.",
        }, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Failed to create contact via tool: {e}")
        await session.rollback()
        return json.dumps({
            "error": f"Echec de la creation du contact: {str(e)}",
        }, ensure_ascii=False)


async def execute_create_project(
    arguments: dict[str, Any],
    session: AsyncSession,
) -> str:
    """
    Execute the create_project tool.

    Creates a project in SQLite and indexes it in Qdrant.

    Returns:
        JSON string with the result for the LLM.
    """
    name = arguments.get("name", "").strip()

    if not name:
        return json.dumps({"error": "Nom du projet requis"}, ensure_ascii=False)

    try:
        project = Project(
            name=name,
            description=arguments.get("description"),
            status=arguments.get("status", "active"),
            budget=arguments.get("budget"),
        )
        session.add(project)
        await session.flush()

        # Index in Qdrant
        try:
            qdrant = get_qdrant_service()
            text_parts = [f"Projet: {project.name}"]
            if project.description:
                text_parts.append(f"Description: {project.description}")
            if project.status:
                text_parts.append(f"Statut: {project.status}")
            if project.budget:
                text_parts.append(f"Budget: {project.budget} EUR")

            await qdrant.async_add_memory(
                text="\n".join(text_parts),
                memory_type="project",
                entity_id=project.id,
                metadata={
                    "name": project.name,
                    "status": project.status,
                    "budget": project.budget,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to embed new project in Qdrant: {e}")

        await session.commit()

        logger.info(f"Created project via tool: {project.name} ({project.id})")
        return json.dumps({
            "success": True,
            "project_id": project.id,
            "name": project.name,
            "message": f"Projet '{project.name}' cree avec succes.",
        }, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Failed to create project via tool: {e}")
        await session.rollback()
        return json.dumps({
            "error": f"Echec de la creation du projet: {str(e)}",
        }, ensure_ascii=False)


async def execute_memory_tool(
    tool_name: str,
    arguments: dict[str, Any],
    session: AsyncSession,
) -> str:
    """
    Route memory tool execution to the correct handler.

    Returns:
        JSON string result for the LLM.
    """
    if tool_name == "create_contact":
        return await execute_create_contact(arguments, session)
    elif tool_name == "create_project":
        return await execute_create_project(arguments, session)
    else:
        return json.dumps({"error": f"Outil inconnu: {tool_name}"}, ensure_ascii=False)


MEMORY_TOOL_NAMES = {"create_contact", "create_project"}
