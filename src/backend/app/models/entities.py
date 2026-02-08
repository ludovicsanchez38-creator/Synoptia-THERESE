"""
THÉRÈSE v2 - SQLModel Entities

Database models for structured data storage.
"""

from datetime import UTC, datetime
from typing import Optional
from uuid import uuid4

from sqlmodel import Field, Relationship, SQLModel


def generate_uuid() -> str:
    """Generate a UUID string for primary keys."""
    return str(uuid4())


class Contact(SQLModel, table=True):
    """Contact entity for memory system."""

    __tablename__ = "contacts"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    email: str | None = Field(default=None, index=True)
    phone: str | None = None
    address: str | None = None  # Adresse postale du contact
    notes: str | None = None
    tags: str | None = None  # JSON array stored as string
    extra_data: str | None = None  # JSON object stored as string

    # CRM Pipeline (Phase 5)
    stage: str = Field(default="contact", index=True)  # contact, discovery, proposition, signature, delivery, active, archive
    score: int = Field(default=50)  # Scoring prospect (0-100+)
    source: str | None = None  # website, referral, linkedin, etc.
    last_interaction: datetime | None = Field(default=None, index=True)  # Derniere interaction (pour decay)

    # RGPD (Phase 6)
    rgpd_base_legale: str | None = None  # consentement, contrat, interet_legitime, obligation_legale
    rgpd_date_collecte: datetime | None = None  # Date de collecte des données
    rgpd_date_expiration: datetime | None = None  # Date d'expiration (collecte + 3 ans par défaut)
    rgpd_consentement: bool = Field(default=False)  # Consentement explicite obtenu

    # Scope fields (E3-05)
    scope: str = Field(default="global", index=True)  # global, project, conversation
    scope_id: str | None = None  # ID of the project or conversation if scoped
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    projects: list["Project"] = Relationship(back_populates="contact")
    activities: list["Activity"] = Relationship(back_populates="contact", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    invoices: list["Invoice"] = Relationship(back_populates="contact", cascade_delete=True)

    @property
    def display_name(self) -> str:
        """Get display name for contact."""
        parts = [self.first_name, self.last_name]
        name = " ".join(p for p in parts if p)
        if self.company and not name:
            return self.company
        return name or "Sans nom"


class Project(SQLModel, table=True):
    """Project entity linked to contacts."""

    __tablename__ = "projects"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    name: str
    description: str | None = None
    contact_id: str | None = Field(default=None, foreign_key="contacts.id", index=True)
    status: str = Field(default="active")  # active, completed, on_hold
    budget: float | None = None
    notes: str | None = None
    tags: str | None = None  # JSON array stored as string
    extra_data: str | None = None  # JSON object stored as string
    # Scope fields (E3-05)
    scope: str = Field(default="global", index=True)  # global, project, conversation
    scope_id: str | None = None  # ID of the parent project or conversation if scoped
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    contact: Contact | None = Relationship(back_populates="projects")
    tasks: list["Task"] = Relationship(back_populates="project", cascade_delete=True)
    deliverables: list["Deliverable"] = Relationship(back_populates="project", cascade_delete=True)


class Conversation(SQLModel, table=True):
    """Conversation container for messages."""

    __tablename__ = "conversations"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    title: str | None = None
    summary: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)

    # Relationships
    messages: list["Message"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Message(SQLModel, table=True):
    """Chat message within a conversation."""

    __tablename__ = "messages"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    conversation_id: str = Field(foreign_key="conversations.id", index=True)
    role: str  # user, assistant, system
    content: str
    tokens_in: int | None = None
    tokens_out: int | None = None
    model: str | None = None
    extra_data: str | None = None  # JSON object stored as string
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)

    # Relationships
    conversation: Conversation | None = Relationship(back_populates="messages")


class FileMetadata(SQLModel, table=True):
    """Metadata for indexed files."""

    __tablename__ = "files"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    path: str = Field(unique=True)
    name: str
    extension: str
    size: int
    mime_type: str | None = None
    content_hash: str | None = None
    chunk_count: int = 0
    # Scope fields (E3-05) - for files linked to specific entities
    scope: str = Field(default="global")  # global, project, conversation, contact
    scope_id: str | None = None  # ID of the linked entity
    indexed_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Preference(SQLModel, table=True):
    """User preferences and settings."""

    __tablename__ = "preferences"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    key: str = Field(unique=True)
    value: str  # JSON-encoded value
    category: str = Field(default="general")  # general, ui, llm, memory
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class BoardDecisionDB(SQLModel, table=True):
    """Board decision stored in database."""

    __tablename__ = "board_decisions"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    question: str
    context: str | None = None
    opinions: str  # JSON array of AdvisorOpinion objects
    synthesis: str  # JSON object of BoardSynthesis
    confidence: str  # high, medium, low (denormalized for quick queries)
    recommendation: str  # Denormalized for quick display
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)


