"""
THERESE v2 - CRM Router

REST API pour les features CRM (pipeline, scoring, activites, livrables, sync Google Sheets).
Phase 5 - CRM Features + Local First Export/Import
"""

import logging
from datetime import UTC, datetime

from app.models.database import get_session
from app.models.entities import Activity, Contact, Deliverable, EmailAccount, Preference, Project
from app.models.schemas import (
    ActivityResponse,
    ContactResponse,
    ContactScoreUpdate,
    CreateActivityRequest,
    CreateCRMContactRequest,
    CreateDeliverableRequest,
    CRMImportErrorSchema,
    CRMImportPreviewSchema,
    CRMImportResultSchema,
    CRMSyncConfigRequest,
    CRMSyncConfigResponse,
    CRMSyncResponse,
    CRMSyncStatsResponse,
    DeliverableResponse,
    UpdateContactStageRequest,
    UpdateDeliverableRequest,
)
from app.services.crm_export import CRMExportService, ExportFormat
from app.services.crm_import import CRMImportService, _sanitize_field
from app.services.crm_utils import (
    compute_total_synced,
    new_sync_stats,
    update_last_sync_time,
    upsert_contact,
    upsert_deliverable_from_import,
    upsert_project,
    upsert_task,
)
from app.services.oauth import (
    GOOGLE_AUTH_URL,
    GOOGLE_TOKEN_URL,
    GSHEETS_SCOPES,
    RUNTIME_PORT,
    OAuthConfig,
    get_oauth_service,
)
from app.services.scoring import update_contact_score
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

logger = logging.getLogger(__name__)


def _sanitize_row(row: dict) -> dict:
    """Sanitize all string values in an import row (SEC-017)."""
    sanitized = {}
    for key, value in row.items():
        sanitized[key] = _sanitize_field(value, key.lower()) if isinstance(value, str) else value
    return sanitized


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
    contact_id: str | None = Query(None, description="Filtrer par contact"),
    type: str | None = Query(None, description="Filtrer par type"),
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

    result = await session.execute(statement)
    activities = result.scalars().all()

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
    contact = await session.get(Contact, request.contact_id)
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
    contact.last_interaction = datetime.now(UTC)
    contact.updated_at = datetime.now(UTC)
    session.add(contact)

    # Recalculer le score (interaction = points)
    if request.type in ["email", "call", "meeting"]:
        await update_contact_score(session, contact, reason=f"interaction_{request.type}")

    await session.commit()
    await session.refresh(activity)

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
    activity = await session.get(Activity, activity_id)

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    await session.delete(activity)
    await session.commit()

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
    project_id: str | None = Query(None, description="Filtrer par projet"),
    status: str | None = Query(None, description="Filtrer par status"),
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

    result = await session.execute(statement)
    deliverables = result.scalars().all()

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
    project = await session.get(Project, request.project_id)
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
    await session.commit()
    await session.refresh(deliverable)

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
    deliverable = await session.get(Deliverable, deliverable_id)

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
            deliverable.completed_at = datetime.now(UTC)

    if request.due_date is not None:
        deliverable.due_date = datetime.fromisoformat(request.due_date.replace("Z", ""))

    deliverable.updated_at = datetime.now(UTC)

    session.add(deliverable)
    await session.commit()
    await session.refresh(deliverable)

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
    deliverable = await session.get(Deliverable, deliverable_id)

    if not deliverable:
        raise HTTPException(status_code=404, detail="Deliverable not found")

    await session.delete(deliverable)
    await session.commit()

    logger.info(f"Deliverable deleted: {deliverable_id}")

    return {"message": "Deliverable deleted successfully"}


# =============================================================================
# CRM CONTACTS (Create with GSheets sync)
# =============================================================================


