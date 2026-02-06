"""
THÉRÈSE v2 - Pydantic Schemas

Request/Response models for API endpoints.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# ============================================================
# Chat Schemas
# ============================================================


class ChatMessageInput(BaseModel):
    """Input message for chat request."""

    role: Literal["user", "assistant", "system"] = "user"
    content: str


class ChatRequest(BaseModel):
    """Chat completion request."""

    message: str
    conversation_id: str | None = None
    include_memory: bool = True
    stream: bool = True


class ChatResponse(BaseModel):
    """Chat completion response (non-streaming)."""

    id: str
    conversation_id: str
    role: Literal["assistant"] = "assistant"
    content: str
    tokens_in: int | None = None
    tokens_out: int | None = None
    model: str | None = None
    created_at: datetime


class StreamChunk(BaseModel):
    """Streaming response chunk."""

    type: Literal["text", "done", "error", "status", "tool_result", "entities_detected"] = "text"
    content: str = ""
    conversation_id: str | None = None
    message_id: str | None = None
    entities: dict | None = None
    tool_name: str | None = None  # For tool_result type


class ExtractedContactSchema(BaseModel):
    """Extracted contact from message."""

    name: str
    company: str | None = None
    role: str | None = None
    email: str | None = None
    phone: str | None = None
    confidence: float = 0.0


class ExtractedProjectSchema(BaseModel):
    """Extracted project from message."""

    name: str
    description: str | None = None
    budget: float | None = None
    status: str | None = None
    confidence: float = 0.0


class EntitiesDetectedResponse(BaseModel):
    """Response when entities are detected in a message."""

    contacts: list[ExtractedContactSchema] = []
    projects: list[ExtractedProjectSchema] = []
    message_id: str | None = None


# ============================================================
# Memory Schemas
# ============================================================


class MemorySearchRequest(BaseModel):
    """Search request for memory system."""

    query: str
    limit: int = Field(default=10, ge=1, le=50)
    entity_types: list[Literal["contact", "project", "conversation", "file"]] | None = (
        None
    )
    include_semantic: bool = True


class MemorySearchResult(BaseModel):
    """Single search result."""

    id: str
    entity_type: str
    title: str
    content: str
    score: float
    metadata: dict | None = None


class MemorySearchResponse(BaseModel):
    """Search response with results."""

    query: str
    results: list[MemorySearchResult]
    total: int
    search_time_ms: float


# ============================================================
# Contact Schemas
# ============================================================


class ContactCreate(BaseModel):
    """Create contact request."""

    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    email: str | None = None
    phone: str | None = None
    notes: str | None = None
    tags: list[str] | None = None

    # CRM fields (Phase 5)
    stage: str = "contact"
    source: str | None = None


class ContactUpdate(BaseModel):
    """Update contact request."""

    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    email: str | None = None
    phone: str | None = None
    notes: str | None = None
    tags: list[str] | None = None

    # CRM fields (Phase 5)
    stage: str | None = None
    source: str | None = None

    # RGPD fields (Phase 6)
    rgpd_base_legale: str | None = None
    rgpd_date_collecte: datetime | None = None
    rgpd_date_expiration: datetime | None = None
    rgpd_consentement: bool | None = None


class ContactResponse(BaseModel):
    """Contact response."""

    id: str
    first_name: str | None
    last_name: str | None
    company: str | None
    email: str | None
    phone: str | None
    notes: str | None
    tags: list[str] | None

    # CRM fields (Phase 5)
    stage: str
    score: int
    source: str | None
    last_interaction: datetime | None

    # RGPD fields (Phase 6)
    rgpd_base_legale: str | None = None
    rgpd_date_collecte: datetime | None = None
    rgpd_date_expiration: datetime | None = None
    rgpd_consentement: bool = False

    created_at: datetime
    updated_at: datetime


# ============================================================
# RGPD Schemas (Phase 6)
# ============================================================


class RGPDExportResponse(BaseModel):
    """RGPD data export response (portability)."""

    contact: dict
    activities: list[dict]
    projects: list[dict]
    tasks: list[dict]
    exported_at: datetime


class RGPDAnonymizeRequest(BaseModel):
    """Request to anonymize a contact."""

    reason: str = "Demande de suppression"


class RGPDAnonymizeResponse(BaseModel):
    """Response after anonymization."""

    success: bool
    message: str
    contact_id: str


class RGPDRenewConsentResponse(BaseModel):
    """Response after consent renewal."""

    success: bool
    message: str
    new_expiration: datetime


class RGPDStatsResponse(BaseModel):
    """RGPD statistics."""

    total_contacts: int
    par_base_legale: dict[str, int]
    sans_info_rgpd: int
    expires_ou_bientot: int  # Expirés ou dans 30 jours
    avec_consentement: int


class RGPDUpdateRequest(BaseModel):
    """Update RGPD fields for a contact."""

    rgpd_base_legale: str | None = None
    rgpd_consentement: bool | None = None


# ============================================================
# Project Schemas
# ============================================================


class ProjectCreate(BaseModel):
    """Create project request."""

    name: str
    description: str | None = None
    contact_id: str | None = None
    status: Literal["active", "completed", "on_hold"] = "active"
    budget: float | None = None
    notes: str | None = None
    tags: list[str] | None = None


class ProjectUpdate(BaseModel):
    """Update project request."""

    name: str | None = None
    description: str | None = None
    contact_id: str | None = None
    status: Literal["active", "completed", "on_hold"] | None = None
    budget: float | None = None
    notes: str | None = None
    tags: list[str] | None = None


class ProjectResponse(BaseModel):
    """Project response."""

    id: str
    name: str
    description: str | None
    contact_id: str | None
    status: str
    budget: float | None
    notes: str | None
    tags: list[str] | None
    created_at: datetime
    updated_at: datetime


# ============================================================
# Conversation Schemas
# ============================================================


class ConversationCreate(BaseModel):
    """Create conversation request."""

    title: str | None = None


class ConversationResponse(BaseModel):
    """Conversation response."""

    id: str
    title: str | None
    summary: str | None
    message_count: int = 0
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    """Message response."""

    id: str
    conversation_id: str
    role: str
    content: str
    tokens_in: int | None
    tokens_out: int | None
    model: str | None
    created_at: datetime


# ============================================================
# File Schemas
# ============================================================


class FileIndexRequest(BaseModel):
    """Request to index a file."""

    path: str


class FileResponse(BaseModel):
    """File metadata response."""

    id: str
    path: str
    name: str
    extension: str
    size: int
    mime_type: str | None
    chunk_count: int
    indexed_at: datetime | None
    created_at: datetime


# ============================================================
# Config Schemas
# ============================================================


class ConfigResponse(BaseModel):
    """Application configuration response."""

    app_name: str
    app_version: str
    llm_provider: str
    has_anthropic_key: bool
    has_mistral_key: bool
    has_openai_key: bool = False
    has_gemini_key: bool = False
    has_groq_key: bool = False
    has_grok_key: bool = False
    # Image generation specific keys (separate from LLM keys)
    has_openai_image_key: bool = False
    has_gemini_image_key: bool = False
    ollama_available: bool
    # Web search settings
    web_search_enabled: bool = True


class ApiKeyUpdate(BaseModel):
    """API key update request."""

    provider: Literal["anthropic", "mistral", "openai", "gemini", "groq", "grok", "openai_image", "gemini_image"]
    api_key: str


# ============================================================
# User Profile Schemas
# ============================================================


class UserProfileUpdate(BaseModel):
    """User profile update request."""

    name: str
    nickname: str = ""
    company: str = ""
    role: str = ""
    context: str = ""
    email: str = ""
    location: str = ""


class UserProfileResponse(BaseModel):
    """User profile response."""

    name: str
    nickname: str
    company: str
    role: str
    context: str
    email: str
    location: str
    display_name: str


class ImportClaudeMdRequest(BaseModel):
    """Request to import THERESE.md file."""

    file_path: str


# ============================================================
# Working Directory Schemas
# ============================================================


class WorkingDirectoryUpdate(BaseModel):
    """Working directory update request."""

    path: str


class WorkingDirectoryResponse(BaseModel):
    """Working directory response."""

    path: str | None
    exists: bool


# ============================================================
# Health Schemas
# ============================================================


class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    database: bool
    qdrant: bool
    llm_available: bool
    uptime_seconds: float


# ============================================================
# LLM Configuration Schemas
# ============================================================


class LLMConfigUpdate(BaseModel):
    """LLM configuration update request."""

    provider: Literal["anthropic", "openai", "gemini", "mistral", "ollama"]
    model: str


class LLMConfigResponse(BaseModel):
    """LLM configuration response."""

    provider: str
    model: str
    available_models: list[str] = []


class OllamaModelInfo(BaseModel):
    """Ollama model information."""

    name: str
    size: int | None = None
    modified_at: str | None = None
    digest: str | None = None


class OllamaStatusResponse(BaseModel):
    """Ollama status response."""

    available: bool
    base_url: str
    models: list[OllamaModelInfo] = []
    error: str | None = None


# ============================================================
# Onboarding Schemas
# ============================================================


class OnboardingStatusResponse(BaseModel):
    """Onboarding status response."""

    completed: bool
    completed_at: str | None = None


class OnboardingCompleteRequest(BaseModel):
    """Request to mark onboarding as completed."""

    completed: bool = True


# =============================================================================
# CALENDAR SCHEMAS (Phase 2)
# =============================================================================


class CalendarResponse(BaseModel):
    """Response schema pour un calendrier."""

    id: str
    account_id: str | None = None
    summary: str
    description: str | None = None
    timezone: str
    primary: bool
    synced_at: str | None = None  # ISO datetime


class CalendarEventResponse(BaseModel):
    """Response schema pour un événement."""

    id: str
    calendar_id: str
    summary: str
    description: str | None = None
    location: str | None = None
    start_datetime: str | None = None  # ISO datetime
    end_datetime: str | None = None
    start_date: str | None = None  # YYYY-MM-DD
    end_date: str | None = None
    all_day: bool
    attendees: list[str] | None = None  # Parsed from JSON
    recurrence: list[str] | None = None  # Parsed from JSON
    status: str
    synced_at: str  # ISO datetime


class CreateEventRequest(BaseModel):
    """Request pour créer un événement."""

    calendar_id: str = "primary"
    summary: str
    description: str | None = None
    location: str | None = None
    # Pour événements avec heure
    start_datetime: str | None = None  # ISO 8601
    end_datetime: str | None = None
    # Pour événements all-day
    start_date: str | None = None  # YYYY-MM-DD
    end_date: str | None = None
    attendees: list[str] | None = None
    recurrence: list[str] | None = None  # RRULE


class UpdateEventRequest(BaseModel):
    """Request pour modifier un événement."""

    summary: str | None = None
    description: str | None = None
    location: str | None = None
    start_datetime: str | None = None
    end_datetime: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    attendees: list[str] | None = None
    recurrence: list[str] | None = None


class ListEventsRequest(BaseModel):
    """Request pour lister les événements."""

    calendar_id: str = "primary"
    time_min: str | None = None  # ISO 8601
    time_max: str | None = None  # ISO 8601
    max_results: int = 50


class QuickAddEventRequest(BaseModel):
    """Request pour quick add."""

    calendar_id: str = "primary"
    text: str  # Ex: "Déjeuner avec Pierre demain à 12h30"


class CalendarSyncResponse(BaseModel):
    """Response après sync."""

    calendars_synced: int
    events_synced: int
    synced_at: str  # ISO datetime


# =============================================================================
# TASK SCHEMAS (Phase 3)
# =============================================================================


class TaskResponse(BaseModel):
    """Response schema pour une tâche."""

    id: str
    title: str
    description: str | None
    status: str  # todo, in_progress, done, cancelled
    priority: str  # low, medium, high, urgent
    due_date: str | None  # ISO datetime
    project_id: str | None
    tags: list[str] | None  # Parsed from JSON
    completed_at: str | None  # ISO datetime
    created_at: str  # ISO datetime
    updated_at: str  # ISO datetime


class CreateTaskRequest(BaseModel):
    """Request pour créer une tâche."""

    title: str
    description: str | None = None
    status: str = "todo"
    priority: str = "medium"
    due_date: str | None = None  # ISO datetime
    project_id: str | None = None
    tags: list[str] | None = None


class UpdateTaskRequest(BaseModel):
    """Request pour modifier une tâche."""

    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    due_date: str | None = None
    project_id: str | None = None
    tags: list[str] | None = None


# =============================================================================
# INVOICE SCHEMAS (Phase 4)
# =============================================================================


class InvoiceLineResponse(BaseModel):
    """Response schema pour une ligne de facture."""

    id: str
    invoice_id: str
    description: str
    quantity: float
    unit_price_ht: float
    tva_rate: float
    total_ht: float
    total_ttc: float


class InvoiceResponse(BaseModel):
    """Response schema pour une facture."""

    id: str
    invoice_number: str
    contact_id: str
    issue_date: str  # ISO datetime
    due_date: str  # ISO datetime
    status: str  # draft, sent, paid, overdue, cancelled
    subtotal_ht: float
    total_tax: float
    total_ttc: float
    notes: str | None
    payment_date: str | None  # ISO datetime
    created_at: str  # ISO datetime
    updated_at: str  # ISO datetime
    lines: list[InvoiceLineResponse] = []


class InvoiceLineRequest(BaseModel):
    """Request pour une ligne de facture."""

    description: str
    quantity: float = 1.0
    unit_price_ht: float
    tva_rate: float = 20.0  # Default TVA française normale


class CreateInvoiceRequest(BaseModel):
    """Request pour créer une facture."""

    contact_id: str
    issue_date: str | None = None  # ISO datetime, default today
    due_date: str | None = None  # ISO datetime, default +30 days
    lines: list[InvoiceLineRequest]
    notes: str | None = None


class UpdateInvoiceRequest(BaseModel):
    """Request pour modifier une facture."""

    contact_id: str | None = None
    issue_date: str | None = None
    due_date: str | None = None
    status: str | None = None
    lines: list[InvoiceLineRequest] | None = None
    notes: str | None = None


class MarkPaidRequest(BaseModel):
    """Request pour marquer une facture comme payée."""

    payment_date: str | None = None  # ISO datetime, default today


# =============================================================================
# CRM SCHEMAS (Phase 5)
# =============================================================================


class ActivityResponse(BaseModel):
    """Response schema pour une activité."""

    id: str
    contact_id: str
    type: str  # email, call, meeting, note, stage_change, score_change
    title: str
    description: str | None
    extra_data: str | None  # JSON extra data
    created_at: str  # ISO datetime


class CreateActivityRequest(BaseModel):
    """Request pour créer une activité."""

    contact_id: str
    type: str
    title: str
    description: str | None = None
    extra_data: str | None = None  # JSON extra data


class DeliverableResponse(BaseModel):
    """Response schema pour un livrable."""

    id: str
    project_id: str
    title: str
    description: str | None
    status: str  # a_faire, en_cours, en_revision, valide
    due_date: str | None  # ISO datetime
    completed_at: str | None  # ISO datetime
    created_at: str  # ISO datetime
    updated_at: str  # ISO datetime


class CreateDeliverableRequest(BaseModel):
    """Request pour créer un livrable."""

    project_id: str
    title: str
    description: str | None = None
    status: str = "a_faire"
    due_date: str | None = None


class UpdateDeliverableRequest(BaseModel):
    """Request pour modifier un livrable."""

    title: str | None = None
    description: str | None = None
    status: str | None = None
    due_date: str | None = None


class UpdateContactStageRequest(BaseModel):
    """Request pour changer le stage d'un contact."""

    stage: str  # contact, discovery, proposition, signature, delivery, active, archive


