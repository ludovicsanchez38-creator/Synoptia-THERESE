"""
THERESE v2 - Data Router (RGPD)

Endpoints for data export, deletion and privacy compliance.

US-SEC-02: Export toutes les donnees utilisateur
US-SEC-05: Logs d'activite
"""

import json
import logging
import re
from datetime import UTC, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.config import settings
from app.models.database import get_session
from app.models.entities import (
    Contact,
    Project,
    Conversation,
    Message,
    FileMetadata,
    Preference,
    BoardDecisionDB,
)
from app.services.audit import (
    AuditService,
    AuditAction,
    ActivityLog,
    log_activity,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# RGPD Export (US-SEC-02)
# ============================================================


@router.get("/export")
async def export_all_data(
    session: AsyncSession = Depends(get_session),
):
    """
    Export toutes les donnees utilisateur (RGPD Art. 20 - Portabilite).

    Retourne un JSON complet avec :
    - Contacts et projets
    - Conversations et messages
    - Fichiers indexes
    - Preferences (sans les cles API)
    - Decisions du Board
    - Logs d'activite

    Les cles API ne sont PAS exportees pour des raisons de securite.
    """
    # Log l'action d'export
    await log_activity(
        session,
        AuditAction.DATA_EXPORTED,
        resource_type="rgpd",
        details=json.dumps({"type": "full_export"}),
    )

    # Contacts
    contacts_result = await session.execute(select(Contact))
    contacts = contacts_result.scalars().all()

    # Projects
    projects_result = await session.execute(select(Project))
    projects = projects_result.scalars().all()

    # Conversations
    conversations_result = await session.execute(select(Conversation))
    conversations = conversations_result.scalars().all()

    # Messages
    messages_result = await session.execute(select(Message))
    messages = messages_result.scalars().all()

    # Files
    files_result = await session.execute(select(FileMetadata))
    files = files_result.scalars().all()

    # Preferences (excluding API keys)
    prefs_result = await session.execute(select(Preference))
    preferences = prefs_result.scalars().all()

    # Board decisions
    decisions_result = await session.execute(select(BoardDecisionDB))
    decisions = decisions_result.scalars().all()

    # Activity logs
    logs_result = await session.execute(
        select(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(1000)
    )
    logs = logs_result.scalars().all()

    export_data = {
        "exported_at": datetime.now(UTC).isoformat(),
        "app_version": settings.app_version,
        "data_format_version": "1.0",
        "contacts": [
            {
                "id": c.id,
                "first_name": c.first_name,
                "last_name": c.last_name,
                "company": c.company,
                "email": c.email,
                "phone": c.phone,
                "notes": c.notes,
                "tags": json.loads(c.tags) if c.tags else None,
                "scope": c.scope,
                "scope_id": c.scope_id,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
            }
            for c in contacts
        ],
        "projects": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "contact_id": p.contact_id,
                "status": p.status,
                "budget": p.budget,
                "notes": p.notes,
                "tags": json.loads(p.tags) if p.tags else None,
                "scope": p.scope,
                "scope_id": p.scope_id,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat(),
            }
            for p in projects
        ],
        "conversations": [
            {
                "id": conv.id,
                "title": conv.title,
                "summary": conv.summary,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "messages": [
                    {
                        "id": m.id,
                        "role": m.role,
                        "content": m.content,
                        "model": m.model,
                        "tokens_in": m.tokens_in,
                        "tokens_out": m.tokens_out,
                        "created_at": m.created_at.isoformat(),
                    }
                    for m in messages
                    if m.conversation_id == conv.id
                ],
            }
            for conv in conversations
        ],
        "files": [
            {
                "id": f.id,
                "path": f.path,
                "name": f.name,
                "extension": f.extension,
                "size": f.size,
                "mime_type": f.mime_type,
                "chunk_count": f.chunk_count,
                "scope": f.scope,
                "scope_id": f.scope_id,
                "indexed_at": f.indexed_at.isoformat() if f.indexed_at else None,
                "created_at": f.created_at.isoformat(),
            }
            for f in files
        ],
        "preferences": [
            {
                "key": p.key,
                "value": p.value if "api_key" not in p.key.lower() else "[REDACTED]",
                "category": p.category,
                "updated_at": p.updated_at.isoformat(),
            }
            for p in preferences
        ],
        "board_decisions": [
            {
                "id": d.id,
                "question": d.question,
                "context": d.context,
                "opinions": json.loads(d.opinions),
                "synthesis": json.loads(d.synthesis),
                "confidence": d.confidence,
                "recommendation": d.recommendation,
                "created_at": d.created_at.isoformat(),
            }
            for d in decisions
        ],
        "activity_logs": [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": log.details,
            }
            for log in logs
        ],
    }

    return JSONResponse(
        content=export_data,
        headers={
            "Content-Disposition": f'attachment; filename="therese-export-{datetime.now(UTC).strftime("%Y%m%d-%H%M%S")}.json"'
        },
    )


