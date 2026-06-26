"""
THÉRÈSE v2 - Schemas Voice

Request/Response models pour la transcription vocale.
"""

from pydantic import BaseModel


class TranscriptionResponse(BaseModel):
    """Transcription response."""

    text: str
    duration_seconds: float | None = None
    language: str | None = None


class TTSRequest(BaseModel):
    """Requête de synthèse vocale locale (Piper)."""

    text: str
    voice: str | None = None