class PromptTemplate(SQLModel, table=True):
    """User-created prompt templates (US-PERS-02)."""

    __tablename__ = "prompt_templates"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    name: str
    prompt: str
    category: str = Field(default="general")
    icon: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ============================================================
# Email Entities (Phase 1 - Core Native Email)
# ============================================================


class EmailAccount(SQLModel, table=True):
    """
    Email account configuration.

    Stores OAuth tokens for Gmail or IMAP/SMTP credentials.
    Phase 1 - Email (Gmail) + Local First (IMAP/SMTP)
    """
    __tablename__ = "email_accounts"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    email: str = Field(unique=True, index=True)
    provider: str = "gmail"  # gmail, imap

    # OAuth credentials (encrypted via encryption.py)
    client_id: str | None = None  # Encrypted - needed for token refresh
    client_secret: str | None = None  # Encrypted - needed for token refresh

    # OAuth tokens (for Gmail - encrypted via encryption.py)
    access_token: str | None = None  # Encrypted
    refresh_token: str | None = None  # Encrypted
    token_expiry: datetime | None = None
    scopes: str | None = None  # JSON array of scopes as string

    # IMAP/SMTP configuration (for IMAP provider - encrypted)
    imap_host: str | None = None
    imap_port: int = 993
    imap_username: str | None = None  # Usually same as email
    imap_password: str | None = None  # Encrypted (app password)

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_use_tls: bool = True

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_sync: datetime | None = None

    # Relationships
    messages: list["EmailMessage"] = Relationship(back_populates="account")


class EmailMessage(SQLModel, table=True):
    """
    Email message synced from Gmail.

    Stores message metadata and body for offline access.
    Phase 1 - Email (Gmail)
    """
    __tablename__ = "email_messages"

    # Gmail IDs
    id: str = Field(primary_key=True)  # Gmail message ID
    thread_id: str = Field(index=True)
    account_id: str = Field(foreign_key="email_accounts.id", index=True)

    # Message metadata
    subject: str | None = None
    snippet: str | None = None  # Short preview
    from_email: str
    from_name: str | None = None
    to_emails: str  # JSON array
    cc_emails: str | None = None  # JSON array
    bcc_emails: str | None = None  # JSON array

    # Timestamps
    date: datetime = Field(index=True)
    internal_date: datetime  # Gmail internal timestamp

    # Labels and flags
    labels: str  # JSON array (INBOX, SENT, etc.)
    is_read: bool = False
    is_starred: bool = False
    is_important: bool = False
    is_draft: bool = False

    # Attachments
    has_attachments: bool = False
    attachment_count: int = 0

    # Body content
    body_plain: str | None = None
    body_html: str | None = None

    # Size
    size_bytes: int = 0

    # Sync metadata
    synced_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Smart Email Features (US-EMAIL-08, US-EMAIL-10)
    priority: str | None = Field(default=None, index=True)  # 'high' | 'medium' | 'low'
    priority_score: int | None = Field(default=None)  # 0-100
    priority_reason: str | None = Field(default=None)  # Explanation
    category: str | None = Field(default=None)  # transactional, administrative, business, promotional, newsletter

    # Relationships
    account: EmailAccount | None = Relationship(back_populates="messages")


class EmailLabel(SQLModel, table=True):
    """
    Gmail labels (folders).

    Synced from Gmail, includes both system and custom labels.
    Phase 1 - Email (Gmail)
    """
    __tablename__ = "email_labels"

    id: str = Field(primary_key=True)  # Gmail label ID
    account_id: str = Field(foreign_key="email_accounts.id", index=True)

    name: str
    type: str  # system or user

    # Display settings
    color_background: str | None = None
    color_text: str | None = None

    # Message counts
    messages_total: int = 0
    messages_unread: int = 0

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

# =============================================================================
# CALENDAR MODELS (Phase 2)
# =============================================================================


class Calendar(SQLModel, table=True):
    """Table calendriers (Google Calendar, CalDAV, Local)."""

    __tablename__ = "calendars"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    account_id: str | None = Field(default=None, foreign_key="email_accounts.id", index=True)
    summary: str  # Nom du calendrier
    description: str | None = None
    timezone: str = "Europe/Paris"
    primary: bool = False  # Est-ce le calendrier principal?

    # Provider configuration (Local First)
    provider: str = "local"  # local, google, caldav
    remote_id: str | None = None  # ID chez le provider externe (Google Calendar ID, etc.)

    # CalDAV configuration (encrypted)
    caldav_url: str | None = None
    caldav_username: str | None = None
    caldav_password: str | None = None  # Encrypted

    # Sync status
    sync_status: str = "idle"  # idle, syncing, error
    last_sync_error: str | None = None
    synced_at: datetime | None = None

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    events: list["CalendarEvent"] = Relationship(back_populates="calendar")