@router.get("/export/conversations")
async def export_conversations(
    format: str = "json",
    session: AsyncSession = Depends(get_session),
):
    """
    Export uniquement les conversations.

    Args:
        format: json ou markdown
    """
    conversations_result = await session.execute(select(Conversation))
    conversations = conversations_result.scalars().all()

    messages_result = await session.execute(select(Message))
    messages = messages_result.scalars().all()

    if format == "markdown":
        # Export Markdown
        content = "# Export Conversations THERESE\n\n"
        content += f"*Exporte le {datetime.now(UTC).strftime('%d/%m/%Y a %H:%M')}*\n\n"
        content += "---\n\n"

        for conv in conversations:
            content += f"## {conv.title or 'Sans titre'}\n\n"
            content += f"*ID: {conv.id} - Cree le {conv.created_at.strftime('%d/%m/%Y')}*\n\n"

            conv_messages = [m for m in messages if m.conversation_id == conv.id]
            conv_messages.sort(key=lambda m: m.created_at)

            for msg in conv_messages:
                role_label = "**Vous**" if msg.role == "user" else "**THERESE**"
                content += f"{role_label} :\n\n{msg.content}\n\n---\n\n"

            content += "\n"

        return JSONResponse(
            content={"format": "markdown", "content": content},
            headers={
                "Content-Disposition": f'attachment; filename="therese-conversations-{datetime.now(UTC).strftime("%Y%m%d")}.md"'
            },
        )
    else:
        # Export JSON
        data = {
            "exported_at": datetime.now(UTC).isoformat(),
            "conversations": [
                {
                    "id": conv.id,
                    "title": conv.title,
                    "created_at": conv.created_at.isoformat(),
                    "messages": [
                        {
                            "role": m.role,
                            "content": m.content,
                            "created_at": m.created_at.isoformat(),
                        }
                        for m in sorted(
                            [msg for msg in messages if msg.conversation_id == conv.id],
                            key=lambda x: x.created_at,
                        )
                    ],
                }
                for conv in conversations
            ],
        }
        return JSONResponse(content=data)


# ============================================================
# Suppression donnees (RGPD Art. 17 - Droit a l'oubli)
# ============================================================


