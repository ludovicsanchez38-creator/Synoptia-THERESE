"""
THÉRÈSE v2 - Pydantic Schemas

Request/Response models for API endpoints.
"""

import re
from datetime import UTC, date, datetime
from typing import Annotated, Any, Literal, Self
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PlainSerializer,
    field_validator,
    model_validator,
)

# ============================================================
# Horodatages (B-216)
# ============================================================


def _iso_utc(instant: datetime) -> str:
    """Rend un instant ABSOLU, jamais une heure de mur.

    B-216 : les entités écrivent `datetime.now(UTC)`, mais SQLite les relit
    sans tzinfo et la réponse partait sans « Z » ni décalage. ECMAScript parse
    une date-heure sans offset comme HEURE LOCALE : le poste affichait donc
    l'heure UTC comme si c'était la sienne (deux heures de retard à Paris en
    septembre). Un datetime naïf venu de la base est de l'UTC — c'est ce que
    les `default_factory` y ont écrit — donc on le rattache à UTC ; un
    datetime déjà conscient est converti, jamais réinterprété.
    """
    if instant.tzinfo is None:
        return instant.replace(tzinfo=UTC).isoformat()
    return instant.astimezone(UTC).isoformat()


#: Horodatage de réponse qui porte toujours son fuseau en JSON.
#: `when_used="json"` : le mode python de `model_dump()` continue de rendre un
#: `datetime`, ce dont dépend le code interne qui consomme ces schémas.
#:
#: RÉSERVÉ AUX INSTANTS ÉCRITS PAR L'HORLOGE DU SERVEUR (`created_at`,
#: `updated_at`, `last_interaction`, `indexed_at`, `exported_at`). NE JAMAIS
#: l'appliquer à un JOUR décidé par quelqu'un — échéance de relance, date
#: RGPD, début/fin d'événement d'agenda, date de facture, tout ce qui vient
#: d'un `<input type="date">`. Coller « +00:00 » sur une date civile ne la
#: date pas : elle DEVIENT minuit UTC, et l'écran qui la convertit affiche un
#: autre jour. C'est le défaut inverse de B-216, et `lib/civilDate.ts`
#: le dit déjà en creux : `parisDateKey` ne convertit QUE si la chaîne porte
#: un fuseau, sinon il garde le jour littéral.
HorodatageUTC = Annotated[
    datetime, PlainSerializer(_iso_utc, return_type=str, when_used="json")
]

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
    skill_id: str | None = None
    file_paths: list[str] | None = None
    disable_tools: bool = False  # BUG-097 : RFC mini-chat - désactiver les outils pour éviter les boucles
    # Finding 1-2 (30/08) : le compte / l'agenda de l'écran. Sans eux, deux
    # comptes font parler le chat au premier de la table. Optionnels : un
    # seul compte reste utilisable comme avant.
    email_account_id: str | None = None
    calendar_id: str | None = None


class ChatResponse(BaseModel):
    """Chat completion response (non-streaming)."""

    id: str
    conversation_id: str
    role: Literal["assistant"] = "assistant"
    content: str
    tokens_in: int | None = None
    tokens_out: int | None = None
    model: str | None = None
    provider: str | None = None  # P0-IA-3 : badge local/cloud par message
    client_action: dict[str, str] | None = None  # Actions déterministes : action à exécuter côté client
    confirmations: list[dict[str, Any]] | None = None  # Mutations préparées, encore non exécutées
    # B-482 : avertissements de plafond (modèle hors grille, budget proche)
    warnings: list[str] | None = None
    created_at: HorodatageUTC