@router.post("/contacts", response_model=ContactResponse)
async def create_crm_contact(
    request: CreateCRMContactRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Cree un contact dans le CRM local et tente de l'ajouter au Google Sheets.

    Le contact est cree avec source='THERESE' s'il n'a pas de source explicite.
    Si la sync CRM est configuree (spreadsheet_id + OAuth token), une ligne est
    ajoutee dans la feuille "Clients" du Google Sheets.
    """
    import uuid

    source = request.source.strip() if request.source else "THERESE"

    contact = Contact(
        id=str(uuid.uuid4()),
        first_name=request.first_name.strip(),
        last_name=request.last_name.strip() if request.last_name else None,
        company=request.company.strip() if request.company else None,
        email=request.email.strip() if request.email else None,
        phone=request.phone.strip() if request.phone else None,
        source=source,
        stage=request.stage,
        score=50,
        scope="global",
    )
    session.add(contact)
    await session.commit()
    await session.refresh(contact)

    logger.info(f"CRM contact created: {contact.id} ({contact.first_name} {contact.last_name})")

    # Try to push to Google Sheets
    try:
        result = await session.execute(
            select(Preference).where(Preference.key == "crm_spreadsheet_id")
        )
        spreadsheet_pref = result.scalar_one_or_none()

        result = await session.execute(
            select(Preference).where(Preference.key == "crm_sheets_access_token")
        )
        token_pref = result.scalar_one_or_none()

        if spreadsheet_pref and spreadsheet_pref.value and token_pref and token_pref.value:
            from app.services.encryption import decrypt_value
            from app.services.sheets_service import GoogleSheetsService

            access_token = decrypt_value(token_pref.value)
            sheets = GoogleSheetsService(access_token=access_token)

            full_name = f"{contact.first_name or ''} {contact.last_name or ''}".strip()
            row_values = [
                contact.id,
                full_name,
                contact.company or "",
                contact.email or "",
                contact.phone or "",
                source,
                contact.stage,
                str(contact.score),
                "",  # Tags
            ]

            await sheets.append_row(spreadsheet_pref.value, "Clients", row_values)
            logger.info(f"Contact {contact.id} pushed to Google Sheets")
        else:
            logger.debug("CRM sync not configured, contact created locally only")

    except Exception as e:
        # Ne pas bloquer la creation si le push GSheets echoue
        logger.warning(f"Failed to push contact to Google Sheets: {e}")

    from app.routers.memory import _contact_to_response
    return _contact_to_response(contact)


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
    contact = await session.get(Contact, contact_id)

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    old_stage = contact.stage
    new_stage = request.stage

    # Mettre à jour le stage
    contact.stage = new_stage
    contact.updated_at = datetime.now(UTC)
    contact.last_interaction = datetime.now(UTC)
    session.add(contact)

    # Créer une activité
    activity = Activity(
        contact_id=contact.id,
        type="stage_change",
        title=f"Stage: {old_stage} -> {new_stage}",
        description="Changement de stage dans le pipeline commercial",
        extra_data=f'{{"old_stage": "{old_stage}", "new_stage": "{new_stage}"}}',
    )
    session.add(activity)

    # Recalculer le score
    await update_contact_score(session, contact, reason=f"stage_change_{new_stage}")

    await session.commit()
    await session.refresh(contact)

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
    contact = await session.get(Contact, contact_id)

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    result = await update_contact_score(session, contact, reason="manual_recalculation")

    await session.commit()

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
    result = await session.execute(stages_count_statement)
    stages_count = result.all()

    # Score moyen par stage
    stages_avg_score_statement = (
        select(Contact.stage, func.avg(Contact.score))
        .group_by(Contact.stage)
    )
    result = await session.execute(stages_avg_score_statement)
    stages_avg_score = result.all()

    # Total contacts
    result = await session.execute(select(func.count(Contact.id)))
    total_contacts = result.scalar_one()

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
    stage: str | None = Query(None, description="Filtrer par stage"),
    source: str | None = Query(None, description="Filtrer par source"),
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
    status: str | None = Query(None, description="Filtrer par statut"),
    contact_id: str | None = Query(None, description="Filtrer par contact"),
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
    status: str | None = Query(None, description="Filtrer par statut"),
    project_id: str | None = Query(None, description="Filtrer par projet"),
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
        pref.updated_at = datetime.now(UTC)
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
    3. EmailAccount Gmail existant (réutilisation des credentials)
    """
    from app.services.encryption import decrypt_value
    from app.services.mcp_service import get_mcp_service

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

    # Fallback 3: réutiliser les credentials d'un EmailAccount Google existant
    if not client_id or not client_secret:
        try:

            email_result = await session.execute(
                select(EmailAccount).where(
                    EmailAccount.provider == "gmail",
                    EmailAccount.client_id.isnot(None),
                    EmailAccount.client_secret.isnot(None),
                )
            )
            email_account = email_result.scalar_one_or_none()
            if email_account and email_account.client_id and email_account.client_secret:
                client_id = decrypt_value(email_account.client_id)
                client_secret = decrypt_value(email_account.client_secret)
                logger.info("Using Google credentials from EmailAccount")
        except Exception as e:
            logger.warning(f"Could not get credentials from EmailAccount: {e}")

    if not client_id or not client_secret:
        raise HTTPException(
            status_code=400,
            detail="Credentials Google OAuth introuvables. Configure d'abord ton email Gmail dans THÉRÈSE, ou ajoute un serveur MCP Google Workspace.",
        )

    config = OAuthConfig(
        client_id=client_id,
        client_secret=client_secret,
        auth_url=GOOGLE_AUTH_URL,
        token_url=GOOGLE_TOKEN_URL,
        scopes=GSHEETS_SCOPES,
        redirect_uri=f"http://localhost:{RUNTIME_PORT}/api/crm/sync/callback",
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
    code: str | None = None,
    error: str | None = None,
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
    from app.services.encryption import decrypt_value
    from app.services.sheets_service import GoogleSheetsService

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
    stats = new_sync_stats()

    try:
        # Sync Clients
        try:
            clients_data = await sheets_service.get_all_data_as_dicts(spreadsheet_id, "Clients")
            logger.info(f"Found {len(clients_data)} clients in Google Sheets")

            for raw_row in clients_data:
                try:
                    row = _sanitize_row(raw_row)
                    _, created = await upsert_contact(session, row)
                    if created:
                        stats["contacts_created"] += 1
                    else:
                        stats["contacts_updated"] += 1
                except ValueError:
                    continue  # ID manquant, on saute
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

            for raw_row in projects_data:
                try:
                    row = _sanitize_row(raw_row)
                    _, created = await upsert_project(session, row)
                    if created:
                        stats["projects_created"] += 1
                    else:
                        stats["projects_updated"] += 1
                except ValueError:
                    continue
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

            for raw_row in tasks_data:
                try:
                    row = _sanitize_row(raw_row)
                    _, created = await upsert_task(session, row)
                    if created:
                        stats["tasks_created"] += 1
                    else:
                        stats["tasks_updated"] += 1
                except ValueError:
                    continue
                except Exception as e:
                    logger.error(f"Error syncing task {row.get('ID', 'unknown')}: {e}")
                    stats["errors"].append(f"Task {row.get('ID', 'unknown')}: {str(e)}")

        except Exception as e:
            logger.error(f"Error syncing tasks: {e}")
            stats["errors"].append(f"Tasks: {str(e)}")

        await session.commit()

        # Mettre a jour le timestamp de derniere synchronisation
        now = await update_last_sync_time(session)

        total_synced = compute_total_synced(stats)

        return CRMSyncResponse(
            success=len(stats["errors"]) == 0,
            message=f"Synchronisation terminee: {total_synced} elements",
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
    Importe les donnees CRM directement (sans passer par Google Sheets API).

    Utilise quand l'acces OAuth/API n'est pas disponible mais qu'on a les donnees
    via d'autres moyens (ex: MCP Claude Code).

    Body JSON:
    {
        "clients": [{"ID": "...", "Nom": "...", ...}],
        "projects": [{"ID": "...", "Name": "...", ...}],
        "deliverables": [{"ID": "...", "Title": "...", ...}],
        "tasks": [{"ID": "...", "Title": "...", ...}]
    }
    """
    stats = new_sync_stats()

    # Import Clients
    if clients:
        logger.info(f"Importing {len(clients)} clients")
        for raw_row in clients:
            try:
                row = _sanitize_row(raw_row)
                _, created = await upsert_contact(session, row, safe_get=True)
                if created:
                    stats["contacts_created"] += 1
                else:
                    stats["contacts_updated"] += 1
            except ValueError:
                continue
            except Exception as e:
                logger.error(f"Error importing contact {raw_row.get('ID', 'unknown')}: {e}")
                stats["errors"].append(f"Contact {raw_row.get('ID', 'unknown')}: {str(e)}")

    # Import Projects
    if projects:
        logger.info(f"Importing {len(projects)} projects")
        for raw_row in projects:
            try:
                row = _sanitize_row(raw_row)
                _, created = await upsert_project(session, row, safe_get=True)
                if created:
                    stats["projects_created"] += 1
                else:
                    stats["projects_updated"] += 1
            except ValueError:
                continue
            except Exception as e:
                logger.error(f"Error importing project {raw_row.get('ID', 'unknown')}: {e}")
                stats["errors"].append(f"Project {raw_row.get('ID', 'unknown')}: {str(e)}")

    # Import Deliverables
    if deliverables:
        logger.info(f"Importing {len(deliverables)} deliverables")
        for raw_row in deliverables:
            try:
                row = _sanitize_row(raw_row)
                _, created = await upsert_deliverable_from_import(session, row, safe_get=True)
                if created:
                    stats["deliverables_created"] += 1
                else:
                    stats["deliverables_updated"] += 1
            except ValueError:
                continue
            except Exception as e:
                logger.error(f"Error importing deliverable {raw_row.get('ID', 'unknown')}: {e}")
                stats["errors"].append(f"Deliverable {raw_row.get('ID', 'unknown')}: {str(e)}")

    # Import Tasks
    if tasks:
        logger.info(f"Importing {len(tasks)} tasks")
        for raw_row in tasks:
            try:
                row = _sanitize_row(raw_row)
                _, created = await upsert_task(session, row, safe_get=True)
                if created:
                    stats["tasks_created"] += 1
                else:
                    stats["tasks_updated"] += 1
            except ValueError:
                continue
            except Exception as e:
                logger.error(f"Error importing task {raw_row.get('ID', 'unknown')}: {e}")
                stats["errors"].append(f"Task {raw_row.get('ID', 'unknown')}: {str(e)}")

    await session.commit()

    # Mettre a jour le timestamp de derniere synchronisation
    now = await update_last_sync_time(session)

    total_synced = compute_total_synced(stats)

    return CRMSyncResponse(
        success=len(stats["errors"]) == 0,
        message=f"Import termine: {total_synced} elements",
        stats=CRMSyncStatsResponse(**stats, total_synced=total_synced),
        sync_time=now,
    )