@router.delete("/all")
async def delete_all_data(
    confirm: bool = False,
    session: AsyncSession = Depends(get_session),
):
    """
    Supprime TOUTES les donnees utilisateur (RGPD Art. 17).

    ATTENTION: Action irreversible.

    Args:
        confirm: Doit etre True pour confirmer la suppression
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Ajoutez ?confirm=true pour confirmer la suppression de toutes vos donnees",
        )

    # Log avant suppression
    await log_activity(
        session,
        AuditAction.DATA_DELETED_ALL,
        resource_type="rgpd",
        details=json.dumps({"confirm": True}),
    )

    from sqlalchemy import delete

    # Supprimer dans l'ordre (relations)
    await session.execute(delete(Message))
    await session.execute(delete(Conversation))
    await session.execute(delete(Project))
    await session.execute(delete(Contact))
    await session.execute(delete(FileMetadata))
    await session.execute(delete(BoardDecisionDB))
    # On garde les preferences systeme mais on supprime les API keys
    await session.execute(
        delete(Preference).where(Preference.key.contains("api_key"))
    )
    # On garde les logs d'audit (trace legale)

    await session.commit()

    logger.warning("Toutes les donnees utilisateur ont ete supprimees (RGPD)")

    return {
        "deleted": True,
        "message": "Toutes vos donnees ont ete supprimees conformement au RGPD Art. 17",
        "note": "Les logs d'audit sont conserves pour des raisons legales",
    }


# ============================================================
# Logs d'activite (US-SEC-05)
# ============================================================


@router.get("/logs")
async def get_activity_logs(
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    """
    Recupere les logs d'activite.

    Args:
        action: Filtrer par type d'action (ex: api_key_set, contact_created)
        resource_type: Filtrer par type de ressource (ex: contact, project)
        limit: Nombre max de resultats (defaut: 100)
        offset: Offset pour pagination
    """
    audit_service = AuditService(session)

    action_enum = None
    if action:
        try:
            action_enum = AuditAction(action)
        except ValueError:
            pass  # On ignore les actions invalides

    logs = await audit_service.get_logs(
        action=action_enum,
        resource_type=resource_type,
        limit=limit,
        offset=offset,
    )

    count = await audit_service.get_logs_count(
        action=action_enum,
        resource_type=resource_type,
    )

    return {
        "logs": [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": json.loads(log.details) if log.details else None,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
            }
            for log in logs
        ],
        "total": count,
        "limit": limit,
        "offset": offset,
    }


@router.get("/logs/actions")
async def get_available_actions():
    """Liste les types d'actions disponibles pour le filtrage."""
    return {
        "actions": [action.value for action in AuditAction],
        "categories": {
            "authentication": ["api_key_set", "api_key_deleted", "api_key_rotated", "auth_failed"],
            "profile": ["profile_updated", "profile_deleted"],
            "data": [
                "contact_created", "contact_updated", "contact_deleted",
                "project_created", "project_updated", "project_deleted",
            ],
            "conversations": ["conversation_created", "conversation_deleted"],
            "files": ["file_indexed", "file_deleted"],
            "rgpd": ["data_exported", "data_deleted_all"],
            "config": ["config_changed", "llm_provider_changed"],
            "board": ["board_decision"],
            "errors": ["encryption_error"],
        },
    }


@router.delete("/logs")
async def cleanup_old_logs(
    days: int = 90,
    session: AsyncSession = Depends(get_session),
):
    """
    Supprime les logs de plus de N jours.

    Args:
        days: Nombre de jours de retention (defaut: 90)
    """
    audit_service = AuditService(session)
    deleted_count = await audit_service.cleanup_old_logs(days=days)

    return {
        "deleted_count": deleted_count,
        "retention_days": days,
    }


# ============================================================
# Backup & Restore (US-BAK-01 to US-BAK-05)
# ============================================================


@router.post("/backup")
async def create_backup(
    session: AsyncSession = Depends(get_session),
):
    """
    Create a backup of all data (US-BAK-03).

    Returns backup info and file path.
    """
    import shutil
    from pathlib import Path

    # Get backup directory
    backup_dir = Path.home() / ".therese" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Create timestamped backup
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    backup_name = f"therese_backup_{timestamp}"

    # Copy database file
    db_path = settings.db_path
    backup_db_path = backup_dir / f"{backup_name}.db"
    shutil.copy2(db_path, backup_db_path)

    # Create backup metadata
    metadata = {
        "created_at": datetime.now(UTC).isoformat(),
        "app_version": settings.app_version,
        "db_path": str(backup_db_path),
        "backup_name": backup_name,
    }

    # Save metadata
    metadata_path = backup_dir / f"{backup_name}.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    # Audit log
    await log_activity(
        session,
        AuditAction.DATA_EXPORTED,
        resource_type="backup",
        resource_id=backup_name,
        details=json.dumps({"type": "backup", "path": str(backup_db_path)}),
    )

    return {
        "success": True,
        "backup_name": backup_name,
        "path": str(backup_db_path),
        "created_at": metadata["created_at"],
    }


