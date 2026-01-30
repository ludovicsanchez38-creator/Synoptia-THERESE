"""
THÉRÈSE v2 - CRM Router

REST API pour les features CRM (pipeline, scoring, activités, livrables, sync Google Sheets).
Phase 5 - CRM Features + Local First Export/Import
"""

import logging
from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.models.database import get_session
from app.models.entities import Contact, Activity, Deliverable, Project, Task, Preference
from app.models.schemas import (
    ActivityResponse,
    CreateActivityRequest,
    DeliverableResponse,
    CreateDeliverableRequest,
    UpdateDeliverableRequest,
    UpdateContactStageRequest,
    ContactScoreUpdate,
    ContactResponse,
    CRMSyncConfigResponse,
    CRMSyncConfigRequest,
    CRMSyncStatsResponse,
    CRMSyncResponse,
    CRMImportResultSchema,
    CRMImportPreviewSchema,
    CRMImportErrorSchema,
)
from app.services.scoring import update_contact_score
from app.services.oauth import (
    get_oauth_service,
    OAuthConfig,
    GOOGLE_AUTH_URL,
    GOOGLE_TOKEN_URL,
    GSHEETS_SCOPES,
)
from app.services.crm_export import CRMExportService, ExportFormat
from app.services.crm_import import CRMImportService

logger = logging.getLogger(__name__)


def _parse_dt(value: str) -> datetime | None:
    """Parse datetime from various formats."""
    if not value or not isinstance(value, str) or not value.strip():
        return None
    value = value.strip()
    for fmt in [
        "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d/%m/%Y",
    ]:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


router = APIRouter(tags=["crm"])


# =============================================================================
# ACTIVITIES (Timeline)
# =============================================================================


def _activity_to_response(activity: Activity) -> ActivityResponse:
    """Convertit Activity entity en ActivityResponse schema."""
    return ActivityResponse(
        id=activity.id,
        contact_id=activity.contact_id,
        type=activity.type,
        title=activity.title,
        description=activity.description,
        extra_data=activity.extra_data,
        created_at=activity.created_at.isoformat(),
    )