class ContactScoreUpdate(BaseModel):
    """Response avec score mis à jour."""

    contact_id: str
    old_score: int
    new_score: int
    reason: str


# ============================================================
# CRM Sync Schemas
# ============================================================


class CRMSyncConfigResponse(BaseModel):
    """Configuration de la synchronisation CRM."""

    spreadsheet_id: str | None = None
    last_sync: str | None = None
    has_token: bool = False
    configured: bool = False


class CRMSyncConfigRequest(BaseModel):
    """Request pour configurer la sync CRM."""

    spreadsheet_id: str


class CRMSyncStatsResponse(BaseModel):
    """Statistiques de synchronisation."""

    contacts_created: int = 0
    contacts_updated: int = 0
    projects_created: int = 0
    projects_updated: int = 0
    deliverables_created: int = 0
    deliverables_updated: int = 0
    tasks_created: int = 0
    tasks_updated: int = 0
    errors: list[str] = []
    total_synced: int = 0


class CRMSyncResponse(BaseModel):
    """Response après synchronisation."""

    success: bool
    message: str
    stats: CRMSyncStatsResponse | None = None
    sync_time: str | None = None  # ISO datetime


# ============================================================
# CRM Import Schemas (Local First)
# ============================================================


class CRMImportErrorSchema(BaseModel):
    """Erreur rencontree lors de l'import."""

    row: int
    column: str | None = None
    message: str
    data: dict | None = None


class CRMImportResultSchema(BaseModel):
    """Resultat d'un import CRM."""

    success: bool
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[CRMImportErrorSchema] = []
    total_rows: int = 0
    message: str = ""


class CRMImportPreviewSchema(BaseModel):
    """Preview d'un import avant execution."""

    total_rows: int
    sample_rows: list[dict]
    detected_columns: list[str]
    column_mapping: dict[str, str]
    validation_errors: list[CRMImportErrorSchema]
    can_import: bool


class CreateCRMContactRequest(BaseModel):
    """Request body for creating a CRM contact."""

    first_name: str
    last_name: str | None = None
    company: str | None = None
    email: str | None = None
    phone: str | None = None
    source: str | None = None
    stage: str = "contact"
