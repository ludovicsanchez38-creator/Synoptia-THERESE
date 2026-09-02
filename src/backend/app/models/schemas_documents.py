"""
THÉRÈSE v2 - Schemas Documents

Request/Response models pour l'atelier documentaire.
"""

from datetime import datetime

from pydantic import BaseModel, Field


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
    # B-184 : `order` est la clé de tri de la trame, et la colonne est NOT NULL.
    # Sans cette borne, « Infinity » passait en 200 puis se relisait `null` sur
    # un champ déclaré `number` et requis, et « NaN » finissait en 500.
    order: float | None = Field(default=None, allow_inf_nan=False)
    depth: int | None = None


class SectionsReorderItem(BaseModel):
    """Position cible d'une section dans une réorganisation de trame."""

    id: str
    order: float = Field(..., allow_inf_nan=False)  # B-184 : même clé de tri
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
