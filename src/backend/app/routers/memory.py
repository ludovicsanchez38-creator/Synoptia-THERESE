"""
THÉRÈSE v2 - Memory Router

Endpoints for memory management (contacts, projects, search).
"""

import json
import logging
import time
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.database import get_session
from app.models.entities import Contact, Project, FileMetadata
from app.models.schemas import (
    ContactCreate,
    ContactResponse,
    ContactUpdate,
    MemorySearchRequest,
    MemorySearchResponse,
    MemorySearchResult,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.qdrant import get_qdrant_service
from app.services.audit import AuditAction, log_activity
from app.services.scoring import update_contact_score

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# Helper Functions for Embeddings
# ============================================================


def _contact_to_embedding_text(contact: Contact) -> str:
    """Build searchable text from a contact for embedding."""
    parts = [
        f"Contact: {contact.display_name}",
    ]
    if contact.company:
        parts.append(f"Entreprise: {contact.company}")
    if contact.email:
        parts.append(f"Email: {contact.email}")
    if contact.phone:
        parts.append(f"Téléphone: {contact.phone}")
    if contact.notes:
        parts.append(f"Notes: {contact.notes}")
    if contact.tags:
        tags = json.loads(contact.tags)
        if tags:
            parts.append(f"Tags: {', '.join(tags)}")
    return "\n".join(parts)


def _project_to_embedding_text(project: Project) -> str:
    """Build searchable text from a project for embedding."""
    parts = [
        f"Projet: {project.name}",
    ]
    if project.description:
        parts.append(f"Description: {project.description}")
    if project.status:
        parts.append(f"Statut: {project.status}")
    if project.budget:
        parts.append(f"Budget: {project.budget}€")
    if project.notes:
        parts.append(f"Notes: {project.notes}")
    if project.tags:
        tags = json.loads(project.tags)
        if tags:
            parts.append(f"Tags: {', '.join(tags)}")
    return "\n".join(parts)


async def _embed_contact(contact: Contact) -> None:
    """Add or update contact embedding in Qdrant."""
    try:
        qdrant = get_qdrant_service()
        # Delete existing embedding first
        await qdrant.async_delete_by_entity(contact.id)
        # Add new embedding
        text = _contact_to_embedding_text(contact)
        await qdrant.async_add_memory(
            text=text,
            memory_type="contact",
            entity_id=contact.id,
            metadata={
                "name": contact.display_name,
                "company": contact.company,
                "email": contact.email,
            },
        )
        logger.debug(f"Embedded contact {contact.id}")
    except Exception as e:
        logger.warning(f"Failed to embed contact {contact.id}: {e}")


async def _embed_project(project: Project) -> None:
    """Add or update project embedding in Qdrant."""
    try:
        qdrant = get_qdrant_service()
        # Delete existing embedding first
        await qdrant.async_delete_by_entity(project.id)
        # Add new embedding
        text = _project_to_embedding_text(project)
        await qdrant.async_add_memory(
            text=text,
            memory_type="project",
            entity_id=project.id,
            metadata={
                "name": project.name,
                "status": project.status,
                "budget": project.budget,
            },
        )
        logger.debug(f"Embedded project {project.id}")
    except Exception as e:
        logger.warning(f"Failed to embed project {project.id}: {e}")


async def _delete_embedding(entity_id: str) -> None:
    """Delete embedding from Qdrant."""
    try:
        qdrant = get_qdrant_service()
        await qdrant.async_delete_by_entity(entity_id)
        logger.debug(f"Deleted embedding for {entity_id}")
    except Exception as e:
        logger.warning(f"Failed to delete embedding {entity_id}: {e}")


# ============================================================
# Search Endpoints
# ============================================================


@router.post("/search", response_model=MemorySearchResponse)
async def search_memory(
    request: MemorySearchRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Search across all memory entities.

    Combines keyword search with semantic search (Qdrant) for hybrid results.
    """
    start_time = time.time()
    results_map: dict[str, MemorySearchResult] = {}

    query_lower = request.query.lower()

    # Map entity_types to Qdrant memory_types
    memory_types = None
    if request.entity_types:
        memory_types = request.entity_types

    # ============================================================
    # Phase 1: Semantic Search (Qdrant)
    # ============================================================
    try:
        qdrant = get_qdrant_service()
        semantic_results = await qdrant.async_search(
            query=request.query,
            memory_types=memory_types,
            limit=request.limit * 2,  # Get more to merge with keyword results
            score_threshold=0.5,  # Lower threshold for semantic
        )

        for hit in semantic_results:
            entity_id = hit.get("entity_id")
            if not entity_id:
                continue

            # Fetch full entity from DB
            entity_type = hit.get("type", "")
            title = ""
            content = ""
            metadata = {}

            if entity_type == "contact":
                result = await session.execute(
                    select(Contact).where(Contact.id == entity_id)
                )
                contact = result.scalar_one_or_none()
                if contact:
                    title = contact.display_name
                    content = contact.notes or ""
                    metadata = {"company": contact.company, "email": contact.email}

            elif entity_type == "project":
                result = await session.execute(
                    select(Project).where(Project.id == entity_id)
                )
                project = result.scalar_one_or_none()
                if project:
                    title = project.name
                    content = project.description or ""
                    metadata = {"status": project.status, "budget": project.budget}

            if title:
                results_map[entity_id] = MemorySearchResult(
                    id=entity_id,
                    entity_type=entity_type,
                    title=title,
                    content=content,
                    score=hit.get("score", 0.0),
                    metadata=metadata,
                )

    except Exception as e:
        logger.warning(f"Semantic search failed, falling back to keyword: {e}")

    # ============================================================
    # Phase 2: Keyword Search (fallback/complement)
    # ============================================================

    # Search contacts
    if not request.entity_types or "contact" in request.entity_types:
        contact_results = await session.execute(select(Contact))
        for contact in contact_results.scalars().all():
            if contact.id in results_map:
                continue  # Already found via semantic

            searchable = " ".join(
                filter(
                    None,
                    [
                        contact.first_name,
                        contact.last_name,
                        contact.company,
                        contact.email,
                        contact.notes,
                    ],
                )
            ).lower()

            if query_lower in searchable:
                score = searchable.count(query_lower) / max(len(searchable.split()), 1)
                results_map[contact.id] = MemorySearchResult(
                    id=contact.id,
                    entity_type="contact",
                    title=contact.display_name,
                    content=contact.notes or "",
                    score=min(score * 0.8, 0.8),  # Cap keyword results below semantic
                    metadata={"company": contact.company, "email": contact.email},
                )

    # Search projects
    if not request.entity_types or "project" in request.entity_types:
        project_results = await session.execute(select(Project))
        for project in project_results.scalars().all():
            if project.id in results_map:
                continue  # Already found via semantic

            searchable = " ".join(
                filter(None, [project.name, project.description, project.notes])
            ).lower()

            if query_lower in searchable:
                score = searchable.count(query_lower) / max(len(searchable.split()), 1)
                results_map[project.id] = MemorySearchResult(
                    id=project.id,
                    entity_type="project",
                    title=project.name,
                    content=project.description or "",
                    score=min(score * 0.8, 0.8),  # Cap keyword results below semantic
                    metadata={"status": project.status, "budget": project.budget},
                )

    # Sort by score and limit
    results = sorted(results_map.values(), key=lambda x: x.score, reverse=True)
    results = results[: request.limit]

    search_time_ms = (time.time() - start_time) * 1000

    return MemorySearchResponse(
        query=request.query,
        results=results,
        total=len(results),
        search_time_ms=search_time_ms,
    )


# ============================================================
# Contact Endpoints
# ============================================================


def _contact_to_response(contact: Contact) -> ContactResponse:
    """Convertit Contact entity en ContactResponse schema avec CRM fields."""
    return ContactResponse(
        id=contact.id,
        first_name=contact.first_name,
        last_name=contact.last_name,
        company=contact.company,
        email=contact.email,
        phone=contact.phone,
        notes=contact.notes,
        tags=json.loads(contact.tags) if contact.tags else None,
        # CRM fields (Phase 5)
        stage=contact.stage,
        score=contact.score,
        source=contact.source,
        last_interaction=contact.last_interaction,
        created_at=contact.created_at,
        updated_at=contact.updated_at,
    )


@router.get("/contacts", response_model=list[ContactResponse])
async def list_contacts(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    scope: Literal["global", "project", "conversation"] | None = Query(default=None),
    scope_id: str | None = Query(default=None),
    include_global: bool = Query(default=True),
    session: AsyncSession = Depends(get_session),
):
    """List all contacts with optional scope filter (E3-05)."""
    query = select(Contact).order_by(Contact.updated_at.desc())

    # Apply scope filter (E3-05)
    if scope:
        if include_global:
            query = query.where(
                ((Contact.scope == scope) & (Contact.scope_id == scope_id))
                | (Contact.scope == "global")
            )
        else:
            query = query.where(
                (Contact.scope == scope) & (Contact.scope_id == scope_id)
            )

    result = await session.execute(query.offset(offset).limit(limit))
    contacts = result.scalars().all()

    return [_contact_to_response(c) for c in contacts]


@router.post("/contacts", response_model=ContactResponse)
async def create_contact(
    request: ContactCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new contact."""
    contact = Contact(
        first_name=request.first_name,
        last_name=request.last_name,
        company=request.company,
        email=request.email,
        phone=request.phone,
        notes=request.notes,
        tags=json.dumps(request.tags) if request.tags else None,
        # CRM fields (Phase 5)
        stage=request.stage,
        source=request.source,
    )
    session.add(contact)
    await session.commit()
    await session.refresh(contact)

    # Auto-embed to Qdrant for semantic search
    await _embed_contact(contact)

    # Calculate initial score (Phase 5 CRM)
    from datetime import datetime
    contact.last_interaction = datetime.utcnow()
    update_contact_score(session, contact, reason="initial_creation")
    await session.commit()
    await session.refresh(contact)

    # Audit log (US-SEC-05)
    await log_activity(
        session,
        AuditAction.CONTACT_CREATED,
        resource_type="contact",
        resource_id=contact.id,
        details=json.dumps({"name": contact.display_name, "stage": contact.stage, "score": contact.score}),
    )

    logger.info(f"Contact created: {contact.id} with stage={contact.stage}, score={contact.score}")

    return _contact_to_response(contact)


@router.get("/contacts/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get a specific contact."""
    result = await session.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    return _contact_to_response(contact)


@router.patch("/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: str,
    request: ContactUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update a contact."""
    result = await session.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    # Update fields
    update_data = request.model_dump(exclude_unset=True)
    if "tags" in update_data:
        update_data["tags"] = json.dumps(update_data["tags"]) if update_data["tags"] else None

    for key, value in update_data.items():
        setattr(contact, key, value)

    from datetime import datetime

    contact.updated_at = datetime.utcnow()
    contact.last_interaction = datetime.utcnow()

    await session.commit()
    await session.refresh(contact)

    # Re-embed to Qdrant with updated data
    await _embed_contact(contact)

    # Recalculate score if relevant fields changed (Phase 5 CRM)
    scoring_fields = {"email", "phone", "company", "stage", "source"}
    if scoring_fields.intersection(update_data.keys()):
        update_contact_score(session, contact, reason=f"update_{','.join(update_data.keys())}")
        await session.commit()
        await session.refresh(contact)
        logger.info(f"Contact {contact_id} score recalculated after update: {contact.score}")

    # Audit log (US-SEC-05)
    await log_activity(
        session,
        AuditAction.CONTACT_UPDATED,
        resource_type="contact",
        resource_id=contact.id,
        details=json.dumps({"fields_updated": list(update_data.keys()), "new_score": contact.score}),
    )

    return _contact_to_response(contact)


@router.delete("/contacts/{contact_id}")
async def delete_contact(
    contact_id: str,
    cascade: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a contact (E3-06 Oubli Selectif).

    Args:
        contact_id: ID of the contact to delete
        cascade: If True, also delete related projects and files
    """
    result = await session.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    cascade_deleted: dict[str, int] = {}

    if cascade:
        # Delete related projects (E3-06)
        projects_result = await session.execute(
            select(Project).where(Project.contact_id == contact_id)
        )
        projects = projects_result.scalars().all()
        for project in projects:
            await _delete_embedding(project.id)
            await session.delete(project)
        cascade_deleted["projects"] = len(projects)

        # Delete scoped files
        files_result = await session.execute(
            select(FileMetadata).where(
                (FileMetadata.scope == "contact") & (FileMetadata.scope_id == contact_id)
            )
        )
        files = files_result.scalars().all()
        for file in files:
            await _delete_embedding(file.id)
            await session.delete(file)
        cascade_deleted["files"] = len(files)

    contact_name = contact.display_name
    await session.delete(contact)
    await session.commit()

    # Remove from Qdrant
    await _delete_embedding(contact_id)

    # Audit log (US-SEC-05)
    await log_activity(
        session,
        AuditAction.CONTACT_DELETED,
        resource_type="contact",
        resource_id=contact_id,
        details=json.dumps({"name": contact_name, "cascade": cascade, "cascade_deleted": cascade_deleted}),
    )

    return {"deleted": True, "id": contact_id, "cascade_deleted": cascade_deleted}


# ============================================================
# Project Endpoints
# ============================================================


@router.get("/projects", response_model=list[ProjectResponse])
async def list_projects(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    status: str | None = None,
    scope: Literal["global", "project", "conversation"] | None = Query(default=None),
    scope_id: str | None = Query(default=None),
    include_global: bool = Query(default=True),
    session: AsyncSession = Depends(get_session),
):
    """List all projects with optional scope filter (E3-05)."""
    query = select(Project).order_by(Project.updated_at.desc())

    if status:
        query = query.where(Project.status == status)

    # Apply scope filter (E3-05)
    if scope:
        if include_global:
            query = query.where(
                ((Project.scope == scope) & (Project.scope_id == scope_id))
                | (Project.scope == "global")
            )
        else:
            query = query.where(
                (Project.scope == scope) & (Project.scope_id == scope_id)
            )

    result = await session.execute(query.offset(offset).limit(limit))
    projects = result.scalars().all()

    return [
        ProjectResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            contact_id=p.contact_id,
            status=p.status,
            budget=p.budget,
            notes=p.notes,
            tags=json.loads(p.tags) if p.tags else None,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in projects
    ]


@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    request: ProjectCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new project."""
    # Validate contact if provided
    if request.contact_id:
        result = await session.execute(
            select(Contact).where(Contact.id == request.contact_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Contact not found")

    project = Project(
        name=request.name,
        description=request.description,
        contact_id=request.contact_id,
        status=request.status,
        budget=request.budget,
        notes=request.notes,
        tags=json.dumps(request.tags) if request.tags else None,
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)

    # Auto-embed to Qdrant for semantic search
    await _embed_project(project)

    # Audit log (US-SEC-05)
    await log_activity(
        session,
        AuditAction.PROJECT_CREATED,
        resource_type="project",
        resource_id=project.id,
        details=json.dumps({"name": project.name}),
    )

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        contact_id=project.contact_id,
        status=project.status,
        budget=project.budget,
        notes=project.notes,
        tags=json.loads(project.tags) if project.tags else None,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get a specific project."""
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        contact_id=project.contact_id,
        status=project.status,
        budget=project.budget,
        notes=project.notes,
        tags=json.loads(project.tags) if project.tags else None,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    request: ProjectUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update a project."""
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate contact if provided
    if request.contact_id:
        result = await session.execute(
            select(Contact).where(Contact.id == request.contact_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Contact not found")

    # Update fields
    update_data = request.model_dump(exclude_unset=True)
    if "tags" in update_data:
        update_data["tags"] = json.dumps(update_data["tags"]) if update_data["tags"] else None

    for key, value in update_data.items():
        setattr(project, key, value)

    from datetime import datetime

    project.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(project)

    # Re-embed to Qdrant with updated data
    await _embed_project(project)

    # Audit log (US-SEC-05)
    await log_activity(
        session,
        AuditAction.PROJECT_UPDATED,
        resource_type="project",
        resource_id=project.id,
        details=json.dumps({"fields_updated": list(update_data.keys())}),
    )

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        contact_id=project.contact_id,
        status=project.status,
        budget=project.budget,
        notes=project.notes,
        tags=json.loads(project.tags) if project.tags else None,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    cascade: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a project (E3-06 Oubli Selectif).

    Args:
        project_id: ID of the project to delete
        cascade: If True, also delete scoped files
    """
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    cascade_deleted: dict[str, int] = {}

    if cascade:
        # Delete scoped files (E3-06)
        files_result = await session.execute(
            select(FileMetadata).where(
                (FileMetadata.scope == "project") & (FileMetadata.scope_id == project_id)
            )
        )
        files = files_result.scalars().all()
        for file in files:
            await _delete_embedding(file.id)
            await session.delete(file)
        cascade_deleted["files"] = len(files)

    project_name = project.name
    await session.delete(project)
    await session.commit()

    # Remove from Qdrant
    await _delete_embedding(project_id)

    # Audit log (US-SEC-05)
    await log_activity(
        session,
        AuditAction.PROJECT_DELETED,
        resource_type="project",
        resource_id=project_id,
        details=json.dumps({"name": project_name, "cascade": cascade, "cascade_deleted": cascade_deleted}),
    )

    return {"deleted": True, "id": project_id, "cascade_deleted": cascade_deleted}
