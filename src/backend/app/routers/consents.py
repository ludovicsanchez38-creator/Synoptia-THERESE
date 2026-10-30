"""Accords de transfert cloud ; le moteur date chaque décision."""
from datetime import datetime
from typing import Any, Literal

from app.services.consentements import (
    accords_courants,
    enregistrer_accord,
    historique,
    importer_accords,
)
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

router = APIRouter()
Purpose = Literal['llm', 'documents', 'images', 'voice']


class Decision(BaseModel):
    data_profile: str | None = None
    event_id: str | None = Field(default=None, max_length=64, pattern=r'^[a-zA-Z0-9-]+$')
    occurred_at: datetime | None = None
    purpose: Purpose
    provider: str = Field(min_length=1, max_length=64, pattern=r'^[a-zA-Z0-9_-]+$')
    granted: bool
    text_version: Literal['3']
    data_categories: list[str] = Field(default_factory=list, max_length=40)


class LegacyGrant(BaseModel):
    purpose: Purpose
    provider: str = Field(min_length=1, max_length=64, pattern=r'^[a-zA-Z0-9_-]+$')
    timestamp: str
    dataCategories: list[str] | None = None

    @field_validator('timestamp')
    @classmethod
    def date_iso(cls, value: str) -> str:
        date = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if date.tzinfo is None:
            raise ValueError('La date doit indiquer son fuseau horaire.')
        return value


class LegacyImport(BaseModel):
    data_profile: str | None = None
    grants: list[LegacyGrant] = Field(default_factory=list, max_length=256)


def _verifier_profil(data_profile: str | None) -> None:
    from pathlib import Path

    from app.config import settings

    if data_profile is not None and (settings.data_dir is None
            or Path(data_profile).resolve() != Path(settings.data_dir).resolve()):
        raise HTTPException(409, "Le profil a changé. Reviens au profil concerné avant de réessayer.")


@router.get('')
def lire() -> dict[str, Any]:
    return {'grants': accords_courants(), 'history': historique()}


@router.post('')
def decider(decision: Decision) -> dict[str, Any]:
    _verifier_profil(decision.data_profile)
    enregistrer_accord(decision.purpose, decision.provider, decision.granted,
                      decision.text_version, decision.data_categories, decision.event_id,
                      decision.occurred_at.isoformat() if decision.occurred_at else None)
    return lire()


@router.post('/import')
def reprendre(data: LegacyImport) -> dict[str, Any]:
    _verifier_profil(data.data_profile)
    importer_accords([g.model_dump() for g in data.grants])
    return lire()