class StreamChunk(BaseModel):
    """Streaming response chunk."""

    type: Literal["text", "done", "error", "status", "tool_result", "entities_detected", "skill_file", "skill_file_error", "confirmation_required", "client_action"] = "text"
    content: str = ""
    conversation_id: str | None = None
    message_id: str | None = None
    entities: dict | None = None
    tool_name: str | None = None  # For tool_result type
    skill_file: dict | None = None  # For skill_file type (auto-detected skill execution)
    confirmation: dict | None = None  # US-002 : action sensible en attente de validation
    client_action: dict[str, str] | None = None  # Actions déterministes : action à exécuter côté client
    provider: str | None = None  # P0-IA-3 : provider LLM utilisé (event done)


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
    """Search request for memory system.

    B-178 : le filtre s'appelle `entity_types`. Un appelant qui écrivait
    `types` (le nom du client avant sa correction) voyait son champ absorbé en
    silence par Pydantic : la réponse rendait 200 avec des fiches ET des
    dossiers, comme si la restriction avait été appliquée. Un filtre que le
    serveur ne connaît pas doit se dire, sans quoi une recherche ouverte passe
    pour une recherche restreinte.
    """

    model_config = ConfigDict(extra="forbid")

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
    # Lot F : ILIKE est plafonné. True = d'autres correspondances existent.
    truncated: bool = False


# ============================================================
# Contact Schemas
# ============================================================


# B-167 : les sept étapes du pipeline, celles que l'écran sait afficher
# (`PIPELINE_STAGES` dans PipelineView.tsx). La vue groupe les fiches en
# parcourant CES colonnes, sans repli : une étape hors liste faisait
# disparaître la fiche du pipeline sans un mot. Le refus vaut mieux qu'un
# enregistrement invisible.
EtapePipeline = Literal[
    "contact",
    "discovery",
    "proposition",
    "signature",
    "delivery",
    "active",
    "archive",
]

# B-168 : bornes des champs texte d'une fiche contact. Un `first_name` de
# 100 000 caractères était stocké entier, et la liste (sans projection) le
# rendait ensuite à chaque affichage - 203 ko pour six fiches. Les valeurs
# laissent large pour un usage réel (une note tient dans 10 000 signes) et
# ferment l'abus.
LONGUEUR_NOM = 200
LONGUEUR_EMAIL = 320  # RFC 5321 : 64 + @ + 255
LONGUEUR_TELEPHONE = 50
LONGUEUR_ADRESSE = 500
LONGUEUR_NOTES = 10_000



def _jour_civil_de_relance(valeur: Any) -> Any:
    """Ramène une échéance de relance au JOUR CIVIL de Paris, avant stockage.

    `contacts_a_relancer` lit `next_follow_up` comme un jour décidé
    (`func.date(...)`), mais l'API l'acceptait en instant absolu. Or SQLite
    JETTE le décalage à l'écriture : `2026-08-30T23:30:00Z` est enregistré
    `2026-08-30 23:30`, dont la date est le 30 alors que le jour civil de Paris
    est le 31 — la relance tombait due un jour trop tôt, et l'information qui
    aurait permis de rattraper le coup à la lecture n'existait plus. On
    normalise donc à l'écriture, comme `EmailFollowUp.due_date` depuis B-062.

    `None` traverse intact : effacer une échéance doit rester possible.
    """
    if valeur is None:
        return None
    from app.services.civil_time import echeance_de_relance

    return echeance_de_relance(valeur if isinstance(valeur, str) else str(valeur))


class ContactCreate(BaseModel):
    """Create contact request."""

    first_name: str | None = Field(default=None, max_length=LONGUEUR_NOM)
    last_name: str | None = Field(default=None, max_length=LONGUEUR_NOM)
    company: str | None = Field(default=None, max_length=LONGUEUR_NOM)
    email: str | None = Field(default=None, max_length=LONGUEUR_EMAIL)
    phone: str | None = Field(default=None, max_length=LONGUEUR_TELEPHONE)
    address: str | None = Field(default=None, max_length=LONGUEUR_ADRESSE)
    notes: str | None = Field(default=None, max_length=LONGUEUR_NOTES)
    tags: list[str] | None = None

    # CRM fields (Phase 5)
    stage: EtapePipeline = "contact"
    source: str | None = Field(default=None, max_length=LONGUEUR_NOM)
    # La prochaine relance DECIDEE. Sans ce champ en ecriture, seule une
    # importation pourrait en poser une (revue du 29/08).
    next_follow_up: datetime | None = None

    @field_validator("next_follow_up", mode="before")
    @classmethod
    def _relance_au_jour_civil_paris(cls, valeur: Any) -> Any:
        return _jour_civil_de_relance(valeur)

    # Scope (L6 revue produit) : rattacher un contact à une conversation/projet.
    scope: str | None = None  # global | project | conversation (defaut global cote modele)
    scope_id: str | None = None


