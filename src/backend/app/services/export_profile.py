"""
THERESE v2 - Profil d'export documentaire (chantier 5, design V2 du 10/07).

Un profil GLOBAL (langue, polices, couleurs, footer, marges) pilote le rendu
DOCX déterministe (markdown_docx : exports Atelier + conversations). Les DOCX
du chat (docx-pro) restent sur leur pipeline - hors périmètre.

Contrat (revue Codex intégrée) :
- schéma Pydantic VERSIONNÉ, strict et borné (défauts = charte actuelle,
  zéro changement si non configuré) ;
- JSON dans le data dir, écriture ATOMIQUE (tmp + rename) ;
- fichier corrompu/invalide -> repli défauts + avertissement SURFACÉ à
  l'appelant (le fichier fautif est conservé pour diagnostic).
"""

import json
import logging
import os
import re
import tempfile
from pathlib import Path

from app.config import get_settings
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

_HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
_PROFILE_FILENAME = "export_profile.json"
_MAX_FILE_BYTES = 64 * 1024  # un profil légitime pèse < 1 Ko


class ExportMargins(BaseModel):
    """Marges de page en centimètres (bornées : 0.5 à 8 cm)."""

    top: float = Field(default=2.5, ge=0.5, le=8)
    bottom: float = Field(default=2.5, ge=0.5, le=8)
    left: float = Field(default=2.5, ge=0.5, le=8)
    right: float = Field(default=2.5, ge=0.5, le=8)


class ExportProfile(BaseModel):
    """Profil d'export DOCX. Les DÉFAUTS reproduisent la charte actuelle
    (Calibri 11, Outfit pour les titres, couleurs Synoptia, fr-FR)."""

    version: int = Field(default=1, ge=1, le=1)
    language: str = Field(default="fr-FR", min_length=2, max_length=15)
    body_font: str = Field(default="Calibri", min_length=1, max_length=64)
    body_size_pt: int = Field(default=11, ge=6, le=72)
    heading_font: str = Field(default="Outfit", min_length=1, max_length=64)
    # Couleurs de la charte actuelle (docx_generator.SYNOPTIA_COLORS)
    title_color: str = Field(default="#0F1E6D", description="Titre principal (hero H1)")
    heading_color: str = Field(default="#0F1E6D", description="H1/H3/H4")
    h2_color: str = Field(default="#1733A6", description="H2 - distincte dans la charte")
    body_color: str = Field(default="#1A1A2E")
    footer_text: str = Field(default="Généré par THÉRÈSE - Synoptïa", max_length=200)
    margins_cm: ExportMargins = Field(default_factory=ExportMargins)

    @field_validator("title_color", "heading_color", "h2_color", "body_color")
    @classmethod
    def _hex_color(cls, v: str) -> str:
        if not _HEX_COLOR.match(v):
            raise ValueError("couleur attendue au format #RRGGBB")
        return v

    @field_validator("language")
    @classmethod
    def _language(cls, v: str) -> str:
        if not re.match(r"^[A-Za-z]{2}(-[A-Za-z]{2})?$", v):
            raise ValueError("langue attendue au format xx ou xx-XX (ex : fr-FR)")
        return v


def export_profile_path() -> Path:
    settings = get_settings()
    return Path(settings.data_dir) / _PROFILE_FILENAME


def load_export_profile() -> tuple[ExportProfile, str | None]:
    """Charge le profil. Absent -> défauts sans avertissement. Corrompu ou
    invalide -> défauts + avertissement (le fichier fautif est CONSERVÉ)."""
    path = export_profile_path()
    if not path.exists():
        return ExportProfile(), None
    try:
        if path.stat().st_size > _MAX_FILE_BYTES:
            raise ValueError(f"fichier trop volumineux ({path.stat().st_size} octets)")
        data = json.loads(path.read_text(encoding="utf-8"))
        return ExportProfile.model_validate(data), None
    except Exception as e:  # noqa: BLE001 - le repli défauts EST le contrat
        warning = (
            f"Profil d'export illisible ({e.__class__.__name__}) : les réglages "
            "par défaut sont utilisés. Corrige ou réinitialise le profil dans "
            "Paramètres > Exports."
        )
        logger.warning("Profil d'export illisible (%s) : repli défauts", e)
        return ExportProfile(), warning


def save_export_profile(profile: ExportProfile) -> None:
    """Écriture atomique : tmp dans le même dossier puis rename."""
    path = export_profile_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(profile.model_dump(), ensure_ascii=False, indent=2)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
        os.replace(tmp_name, path)
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def reset_export_profile() -> None:
    export_profile_path().unlink(missing_ok=True)
