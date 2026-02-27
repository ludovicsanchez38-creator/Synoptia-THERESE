"""
THÉRÈSE V3 - Modèle CommandDefinition

Modèle unifié pour toutes les commandes : builtins, skills, user, MCP.
"""

from enum import Enum

from pydantic import BaseModel, Field


class CommandSource(str, Enum):
    """Origine de la commande."""
    BUILTIN = "builtin"     # Ex-guided prompts + ex-slash commands
    SKILL = "skill"         # Liées à un BaseSkill backend
    USER = "user"           # Créées par l'utilisateur (fichiers .md)
    MCP = "mcp"             # Futures : exposées par un serveur MCP


class CommandAction(str, Enum):
    """Type d'action exécutée par la commande."""
    PROMPT = "prompt"                      # Injecte un prompt dans le chat
    FORM_THEN_PROMPT = "form_then_prompt"  # Formulaire dynamique → prompt + skill_id
    FORM_THEN_FILE = "form_then_file"      # Formulaire → génère fichier
    IMAGE = "image"                        # Génère une image
    NAVIGATE = "navigate"                  # Ouvre un panel (email, calendrier...)
    RFC = "rfc"                            # Lance le workflow Réfléchir-Faire-Capturer


class CommandDefinition(BaseModel):
    """Définition unifiée d'une commande THÉRÈSE."""

    id: str = Field(..., description="Slug unique de la commande")
    name: str = Field(..., description="Nom affiché")
    description: str = Field("", description="Description courte")
    icon: str = Field("", description="Emoji ou nom d'icône Lucide")
    category: str = Field("general", description="Catégorie : production, analyse, organisation")
    source: CommandSource = Field(..., description="Origine de la commande")
    action: CommandAction = Field(..., description="Type d'action")
    prompt_template: str = Field("", description="Template avec {{placeholders}}")
    skill_id: str | None = Field(None, description="Lien vers un BaseSkill")
    system_prompt: str | None = Field(None, description="System prompt spécialisé")
    show_on_home: bool = Field(False, description="Afficher sur la page d'accueil")
    show_in_slash: bool = Field(True, description="Afficher dans le menu /")
    sort_order: int = Field(100, description="Ordre de tri")
    image_config: dict | None = Field(None, description="Config image (provider, size, quality)")
    navigate_target: str | None = Field(None, description="Panel cible pour action navigate")
    is_editable: bool = Field(False, description="True pour les commandes user")


class CommandDefinitionResponse(BaseModel):
    """Réponse API pour une commande."""

    id: str
    name: str
    description: str
    icon: str
    category: str
    source: CommandSource
    action: CommandAction
    prompt_template: str
    skill_id: str | None = None
    system_prompt: str | None = None
    show_on_home: bool
    show_in_slash: bool
    sort_order: int
    image_config: dict | None = None
    navigate_target: str | None = None
    is_editable: bool


class CreateUserCommandRequest(BaseModel):
    """Requête de création de commande utilisateur V3."""

    name: str = Field(..., min_length=1, max_length=50)
    description: str = Field("", max_length=200)
    icon: str = Field("", max_length=10)
    category: str = Field("production", max_length=50)
    prompt_template: str = Field("", description="Template avec {{placeholders}}")
    show_on_home: bool = True
    show_in_slash: bool = True


class UpdateUserCommandRequest(BaseModel):
    """Requête de mise à jour de commande utilisateur V3."""

    name: str | None = None
    description: str | None = None
    icon: str | None = None
    category: str | None = None
    prompt_template: str | None = None
    show_on_home: bool | None = None
    show_in_slash: bool | None = None


class GenerateTemplateRequest(BaseModel):
    """Requête RFC : générer un template de commande depuis un brief."""

    brief: str = Field(..., description="Description libre de ce que la commande doit faire")
    context: list[dict] | None = Field(None, description="Messages de contexte RFC")
