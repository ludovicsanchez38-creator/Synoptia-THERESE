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
from pathlib import Path
from typing import Any

from app.config import settings
from app.models.database import close_db, get_session
from app.models.entities import (
    Activity,
    BoardDecisionDB,
    Calendar,
    CalendarEvent,
    Contact,
    Conversation,
    Deliverable,
    Document,
    DocumentPiste,
    DocumentSection,
    EmailAccount,
    EmailFollowUp,
    EmailLabel,
    EmailMessage,
    FileMetadata,
    Invoice,
    InvoiceLine,
    Message,
    Notification,
    Preference,
    Project,
    PromptTemplate,
    Task,
    Variable,
)
from app.models.entities_agents import AgentMessage, AgentSession, AgentTask, CodeChange
from app.services.audit import (
    ActivityLog,
    AuditAction,
    AuditService,
    log_activity,
)
from app.services.encryption import decrypt_backup_archive, encrypt_backup_archive
from app.services.maintenance import maintenance_mode
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

logger = logging.getLogger(__name__)

router = APIRouter()


def _export_row(
    row: Any,
    *,
    exclude: set[str] | None = None,
    json_fields: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Sérialise une ligne SQLModel sans perdre les champs ajoutés au modèle.

    Les colonnes qui contiennent du JSON sous forme de texte sont décodées pour
    produire un export portable. Les secrets de connexion sont exclus par
    l'appelant : un export RGPD contient les données, jamais les identifiants
    permettant d'accéder à un service tiers.
    """
    payload: dict[str, Any] = row.model_dump(mode="json", exclude=exclude or set())
    for field in json_fields:
        value = payload.get(field)
        if not isinstance(value, str):
            continue
        try:
            payload[field] = json.loads(value)
        except json.JSONDecodeError:
            # Ne jamais perdre une valeur historique devenue invalide : elle
            # reste exportée telle quelle et pourra être examinée/importée.
            pass
    return payload


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

    # Documents (atelier documentaire - US-SEC-02 / Art. 20)
    documents_result = await session.execute(select(Document))
    documents = documents_result.scalars().all()

    document_sections_result = await session.execute(select(DocumentSection))
    document_sections = document_sections_result.scalars().all()

    document_pistes_result = await session.execute(select(DocumentPiste))
    document_pistes = document_pistes_result.scalars().all()

    # Variables utilisateur (chantier 4 - finding Codex 11 : énumération
    # manuelle, ajout explicite obligatoire)
    variables_result = await session.execute(select(Variable))
    variables = variables_result.scalars().all()

    # Données fonctionnelles et connexions. Les secrets des comptes externes
    # sont volontairement exclus plus bas, mais leurs contenus synchronisés
    # font partie du droit à la portabilité.
    prompt_templates = (await session.execute(select(PromptTemplate))).scalars().all()
    email_accounts = (await session.execute(select(EmailAccount))).scalars().all()
    email_messages = (await session.execute(select(EmailMessage))).scalars().all()
    email_labels = (await session.execute(select(EmailLabel))).scalars().all()
    email_follow_ups = (await session.execute(select(EmailFollowUp))).scalars().all()
    calendars = (await session.execute(select(Calendar))).scalars().all()
    calendar_events = (await session.execute(select(CalendarEvent))).scalars().all()
    tasks = (await session.execute(select(Task))).scalars().all()
    invoices = (await session.execute(select(Invoice))).scalars().all()
    invoice_lines = (await session.execute(select(InvoiceLine))).scalars().all()
    activities = (await session.execute(select(Activity))).scalars().all()
    deliverables = (await session.execute(select(Deliverable))).scalars().all()
    notifications = (await session.execute(select(Notification))).scalars().all()
    agent_tasks = (await session.execute(select(AgentTask))).scalars().all()
    agent_messages = (await session.execute(select(AgentMessage))).scalars().all()
    code_changes = (await session.execute(select(CodeChange))).scalars().all()
    agent_sessions = (await session.execute(select(AgentSession))).scalars().all()

    # Activity logs
    logs_result = await session.execute(
        select(ActivityLog).order_by(ActivityLog.timestamp.desc())
    )
    logs = logs_result.scalars().all()

    export_data = {
        "exported_at": datetime.now(UTC).isoformat(),
        "app_version": settings.app_version,
        "data_format_version": "1.2",  # 1.2 : couverture de toutes les tables utilisateur
        "variables": [
            {
                "id": v.id,
                "name": v.name,
                "kind": v.kind,
                "value": v.parsed_value,
                "description": v.description,
                "created_at": v.created_at.isoformat(),
                "updated_at": v.updated_at.isoformat(),
            }
            for v in variables
        ],
        "contacts": [
            _export_row(item, json_fields=("tags", "extra_data")) for item in contacts
        ],
        "projects": [
            _export_row(item, json_fields=("tags", "extra_data")) for item in projects
        ],
        "conversations": [
            {
                "id": conv.id,
                "title": conv.title,
                "summary": conv.summary,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "messages": [
                    _export_row(m, json_fields=("extra_data",))
                    for m in messages
                    if m.conversation_id == conv.id
                ],
            }
            for conv in conversations
        ],
        "files": [_export_row(item) for item in files],
        "preferences": [
            {
                "id": p.id,
                "key": p.key,
                "value": p.value if "api_key" not in p.key.lower() else "[REDACTED]",
                "category": p.category,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat(),
            }
            for p in preferences
        ],
        "board_decisions": [
            _export_row(item, json_fields=("opinions", "synthesis"))
            for item in decisions
        ],
        "prompt_templates": [_export_row(item) for item in prompt_templates],
        "email_accounts": [
            _export_row(
                item,
                exclude={
                    "client_id",
                    "client_secret",
                    "access_token",
                    "refresh_token",
                    "imap_password",
                },
                json_fields=("scopes",),
            )
            for item in email_accounts
        ],
        "email_messages": [
            _export_row(
                item,
                json_fields=("to_emails", "cc_emails", "bcc_emails", "labels"),
            )
            for item in email_messages
        ],
        "email_labels": [_export_row(item) for item in email_labels],
        "email_follow_ups": [_export_row(item) for item in email_follow_ups],
        "calendars": [
            _export_row(item, exclude={"caldav_password"}) for item in calendars
        ],
        "calendar_events": [
            _export_row(item, json_fields=("attendees", "recurrence"))
            for item in calendar_events
        ],
        "tasks": [_export_row(item, json_fields=("tags",)) for item in tasks],
        "invoices": [_export_row(item) for item in invoices],
        "invoice_lines": [_export_row(item) for item in invoice_lines],
        "activities": [
            _export_row(item, json_fields=("extra_data",)) for item in activities
        ],
        "deliverables": [_export_row(item) for item in deliverables],
        "notifications": [_export_row(item) for item in notifications],
        "agent_tasks": [
            _export_row(item, json_fields=("files_changed",)) for item in agent_tasks
        ],
        "agent_messages": [
            _export_row(item, json_fields=("tool_calls",)) for item in agent_messages
        ],
        "code_changes": [_export_row(item) for item in code_changes],
        "agent_sessions": [_export_row(item) for item in agent_sessions],
        "documents": [
            {
                "id": doc.id,
                "title": doc.title,
                "brief": doc.brief,
                "status": doc.status,
                "project_id": doc.project_id,
                "contact_id": doc.contact_id,
                "created_at": doc.created_at.isoformat(),
                "updated_at": doc.updated_at.isoformat(),
            }
            for doc in documents
        ],
        "document_sections": [
            {
                "id": s.id,
                "document_id": s.document_id,
                "title": s.title,
                "brief": s.brief,
                "order": s.order,
                "depth": s.depth,
                "content": s.content,
                "summary": s.summary,
                "status": s.status,
                "orphan": s.orphan,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
            }
            for s in document_sections
        ],
        "document_pistes": [
            {
                "id": p.id,
                "document_id": p.document_id,
                "section_origine_id": p.section_origine_id,
                "texte": p.texte,
                "status": p.status,
                "created_at": p.created_at.isoformat(),
            }
            for p in document_pistes
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
            detail="Ajoute ?confirm=true pour confirmer la suppression de toutes tes données",
        )

    # Log avant suppression
    await log_activity(
        session,
        AuditAction.DATA_DELETED_ALL,
        resource_type="rgpd",
        details=json.dumps({"confirm": True}),
    )

    from sqlalchemy import delete

    # Supprimer dans l'ordre (FK en premier)
    # -- Tables agents
    await session.execute(delete(CodeChange))
    await session.execute(delete(AgentMessage))
    await session.execute(delete(AgentTask))
    await session.execute(delete(AgentSession))
    # -- Atelier documentaire (RGPD Art. 17) : pistes -> sections -> documents
    await session.execute(delete(DocumentPiste))
    await session.execute(delete(DocumentSection))
    await session.execute(delete(Document))
    # -- Tables avec FK
    await session.execute(delete(InvoiceLine))
    await session.execute(delete(Invoice))
    await session.execute(delete(CalendarEvent))
    await session.execute(delete(Calendar))
    await session.execute(delete(EmailFollowUp))
    await session.execute(delete(EmailLabel))
    await session.execute(delete(EmailMessage))
    await session.execute(delete(EmailAccount))
    await session.execute(delete(Task))
    await session.execute(delete(Deliverable))
    await session.execute(delete(Activity))
    await session.execute(delete(PromptTemplate))
    await session.execute(delete(Notification))
    # -- Tables principales (deja presentes)
    await session.execute(delete(Message))
    await session.execute(delete(Conversation))
    await session.execute(delete(Project))
    await session.execute(delete(Contact))
    await session.execute(delete(FileMetadata))
    await session.execute(delete(BoardDecisionDB))
    await session.execute(delete(Variable))
    # Les préférences contiennent aussi le profil et les choix personnels :
    # « toutes les données » doit donc réellement remettre cet espace à zéro.
    await session.execute(delete(Preference))
    # On garde les logs d'audit (trace legale)

    await session.commit()

    # Purger Qdrant (embeddings vectoriels)
    try:
        from app.services.qdrant import get_qdrant_service

        qdrant = get_qdrant_service()
        if qdrant.client:
            qdrant.client.delete_collection(settings.qdrant_collection)
    except Exception:
        logger.warning("Impossible de purger la collection Qdrant")

    # Revue 0.40 : « toutes mes données » doit couvrir les fichiers sur disque
    # (images générées, fichiers produits par les skills), pas seulement les
    # tables. Les sauvegardes sont conservées à dessein (filet de l'utilisateur,
    # supprimables une à une depuis l'interface) - et on l'annonce.
    import shutil
    from pathlib import Path

    data_dir = Path(settings.data_dir)
    for sub in ("images", "outputs"):
        target = data_dir / sub
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        target.mkdir(parents=True, exist_ok=True)

    backups_dir = data_dir / "backups"
    backups_kept = len(list(backups_dir.glob("*.json"))) if backups_dir.exists() else 0

    logger.warning("Toutes les donnees utilisateur ont ete supprimees (RGPD)")

    if backups_kept:
        note = (
            "Les logs d'audit sont conservés pour des raisons légales. "
            f"{backups_kept} sauvegarde(s) conservée(s) : supprime-les depuis "
            "la liste des sauvegardes si tu veux vraiment tout effacer."
        )
    else:
        note = "Les logs d'audit sont conservés pour des raisons légales"

    return {
        "deleted": True,
        "message": "Toutes tes données ont été supprimées conformément au RGPD Art. 17",
        "note": note,
        "backups_kept": backups_kept,
    }


# ============================================================
# Logs d'activite (US-SEC-05)
# ============================================================


@router.get("/logs")
async def get_activity_logs(
    action: str | None = None,
    resource_type: str | None = None,
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


def _backups_dir():
    """Dossier des backups, sous le data dir (respecte THERESE_DATA_DIR)."""
    from pathlib import Path

    d = Path(settings.data_dir) / "backups"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _checkpoint_db() -> bool:
    """US-011 : flush le WAL SQLite dans therese.db avant backup/restore.

    En mode WAL, les transactions récentes restent dans `therese.db-wal` et ne
    sont PAS dans l'archive si on copie seulement `therese.db` → perte de
    données. Le checkpoint TRUNCATE les rapatrie dans le fichier principal.

    Retourne ``False`` uniquement lorsque SQLite reste occupé après plusieurs
    essais : l'appelant doit alors archiver les sidecars WAL/SHM. Toute réponse
    absente ou incohérente échoue explicitement.
    """
    from contextlib import closing
    from pathlib import Path
    from time import sleep

    from app.models.database import db_connect

    db_path = settings.db_path
    if not db_path or not Path(str(db_path)).exists():
        return True

    attempts = 3
    # closing() ferme bien la connexion : le context manager natif de sqlite3
    # ne gère que la transaction, pas la fermeture du handle. US-014 :
    # db_connect pose la clé SQLCipher si la base est chiffrée.
    with closing(db_connect(db_path)) as conn:
        for attempt in range(1, attempts + 1):
            row = conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
            if row is None or len(row) < 3:
                raise RuntimeError("SQLite n'a retourné aucun statut de checkpoint WAL")

            try:
                busy, log_frames, checkpointed_frames = (int(row[0]), int(row[1]), int(row[2]))
            except (TypeError, ValueError) as exc:
                raise RuntimeError(f"Statut de checkpoint WAL invalide : {row!r}") from exc

            if busy < 0 or log_frames < 0 or checkpointed_frames < 0:
                raise RuntimeError(
                    "Statut de checkpoint WAL incohérent : "
                    f"busy={busy}, log={log_frames}, checkpointed={checkpointed_frames}"
                )

            if busy == 0 and checkpointed_frames >= log_frames:
                return True

            logger.warning(
                "Checkpoint WAL occupé (%s/%s) : busy=%s, log=%s, checkpointed=%s",
                attempt,
                attempts,
                busy,
                log_frames,
                checkpointed_frames,
            )
            if attempt < attempts:
                sleep(0.05)

    return False


def _create_archive(archive_path) -> list[str]:
    """Crée une archive .tar.gz complète : DB (checkpointée) + Qdrant + images
    + mcp_servers.json + clé de chiffrement. Retourne la liste des éléments inclus.

    Revue adversariale US-014 : sans .encryption_key, le backup n'était PLUS
    restaurable après perte de la machine (DB chiffrée, clé dans le Keychain
    mort) - la raison d'être du backup. L'archive contient déjà Qdrant et les
    images EN CLAIR : inclure la clé n'abaisse pas la posture, mais le fichier
    de backup doit être protégé comme la base elle-même (documenté SECURITY.md).
    """
    import tarfile
    from pathlib import Path

    archive_path = Path(archive_path)
    checkpoint_complete = _checkpoint_db()
    data_dir = Path(settings.data_dir)
    db_path = Path(settings.db_path) if settings.db_path else None
    targets = [
        (db_path, "therese.db"),
        (Path(settings.qdrant_path) if settings.qdrant_path else None, "qdrant"),
        (data_dir / "images", "images"),
        (data_dir / "mcp_servers.json", "mcp_servers.json"),
        (data_dir / "export_profile.json", "export_profile.json"),
        (data_dir / ".encryption_key", ".encryption_key"),
        (data_dir / ".encryption_salt", ".encryption_salt"),
    ]

    if not checkpoint_complete:
        if db_path is None:
            raise RuntimeError("Checkpoint WAL incomplet sans chemin de base exploitable")
        wal_path = Path(f"{db_path}-wal")
        shm_path = Path(f"{db_path}-shm")
        missing = [str(path) for path in (wal_path, shm_path) if not path.is_file()]
        if missing:
            raise RuntimeError(
                "Checkpoint WAL toujours occupé et sauvegarde des sidecars impossible : "
                f"fichier(s) absent(s) {', '.join(missing)}"
            )
        targets.extend(((wal_path, "therese.db-wal"), (shm_path, "therese.db-shm")))
        logger.warning(
            "Checkpoint WAL incomplet : therese.db-wal et therese.db-shm seront archivés"
        )

    included: list[str] = []
    try:
        with tarfile.open(archive_path, "w:gz") as tar:
            for src, arcname in targets:
                if src and src.exists():
                    tar.add(str(src), arcname=arcname)
                    included.append(arcname)
    except Exception:
        archive_path.unlink(missing_ok=True)
        raise

    if not checkpoint_complete and not {"therese.db-wal", "therese.db-shm"} <= set(included):
        archive_path.unlink(missing_ok=True)
        raise RuntimeError("Archive WAL incomplète : sauvegarde annulée")
    return included


def _verify_restored_db() -> None:
    """Revue adversariale US-014 : la DB restaurée doit être LISIBLE avant de
    déclarer le succès - sinon restore répondait success puis l'app était
    brickée au redémarrage (clé d'une autre machine). Clés candidates : celle
    dérivée du .encryption_key restauré (restauration cross-machine), puis la
    clé locale courante. Une DB claire (backup pré-US-014) est acceptée : elle
    sera re-chiffrée au prochain démarrage."""
    from contextlib import closing
    from pathlib import Path

    from app.models.database import db_is_encrypted

    db_path = Path(str(settings.db_path))
    if not db_path.exists() or not db_is_encrypted(db_path):
        return

    import sqlcipher3
    from app.services.encryption import derive_db_key_from_master, get_db_key_hex

    candidates: list[str] = []
    key_file = Path(settings.data_dir) / ".encryption_key"
    if key_file.exists():
        try:
            candidates.append(derive_db_key_from_master(key_file.read_bytes()))
        except Exception as e:
            logger.warning("Clé du backup illisible : %s", e)
    try:
        current = get_db_key_hex()
        if current not in candidates:
            candidates.append(current)
    except Exception as e:
        logger.warning("Clé locale indisponible : %s", e)

    for key_hex in candidates:
        try:
            with closing(sqlcipher3.connect(str(db_path))) as conn:
                conn.execute(f"PRAGMA key = \"x'{key_hex}'\"")
                conn.execute("SELECT count(*) FROM sqlite_master").fetchone()
            return
        except Exception:
            continue

    raise HTTPException(
        status_code=409,
        detail=(
            "La base restaurée est chiffrée avec une clé introuvable sur cette "
            "machine (archive sans .encryption_key ?). Restauration annulée, "
            "tes données actuelles sont intactes."
        ),
    )


def _safe_extractall(tar, dest) -> None:
    """Extraction protégée contre le path traversal, compatible Python 3.11+.

    Utilise filter='data' (PEP 706, Python 3.12+) si disponible ; sinon valide
    chaque membre à la main (pas de chemin absolu / .. / lien)."""
    from pathlib import Path

    try:
        tar.extractall(dest, filter="data")
        return
    except TypeError:
        pass  # Python < 3.12 : pas de paramètre filter
    dest_resolved = Path(dest).resolve()
    for member in tar.getmembers():
        target = (Path(dest) / member.name).resolve()
        if not str(target).startswith(str(dest_resolved)) or member.issym() or member.islnk():
            raise HTTPException(
                status_code=400, detail="Archive de backup non sûre (path traversal ou lien)"
            )
    tar.extractall(dest)


@router.post("/backup")
async def create_backup(
    session: AsyncSession = Depends(get_session),
    password: str | None = Body(default=None, embed=True),
):
    """
    Create a complete backup of all data (US-011 / US-BAK-03).

    US-011 : sauvegarde TOUT (DB + Qdrant + images + mcp_servers.json) dans une
    archive .tar.gz, pas seulement therese.db. Sans ça, un restore perdait la
    mémoire vectorielle, les images et la config MCP.

    US-003 : si une passphrase est fournie, l'archive complète est chiffrée
    (.tar.gz.enc) - l'archive contient la clé de chiffrement pour rester
    restaurable après perte de la machine (US-014), donc sans chiffrement elle
    équivaut à une base en clair. La passphrase doit être non vide.
    """
    backup_dir = _backups_dir()

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    backup_name = f"therese_backup_{timestamp}"
    archive_path = backup_dir / f"{backup_name}.tar.gz"

    # US-003 : la passphrase est requise. L'archive embarque la clé de
    # chiffrement (pour rester restaurable après perte de la machine, US-014),
    # donc une sauvegarde en clair équivaudrait à une base en clair : on refuse.
    if password is None or not password.strip():
        raise HTTPException(
            status_code=400,
            detail=(
                "Une passphrase est requise pour chiffrer la sauvegarde. "
                "Conserve-la précieusement : elle est indispensable pour restaurer."
            ),
        )

    try:
        included = _create_archive(archive_path)
    except Exception as exc:
        logger.exception("Sauvegarde annulée : impossible de garantir la cohérence")
        raise HTTPException(
            status_code=503,
            detail=f"Sauvegarde impossible à garantir : {exc}",
        ) from exc

    enc_path = backup_dir / f"{backup_name}.tar.gz.enc"
    try:
        encrypt_backup_archive(archive_path, enc_path, password)
    except Exception as exc:
        archive_path.unlink(missing_ok=True)
        enc_path.unlink(missing_ok=True)
        logger.exception("Chiffrement de la sauvegarde échoué")
        raise HTTPException(
            status_code=500, detail=f"Chiffrement de la sauvegarde impossible : {exc}"
        ) from exc
    # L'archive en clair ne doit jamais subsister à côté de la version chiffrée.
    archive_path.unlink(missing_ok=True)
    archive_path = enc_path
    encrypted = True

    metadata = {
        "created_at": datetime.now(UTC).isoformat(),
        "app_version": settings.app_version,
        "archive_path": str(archive_path),
        "backup_name": backup_name,
        "included": included,
        "encrypted": encrypted,
    }
    metadata_path = backup_dir / f"{backup_name}.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    await log_activity(
        session,
        AuditAction.DATA_EXPORTED,
        resource_type="backup",
        resource_id=backup_name,
        details=json.dumps({"type": "backup", "path": str(archive_path)}),
    )

    return {
        "success": True,
        "backup_name": backup_name,
        "path": str(archive_path),
        "created_at": metadata["created_at"],
        "included": included,
        "encrypted": encrypted,
    }


@router.get("/backups")
async def list_backups():
    """
    List available backups (US-BAK-04).
    """
    from pathlib import Path

    backup_dir = _backups_dir()

    backups = []
    for metadata_file in backup_dir.glob("*.json"):
        try:
            with open(metadata_file) as f:
                metadata = json.load(f)

            # US-011 : archive .tar.gz (nouveau) ou .db legacy (compat ascendante)
            artifact = Path(metadata.get("archive_path") or metadata.get("db_path", ""))
            if artifact.exists():
                metadata["size_bytes"] = artifact.stat().st_size
                metadata["exists"] = True
            else:
                metadata["exists"] = False

            backups.append(metadata)
        except Exception as e:
            logger.debug("Erreur lecture metadata backup: %s", e)
            continue

    # Sort by date, most recent first
    backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return {"backups": backups}


def _register_pre_restore_backup(
    backup_dir: Path, name: str, artifact: Path, encrypted: bool, included: list[str]
) -> None:
    """Donne des métadonnées à l'archive de sécurité pre_restore_*.

    Revue 0.40 : sans .json, list_backups ne la voyait pas -> archive invisible
    dans l'interface, impossible à supprimer, ~230 Mo cachés par restauration.
    Ne lève jamais : la restauration a réussi, l'enregistrement est best-effort."""
    try:
        metadata = {
            "created_at": datetime.now(UTC).isoformat(),
            "app_version": settings.app_version,
            "archive_path": str(artifact),
            "backup_name": name,
            "included": included,
            "encrypted": encrypted,
            "kind": "pre_restore",
        }
        with open(backup_dir / f"{name}.json", "w") as f:
            json.dump(metadata, f, indent=2)
    except Exception:
        logger.exception("Métadonnées de l'archive de sécurité non écrites")


def _prune_pre_restore_backups(backup_dir: Path, keep: str) -> None:
    """Rétention : une seule archive de sécurité, la plus récente.

    Purge artefacts ET métadonnées des pre_restore_* antérieurs, y compris les
    archives invisibles laissées par les versions d'avant 0.40.1."""
    try:
        for path in backup_dir.glob("pre_restore_*"):
            if path.name.startswith(keep):
                continue
            path.unlink(missing_ok=True)
    except Exception:
        logger.exception("Purge des anciennes archives de sécurité en échec")


@router.post("/restore/{backup_name}")
async def restore_backup(
    backup_name: str,
    confirm: bool = False,
    password: str | None = Body(default=None, embed=True),
):
    """
    Restore from a backup (US-BAK-04).

    ATTENTION: This will replace current data.

    US-003 : une sauvegarde chiffrée (.tar.gz.enc) exige la passphrase, déchiffrée
    vers une archive temporaire AVANT toute étape destructive (un mauvais mot de
    passe échoue proprement sans toucher aux données courantes).
    """
    import shutil
    from pathlib import Path

    # Validation du nom de backup (SEC-019)
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', backup_name):
        raise HTTPException(
            status_code=400,
            detail="Nom de backup invalide. Seuls les caractères alphanumériques, tirets, underscores et points sont autorisés.",
        )

    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Ajoute ?confirm=true pour confirmer la restauration",
        )

    import tarfile

    backup_dir = _backups_dir()
    data_dir = Path(settings.data_dir)

    # Verify path is within backups directory
    backup_path = backup_dir / backup_name
    if not str(backup_path.resolve()).startswith(str(backup_dir.resolve())):
        raise HTTPException(status_code=403, detail="Chemin de backup non autorisé")

    archive = backup_dir / f"{backup_name}.tar.gz"
    encrypted_archive = backup_dir / f"{backup_name}.tar.gz.enc"
    legacy_db = backup_dir / f"{backup_name}.db"  # compat ascendante
    metadata_file = backup_dir / f"{backup_name}.json"

    if not archive.exists() and not encrypted_archive.exists() and not legacy_db.exists():
        raise HTTPException(status_code=404, detail=f"Backup '{backup_name}' non trouvé")

    # US-003 : sauvegarde chiffrée -> on déchiffre vers une archive temporaire
    # AVANT toute étape destructive. Passphrase absente/incorrecte = échec propre,
    # aucune donnée courante touchée. Le temp clair est supprimé dans le finally.
    decrypted_temp: Path | None = None
    if encrypted_archive.exists() and not archive.exists():
        if not password:
            raise HTTPException(
                status_code=400,
                detail="Cette sauvegarde est chiffrée : fournis la passphrase pour la restaurer.",
            )
        decrypted_temp = backup_dir / f".{backup_name}.restore.tar.gz"
        try:
            decrypt_backup_archive(encrypted_archive, decrypted_temp, password)
        except ValueError as exc:
            decrypted_temp.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        archive = decrypted_temp

    # US-011 : filet de sécurité COMPLET (DB + Qdrant + images + MCP), pas juste
    # la DB, pour pouvoir faire un rollback intégral si l'extraction échoue.
    # %f : deux restaurations dans la même seconde ne doivent pas se partager
    # la même archive de sécurité.
    current_backup_name = f"pre_restore_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S_%f')}"
    safety_archive = backup_dir / f"{current_backup_name}.tar.gz"
    safety_included: list[str] = []

    def _wipe_volatile_dirs() -> None:
        # Restore PROPRE : on retire qdrant/ et images/ avant extraction pour ne
        # pas laisser d'orphelins (fichiers créés après le backup).
        for sub in ("qdrant", "images"):
            p = data_dir / sub
            if p.exists():
                shutil.rmtree(p, ignore_errors=True)

    def _rollback() -> None:
        # Rollback INTÉGRAL depuis l'archive de sécurité (état d'avant restore).
        # _wipe_volatile_dirs() a pu détruire qdrant/ et images/ avant qu'une
        # erreur (corruption OU archive piégée) ne survienne : on remet tout.
        try:
            _wipe_volatile_dirs()
            with tarfile.open(safety_archive, "r:gz") as tar:
                _safe_extractall(tar, data_dir)
        except Exception:
            logger.exception("Rollback du restore en échec")

    try:
        await maintenance_mode.begin()
    except RuntimeError as exc:
        if decrypted_temp is not None:
            decrypted_temp.unlink(missing_ok=True)
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        # Aucune session n'est injectée à cette route : tous les appels API
        # admis avant le verrou sont terminés. Les pools sont disposés AVANT
        # l'archive de sécurité et, surtout, avant toute extraction.
        await close_db()

        try:
            safety_included = _create_archive(safety_archive)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Archive de sécurité impossible : {exc}. Restauration annulée.",
            ) from exc

        # Restore (US-011 : archive complète ; .db legacy = DB seule)
        try:
            if archive.exists():
                if not _checkpoint_db():
                    raise RuntimeError(
                        "Checkpoint WAL toujours occupé après fermeture des connexions"
                    )
                _wipe_volatile_dirs()
                with tarfile.open(archive, "r:gz") as tar:
                    _safe_extractall(tar, data_dir)
                # US-014 : vérifier que la DB restaurée s'ouvre AVANT de déclarer
                # le succès (sinon rollback via le except HTTPException ci-dessous)
                _verify_restored_db()
            else:
                shutil.copy2(legacy_db, settings.db_path)
        except HTTPException:
            # Archive non sûre (path traversal) détectée APRÈS le wipe → rollback.
            _rollback()
            _register_pre_restore_backup(
                backup_dir, current_backup_name, safety_archive, False, safety_included
            )
            raise
        except Exception as e:
            _rollback()
            _register_pre_restore_backup(
                backup_dir, current_backup_name, safety_archive, False, safety_included
            )
            raise HTTPException(
                status_code=500,
                detail=f"Échec de la restauration: {e}. Données restaurées à l'état précédent.",
            ) from e
    finally:
        maintenance_mode.end()
        # US-003 : ne jamais laisser subsister l'archive déchiffrée en clair.
        if decrypted_temp is not None:
            decrypted_temp.unlink(missing_ok=True)

    # Revue 0.40 : l'archive de sécurité devient une sauvegarde à part entière
    # (visible dans la liste, supprimable), chiffrée avec la passphrase que
    # l'utilisateur vient de saisir quand il y en a une (restauration legacy en
    # clair : pas de passphrase disponible, on la garde en clair mais visible).
    safety_artifact = safety_archive
    safety_encrypted = False
    if password:
        safety_enc = backup_dir / f"{current_backup_name}.tar.gz.enc"
        try:
            encrypt_backup_archive(safety_archive, safety_enc, password)
            safety_archive.unlink(missing_ok=True)
            safety_artifact = safety_enc
            safety_encrypted = True
        except Exception:
            safety_enc.unlink(missing_ok=True)
            logger.exception("Archive de sécurité non chiffrable : conservée en clair")
    _register_pre_restore_backup(
        backup_dir, current_backup_name, safety_artifact, safety_encrypted, safety_included
    )
    _prune_pre_restore_backups(backup_dir, keep=current_backup_name)

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
        "note": "Redémarre l'application pour appliquer les changements",
    }