@router.get("/backups")
async def list_backups():
    """
    List available backups (US-BAK-04).
    """
    from pathlib import Path

    backup_dir = Path.home() / ".therese" / "backups"
    if not backup_dir.exists():
        return {"backups": []}

    backups = []
    for metadata_file in backup_dir.glob("*.json"):
        try:
            with open(metadata_file) as f:
                metadata = json.load(f)

            # Check if DB file exists
            db_path = Path(metadata.get("db_path", ""))
            if db_path.exists():
                metadata["size_bytes"] = db_path.stat().st_size
                metadata["exists"] = True
            else:
                metadata["exists"] = False

            backups.append(metadata)
        except Exception:
            continue

    # Sort by date, most recent first
    backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return {"backups": backups}


@router.post("/restore/{backup_name}")
async def restore_backup(
    backup_name: str,
    confirm: bool = False,
    session: AsyncSession = Depends(get_session),
):
    """
    Restore from a backup (US-BAK-04).

    ATTENTION: This will replace current data.
    """
    import shutil
    from pathlib import Path

    # Validation du nom de backup (SEC-019)
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', backup_name):
        raise HTTPException(
            status_code=400,
            detail="Nom de backup invalide. Seuls les caracteres alphanumeriques, tirets, underscores et points sont autorises.",
        )

    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Ajoutez ?confirm=true pour confirmer la restauration",
        )

    backup_dir = Path.home() / ".therese" / "backups"

    # Verify path is within backups directory
    backup_path = backup_dir / backup_name
    if not str(backup_path.resolve()).startswith(str(backup_dir.resolve())):
        raise HTTPException(status_code=403, detail="Chemin de backup non autorise")

    backup_db = backup_dir / f"{backup_name}.db"
    metadata_file = backup_dir / f"{backup_name}.json"

    if not backup_db.exists():
        raise HTTPException(status_code=404, detail=f"Backup '{backup_name}' non trouve")

    # Create a backup of current state before restore
    current_backup_name = f"pre_restore_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
    current_backup_path = backup_dir / f"{current_backup_name}.db"
    shutil.copy2(settings.db_path, current_backup_path)

    # Restore from backup
    try:
        shutil.copy2(backup_db, settings.db_path)
    except Exception as e:
        # Rollback
        shutil.copy2(current_backup_path, settings.db_path)
        raise HTTPException(
            status_code=500,
            detail=f"Echec de la restauration: {e}. Donnees restaurees a l'etat precedent.",
        )

    # Load metadata if exists
    metadata = {}
    if metadata_file.exists():
        with open(metadata_file) as f:
            metadata = json.load(f)

    return {
        "success": True,
        "restored_from": backup_name,
        "restored_at": datetime.now(UTC).isoformat(),
        "backup_metadata": metadata,
        "safety_backup": current_backup_name,
        "note": "Redemarrez l'application pour appliquer les changements",
    }


@router.delete("/backups/{backup_name}")
async def delete_backup(backup_name: str):
    """Delete a backup."""
    from pathlib import Path

    backup_dir = Path.home() / ".therese" / "backups"
    backup_db = backup_dir / f"{backup_name}.db"
    metadata_file = backup_dir / f"{backup_name}.json"

    if not backup_db.exists():
        raise HTTPException(status_code=404, detail=f"Backup '{backup_name}' non trouve")

    # Delete both files
    backup_db.unlink()
    if metadata_file.exists():
        metadata_file.unlink()

    return {"deleted": True, "backup_name": backup_name}