class ContactUpdate(BaseModel):
    """Update contact request."""

    # B-168 : mêmes bornes qu'à la création. Sans elles, la garde se
    # contournait en deux requêtes (créer court, puis mettre à jour long).
    first_name: str | None = Field(default=None, max_length=LONGUEUR_NOM)
    last_name: str | None = Field(default=None, max_length=LONGUEUR_NOM)
    company: str | None = Field(default=None, max_length=LONGUEUR_NOM)
    email: str | None = Field(default=None, max_length=LONGUEUR_EMAIL)
    phone: str | None = Field(default=None, max_length=LONGUEUR_TELEPHONE)
    address: str | None = Field(default=None, max_length=LONGUEUR_ADRESSE)
    notes: str | None = Field(default=None, max_length=LONGUEUR_NOTES)
    tags: list[str] | None = None

    # C2 (28/08) : le périmètre doit pouvoir CHANGER. `ContactCreate` porte un
    # `scope` depuis la revue L6, mais aucun écran ne l'envoie, et une fiche née
    # globale le restait pour toujours — le code promettait pourtant de pouvoir
    # la « promouvoir » (memory_tools.py:228), sans jamais offrir le contrôle.
    # `None` = ne pas toucher au périmètre existant.
    scope: str | None = None  # global | project | conversation
    scope_id: str | None = None

    # CRM fields (Phase 5)
    # B-167 : même domaine qu'à la création - sinon l'étape inconnue rentre
    # par la mise à jour.
    stage: EtapePipeline | None = None
    source: str | None = Field(default=None, max_length=LONGUEUR_NOM)
    # P0-PROD-1 : override manuel du score (sinon le PATCH du champ score était
    # silencieusement ignoré faute de champ sur le schéma).
    score: int | None = None

    # RGPD fields (Phase 6)
    rgpd_base_legale: str | None = None
    rgpd_date_collecte: datetime | None = None
    rgpd_date_expiration: datetime | None = None
    rgpd_consentement: bool | None = None
    next_follow_up: datetime | None = None

    @field_validator("next_follow_up", mode="before")
    @classmethod
    def _relance_au_jour_civil_paris(cls, valeur: Any) -> Any:
        return _jour_civil_de_relance(valeur)


class ContactResponse(BaseModel):
    """Contact response."""

    id: str
    first_name: str | None
    last_name: str | None
    company: str | None
    email: str | None
    phone: str | None
    address: str | None
    notes: str | None
    tags: list[str] | None

    # CRM fields (Phase 5)
    stage: str
    score: int
    source: str | None
    last_interaction: HorodatageUTC | None

    # Scope (L6 revue produit) : expose le rattachement pour les filtres et la pastille.
    scope: str = "global"
    scope_id: str | None = None

    # RGPD fields (Phase 6)
    rgpd_base_legale: str | None = None
    rgpd_date_collecte: datetime | None = None
    rgpd_date_expiration: datetime | None = None
    rgpd_consentement: bool = False

    created_at: HorodatageUTC
    updated_at: HorodatageUTC


# ============================================================
# RGPD Schemas (Phase 6)
# ============================================================
    next_follow_up: datetime | None = None


class RGPDExportResponse(BaseModel):
    """RGPD data export response (portability)."""

    contact: dict
    activities: list[dict]
    projects: list[dict]
    tasks: list[dict]
    exported_at: HorodatageUTC


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
    # C2 : l'avocat a lu « Présente dans le projet Valette » depuis le dossier
    # Rousset. Le FICHIER était bien cloisonné ; l'entité projet, non — elle
    # naissait globale sans recours. Défaut inchangé pour ne rien casser en
    # silence.
    scope: str = "global"
    scope_id: str | None = None
    status: Literal["active", "completed", "on_hold", "cancelled"] = "active"
    budget: float | None = None
    notes: str | None = None
    tags: list[str] | None = None