class CalendarEvent(SQLModel, table=True):
    """Table événements calendrier."""

    __tablename__ = "calendar_events"

    id: str = Field(primary_key=True)  # Google event ID
    calendar_id: str = Field(foreign_key="calendars.id", index=True)
    summary: str  # Titre événement
    description: str | None = None
    location: str | None = None
    start_datetime: datetime | None = None  # Pour events avec heure
    end_datetime: datetime | None = None
    start_date: str | None = None  # Pour all-day events (format YYYY-MM-DD)
    end_date: str | None = None
    all_day: bool = False
    attendees: str | None = None  # JSON array d'emails
    recurrence: str | None = None  # JSON array de règles RRULE
    status: str = "confirmed"  # confirmed, tentative, cancelled
    synced_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    calendar: Calendar | None = Relationship(back_populates="events")

# =============================================================================
# TASK MODELS (Phase 3)
# =============================================================================


class Task(SQLModel, table=True):
    """Table tâches locales."""

    __tablename__ = "tasks"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    title: str
    description: str | None = None
    status: str = "todo"  # todo, in_progress, done, cancelled
    priority: str = "medium"  # low, medium, high, urgent
    due_date: datetime | None = None
    project_id: str | None = Field(default=None, foreign_key="projects.id", index=True)
    tags: str | None = None  # JSON array
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    project: Optional["Project"] = Relationship(back_populates="tasks")


# =============================================================================
# INVOICE MODELS (Phase 4)
# =============================================================================


class Invoice(SQLModel, table=True):
    """Table factures."""

    __tablename__ = "invoices"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    invoice_number: str = Field(unique=True, index=True)  # FACT-2026-001, DEV-2026-001, AV-2026-001
    contact_id: str = Field(foreign_key="contacts.id", index=True)
    document_type: str = Field(default="facture", index=True)  # devis, facture, avoir
    tva_applicable: bool = Field(default=True)  # Si False: "TVA non applicable, art. 293 B du CGI"
    issue_date: datetime = Field(default_factory=lambda: datetime.now(UTC))
    due_date: datetime
    status: str = "draft"  # draft, sent, paid, overdue, cancelled
    subtotal_ht: float = 0.0  # Hors taxe
    total_tax: float = 0.0
    total_ttc: float = 0.0  # Toutes taxes comprises
    notes: str | None = None
    payment_date: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    lines: list["InvoiceLine"] = Relationship(back_populates="invoice", cascade_delete=True)
    contact: Optional["Contact"] = Relationship(back_populates="invoices")


class InvoiceLine(SQLModel, table=True):
    """Table lignes de facturation."""

    __tablename__ = "invoice_lines"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    invoice_id: str = Field(foreign_key="invoices.id", index=True)
    description: str
    quantity: float = 1.0
    unit_price_ht: float  # Prix unitaire hors taxe
    tva_rate: float  # 20.0, 10.0, 5.5, 2.1
    total_ht: float  # quantity * unit_price_ht
    total_ttc: float  # total_ht * (1 + tva_rate/100)

    # Relationships
    invoice: Optional["Invoice"] = Relationship(back_populates="lines")


# =============================================================================
# CRM MODELS (Phase 5)
# =============================================================================


class Activity(SQLModel, table=True):
    """Timeline d'activités par contact."""

    __tablename__ = "activities"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    contact_id: str = Field(foreign_key="contacts.id", index=True)
    type: str  # email, call, meeting, note, stage_change, score_change
    title: str
    description: str | None = None
    extra_data: str | None = None  # JSON extra data (renamed from metadata to avoid SQLModel conflict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    contact: Optional["Contact"] = Relationship(back_populates="activities")


class Deliverable(SQLModel, table=True):
    """Livrables par projet (granularité)."""

    __tablename__ = "deliverables"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    project_id: str = Field(foreign_key="projects.id", index=True)
    title: str
    description: str | None = None
    status: str = Field(default="a_faire")  # a_faire, en_cours, en_revision, valide
    due_date: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    project: Optional["Project"] = Relationship(back_populates="deliverables")


# =============================================================================
# UPDATE RELATIONSHIPS
# =============================================================================

# Update Contact model to have invoices relationship
Contact.invoices = Relationship(back_populates="contact")

# Update Project model to have deliverables relationship
Project.deliverables = Relationship(back_populates="project", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
