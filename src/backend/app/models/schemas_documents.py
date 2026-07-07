"""
THÉRÈSE v2 - Schemas Documents

Request/Response models pour l'atelier documentaire.
"""

from datetime import datetime

from pydantic import BaseModel


class DocumentCreate(BaseModel):
    """Requête de création d'un document."""

    title: str
    brief: str
    project_id: str | None = None
    contact_id: str | None = None


class DocumentResponse(BaseModel):
    """Réponse d'un document, avec le décompte de ses sections."""

    id: str
    title: str
    brief: str
    status: str
    project_id: str | None
    contact_id: str | None
    created_at: datetime
    updated_at: datetime
    sections_total: int
    sections_validees: int


class SectionResponse(BaseModel):
    """Réponse d'une section de document."""

    id: str
    document_id: str
    title: str
    brief: str
    order: float
    depth: int
    content: str
    summary: str
    status: str
    orphan: bool
    created_at: datetime
    updated_at: datetime


class SectionUpdate(BaseModel):
    """Requête de mise à jour partielle d'une section."""

    title: str | None = None
    brief: str | None = None
    content: str | None = None
    order: float | None = None
    depth: int | None = None


class SectionsReorderItem(BaseModel):
    """Position cible d'une section dans une réorganisation de trame."""

    id: str
    order: float
    depth: int


class SectionsReorder(BaseModel):
    """Requête de réorganisation de la trame d'un document."""

    items: list[SectionsReorderItem]


class PisteResponse(BaseModel):
    """Réponse d'une piste (idée annexe capturée pendant la rédaction)."""

    id: str
    document_id: str
    section_origine_id: str | None
    texte: str
    status: str
    created_at: datetime


class PisteUpdate(BaseModel):
    """Requête de mise à jour du statut d'une piste."""

    status: str


class DraftRequest(BaseModel):
    """Requête de génération de brouillon pour une section, avec consigne optionnelle."""

    instruction: str | None = None