class ProjectUpdate(BaseModel):
    """Update project request."""

    name: str | None = None
    description: str | None = None
    contact_id: str | None = None
    status: Literal["active", "completed", "on_hold", "cancelled"] | None = None
    budget: float | None = None
    notes: str | None = None
    tags: list[str] | None = None

    # C2 (28/08) : le périmètre est un CHOIX, et il doit pouvoir changer.
    # Sans lui, une fiche née globale le restait pour toujours — et le mode
    # cloisonné (C3) viderait un dossier de sa propre personne, dont la fiche
    # est justement globale. `None` = ne pas toucher au périmètre existant.
    scope: str | None = None  # global | project | conversation
    scope_id: str | None = None


class ProjectResponse(BaseModel):
    """Project response."""

    id: str
    name: str
    description: str | None
    contact_id: str | None
    # C2 : le périmètre est écrit en base — sans lui ici, aucun écran ne
    # peut l'afficher ni le modifier. Un champ que l'API ne relit pas est
    # un contrôle mort, comme `ContactCreate.scope` l'a été depuis L6.
    scope: str = "global"
    scope_id: str | None = None
    status: str
    budget: float | None
    notes: str | None
    tags: list[str] | None
    created_at: HorodatageUTC
    updated_at: HorodatageUTC


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
    created_at: HorodatageUTC
    updated_at: HorodatageUTC
    # 0.43 : rattachement à un projet. Exposé pour que l'interface puisse dire
    # à l'utilisateur quels documents cette conversation consultera — une
    # cloison invisible serait pire que pas de cloison du tout.
    project_id: str | None = None
    #: `global` (défaut) | `project` | `all`.
    memory_scope: str = "global"


class ConversationProjectUpdate(BaseModel):
    """Politique documentaire d'une conversation.

    - `project_id` renseigné : cloisonné sur ce projet ;
    - `memory_scope="all"` : aucune cloison, choix explicite de l'utilisateur ;
    - sinon : documents généraux uniquement (moindre privilège).
    """

    project_id: str | None = None
    memory_scope: str = "global"


class MessageResponse(BaseModel):
    """Message response."""

    id: str
    conversation_id: str
    role: str
    content: str
    tokens_in: int | None
    tokens_out: int | None
    model: str | None
    provider: str | None = None  # P0-IA-3 : badge local/cloud par message
    extra_data: str | None = None  # BUG-130 : JSON {skill_file: {...}} pour restaurer le fichier généré
    created_at: HorodatageUTC


# ============================================================
# File Schemas
# ============================================================


class FileIndexRequest(BaseModel):
    """Request to index a file."""

    path: str
    # BUG-165 : le composeur du chat indexe la pièce jointe dès l'attachement,
    # avant l'envoi. Sans cette information, le fichier naissait GLOBAL et
    # restait lisible depuis tous les autres dossiers clients — le
    # cloisonnement livré en 0.43 ne s'appliquait donc jamais aux pièces
    # jointes, alors qu'elles sont le cas le plus courant.
    conversation_id: str | None = None
    # Revue Soso, passe 2 : le caractère provisoire doit être DEMANDÉ, jamais
    # déduit de l'absence de conversation. L'explorateur indexe lui aussi sans
    # conversation, et son périmètre est parfaitement voulu : le déduire
    # rendait ses documents confiscables par la première conversation de projet
    # qui les joignait — exactement le défaut qu'on cherchait à fermer.
    perimetre_provisoire: bool = False