@router.delete("/backups/{backup_name}")
async def delete_backup(backup_name: str):
    """Delete a backup."""

    # Validation du nom de backup (SEC-019)
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', backup_name):
        raise HTTPException(
            status_code=400,
            detail="Nom de backup invalide. Seuls les caractères alphanumériques, tirets, underscores et points sont autorisés.",
        )

    backup_dir = _backups_dir()

    # Verify path is within backups directory
    backup_path = backup_dir / backup_name
    if not str(backup_path.resolve()).startswith(str(backup_dir.resolve())):
        raise HTTPException(status_code=403, detail="Chemin de backup non autorisé")

    # US-011/US-003 : archive .tar.gz (pré-chiffrement), .tar.gz.enc (0.40+,
    # seul format encore produit) ou .db legacy. Revue 0.40 : sans le .enc,
    # toute sauvegarde récente répondait 404 et restait sur disque.
    from pathlib import Path

    candidates = [
        backup_dir / f"{backup_name}.tar.gz",
        backup_dir / f"{backup_name}.tar.gz.enc",
        backup_dir / f"{backup_name}.db",
    ]
    metadata_file = backup_dir / f"{backup_name}.json"

    # L'artefact référencé par les métadonnées fait foi (chemin borné au
    # dossier backups, même garde que le nom plus haut).
    if metadata_file.exists():
        try:
            with open(metadata_file) as f:
                metadata = json.load(f)
            artifact = Path(str(metadata.get("archive_path") or metadata.get("db_path") or ""))
            if artifact.name and str(artifact.resolve()).startswith(str(backup_dir.resolve())):
                candidates.append(artifact)
        except Exception:
            logger.debug("Métadonnées illisibles pour le backup %s", backup_name)

    if not any(c.exists() for c in candidates) and not metadata_file.exists():
        raise HTTPException(status_code=404, detail=f"Backup '{backup_name}' non trouvé")

    for f in (*candidates, metadata_file):
        if f.exists():
            f.unlink()

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
    # US-011 : respecter THERESE_DATA_DIR (cohérence avec list/create/restore).
    backup_dir = _backups_dir()

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
        except Exception as e:
            logger.debug("Erreur lecture metadata backup: %s", e)
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
        recommendation = f"Ta dernière sauvegarde date de {age_days} jours. Pense à en créer une nouvelle."
    elif age_days > 1:
        recommendation = f"Dernière sauvegarde il y a {age_days} jours."

    return {
        "has_backups": True,
        "last_backup": latest,
        "days_since_backup": age_days,
        "recommendation": recommendation,
    }
