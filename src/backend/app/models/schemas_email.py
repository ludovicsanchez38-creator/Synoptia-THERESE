"""
THÉRÈSE v2 - Schemas Email

Request/Response models pour les opérations email (OAuth, IMAP, messages, labels).
"""

from datetime import datetime

from pydantic import BaseModel

# ============================================================
# OAuth
# ============================================================


class OAuthInitiateRequest(BaseModel):
    """OAuth flow initiation request (POST body).

    SEC-008: Les credentials OAuth sont transmis dans le body POST,
    pas en query parameters (visibles dans les logs serveur et l'historique navigateur).
    """

    client_id: str
    client_secret: str


class OAuthInitiateResponse(BaseModel):
    """OAuth flow initiation response."""

    auth_url: str
    state: str
    redirect_uri: str


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request."""

    state: str
    code: str | None = None
    error: str | None = None


class EmailAccountResponse(BaseModel):
    """Email account response."""

    id: str
    email: str
    provider: str
    scopes: list[str] = []
    created_at: datetime
    last_sync: datetime | None = None


# ============================================================
# IMAP/SMTP
# ============================================================


class ImapSetupRequest(BaseModel):
    """IMAP/SMTP account setup request."""

    email: str
    password: str  # App password
    imap_host: str
    imap_port: int = 993
    smtp_host: str
    smtp_port: int = 587
    smtp_use_tls: bool = True


class ImapTestRequest(BaseModel):
    """Test IMAP/SMTP connection request."""

    email: str
    password: str
    imap_host: str
    imap_port: int = 993
    smtp_host: str
    smtp_port: int = 587
    smtp_use_tls: bool = True


# ============================================================
# Messages
# ============================================================


class MessageListRequest(BaseModel):
    """List messages request."""

    max_results: int = 50
    page_token: str | None = None
    query: str | None = None
    label_ids: list[str] | None = None


class SendEmailRequest(BaseModel):
    """Send email request."""

    to: list[str]
    subject: str
    body: str
    cc: list[str] | None = None
    bcc: list[str] | None = None
    html: bool = False


class ModifyMessageRequest(BaseModel):
    """Modify message request."""

    add_label_ids: list[str] | None = None
    remove_label_ids: list[str] | None = None


# ============================================================
# Labels
# ============================================================


class LabelCreateRequest(BaseModel):
    """Create label request."""

    name: str


# ============================================================
# Smart Email Features
# ============================================================


class ClassifyEmailRequest(BaseModel):
    """Classify email request."""

    force_reclassify: bool = False  # Force re-classification même si déjà classé


class GenerateResponseRequest(BaseModel):
    """Generate email response request."""

    tone: str = "formal"  # formal | friendly | neutral
    length: str = "medium"  # short | medium | detailed


class UpdatePriorityRequest(BaseModel):
    """Update email priority request."""

    priority: str  # 'high' | 'medium' | 'low'


# ============================================================
# Email Setup Wizard
# ============================================================


class ValidateCredentialsRequest(BaseModel):
    """Validate Gmail OAuth credentials request."""

    client_id: str
    client_secret: str


class ValidateCredentialsResponse(BaseModel):
    """Validate Gmail OAuth credentials response."""

    client_id: dict  # ValidationResult (dataclass depuis email_setup_assistant)
    client_secret: dict  # ValidationResult (dataclass depuis email_setup_assistant)
    all_valid: bool


class GenerateGuideRequest(BaseModel):
    """Generate setup guide request."""

    provider: str
    has_project: bool


class GenerateGuideResponse(BaseModel):
    """Generate setup guide response."""

    message: str