class FileResponse(BaseModel):
    """File metadata response."""

    id: str
    path: str
    name: str
    extension: str
    size: int
    mime_type: str | None
    chunk_count: int
    indexed_at: HorodatageUTC | None
    created_at: HorodatageUTC
    # J2 : le rattachement d'un document doit être lisible par l'interface.
    # Sans lui, l'utilisateur ne peut pas savoir ce que la machine consultera
    # dans quelle conversation.
    scope: str = "global"
    scope_id: str | None = None


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
    has_openrouter_key: bool = False
    # Image generation specific keys (separate from LLM keys)
    has_openai_image_key: bool = False
    has_gemini_image_key: bool = False
    has_fal_key: bool = False
    has_brave_key: bool = False
    # Revue dette 0.43.4 : les champs has_*_key ci-dessus n'ont jamais suivi
    # les fournisseurs (perplexity, deepseek, infomaniak, puis glm/kimi/qwen/
    # minimax : cle enregistree, jamais restituee, l'interface la redemandait).
    # Cette carte couvre TOUS les fournisseurs LLM ; les champs historiques
    # restent pour compatibilite.
    api_keys: dict[str, bool] = {}
    # B-239 : le booléen ci-dessus dit qu'une clé existe, jamais d'où elle
    # vient. L'écran en déduisait « chiffrée localement » pour une variable
    # d'environnement que l'application n'a ni reçue ni stockée. Cette carte
    # jumelle donne l'origine réelle : coffre, environnement, corrompue,
    # absente — dans l'ordre de résolution du runtime (base avant env).
    api_keys_source: dict[str, str] = {}
    ollama_available: bool
    # Web search settings
    web_search_enabled: bool = True
    # BUG-051 : clés API corrompues (blob Fernet illisible après perte de clé)
    corrupted_keys: list[str] = []


class ApiKeyUpdate(BaseModel):
    """API key update request."""

    provider: Literal[
        "anthropic", "mistral", "openai", "gemini", "groq", "grok", "openrouter",
        "openai_image", "gemini_image", "fal", "brave", "infomaniak", "deepseek",
        "perplexity",
        # Ajoutés le 24/08/2026 : sans eux, la clé d'API de ces fournisseurs
        # ne peut même pas être enregistrée.
        "glm", "kimi", "qwen", "minimax",
    ]
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
    address: str = ""
    siren: str = ""
    tva_intra: str = ""
    siret: str = ""
    code_ape: str = ""
    nda: str = ""


class UserProfileResponse(BaseModel):
    """User profile response."""

    name: str
    nickname: str
    company: str
    role: str
    context: str
    email: str
    location: str
    address: str = ""
    siren: str = ""
    tva_intra: str = ""
    siret: str = ""
    code_ape: str = ""
    nda: str = ""
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

    provider: Literal[
        "anthropic",
        "openai",
        "gemini",
        "mistral",
        "grok",
        "openrouter",
        "perplexity",
        "deepseek",
        "infomaniak",
        # Ajoutés le 24/08/2026. Sans ces valeurs, les classes de fournisseur
        # existaient mais AUCUNE configuration n'était acceptée : le travail
        # était invisible depuis l'application.
        "glm",
        "kimi",
        "qwen",
        "minimax",
        "ollama",
    ]
    model: str
    # Dette 0.43.4 : l'adresse Qwen contient l'identifiant d'espace de travail
    # du compte - sans ce champ, le fournisseur ne marchait pour personne.
    # None = conserver l'adresse deja enregistree ; "" = l'effacer.
    base_url: str | None = None
    # Effort de raisonnement (10/07/2026) : auto = defaut serveur (rien
    # d'envoye). None = ne pas toucher au reglage existant.
    effort: Literal["auto", "low", "medium", "high", "max"] | None = None


class LLMConfigResponse(BaseModel):
    """LLM configuration response."""

    provider: str
    model: str
    available_models: list[str] = []
    available: bool = False
    effort: str | None = None  # Effort de raisonnement courant (None = Auto)
    base_url: str | None = None  # Adresse personnalisee (Qwen : espace de travail)


class OllamaModelInfo(BaseModel):
    """Ollama model information."""

    name: str
    size: int | None = None
    modified_at: str | None = None
    digest: str | None = None
    usage_type: str = "chat"  # chat, embedding, vision, transcription
    # BUG-169. Un modèle sans appel d'outils ne peut ni créer un contact, ni
    # poser un rendez-vous, ni produire un document. Le masquer laisserait une
    # liste vide sans explication ; on le marque pour que l'interface le montre
    # désactivé, avec son motif.
    gere_les_outils: bool = True
    motif_indisponible: str | None = None


