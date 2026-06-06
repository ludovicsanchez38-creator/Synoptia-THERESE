"""
THERESE v2 - Memory Tools for LLM Tool Calling

Provides create_contact and create_project tools that the LLM can call
to directly add entities to the memory system during conversation.
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any

from app.models.entities import Contact, Project
from app.services.qdrant import get_qdrant_service
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

logger = logging.getLogger(__name__)


# ============================================================
# Tool Definitions (OpenAI function calling format)
# ============================================================

CREATE_CONTACT_TOOL = {
    "type": "function",
    "function": {
        "name": "create_contact",
        "description": (
            "Cree un contact dans la memoire de THERESE (ou le reutilise s'il existe deja). "
            "Utilise cet outil UNE SEULE FOIS par personne mentionnee. "
            "Ne cree jamais de doublon : si le contact existe deja, il est reutilise automatiquement. "
            "Le nom de famille est optionnel."
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
            "required": ["first_name"],
        },
    },
}

CREATE_PROJECT_TOOL = {
    "type": "function",
    "function": {
        "name": "create_project",
        "description": (
            "Cree un projet dans la memoire de THERESE (ou le reutilise s'il existe deja). "
            "Utilise cet outil UNE SEULE FOIS par projet mentionne. "
            "Ne cree jamais de doublon : si un projet du meme nom existe deja, il est reutilise."
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

READ_CONTACT_TOOL = {
    "type": "function",
    "function": {
        "name": "read_contact",
        "description": (
            "Lit la fiche COMPLETE d'un contact existant dans la memoire de THERESE "
            "(coordonnees, notes, stage commercial, score, source, dernieres interactions). "
            "Utilise CET OUTIL plutot que d'inventer quand l'utilisateur demande le contexte, "
            "le suivi, les notes ou l'historique d'une personne ou d'une entreprise. "
            "Recherche par nom, prenom ou entreprise."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Nom, prenom ou entreprise du contact a retrouver",
                },
            },
            "required": ["query"],
        },
    },
}

MEMORY_TOOLS = [CREATE_CONTACT_TOOL, CREATE_PROJECT_TOOL, READ_CONTACT_TOOL]


# ============================================================
# Deduplication helpers (anti creation en masse)
# ============================================================

async def _find_existing_project(session: AsyncSession, name: str) -> Project | None:
    """Retourne un projet existant de meme nom (insensible casse/espaces)."""
    norm = name.strip().lower()
    if not norm:
        return None
    result = await session.execute(
        select(Project).where(func.lower(func.trim(Project.name)) == norm)
    )
    return result.scalars().first()


async def _find_existing_contact(
    session: AsyncSession,
    first_name: str,
    last_name: str,
    email: str | None,
) -> Contact | None:
    """Retourne un contact existant (par email, sinon par prenom+nom)."""
    if email:
        result = await session.execute(
            select(Contact).where(func.lower(Contact.email) == email.lower())
        )
        match = result.scalars().first()
        if match is not None:
            return match

    fn = first_name.strip().lower()
    ln = last_name.strip().lower()
    if not fn and not ln:
        return None
    result = await session.execute(select(Contact))
    for c in result.scalars().all():
        if (c.first_name or "").strip().lower() == fn and (c.last_name or "").strip().lower() == ln:
            return c
    return None


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
    first_name = (arguments.get("first_name") or "").strip()
    last_name = (arguments.get("last_name") or "").strip()
    email = (arguments.get("email") or "").strip() or None

    # Le nom de famille est optionnel : un prenom (ou une entreprise) suffit.
    company = (arguments.get("company") or "").strip() or None
    if not first_name and not last_name and not company:
        return json.dumps({"error": "Au moins un nom ou une entreprise est requis"}, ensure_ascii=False)

    # Deduplication : si un contact equivalent existe deja, on le reutilise
    # plutot que de creer un doublon (regression "creation en masse").
    existing = await _find_existing_contact(session, first_name, last_name, email)
    if existing is not None:
        return json.dumps({
            "success": True,
            "contact_id": existing.id,
            "display_name": existing.display_name,
            "already_existed": True,
            "message": f"Contact '{existing.display_name}' existe déjà, je le réutilise.",
        }, ensure_ascii=False)

    try:
        contact = Contact(
            first_name=first_name or None,
            last_name=last_name or None,
            company=company,
            email=email,
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
            "message": f"Contact '{contact.display_name}' créé avec succès.",
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
    name = (arguments.get("name") or "").strip()

    if not name:
        return json.dumps({"error": "Nom du projet requis"}, ensure_ascii=False)

    # Deduplication : reutilise un projet de meme nom au lieu de creer un doublon
    # (regression "creation en masse" via les commandes / interpretees par le LLM).
    existing = await _find_existing_project(session, name)
    if existing is not None:
        return json.dumps({
            "success": True,
            "project_id": existing.id,
            "name": existing.name,
            "already_existed": True,
            "message": f"Projet '{existing.name}' existe déjà, je le réutilise.",
        }, ensure_ascii=False)

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
            "message": f"Projet '{project.name}' créé avec succès.",
        }, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Failed to create project via tool: {e}")
        await session.rollback()
        return json.dumps({
            "error": f"Echec de la creation du projet: {str(e)}",
        }, ensure_ascii=False)


async def execute_read_contact(
    arguments: dict[str, Any],
    session: AsyncSession,
) -> str:
    """Execute the read_contact tool : retourne la fiche complète + interactions.

    Permet au chat de LIRE le CRM au lieu d'halluciner le contexte client (P0-PROD-3,
    constat C9 : la fiche client ne remontait pas dans le chat).
    """
    from app.models.entities import Activity

    query = (arguments.get("query") or "").strip()
    if not query:
        return json.dumps(
            {"error": "Indique un nom, prénom ou entreprise à rechercher"},
            ensure_ascii=False,
        )

    q = query.lower()
    result = await session.execute(select(Contact))
    matches = [
        c
        for c in result.scalars().all()
        if q in (c.first_name or "").lower()
        or q in (c.last_name or "").lower()
        or q in (c.display_name or "").lower()
        or q in (c.company or "").lower()
    ]

    if not matches:
        return json.dumps(
            {"found": False, "message": f"Aucun contact trouvé pour « {query} »."},
            ensure_ascii=False,
        )

    contacts_out = []
    for c in matches[:5]:
        act_result = await session.execute(
            select(Activity)
            .where(Activity.contact_id == c.id)
            .order_by(Activity.created_at.desc())
            .limit(5)
        )
        activities = act_result.scalars().all()
        contacts_out.append(
            {
                "contact_id": c.id,
                "display_name": c.display_name,
                "company": c.company,
                "email": c.email,
                "phone": c.phone,
                "source": c.source,
                "stage": c.stage,
                "score": c.score,
                "notes": c.notes,
                "last_interaction": c.last_interaction.isoformat()
                if c.last_interaction
                else None,
                "recent_activities": [
                    {
                        "type": a.type,
                        "title": a.title,
                        "description": a.description,
                        "date": a.created_at.isoformat() if a.created_at else None,
                    }
                    for a in activities
                ],
            }
        )

    return json.dumps(
        {"found": True, "count": len(contacts_out), "contacts": contacts_out},
        ensure_ascii=False,
    )


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
    elif tool_name == "read_contact":
        return await execute_read_contact(arguments, session)
    else:
        return json.dumps({"error": f"Outil inconnu: {tool_name}"}, ensure_ascii=False)


MEMORY_TOOL_NAMES = {"create_contact", "create_project", "read_contact"}