@router.get("/activities", response_model=list[ActivityResponse])
async def list_activities(
    contact_id: Optional[str] = Query(None, description="Filtrer par contact"),
    type: Optional[str] = Query(None, description="Filtrer par type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    """
    Liste les activités avec pagination et filtres.
    """
    statement = select(Activity)

    # Filtres
    if contact_id:
        statement = statement.where(Activity.contact_id == contact_id)
    if type:
        statement = statement.where(Activity.type == type)

    # Ordre anti-chronologique
    statement = statement.order_by(Activity.created_at.desc())

    # Pagination
    statement = statement.offset(skip).limit(limit)

    activities = session.exec(statement).all()

    return [_activity_to_response(activity) for activity in activities]


@router.post("/activities", response_model=ActivityResponse)
async def create_activity(
    request: CreateActivityRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Crée une nouvelle activité dans la timeline.
    """
    # Vérifier que le contact existe
    contact = session.get(Contact, request.contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    # Créer l'activité
    activity = Activity(
        contact_id=request.contact_id,
        type=request.type,
        title=request.title,
        description=request.description,
        extra_data=request.extra_data,
    )

    session.add(activity)

    # Mettre à jour last_interaction du contact
    contact.last_interaction = datetime.utcnow()
    contact.updated_at = datetime.utcnow()
    session.add(contact)

    # Recalculer le score (interaction = points)
    if request.type in ["email", "call", "meeting"]:
        update_contact_score(session, contact, reason=f"interaction_{request.type}")

    session.commit()
    session.refresh(activity)

    logger.info(f"Activity created: {activity.id} for contact {contact.id}")

    return _activity_to_response(activity)


@router.delete("/activities/{activity_id}")
async def delete_activity(
    activity_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Supprime une activité.
    """
    activity = session.get(Activity, activity_id)

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    session.delete(activity)
    session.commit()

    logger.info(f"Activity deleted: {activity_id}")

    return {"message": "Activity deleted successfully"}


# =============================================================================
# DELIVERABLES (Livrables)
# =============================================================================


def _deliverable_to_response(deliverable: Deliverable) -> DeliverableResponse:
    """Convertit Deliverable entity en DeliverableResponse schema."""
    return DeliverableResponse(
        id=deliverable.id,
        project_id=deliverable.project_id,
        title=deliverable.title,
        description=deliverable.description,
        status=deliverable.status,
        due_date=deliverable.due_date.isoformat() if deliverable.due_date else None,
        completed_at=deliverable.completed_at.isoformat() if deliverable.completed_at else None,
        created_at=deliverable.created_at.isoformat(),
        updated_at=deliverable.updated_at.isoformat(),
    )


@router.get("/deliverables", response_model=list[DeliverableResponse])
async def list_deliverables(
    project_id: Optional[str] = Query(None, description="Filtrer par projet"),
    status: Optional[str] = Query(None, description="Filtrer par status"),
    session: AsyncSession = Depends(get_session),
):
    """
    Liste les livrables avec filtres.
    """
    statement = select(Deliverable)

    # Filtres
    if project_id:
        statement = statement.where(Deliverable.project_id == project_id)
    if status:
        statement = statement.where(Deliverable.status == status)

    # Ordre par création
    statement = statement.order_by(Deliverable.created_at.desc())

    deliverables = session.exec(statement).all()

    return [_deliverable_to_response(d) for d in deliverables]


@router.post("/deliverables", response_model=DeliverableResponse)
async def create_deliverable(
    request: CreateDeliverableRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Crée un nouveau livrable.
    """
    # Vérifier que le projet existe
    project = session.get(Project, request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Parser due_date si fournie
    due_date = None
    if request.due_date:
        due_date = datetime.fromisoformat(request.due_date.replace("Z", ""))

    # Créer le livrable
    deliverable = Deliverable(
        project_id=request.project_id,
        title=request.title,
        description=request.description,
        status=request.status,
        due_date=due_date,
    )

    session.add(deliverable)
    session.commit()
    session.refresh(deliverable)

    logger.info(f"Deliverable created: {deliverable.id} for project {project.id}")

    return _deliverable_to_response(deliverable)


@router.put("/deliverables/{deliverable_id}", response_model=DeliverableResponse)
async def update_deliverable(
    deliverable_id: str,
    request: UpdateDeliverableRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Met à jour un livrable.
    """
    deliverable = session.get(Deliverable, deliverable_id)

    if not deliverable:
        raise HTTPException(status_code=404, detail="Deliverable not found")

    # Mise à jour des champs
    if request.title is not None:
        deliverable.title = request.title

    if request.description is not None:
        deliverable.description = request.description

    if request.status is not None:
        deliverable.status = request.status

        # Auto-remplir completed_at si validé
        if request.status == "valide" and deliverable.completed_at is None:
            deliverable.completed_at = datetime.utcnow()

    if request.due_date is not None:
        deliverable.due_date = datetime.fromisoformat(request.due_date.replace("Z", ""))

    deliverable.updated_at = datetime.utcnow()

    session.add(deliverable)
    session.commit()
    session.refresh(deliverable)

    logger.info(f"Deliverable updated: {deliverable_id}")

    return _deliverable_to_response(deliverable)


@router.delete("/deliverables/{deliverable_id}")
async def delete_deliverable(
    deliverable_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Supprime un livrable.
    """
    deliverable = session.get(Deliverable, deliverable_id)

    if not deliverable:
        raise HTTPException(status_code=404, detail="Deliverable not found")

    session.delete(deliverable)
    session.commit()

    logger.info(f"Deliverable deleted: {deliverable_id}")

    return {"message": "Deliverable deleted successfully"}


# =============================================================================
# PIPELINE (Stages & Scoring)
# =============================================================================


@router.patch("/contacts/{contact_id}/stage", response_model=ContactResponse)
async def update_contact_stage(
    contact_id: str,
    request: UpdateContactStageRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Change le stage d'un contact dans le pipeline.

    Crée automatiquement une activité et recalcule le score.
    """
    contact = session.get(Contact, contact_id)

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    old_stage = contact.stage
    new_stage = request.stage

    # Mettre à jour le stage
    contact.stage = new_stage
    contact.updated_at = datetime.utcnow()
    contact.last_interaction = datetime.utcnow()
    session.add(contact)

    # Créer une activité
    activity = Activity(
        contact_id=contact.id,
        type="stage_change",
        title=f"Stage: {old_stage} → {new_stage}",
        description=f"Changement de stage dans le pipeline commercial",
        extra_data=f'{{"old_stage": "{old_stage}", "new_stage": "{new_stage}"}}',
    )
    session.add(activity)

    # Recalculer le score
    update_contact_score(session, contact, reason=f"stage_change_{new_stage}")

    session.commit()
    session.refresh(contact)

    logger.info(f"Contact {contact_id} stage updated: {old_stage} → {new_stage}")

    # Retourner le contact avec le format ContactResponse
    from app.routers.memory import _contact_to_response
    return _contact_to_response(contact)


@router.post("/contacts/{contact_id}/recalculate-score", response_model=ContactScoreUpdate)
async def recalculate_contact_score(
    contact_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Recalcule manuellement le score d'un contact.
    """
    contact = session.get(Contact, contact_id)

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    result = update_contact_score(session, contact, reason="manual_recalculation")

    session.commit()

    return ContactScoreUpdate(**result)


@router.get("/pipeline/stats")
async def get_pipeline_stats(
    session: AsyncSession = Depends(get_session),
):
    """
    Retourne des statistiques sur le pipeline commercial.

    - Nombre de contacts par stage
    - Score moyen par stage
    - Taux de conversion
    """
    # Compter contacts par stage
    stages_count_statement = (
        select(Contact.stage, func.count(Contact.id))
        .group_by(Contact.stage)
    )
    stages_count = session.exec(stages_count_statement).all()

    # Score moyen par stage
    stages_avg_score_statement = (
        select(Contact.stage, func.avg(Contact.score))
        .group_by(Contact.stage)
    )
    stages_avg_score = session.exec(stages_avg_score_statement).all()

    # Total contacts
    total_contacts = session.exec(select(func.count(Contact.id))).one()

    # Construire la réponse
    stages_data = {}

    for stage, count in stages_count:
        stages_data[stage] = {"count": count}

    for stage, avg_score in stages_avg_score:
        if stage in stages_data:
            stages_data[stage]["avg_score"] = float(avg_score) if avg_score else 0.0

    return {
        "total_contacts": total_contacts,
        "stages": stages_data,
    }


# =============================================================================
# CRM EXPORT (Local First)
# =============================================================================


@router.post("/export/contacts")
async def export_contacts(
    format: ExportFormat = Query("csv", description="Format d'export (csv, xlsx, json)"),
    stage: Optional[str] = Query(None, description="Filtrer par stage"),
    source: Optional[str] = Query(None, description="Filtrer par source"),
    session: AsyncSession = Depends(get_session),
):
    """
    Exporte les contacts au format CSV, Excel ou JSON.

    Retourne le fichier directement (download).
    """
    export_service = CRMExportService(session)
    result = await export_service.export_contacts(format=format, stage=stage, source=source)

    logger.info(f"Exported {result.row_count} contacts to {format}")

    return Response(
        content=result.data,
        media_type=result.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"',
            "X-Row-Count": str(result.row_count),
        },
    )


@router.post("/export/projects")
async def export_projects(
    format: ExportFormat = Query("csv", description="Format d'export (csv, xlsx, json)"),
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    contact_id: Optional[str] = Query(None, description="Filtrer par contact"),
    session: AsyncSession = Depends(get_session),
):
    """
    Exporte les projets au format CSV, Excel ou JSON.

    Retourne le fichier directement (download).
    """
    export_service = CRMExportService(session)
    result = await export_service.export_projects(format=format, status=status, contact_id=contact_id)

    logger.info(f"Exported {result.row_count} projects to {format}")

    return Response(
        content=result.data,
        media_type=result.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"',
            "X-Row-Count": str(result.row_count),
        },
    )


@router.post("/export/deliverables")
async def export_deliverables(
    format: ExportFormat = Query("csv", description="Format d'export (csv, xlsx, json)"),
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    project_id: Optional[str] = Query(None, description="Filtrer par projet"),
    session: AsyncSession = Depends(get_session),
):
    """
    Exporte les livrables au format CSV, Excel ou JSON.

    Retourne le fichier directement (download).
    """
    export_service = CRMExportService(session)
    result = await export_service.export_deliverables(format=format, status=status, project_id=project_id)

    logger.info(f"Exported {result.row_count} deliverables to {format}")

    return Response(
        content=result.data,
        media_type=result.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"',
            "X-Row-Count": str(result.row_count),
        },
    )


@router.post("/export/all")
async def export_all_crm(
    format: ExportFormat = Query("xlsx", description="Format d'export (csv, xlsx, json)"),
    session: AsyncSession = Depends(get_session),
):
    """
    Exporte toutes les donnees CRM (contacts, projets, livrables).

    Pour Excel: cree plusieurs onglets.
    Pour JSON: structure imbriquee.
    Pour CSV: contacts uniquement (utiliser les endpoints individuels pour les autres).
    """
    export_service = CRMExportService(session)
    result = await export_service.export_all(format=format)

    logger.info(f"Exported all CRM data ({result.row_count} total rows) to {format}")

    return Response(
        content=result.data,
        media_type=result.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"',
            "X-Row-Count": str(result.row_count),
        },
    )


# =============================================================================
# CRM IMPORT (Local First)
# =============================================================================


@router.post("/import/contacts/preview", response_model=CRMImportPreviewSchema)
async def preview_contacts_import(
    file: UploadFile = File(..., description="Fichier CSV, Excel ou JSON"),
    session: AsyncSession = Depends(get_session),
):
    """
    Preview d'import de contacts sans execution.

    Retourne un apercu des donnees et les erreurs de validation.
    """
    content = await file.read()
    import_service = CRMImportService(session)
    preview = await import_service.preview_contacts(content, filename=file.filename)

    return CRMImportPreviewSchema(
        total_rows=preview.total_rows,
        sample_rows=preview.sample_rows,
        detected_columns=preview.detected_columns,
        column_mapping=preview.column_mapping,
        validation_errors=[
            CRMImportErrorSchema(
                row=e.row,
                column=e.column,
                message=e.message,
                data=e.data,
            )
            for e in preview.validation_errors
        ],
        can_import=preview.can_import,
    )


@router.post("/import/contacts", response_model=CRMImportResultSchema)
async def import_contacts(
    file: UploadFile = File(..., description="Fichier CSV, Excel ou JSON"),
    update_existing: bool = Query(True, description="Mettre a jour les contacts existants"),
    session: AsyncSession = Depends(get_session),
):
    """
    Importe des contacts depuis un fichier CSV, Excel ou JSON.

    Supporte le mapping automatique des colonnes en francais et anglais.
    """
    content = await file.read()
    import_service = CRMImportService(session)
    result = await import_service.import_contacts(
        content,
        filename=file.filename,
        update_existing=update_existing,
    )

    logger.info(f"Contacts import: {result.message}")

    return CRMImportResultSchema(
        success=result.success,
        created=result.created,
        updated=result.updated,
        skipped=result.skipped,
        errors=[
            CRMImportErrorSchema(
                row=e.row,
                column=e.column,
                message=e.message,
                data=e.data,
            )
            for e in result.errors
        ],
        total_rows=result.total_rows,
        message=result.message,
    )


@router.post("/import/projects", response_model=CRMImportResultSchema)
async def import_projects(
    file: UploadFile = File(..., description="Fichier CSV, Excel ou JSON"),
    update_existing: bool = Query(True, description="Mettre a jour les projets existants"),
    session: AsyncSession = Depends(get_session),
):
    """
    Importe des projets depuis un fichier CSV, Excel ou JSON.

    Supporte le mapping automatique des colonnes en francais et anglais.
    """
    content = await file.read()
    import_service = CRMImportService(session)
    result = await import_service.import_projects(
        content,
        filename=file.filename,
        update_existing=update_existing,
    )

    logger.info(f"Projects import: {result.message}")

    return CRMImportResultSchema(
        success=result.success,
        created=result.created,
        updated=result.updated,
        skipped=result.skipped,
        errors=[
            CRMImportErrorSchema(
                row=e.row,
                column=e.column,
                message=e.message,
                data=e.data,
            )
            for e in result.errors
        ],
        total_rows=result.total_rows,
        message=result.message,
    )


@router.post("/import/deliverables", response_model=CRMImportResultSchema)
async def import_deliverables(
    file: UploadFile = File(..., description="Fichier CSV, Excel ou JSON"),
    update_existing: bool = Query(True, description="Mettre a jour les livrables existants"),
    session: AsyncSession = Depends(get_session),
):
    """
    Importe des livrables depuis un fichier CSV, Excel ou JSON.

    Supporte le mapping automatique des colonnes en francais et anglais.
    """
    content = await file.read()
    import_service = CRMImportService(session)
    result = await import_service.import_deliverables(
        content,
        filename=file.filename,
        update_existing=update_existing,
    )

    logger.info(f"Deliverables import: {result.message}")

    return CRMImportResultSchema(
        success=result.success,
        created=result.created,
        updated=result.updated,
        skipped=result.skipped,
        errors=[
            CRMImportErrorSchema(
                row=e.row,
                column=e.column,
                message=e.message,
                data=e.data,
            )
            for e in result.errors
        ],
        total_rows=result.total_rows,
        message=result.message,
    )


# =============================================================================
# CRM SYNC (Google Sheets - Connecteur Optionnel)
# =============================================================================


@router.get("/sync/config", response_model=CRMSyncConfigResponse)
async def get_sync_config(
    session: AsyncSession = Depends(get_session),
):
    """
    Récupère la configuration de synchronisation CRM.
    """
    # Get spreadsheet ID
    result = await session.execute(
        select(Preference).where(Preference.key == "crm_spreadsheet_id")
    )
    spreadsheet_pref = result.scalar_one_or_none()
    spreadsheet_id = spreadsheet_pref.value if spreadsheet_pref else None

    # Get last sync time
    result = await session.execute(
        select(Preference).where(Preference.key == "crm_last_sync")
    )
    last_sync_pref = result.scalar_one_or_none()
    last_sync = last_sync_pref.value if last_sync_pref else None

    # Check if token exists
    result = await session.execute(
        select(Preference).where(Preference.key == "crm_sheets_access_token")
    )
    token_pref = result.scalar_one_or_none()
    has_token = token_pref is not None and bool(token_pref.value)

    return CRMSyncConfigResponse(
        spreadsheet_id=spreadsheet_id,
        last_sync=last_sync,
        has_token=has_token,
        configured=bool(spreadsheet_id and has_token),
    )


@router.post("/sync/config", response_model=CRMSyncConfigResponse)
async def set_sync_config(
    request: CRMSyncConfigRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Configure le spreadsheet ID pour la synchronisation CRM.
    """
    # Validate spreadsheet ID format
    spreadsheet_id = request.spreadsheet_id.strip()
    if not spreadsheet_id:
        raise HTTPException(status_code=400, detail="Spreadsheet ID cannot be empty")

    # Upsert spreadsheet ID preference
    result = await session.execute(
        select(Preference).where(Preference.key == "crm_spreadsheet_id")
    )
    pref = result.scalar_one_or_none()

    if pref:
        pref.value = spreadsheet_id
        pref.updated_at = datetime.utcnow()
    else:
        pref = Preference(
            key="crm_spreadsheet_id",
            value=spreadsheet_id,
            category="crm",
        )
        session.add(pref)

    await session.commit()

    logger.info(f"CRM sync configured with spreadsheet: {spreadsheet_id[:20]}...")

    # Return updated config
    return await get_sync_config(session)


@router.post("/sync/connect")
async def initiate_sheets_oauth(
    session: AsyncSession = Depends(get_session),
):
    """
    Lance le flux OAuth pour connecter Google Sheets.

    Retourne l'URL d'autorisation à ouvrir dans le navigateur.
    Recherche les credentials Google dans :
    1. Serveur MCP Google Workspace configuré
    2. Préférences stockées
    """
    from app.services.mcp_service import get_mcp_service
    from app.services.encryption import decrypt_value

    client_id = None
    client_secret = None

    # Try to get credentials from MCP Google Workspace server
    try:
        mcp_service = get_mcp_service()
        for server in mcp_service.list_servers():
            if server.get("name", "").lower() in ["google-workspace", "google workspace"]:
                env_vars = server.get("env", {})
                cid = env_vars.get("GOOGLE_OAUTH_CLIENT_ID")
                csecret = env_vars.get("GOOGLE_OAUTH_CLIENT_SECRET")

                # Decrypt credentials (they are stored encrypted)
                if cid:
                    try:
                        cid = decrypt_value(cid)
                    except Exception:
                        pass  # May not be encrypted
                if csecret:
                    try:
                        csecret = decrypt_value(csecret)
                    except Exception:
                        pass

                if cid and csecret:
                    client_id = cid
                    client_secret = csecret
                    logger.info("Using Google credentials from MCP server")
                    break
    except Exception as e:
        logger.warning(f"Could not get credentials from MCP: {e}")

    # Fallback to preferences
    if not client_id or not client_secret:
        result = await session.execute(
            select(Preference).where(Preference.key == "google_client_id")
        )
        client_id_pref = result.scalar_one_or_none()

        result = await session.execute(
            select(Preference).where(Preference.key == "google_client_secret")
        )
        client_secret_pref = result.scalar_one_or_none()

        if client_id_pref and client_secret_pref:
            try:
                client_id = decrypt_value(client_id_pref.value)
                client_secret = decrypt_value(client_secret_pref.value)
                logger.info("Using Google credentials from preferences")
            except Exception:
                pass

    if not client_id or not client_secret:
        raise HTTPException(
            status_code=400,
            detail="Google OAuth credentials not found. Please configure the Google Workspace MCP server or add credentials in Settings."
        )

    config = OAuthConfig(
        client_id=client_id,
        client_secret=client_secret,
        auth_url=GOOGLE_AUTH_URL,
        token_url=GOOGLE_TOKEN_URL,
        scopes=GSHEETS_SCOPES,
        redirect_uri="http://localhost:8000/api/crm/sync/callback",
    )

    oauth_service = get_oauth_service()
    result = oauth_service.initiate_flow("gsheets", config)

    return {
        "auth_url": result["auth_url"],
        "state": result["state"],
        "message": "Ouvrez cette URL dans votre navigateur pour autoriser l'accès à Google Sheets",
    }


@router.get("/sync/callback")
async def handle_sheets_oauth_callback(
    state: str,
    code: Optional[str] = None,
    error: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """
    Callback OAuth pour Google Sheets.
    """
    oauth_service = get_oauth_service()

    tokens = await oauth_service.handle_callback(state, code, error)

    # Store tokens (Sprint 2 - PERF-2.4: await async function)
    from app.services.crm_sync import set_crm_tokens
    await set_crm_tokens(
        session,
        tokens["access_token"],
        tokens.get("refresh_token"),
    )

    return {
        "success": True,
        "message": "Google Sheets connecté avec succès",
    }


@router.post("/sync", response_model=CRMSyncResponse)
async def sync_crm(
    session: AsyncSession = Depends(get_session),
):
    """
    Lance la synchronisation CRM depuis Google Sheets.

    Synchronise: Clients -> Contacts, Projects, Deliverables.

    Modes d'authentification (par ordre de priorité):
    1. Token OAuth CRM dédié
    2. Clé API Gemini (fallback pour spreadsheets accessibles)
    """
    from app.services.sheets_service import GoogleSheetsService
    from app.services.encryption import decrypt_value

    # Get spreadsheet ID
    result = await session.execute(
        select(Preference).where(Preference.key == "crm_spreadsheet_id")
    )
    spreadsheet_pref = result.scalar_one_or_none()

    if not spreadsheet_pref or not spreadsheet_pref.value:
        raise HTTPException(
            status_code=400,
            detail="Spreadsheet ID non configuré. Utilisez POST /api/crm/sync/config d'abord."
        )

    spreadsheet_id = spreadsheet_pref.value

    access_token = None
    api_key = None

    # Try OAuth token first
    result = await session.execute(
        select(Preference).where(Preference.key == "crm_sheets_access_token")
    )
    token_pref = result.scalar_one_or_none()
    if token_pref and token_pref.value:
        try:
            access_token = decrypt_value(token_pref.value)
            logger.info("Using OAuth token for CRM sync")
        except Exception:
            pass

    # Try Gemini API key as fallback
    if not access_token:
        result = await session.execute(
            select(Preference).where(Preference.key == "gemini_api_key")
        )
        gemini_pref = result.scalar_one_or_none()
        if gemini_pref and gemini_pref.value:
            try:
                api_key = decrypt_value(gemini_pref.value)
                logger.info("Using Gemini API key for CRM sync")
            except Exception:
                api_key = gemini_pref.value

    if not access_token and not api_key:
        raise HTTPException(
            status_code=401,
            detail="Aucune authentification disponible. Connectez Google Sheets (OAuth) ou configurez une clé API Gemini."
        )

    # Create sheets service
    try:
        sheets_service = GoogleSheetsService(access_token=access_token, api_key=api_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Run sync
    stats = {
        "contacts_created": 0,
        "contacts_updated": 0,
        "projects_created": 0,
        "projects_updated": 0,
        "deliverables_created": 0,
        "deliverables_updated": 0,
        "tasks_created": 0,
        "tasks_updated": 0,
        "errors": [],
    }

    try:
        # Sync Clients
        try:
            clients_data = await sheets_service.get_all_data_as_dicts(spreadsheet_id, "Clients")
            logger.info(f"Found {len(clients_data)} clients in Google Sheets")

            for row in clients_data:
                try:
                    crm_id = row.get("ID", "").strip()
                    if not crm_id:
                        continue

                    # Check if contact exists
                    result = await session.execute(
                        select(Contact).where(Contact.id == crm_id)
                    )
                    existing = result.scalar_one_or_none()

                    # Parse name
                    full_name = row.get("Nom", "").strip()
                    parts = full_name.split(" ", 1)
                    first_name = parts[0] if parts else ""
                    last_name = parts[1] if len(parts) > 1 else None

                    # Parse score
                    score_str = row.get("Score", "50").strip()
                    try:
                        score = int(float(score_str)) if score_str else 50
                    except ValueError:
                        score = 50

                    # Parse tags
                    tags_str = row.get("Tags", "").strip()
                    import json
                    tags_json = json.dumps(tags_str.split(",")) if tags_str else None

                    if existing:
                        existing.first_name = first_name
                        existing.last_name = last_name
                        existing.company = row.get("Entreprise", "").strip() or None
                        existing.email = row.get("Email", "").strip() or None
                        existing.phone = row.get("Tel", "").strip() or None
                        existing.source = row.get("Source", "").strip() or None
                        existing.stage = row.get("Stage", "contact").strip() or "contact"
                        existing.score = score
                        existing.tags = tags_json
                        existing.updated_at = datetime.utcnow()
                        stats["contacts_updated"] += 1
                    else:
                        contact = Contact(
                            id=crm_id,
                            first_name=first_name,
                            last_name=last_name,
                            company=row.get("Entreprise", "").strip() or None,
                            email=row.get("Email", "").strip() or None,
                            phone=row.get("Tel", "").strip() or None,
                            source=row.get("Source", "").strip() or None,
                            stage=row.get("Stage", "contact").strip() or "contact",
                            score=score,
                            tags=tags_json,
                            scope="global",
                        )
                        session.add(contact)
                        stats["contacts_created"] += 1

                except Exception as e:
                    logger.error(f"Error syncing contact {row.get('ID', 'unknown')}: {e}")
                    stats["errors"].append(f"Contact {row.get('ID', 'unknown')}: {str(e)}")

        except Exception as e:
            logger.error(f"Error syncing clients: {e}")
            stats["errors"].append(f"Clients: {str(e)}")

        # Sync Projects
        try:
            projects_data = await sheets_service.get_all_data_as_dicts(spreadsheet_id, "Projects")
            logger.info(f"Found {len(projects_data)} projects in Google Sheets")

            status_map = {
                "en_cours": "active",
                "en_pause": "on_hold",
                "termine": "completed",
                "annule": "cancelled",
            }

            for row in projects_data:
                try:
                    project_id = row.get("ID", "").strip()
                    if not project_id:
                        continue

                    result = await session.execute(
                        select(Project).where(Project.id == project_id)
                    )
                    existing = result.scalar_one_or_none()

                    client_id = row.get("ClientID", "").strip() or None
                    raw_status = row.get("Status", "active").strip().lower()
                    status = status_map.get(raw_status, raw_status)
                    if status not in ["active", "completed", "on_hold", "cancelled"]:
                        status = "active"

                    budget_str = row.get("Budget", "").strip()
                    try:
                        budget = float(budget_str) if budget_str else None
                    except ValueError:
                        budget = None

                    if existing:
                        existing.name = row.get("Name", "Sans nom").strip()
                        existing.description = row.get("Description", "").strip() or None
                        existing.contact_id = client_id
                        existing.status = status
                        existing.budget = budget
                        existing.notes = row.get("Notes", "").strip() or None
                        existing.updated_at = datetime.utcnow()
                        stats["projects_updated"] += 1
                    else:
                        project = Project(
                            id=project_id,
                            name=row.get("Name", "Sans nom").strip(),
                            description=row.get("Description", "").strip() or None,
                            contact_id=client_id,
                            status=status,
                            budget=budget,
                            notes=row.get("Notes", "").strip() or None,
                            scope="global",
                        )
                        session.add(project)
                        stats["projects_created"] += 1

                except Exception as e:
                    logger.error(f"Error syncing project {row.get('ID', 'unknown')}: {e}")
                    stats["errors"].append(f"Project {row.get('ID', 'unknown')}: {str(e)}")

        except Exception as e:
            logger.error(f"Error syncing projects: {e}")
            stats["errors"].append(f"Projects: {str(e)}")

        # Sync Tasks
        try:
            tasks_data = await sheets_service.get_all_data_as_dicts(spreadsheet_id, "Tasks")
            logger.info(f"Found {len(tasks_data)} tasks in Google Sheets")

            priority_map = {
                "normal": "medium", "urgent": "urgent",
                "low": "low", "high": "high", "medium": "medium",
            }

            for row in tasks_data:
                try:
                    task_id = row.get("ID", "").strip()
                    if not task_id:
                        continue

                    existing = await session.get(Task, task_id)

                    raw_priority = row.get("Priority", "medium").strip().lower()
                    priority = priority_map.get(raw_priority, "medium")

                    raw_status = row.get("Status", "todo").strip().lower()
                    if raw_status not in ("todo", "in_progress", "done", "cancelled"):
                        raw_status = "todo"

                    # Parse dates
                    due_date = _parse_dt(row.get("DueDate", ""))
                    created_at = _parse_dt(row.get("CreatedAt", ""))
                    completed_at = _parse_dt(row.get("CompletedAt", ""))

                    if existing:
                        existing.title = row.get("Title", "Sans titre").strip()
                        existing.description = row.get("Description", "").strip() or None
                        existing.priority = priority
                        existing.status = raw_status
                        existing.due_date = due_date
                        existing.completed_at = completed_at
                        existing.updated_at = datetime.utcnow()
                        stats["tasks_updated"] += 1
                    else:
                        task = Task(
                            id=task_id,
                            title=row.get("Title", "Sans titre").strip(),
                            description=row.get("Description", "").strip() or None,
                            priority=priority,
                            status=raw_status,
                            due_date=due_date,
                            completed_at=completed_at,
                            created_at=created_at or datetime.utcnow(),
                        )
                        session.add(task)
                        stats["tasks_created"] += 1

                except Exception as e:
                    logger.error(f"Error syncing task {row.get('ID', 'unknown')}: {e}")
                    stats["errors"].append(f"Task {row.get('ID', 'unknown')}: {str(e)}")

        except Exception as e:
            logger.error(f"Error syncing tasks: {e}")
            stats["errors"].append(f"Tasks: {str(e)}")

        await session.commit()

        # Update last sync time
        result = await session.execute(
            select(Preference).where(Preference.key == "crm_last_sync")
        )
        last_sync_pref = result.scalar_one_or_none()
        now = datetime.utcnow().isoformat()

        if last_sync_pref:
            last_sync_pref.value = now
            last_sync_pref.updated_at = datetime.utcnow()
        else:
            last_sync_pref = Preference(key="crm_last_sync", value=now, category="crm")
            session.add(last_sync_pref)

        await session.commit()

        total_synced = (
            stats["contacts_created"] + stats["contacts_updated"] +
            stats["projects_created"] + stats["projects_updated"] +
            stats["deliverables_created"] + stats["deliverables_updated"] +
            stats["tasks_created"] + stats["tasks_updated"]
        )

        return CRMSyncResponse(
            success=len(stats["errors"]) == 0,
            message=f"Synchronisation terminée: {total_synced} éléments",
            stats=CRMSyncStatsResponse(**stats, total_synced=total_synced),
            sync_time=now,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CRM sync failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de synchronisation: {str(e)}"
        )


@router.post("/sync/import", response_model=CRMSyncResponse)
async def import_crm_data(
    clients: list[dict] | None = None,
    projects: list[dict] | None = None,
    deliverables: list[dict] | None = None,
    tasks: list[dict] | None = None,
    session: AsyncSession = Depends(get_session),
):
    """
    Importe les données CRM directement (sans passer par Google Sheets API).

    Utilisé quand l'accès OAuth/API n'est pas disponible mais qu'on a les données
    via d'autres moyens (ex: MCP Claude Code).

    Body JSON:
    {
        "clients": [{"ID": "...", "Nom": "...", ...}],
        "projects": [{"ID": "...", "Name": "...", ...}],
        "deliverables": [{"ID": "...", "Title": "...", ...}],
        "tasks": [{"ID": "...", "Title": "...", ...}]
    }
    """
    import json

    stats = {
        "contacts_created": 0,
        "contacts_updated": 0,
        "projects_created": 0,
        "projects_updated": 0,
        "deliverables_created": 0,
        "deliverables_updated": 0,
        "tasks_created": 0,
        "tasks_updated": 0,
        "errors": [],
    }

    # Import Clients
    if clients:
        logger.info(f"Importing {len(clients)} clients")
        for row in clients:
            try:
                crm_id = row.get("ID", "").strip()
                if not crm_id:
                    continue

                result = await session.execute(
                    select(Contact).where(Contact.id == crm_id)
                )
                existing = result.scalar_one_or_none()

                # Parse name
                full_name = row.get("Nom", "").strip()
                parts = full_name.split(" ", 1)
                first_name = parts[0] if parts else ""
                last_name = parts[1] if len(parts) > 1 else None

                # Parse score
                score_str = row.get("Score", "50")
                if isinstance(score_str, str):
                    score_str = score_str.strip()
                try:
                    score = int(float(score_str)) if score_str else 50
                except (ValueError, TypeError):
                    score = 50

                # Parse tags
                tags_str = row.get("Tags", "")
                if isinstance(tags_str, str):
                    tags_str = tags_str.strip()
                tags_json = json.dumps(tags_str.split(",")) if tags_str else None

                if existing:
                    existing.first_name = first_name
                    existing.last_name = last_name
                    existing.company = (row.get("Entreprise", "") or "").strip() or None
                    existing.email = (row.get("Email", "") or "").strip() or None
                    existing.phone = (row.get("Tel", "") or "").strip() or None
                    existing.source = (row.get("Source", "") or "").strip() or None
                    existing.stage = (row.get("Stage", "contact") or "contact").strip()
                    existing.score = score
                    existing.tags = tags_json
                    existing.updated_at = datetime.utcnow()
                    stats["contacts_updated"] += 1
                else:
                    contact = Contact(
                        id=crm_id,
                        first_name=first_name,
                        last_name=last_name,
                        company=(row.get("Entreprise", "") or "").strip() or None,
                        email=(row.get("Email", "") or "").strip() or None,
                        phone=(row.get("Tel", "") or "").strip() or None,
                        source=(row.get("Source", "") or "").strip() or None,
                        stage=(row.get("Stage", "contact") or "contact").strip(),
                        score=score,
                        tags=tags_json,
                        scope="global",
                    )
                    session.add(contact)
                    stats["contacts_created"] += 1

            except Exception as e:
                logger.error(f"Error importing contact {row.get('ID', 'unknown')}: {e}")
                stats["errors"].append(f"Contact {row.get('ID', 'unknown')}: {str(e)}")

    # Import Projects
    if projects:
        logger.info(f"Importing {len(projects)} projects")
        status_map = {
            "en_cours": "active",
            "en_pause": "on_hold",
            "termine": "completed",
            "annule": "cancelled",
            "en_attente": "on_hold",
            "livre": "completed",
            "planifie": "active",
        }

        for row in projects:
            try:
                project_id = row.get("ID", "").strip()
                if not project_id:
                    continue

                result = await session.execute(
                    select(Project).where(Project.id == project_id)
                )
                existing = result.scalar_one_or_none()

                client_id = (row.get("ClientID", "") or "").strip() or None
                raw_status = (row.get("Status", "active") or "active").strip().lower()
                status = status_map.get(raw_status, raw_status)
                if status not in ["active", "completed", "on_hold", "cancelled"]:
                    status = "active"

                budget_str = row.get("Budget", "")
                if isinstance(budget_str, str):
                    budget_str = budget_str.strip()
                try:
                    budget = float(budget_str) if budget_str else None
                except (ValueError, TypeError):
                    budget = None

                if existing:
                    existing.name = (row.get("Name", "Sans nom") or "Sans nom").strip()
                    existing.description = (row.get("Description", "") or "").strip() or None
                    existing.contact_id = client_id
                    existing.status = status
                    existing.budget = budget
                    existing.notes = (row.get("Notes", "") or "").strip() or None
                    existing.updated_at = datetime.utcnow()
                    stats["projects_updated"] += 1
                else:
                    project = Project(
                        id=project_id,
                        name=(row.get("Name", "Sans nom") or "Sans nom").strip(),
                        description=(row.get("Description", "") or "").strip() or None,
                        contact_id=client_id,
                        status=status,
                        budget=budget,
                        notes=(row.get("Notes", "") or "").strip() or None,
                        scope="global",
                    )
                    session.add(project)
                    stats["projects_created"] += 1

            except Exception as e:
                logger.error(f"Error importing project {row.get('ID', 'unknown')}: {e}")
                stats["errors"].append(f"Project {row.get('ID', 'unknown')}: {str(e)}")

    # Import Deliverables
    if deliverables:
        logger.info(f"Importing {len(deliverables)} deliverables")
        for row in deliverables:
            try:
                deliv_id = row.get("ID", "").strip()
                if not deliv_id:
                    continue

                result = await session.execute(
                    select(Deliverable).where(Deliverable.id == deliv_id)
                )
                existing = result.scalar_one_or_none()

                project_id = (row.get("ProjectID", "") or "").strip() or None
                raw_status = (row.get("Status", "pending") or "pending").strip().lower()
                status = raw_status if raw_status in ["pending", "in_progress", "completed", "blocked"] else "pending"

                if existing:
                    existing.title = (row.get("Title", "Sans titre") or "Sans titre").strip()
                    existing.description = (row.get("Description", "") or "").strip() or None
                    existing.project_id = project_id
                    existing.status = status
                    existing.updated_at = datetime.utcnow()
                    stats["deliverables_updated"] += 1
                else:
                    deliverable = Deliverable(
                        id=deliv_id,
                        title=(row.get("Title", "Sans titre") or "Sans titre").strip(),
                        description=(row.get("Description", "") or "").strip() or None,
                        project_id=project_id,
                        status=status,
                    )
                    session.add(deliverable)
                    stats["deliverables_created"] += 1

            except Exception as e:
                logger.error(f"Error importing deliverable {row.get('ID', 'unknown')}: {e}")
                stats["errors"].append(f"Deliverable {row.get('ID', 'unknown')}: {str(e)}")

    # Import Tasks
    if tasks:
        logger.info(f"Importing {len(tasks)} tasks")
        priority_map = {
            "normal": "medium",
            "urgent": "urgent",
            "low": "low",
            "high": "high",
            "medium": "medium",
        }

        for row in tasks:
            try:
                task_id = (row.get("ID", "") or "").strip()
                if not task_id:
                    continue

                result = await session.execute(
                    select(Task).where(Task.id == task_id)
                )
                existing = result.scalar_one_or_none()

                raw_priority = (row.get("Priority", "medium") or "medium").strip().lower()
                priority = priority_map.get(raw_priority, "medium")

                raw_status = (row.get("Status", "todo") or "todo").strip().lower()
                if raw_status not in ("todo", "in_progress", "done", "cancelled"):
                    raw_status = "todo"

                # Parse dates
                due_date = None
                due_str = (row.get("DueDate", "") or "").strip()
                if due_str:
                    for fmt in ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"]:
                        try:
                            due_date = datetime.strptime(due_str, fmt)
                            break
                        except ValueError:
                            continue

                completed_at = None
                comp_str = (row.get("CompletedAt", "") or "").strip()
                if comp_str:
                    for fmt in ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
                        try:
                            completed_at = datetime.strptime(comp_str, fmt)
                            break
                        except ValueError:
                            continue

                created_at = None
                created_str = (row.get("CreatedAt", "") or "").strip()
                if created_str:
                    for fmt in ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
                        try:
                            created_at = datetime.strptime(created_str, fmt)
                            break
                        except ValueError:
                            continue

                if existing:
                    existing.title = (row.get("Title", "Sans titre") or "Sans titre").strip()
                    existing.description = (row.get("Description", "") or "").strip() or None
                    existing.priority = priority
                    existing.status = raw_status
                    existing.due_date = due_date
                    existing.completed_at = completed_at
                    existing.updated_at = datetime.utcnow()
                    stats["tasks_updated"] += 1
                else:
                    task = Task(
                        id=task_id,
                        title=(row.get("Title", "Sans titre") or "Sans titre").strip(),
                        description=(row.get("Description", "") or "").strip() or None,
                        priority=priority,
                        status=raw_status,
                        due_date=due_date,
                        completed_at=completed_at,
                        created_at=created_at or datetime.utcnow(),
                    )
                    session.add(task)
                    stats["tasks_created"] += 1

            except Exception as e:
                logger.error(f"Error importing task {row.get('ID', 'unknown')}: {e}")
                stats["errors"].append(f"Task {row.get('ID', 'unknown')}: {str(e)}")

    await session.commit()

    # Update last sync time
    result = await session.execute(
        select(Preference).where(Preference.key == "crm_last_sync")
    )
    last_sync_pref = result.scalar_one_or_none()
    now = datetime.utcnow().isoformat()

    if last_sync_pref:
        last_sync_pref.value = now
        last_sync_pref.updated_at = datetime.utcnow()
    else:
        last_sync_pref = Preference(key="crm_last_sync", value=now, category="crm")
        session.add(last_sync_pref)

    await session.commit()

    total_synced = (
        stats["contacts_created"] + stats["contacts_updated"] +
        stats["projects_created"] + stats["projects_updated"] +
        stats["deliverables_created"] + stats["deliverables_updated"] +
        stats["tasks_created"] + stats["tasks_updated"]
    )

    return CRMSyncResponse(
        success=len(stats["errors"]) == 0,
        message=f"Import terminé: {total_synced} éléments",
        stats=CRMSyncStatsResponse(**stats, total_synced=total_synced),
        sync_time=now,
    )