class OllamaModelRecommendation(BaseModel):
    """Recommandation de modèle Ollama selon la tâche."""

    general: str | None = None
    coding: str | None = None
    writing: str | None = None
    fast: str | None = None


class OllamaStatusResponse(BaseModel):
    """Ollama status response."""

    available: bool
    base_url: str
    models: list[OllamaModelInfo] = []
    recommendations: OllamaModelRecommendation | None = None
    error: str | None = None


class SystemResourcesResponse(BaseModel):
    """Ressources utiles au choix prudent d'un modèle local."""

    total_ram_bytes: int | None
    safe_local_model_ram_bytes: int | None
    ollama_context_margin_bytes: int
    detection_method: str


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
    provider: str
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
    # « Bloque » n'est pas « annule ». Sans ce champ en LECTURE, un blocage
    # pose disparaissait a la relecture : l'application disait avoir
    # enregistre quelque chose qui s'evaporait.
    blocage: str | None = None


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
    # Fuseau IANA du poste (ex: "America/Toronto"). Indispensable pour que Google
    # interprète l'heure saisie dans le bon fuseau (sinon décalage selon le serveur).
    timezone: str | None = None

    @model_validator(mode="after")
    def validate_event_window(self) -> Self:
        """Refuse les événements ambigus ou incohérents avant tout fournisseur."""
        self.summary = self.summary.strip()
        if not self.summary:
            raise ValueError("Le titre de l'événement est obligatoire")

        timed_values = (self.start_datetime, self.end_datetime)
        dated_values = (self.start_date, self.end_date)
        timed_any, timed_complete = any(timed_values), all(timed_values)
        dated_any, dated_complete = any(dated_values), all(dated_values)
        if timed_any and not timed_complete:
            raise ValueError("Le début et la fin horodatés sont obligatoires ensemble")
        if dated_any and not dated_complete:
            raise ValueError("Les dates de début et de fin sont obligatoires ensemble")
        if timed_complete == dated_complete:
            raise ValueError("Renseigne soit des horaires, soit des dates de journée entière")

        try:
            if timed_complete:
                if self.start_datetime is None or self.end_datetime is None:
                    raise ValueError("Le début et la fin horodatés sont obligatoires ensemble")
                start: date = datetime.fromisoformat(self.start_datetime.replace("Z", "+00:00"))
                end: date = datetime.fromisoformat(self.end_datetime.replace("Z", "+00:00"))
            else:
                if self.start_date is None or self.end_date is None:
                    raise ValueError("Les dates de début et de fin sont obligatoires ensemble")
                start = date.fromisoformat(self.start_date)
                end = date.fromisoformat(self.end_date)
        except ValueError as exc:
            raise ValueError("Format de date ou d'heure invalide") from exc
        # BUG-144 : en journée entière, début = fin est un événement d'un seul
        # jour (la fin est INCLUSIVE dans l'app). Les horaires restent
        # strictement croissants.
        if timed_complete:
            if end <= start:
                raise ValueError("La fin doit être postérieure au début")
        elif end < start:
            raise ValueError("La fin ne peut pas précéder le début")

        if self.timezone:
            try:
                ZoneInfo(self.timezone)
            except ZoneInfoNotFoundError as exc:
                raise ValueError("Fuseau horaire IANA invalide") from exc

        for attendee in self.attendees or []:
            address = attendee.strip()
            if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", address):
                raise ValueError(f"Adresse participant invalide : {attendee}")
        return self


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
    timezone: str | None = None  # Fuseau IANA du poste (cf. CreateEventRequest)
    # B-481 : statut et rappels n'étaient jamais transmis au provider
    status: Literal["confirmed", "tentative", "cancelled"] | None = None
    reminders: list[int] | None = None


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
    contact_id: str | None = None