@router.post("/import/conversations")
async def import_conversations(
    data: dict,
    session: AsyncSession = Depends(get_session),
):
    """
    Import conversations from JSON export (US-BAK-02).

    Expects format from /export/conversations endpoint.
    """
    if "conversations" not in data:
        raise HTTPException(status_code=400, detail="Format invalide: 'conversations' manquant")

    imported = {"conversations": 0, "messages": 0}

    for conv_data in data["conversations"]:
        # Check if conversation already exists (by ID)
        existing = await session.execute(
            select(Conversation).where(Conversation.id == conv_data.get("id"))
        )
        if existing.scalar_one_or_none():
            continue  # Skip existing

        # Create conversation
        conversation = Conversation(
            id=conv_data.get("id"),  # Preserve ID if provided
            title=conv_data.get("title"),
            summary=conv_data.get("summary"),
        )
        session.add(conversation)
        await session.flush()
        imported["conversations"] += 1

        # Import messages
        for msg_data in conv_data.get("messages", []):
            message = Message(
                conversation_id=conversation.id,
                role=msg_data.get("role", "user"),
                content=msg_data.get("content", ""),
            )
            session.add(message)
            imported["messages"] += 1

    await session.commit()

    return {
        "success": True,
        "imported": imported,
    }


@router.post("/import/contacts")
async def import_contacts(
    data: dict,
    session: AsyncSession = Depends(get_session),
):
    """
    Import contacts from JSON export (US-BAK-02).
    """
    if "contacts" not in data:
        raise HTTPException(status_code=400, detail="Format invalide: 'contacts' manquant")

    imported = 0

    for contact_data in data["contacts"]:
        # Check if contact already exists
        existing = await session.execute(
            select(Contact).where(Contact.id == contact_data.get("id"))
        )
        if existing.scalar_one_or_none():
            continue

        contact = Contact(
            id=contact_data.get("id"),
            first_name=contact_data.get("first_name"),
            last_name=contact_data.get("last_name"),
            company=contact_data.get("company"),
            email=contact_data.get("email"),
            phone=contact_data.get("phone"),
            notes=contact_data.get("notes"),
            tags=json.dumps(contact_data.get("tags")) if contact_data.get("tags") else None,
        )
        session.add(contact)
        imported += 1

    await session.commit()

    return {"success": True, "imported": imported}


@router.get("/backup/status")
async def get_backup_status():
    """
    Get backup status and recommendations.
    """
    from pathlib import Path

    backup_dir = Path.home() / ".therese" / "backups"
    if not backup_dir.exists():
        return {
            "has_backups": False,
            "last_backup": None,
            "recommendation": "Aucune sauvegarde. Creez-en une maintenant.",
        }

    # Find most recent backup
    backups = list(backup_dir.glob("*.json"))
    if not backups:
        return {
            "has_backups": False,
            "last_backup": None,
            "recommendation": "Aucune sauvegarde. Creez-en une maintenant.",
        }

    latest = None
    latest_time = None

    for metadata_file in backups:
        try:
            with open(metadata_file) as f:
                metadata = json.load(f)
            created = datetime.fromisoformat(metadata.get("created_at", ""))
            if latest_time is None or created > latest_time:
                latest_time = created
                latest = metadata
        except Exception:
            continue

    if not latest:
        return {
            "has_backups": False,
            "last_backup": None,
            "recommendation": "Aucune sauvegarde valide. Creez-en une maintenant.",
        }

    # Check if backup is recent
    if latest_time.tzinfo is None:
        latest_time = latest_time.replace(tzinfo=UTC)
    age_days = (datetime.now(UTC) - latest_time).days
    recommendation = None

    if age_days > 7:
        recommendation = f"Votre derniere sauvegarde date de {age_days} jours. Pensez a en creer une nouvelle."
    elif age_days > 1:
        recommendation = f"Derniere sauvegarde il y a {age_days} jours."

    return {
        "has_backups": True,
        "last_backup": latest,
        "days_since_backup": age_days,
        "recommendation": recommendation,
    }
