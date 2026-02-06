"""
THÉRÈSE v2 - Skills Base

Classes abstraites et modèles de base pour le système de skills.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class FileFormat(str, Enum):
    """Formats de fichiers supportés."""
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    PDF = "pdf"
    MD = "md"


class SkillOutputType(str, Enum):
    """Types de sortie pour les skills."""
    TEXT = "text"          # Texte affiché dans le chat
    FILE = "file"          # Fichier téléchargeable
    ANALYSIS = "analysis"  # Analyse avec insights


@dataclass
class InputField:
    """
    Définition d'un champ d'entrée pour un skill.

    Utilisé pour générer dynamiquement les formulaires côté frontend.
    """
    type: str  # 'text', 'textarea', 'select', 'number', 'file'
    label: str
    placeholder: str = ""
    required: bool = True
    options: list[str] = field(default_factory=list)  # Pour type='select'
    default: str | None = None
    help_text: str | None = None  # Texte d'aide affiché sous le champ


class SkillParams(BaseModel):
    """Paramètres d'entrée pour un skill."""
    title: str = Field(..., description="Titre du document")
    content: str = Field(..., description="Contenu principal généré par le LLM")
    template: str = Field(default="synoptia-dark", description="Style/template à appliquer")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Métadonnées additionnelles")


class SkillResult(BaseModel):
    """Résultat d'exécution d'un skill."""
    file_id: str = Field(..., description="Identifiant unique du fichier")
    file_path: Path = Field(..., description="Chemin vers le fichier généré")
    file_name: str = Field(..., description="Nom du fichier")
    file_size: int = Field(..., description="Taille en octets")
    mime_type: str = Field(..., description="Type MIME du fichier")
    format: FileFormat = Field(..., description="Format du fichier")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Config:
        arbitrary_types_allowed = True


class SkillExecuteRequest(BaseModel):
    """Requête d'exécution d'un skill depuis l'API."""
    prompt: str = Field(..., description="Prompt utilisateur pour générer le contenu")
    title: str | None = Field(None, description="Titre du document (si non fourni, sera extrait du prompt)")
    template: str = Field(default="synoptia-dark", description="Style/template")
    context: dict[str, Any] = Field(default_factory=dict, description="Contexte additionnel")


class SkillExecuteResponse(BaseModel):
    """Réponse après exécution d'un skill."""
    success: bool
    file_id: str | None = None
    file_name: str | None = None
    file_size: int | None = None
    download_url: str = Field(..., description="URL de téléchargement")
    preview: str | None = Field(None, description="Aperçu textuel du contenu généré")
    error: str | None = None


class BaseSkill(ABC):
    """
    Classe abstraite pour tous les skills de génération de documents.

    Chaque skill implémente la génération d'un type de document spécifique
    (Word, PowerPoint, Excel) avec le style Synoptïa, ou génère du texte/analyse.
    """

    # Métadonnées du skill (à définir dans les sous-classes)
    skill_id: str
    name: str
    description: str
    output_format: FileFormat  # Utilisé uniquement pour les skills FILE
    output_type: SkillOutputType = SkillOutputType.FILE  # Par défaut : fichier

    def __init__(self, output_dir: Path):
        """
        Initialise le skill.

        Args:
            output_dir: Répertoire où sauvegarder les fichiers générés
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_file_id(self) -> str:
        """Génère un identifiant unique pour le fichier."""
        return str(uuid4())

    def get_output_path(self, file_id: str, title: str) -> Path:
        """
        Génère le chemin de sortie pour un fichier.

        Args:
            file_id: Identifiant unique du fichier
            title: Titre pour le nom du fichier

        Returns:
            Chemin complet vers le fichier
        """
        # Nettoyer le titre pour en faire un nom de fichier valide
        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)
        safe_title = safe_title[:50].strip()  # Limiter la longueur

        filename = f"{safe_title}_{file_id[:8]}.{self.output_format.value}"
        return self.output_dir / filename

    def get_input_schema(self) -> dict[str, InputField]:
        """
        Définit le schéma des champs d'entrée pour ce skill.

        Utilisé pour générer dynamiquement le formulaire côté frontend.

        Returns:
            Dictionnaire mapping nom du champ → InputField

        Example:
            {
                'recipient': InputField(
                    type='text',
                    label='Destinataire',
                    placeholder='Nom de la personne',
                    required=True
                ),
                'tone': InputField(
                    type='select',
                    label='Ton',
                    options=['formel', 'amical', 'neutre'],
                    default='formel',
                    required=False
                )
            }
        """
        # Implémentation par défaut pour les skills FILE legacy (DOCX, PPTX, XLSX)
        # Ces skills utilisent l'ancien flow avec prompt libre
        return {
            'prompt': InputField(
                type='textarea',
                label='Prompt',
                placeholder='Décris ce que tu veux créer...',
                required=True,
                help_text='Décris le document à générer'
            )
        }

    def get_enrichment_context(self, user_profile: dict[str, Any], memory_context: dict[str, Any]) -> dict[str, Any]:
        """
        Enrichit le contexte avec des informations additionnelles.

        Cette méthode peut être surchargée par les skills pour ajouter
        du contexte spécifique (profil utilisateur, mémoire CRM, etc.).

        Args:
            user_profile: Profil de l'utilisateur (nom, entreprise, rôle)
            memory_context: Contexte mémoire (contacts, projets)

        Returns:
            Dictionnaire de contexte enrichi à injecter dans le prompt

        Example:
            {
                'sender_name': 'Ludo Sanchez',
                'sender_company': 'Synoptïa',
                'sender_role': 'Consultant IA',
                'recipient_context': 'Client actif depuis 2 mois'
            }
        """
        # Implémentation par défaut : retourne le profil utilisateur
        return {
            'user_name': user_profile.get('name', ''),
            'user_company': user_profile.get('company', ''),
            'user_role': user_profile.get('role', ''),
        }

    @abstractmethod
    async def execute(self, params: SkillParams) -> SkillResult:
        """
        Génère le fichier.

        Args:
            params: Paramètres de génération

        Returns:
            Résultat avec informations sur le fichier généré
        """
        pass

    @abstractmethod
    def get_system_prompt_addition(self) -> str:
        """
        Instructions spécifiques à ajouter au prompt système pour le LLM.

        Ces instructions guident le LLM pour générer du contenu structuré
        adapté au format de sortie (Word, PowerPoint, Excel).

        Returns:
            Instructions à ajouter au prompt système
        """
        pass

    def get_mime_type(self) -> str:
        """Retourne le type MIME du format de sortie."""
        mime_types = {
            FileFormat.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            FileFormat.PPTX: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            FileFormat.XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            FileFormat.PDF: "application/pdf",
            FileFormat.MD: "text/markdown",
        }
        return mime_types.get(self.output_format, "application/octet-stream")


class MarkdownSkill(BaseSkill):
    """Classe de base pour les skills TEXT/ANALYSIS/PLANNING.

    Sauvegarde la réponse du LLM en fichier .md téléchargeable.
    """
    output_format = FileFormat.MD

    async def execute(self, params: SkillParams) -> SkillResult:
        file_id = self.generate_file_id()
        output_path = self.get_output_path(file_id, params.title)

        content = params.content or ""
        output_path.write_text(content, encoding="utf-8")

        return SkillResult(
            file_id=file_id,
            file_path=output_path,
            file_name=output_path.name,
            file_size=output_path.stat().st_size,
            mime_type="text/markdown",
            format=FileFormat.MD,
        )