# B-185 : le domaine des tâches est déclaré partout (entité, docstring de la
# route de liste, `VALID_TASK_STATUSES` de l'import CRM, formulaire de
# l'écran) SAUF là où les valeurs entrent. Une tâche « nimportequoi » n'a
# aucune colonne au tableau : elle disparaît sans message.
TaskStatus = Literal["todo", "in_progress", "done", "cancelled"]
TaskPriority = Literal["low", "medium", "high", "urgent"]


def _titre_de_tache_non_vide(valeur: str) -> str:
    """Un intitulé fait de blancs est une ligne vide dans le tableau."""
    nettoye = valeur.strip()
    if not nettoye:
        raise ValueError("Le titre de la tâche ne peut pas être vide")
    return nettoye


class CreateTaskRequest(BaseModel):
    """Request pour créer une tâche."""

    title: str
    description: str | None = None
    status: TaskStatus = "todo"
    priority: TaskPriority = "medium"
    due_date: str | None = None  # ISO datetime
    project_id: str | None = None
    tags: list[str] | None = None
    contact_id: str | None = None

    @field_validator("title")
    @classmethod
    def _valider_titre(cls, valeur: str) -> str:
        return _titre_de_tache_non_vide(valeur)


class UpdateTaskRequest(BaseModel):
    """Request pour modifier une tâche."""

    title: str | None = None
    description: str | None = None
    # Le même trou côté PUT : borner la seule création laisserait la porte de
    # service ouverte sur exactement le même champ.
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: str | None = None
    project_id: str | None = None
    tags: list[str] | None = None
    # B-032 : ce champ vivait APRÈS le bandeau « INVOICE SCHEMAS » ci-dessous.
    # Trois commentaires en colonne 0 ne dédentent rien, il appartenait donc
    # bien à cette classe - mais plus personne ne le voyait, et le routeur
    # avait cessé de l'écrire. Remis à sa place, à côté de son jumeau
    # `project_id`.
    contact_id: str | None = None

    @field_validator("title")
    @classmethod
    def _valider_titre(cls, valeur: str | None) -> str | None:
        return None if valeur is None else _titre_de_tache_non_vide(valeur)


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
    contact_id: str | None
    # B4 : « Je ne retiens pas les numéros DEV-2026-001, je retiens
    # Moreau. » Un join, pas une dénormalisation : Invoice.contact
    # existe déjà.
    contact_name: str | None = None
    document_type: str = "facture"  # devis, facture, avoir
    tva_applicable: bool = True
    currency: Literal["EUR", "CHF", "USD", "GBP", "CAD"] = "EUR"
    issue_date: str  # ISO datetime
    due_date: str  # ISO datetime
    status: str  # draft, sent, paid, overdue, cancelled
    subtotal_ht: float
    total_tax: float
    total_ttc: float
    notes: str | None
    payment_terms: str | None = None
    payment_method: str | None = None
    late_penalty_rate: float | None = None
    legal_mentions: str | None = None
    converted_from_id: str | None = None
    validite_jours: int | None = None  # Duree de validite en jours (devis)
    payment_date: str | None  # ISO datetime
    created_at: str  # ISO datetime
    updated_at: str  # ISO datetime
    lines: list[InvoiceLineResponse] = []


class InvoiceLineRequest(BaseModel):
    """Request pour une ligne de facture.

    Bornes posées en 0.55 : le garde-fou n'existait que dans le formulaire
    (`InvoiceForm.tsx` refuse quantity < 1 et unit_price_ht < 0). L'API et le
    serveur MCP acceptaient tout, et un montant négatif produit un avoir
    FANTÔME - un encours négatif sans qu'aucun avoir existe.

    Un avoir est un `document_type` à part entière, avec un `total_ttc` stocké
    positif : le borner ici ne l'empêche pas.

    On refuse le négatif, pas la gratuité : une ligne offerte à 0 EUR reste
    possible, l'écran l'autorise. Et la quantité accepte le fractionnaire
    (une demi-journée de formation), seulement pas le zéro ni le négatif.
    """

    description: str
    quantity: float = Field(default=1.0, gt=0)
    unit_price_ht: float = Field(ge=0)
    tva_rate: float = Field(default=20.0, ge=0)  # Default TVA française normale


class CreateInvoiceRequest(BaseModel):
    """Request pour créer une facture."""

    contact_id: str
    document_type: str = "facture"  # devis, facture, avoir
    tva_applicable: bool = True
    currency: Literal["EUR", "CHF", "USD", "GBP", "CAD"] = "EUR"
    issue_date: str | None = None  # ISO datetime, default today
    due_date: str | None = None  # ISO datetime, default +30 days
    lines: list[InvoiceLineRequest]
    notes: str | None = None
    validite_jours: int | None = None  # Duree de validite en jours (devis, defaut 30)


class UpdateInvoiceRequest(BaseModel):
    """Request pour modifier une facture."""

    contact_id: str | None = None
    currency: Literal["EUR", "CHF", "USD", "GBP", "CAD"] | None = None
    issue_date: str | None = None
    due_date: str | None = None
    status: str | None = None
    lines: list[InvoiceLineRequest] | None = None
    notes: str | None = None
    validite_jours: int | None = None  # Duree de validite en jours (devis)


class MarkPaidRequest(BaseModel):
    """Request pour marquer une facture comme payée."""

    payment_date: str | None = None  # ISO datetime, default today


class ConvertDevisRequest(BaseModel):
    """Request pour convertir un devis en facture."""

    payment_terms: str = "30 jours"
    payment_method: str = "Virement bancaire"



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
    # B-206 : instant d'horloge serveur, donc daté (cf. `HorodatageUTC`). Sans
    # fuseau, le navigateur lisait cette heure UTC comme la sienne et une
    # activité de trois minutes s'affichait « Il y a 2h ».
    created_at: HorodatageUTC
    statut: str = "en_vigueur"
    remplace_id: str | None = None


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
    # `due_date` reste une heure de mur : c'est un JOUR décidé par quelqu'un
    # (`<input type="date">`), et le dater le ferait basculer d'un jour.
    due_date: str | None  # ISO datetime
    # B-206 : les trois autres sont écrits par l'horloge du serveur.
    completed_at: HorodatageUTC | None
    created_at: HorodatageUTC
    updated_at: HorodatageUTC


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

    # B-167 : la porte de déplacement dans le pipeline partage le domaine des
    # sept colonnes affichables.
    stage: EtapePipeline


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

    # B-498 (05/09/2026) : mêmes bornes que ContactCreate, la porte CRM
    # acceptait un prénom de dix mille caractères.
    first_name: str = Field(max_length=LONGUEUR_NOM)
    last_name: str | None = Field(default=None, max_length=LONGUEUR_NOM)
    company: str | None = Field(default=None, max_length=LONGUEUR_NOM)
    email: str | None = Field(default=None, max_length=LONGUEUR_EMAIL)
    phone: str | None = Field(default=None, max_length=LONGUEUR_TELEPHONE)
    source: str | None = Field(default=None, max_length=LONGUEUR_NOM)
    # B-167 : la création CRM écrit dans le MÊME pipeline que la création
    # mémoire ; elle partage donc le domaine des sept étapes affichables.
    stage: EtapePipeline = "contact"
    # QW1 : ces champs étaient jetés silencieusement à la création (la note métier
    # n'était ni stockée, ni cherchable). Cf. 2e passage personas (RH/santé/compta).
    notes: str | None = Field(default=None, max_length=LONGUEUR_NOTES)
    address: str | None = Field(default=None, max_length=LONGUEUR_ADRESSE)
    tags: list[str] | None = None


# ============================================================
# Notification Schemas (US-004 - v0.9.0)
# ============================================================


class NotificationResponse(BaseModel):
    """Response schema pour une notification."""

    id: str
    title: str
    message: str
    type: str  # info, warning, action, reminder
    source: str  # crm, invoice, calendar, task, agent, system
    action_url: str | None = None
    action_label: str | None = None
    is_read: bool
    created_at: str  # ISO datetime
    read_at: str | None = None


class NotificationCountResponse(BaseModel):
    """Response pour le compteur de notifications non lues."""

    unread_count: int
