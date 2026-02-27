"""
THÉRÈSE V3 - Command Registry

Registre unifié de toutes les commandes : builtins, skills, user, MCP.
Wrappe les BaseSkill existants et les user commands en CommandDefinition.
"""

import logging
from typing import Optional

from app.models.command import (
    CommandAction,
    CommandDefinition,
    CommandSource,
)
from app.services.skills.base import SkillOutputType
from app.services.skills.registry import get_skills_registry
from app.services.user_commands import UserCommandsService

logger = logging.getLogger(__name__)


# Mapping skill_id → catégorie (conserve la logique de actionData.ts)
_SKILL_CATEGORIES: dict[str, str] = {
    # Production
    "email-pro": "production",
    "linkedin-post": "production",
    "proposal-pro": "production",
    "docx-pro": "production",
    "pptx-pro": "production",
    "xlsx-pro": "production",
    # Analyse
    "analyze-xlsx": "analyse",
    "analyze-pdf": "analyse",
    "analyze-website": "analyse",
    "market-research": "analyse",
    "analyze-ai-tool": "analyse",
    "explain-concept": "analyse",
    "best-practices": "analyse",
    # Organisation
    "plan-meeting": "organisation",
    "plan-project": "organisation",
    "plan-week": "organisation",
    "plan-goals": "organisation",
    "workflow-automation": "organisation",
}

# Mapping skill_id → icône
_SKILL_ICONS: dict[str, str] = {
    "email-pro": "Mail",
    "linkedin-post": "Linkedin",
    "proposal-pro": "FileText",
    "docx-pro": "FileText",
    "pptx-pro": "Presentation",
    "xlsx-pro": "FileSpreadsheet",
    "analyze-xlsx": "FileSpreadsheet",
    "analyze-pdf": "FileText",
    "analyze-website": "Globe",
    "market-research": "TrendingUp",
    "analyze-ai-tool": "Bot",
    "explain-concept": "Lightbulb",
    "best-practices": "CheckCircle",
    "plan-meeting": "Calendar",
    "plan-project": "FolderKanban",
    "plan-week": "CalendarDays",
    "plan-goals": "Target",
    "workflow-automation": "Workflow",
}

# Mapping skill_id → nom affiché
_SKILL_NAMES: dict[str, str] = {
    "email-pro": "Email pro",
    "linkedin-post": "Post LinkedIn",
    "proposal-pro": "Proposition commerciale",
    "docx-pro": "Document Word",
    "pptx-pro": "Présentation PPT",
    "xlsx-pro": "Tableur Excel",
    "analyze-xlsx": "Fichier Excel",
    "analyze-pdf": "Document PDF",
    "analyze-website": "Site web",
    "market-research": "Marché",
    "analyze-ai-tool": "Outil IA",
    "explain-concept": "Concept",
    "best-practices": "Best practices",
    "plan-meeting": "Réunion",
    "plan-project": "Projet",
    "plan-week": "Semaine",
    "plan-goals": "Objectifs",
    "workflow-automation": "Workflow",
}

# Ordre de tri par skill_id
_SKILL_SORT_ORDER: dict[str, int] = {
    "email-pro": 10,
    "linkedin-post": 20,
    "proposal-pro": 30,
    "docx-pro": 40,
    "pptx-pro": 50,
    "xlsx-pro": 60,
    "analyze-xlsx": 10,
    "analyze-pdf": 20,
    "analyze-website": 30,
    "market-research": 40,
    "analyze-ai-tool": 50,
    "explain-concept": 60,
    "best-practices": 70,
    "plan-meeting": 10,
    "plan-project": 20,
    "plan-week": 30,
    "plan-goals": 40,
    "workflow-automation": 50,
}


class CommandRegistry:
    """Registre unifié de toutes les commandes."""

    _instance: Optional["CommandRegistry"] = None

    def __init__(self) -> None:
        self._commands: dict[str, CommandDefinition] = {}

    @classmethod
    def get_instance(cls) -> "CommandRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def init(self) -> None:
        """Initialise le registre avec toutes les sources de commandes."""
        self._commands.clear()
        self._register_builtin_commands()
        self._register_skill_commands()
        await self._load_user_commands()
        logger.info(f"CommandRegistry initialisé avec {len(self._commands)} commandes")

    def _register_builtin_commands(self) -> None:
        """Enregistre les commandes builtins (ex-slash commands + images)."""
        builtins = [
            # Ex-slash commands
            CommandDefinition(
                id="contact",
                name="contact",
                description="Mentionner ou créer un contact",
                icon="UserPlus",
                category="builtin",
                source=CommandSource.BUILTIN,
                action=CommandAction.PROMPT,
                prompt_template="/contact ",
                show_on_home=False,
                show_in_slash=True,
                sort_order=10,
            ),
            CommandDefinition(
                id="projet",
                name="projet",
                description="Mentionner ou créer un projet",
                icon="FolderPlus",
                category="builtin",
                source=CommandSource.BUILTIN,
                action=CommandAction.PROMPT,
                prompt_template="/projet ",
                show_on_home=False,
                show_in_slash=True,
                sort_order=20,
            ),
            CommandDefinition(
                id="recherche",
                name="recherche",
                description="Rechercher dans la mémoire",
                icon="Search",
                category="builtin",
                source=CommandSource.BUILTIN,
                action=CommandAction.PROMPT,
                prompt_template="/recherche ",
                show_on_home=False,
                show_in_slash=True,
                sort_order=30,
            ),
            CommandDefinition(
                id="fichier",
                name="fichier",
                description="Analyser un fichier local",
                icon="FileText",
                category="builtin",
                source=CommandSource.BUILTIN,
                action=CommandAction.PROMPT,
                prompt_template="/fichier ",
                show_on_home=False,
                show_in_slash=True,
                sort_order=40,
            ),
            CommandDefinition(
                id="resume",
                name="résumé",
                description="Résumer la conversation",
                icon="Sparkles",
                category="builtin",
                source=CommandSource.BUILTIN,
                action=CommandAction.PROMPT,
                prompt_template="/résumé",
                show_on_home=False,
                show_in_slash=True,
                sort_order=50,
            ),
            CommandDefinition(
                id="taches",
                name="tâches",
                description="Extraire les tâches de la conversation",
                icon="ListTodo",
                category="builtin",
                source=CommandSource.BUILTIN,
                action=CommandAction.PROMPT,
                prompt_template="/tâches",
                show_on_home=False,
                show_in_slash=True,
                sort_order=60,
            ),
            CommandDefinition(
                id="email",
                name="email",
                description="Rédiger un email",
                icon="Mail",
                category="builtin",
                source=CommandSource.BUILTIN,
                action=CommandAction.PROMPT,
                prompt_template="/email ",
                show_on_home=False,
                show_in_slash=True,
                sort_order=70,
            ),
            CommandDefinition(
                id="rdv",
                name="rdv",
                description="Préparer un rendez-vous",
                icon="Calendar",
                category="builtin",
                source=CommandSource.BUILTIN,
                action=CommandAction.PROMPT,
                prompt_template="/rdv ",
                show_on_home=False,
                show_in_slash=True,
                sort_order=80,
            ),
            # Images - affiché sur l'accueil
            CommandDefinition(
                id="image-gpt",
                name="Image IA (GPT)",
                description="Générer une image avec GPT",
                icon="ImagePlus",
                category="production",
                source=CommandSource.BUILTIN,
                action=CommandAction.IMAGE,
                show_on_home=True,
                show_in_slash=True,
                sort_order=70,
                image_config={
                    "provider": "gpt-image-1.5",
                    "default_size": "1024x1024",
                    "default_quality": "high",
                },
            ),
            CommandDefinition(
                id="image-gemini",
                name="Image IA (Gemini)",
                description="Générer une image avec Gemini",
                icon="ImagePlus",
                category="production",
                source=CommandSource.BUILTIN,
                action=CommandAction.IMAGE,
                show_on_home=True,
                show_in_slash=True,
                sort_order=80,
                image_config={
                    "provider": "nanobanan-pro",
                    "default_size": "2K",
                    "default_quality": "high",
                },
            ),
            CommandDefinition(
                id="image-fal",
                name="Image IA (Fal)",
                description="Générer une image avec Fal Flux Pro",
                icon="ImagePlus",
                category="production",
                source=CommandSource.BUILTIN,
                action=CommandAction.IMAGE,
                show_on_home=True,
                show_in_slash=True,
                sort_order=90,
                image_config={
                    "provider": "fal-flux-pro",
                    "default_quality": "high",
                },
            ),
        ]

        for cmd in builtins:
            self._commands[cmd.id] = cmd

    def _register_skill_commands(self) -> None:
        """Wrappe les BaseSkill existants en CommandDefinition."""
        registry = get_skills_registry()
        for skill_info in registry.list_skills():
            skill_id = skill_info["skill_id"]
            skill = registry.get(skill_id)
            if not skill:
                continue

            # Déterminer l'action selon le type de sortie
            if skill.output_type == SkillOutputType.FILE:
                action = CommandAction.FORM_THEN_FILE
            else:
                action = CommandAction.FORM_THEN_PROMPT

            category = _SKILL_CATEGORIES.get(skill_id, "general")
            icon = _SKILL_ICONS.get(skill_id, "Zap")
            name = _SKILL_NAMES.get(skill_id, skill.name)
            sort_order = _SKILL_SORT_ORDER.get(skill_id, 100)

            cmd = CommandDefinition(
                id=skill_id,
                name=name,
                description=skill.description,
                icon=icon,
                category=category,
                source=CommandSource.SKILL,
                action=action,
                skill_id=skill_id,
                show_on_home=True,
                show_in_slash=True,
                sort_order=sort_order,
            )
            self._commands[cmd.id] = cmd

    async def _load_user_commands(self) -> None:
        """Charge les commandes utilisateur depuis ~/.therese/commands/user/."""
        service = UserCommandsService.get_instance()
        for user_cmd in service.list_commands():
            cmd = CommandDefinition(
                id=f"user-{user_cmd.name}",
                name=user_cmd.name,
                description=user_cmd.description,
                icon=user_cmd.icon,
                category=user_cmd.category or "production",
                source=CommandSource.USER,
                action=CommandAction.PROMPT,
                prompt_template=user_cmd.content,
                show_on_home=user_cmd.show_on_home,
                show_in_slash=True,
                sort_order=200,
                is_editable=True,
            )
            self._commands[cmd.id] = cmd

    def list(
        self,
        category: str | None = None,
        show_on_home: bool | None = None,
        show_in_slash: bool | None = None,
        source: str | None = None,
    ) -> list[CommandDefinition]:
        """Liste les commandes avec filtres optionnels."""
        result = list(self._commands.values())

        if category is not None:
            result = [c for c in result if c.category == category]
        if show_on_home is not None:
            result = [c for c in result if c.show_on_home == show_on_home]
        if show_in_slash is not None:
            result = [c for c in result if c.show_in_slash == show_in_slash]
        if source is not None:
            result = [c for c in result if c.source.value == source]

        return sorted(result, key=lambda c: (c.category, c.sort_order, c.name))

    def get(self, command_id: str) -> CommandDefinition | None:
        """Récupère une commande par son ID."""
        return self._commands.get(command_id)

    async def create_user_command(
        self,
        name: str,
        description: str = "",
        icon: str = "",
        category: str = "production",
        prompt_template: str = "",
        show_on_home: bool = True,
        show_in_slash: bool = True,
    ) -> CommandDefinition:
        """Crée une commande utilisateur et l'ajoute au registre."""
        service = UserCommandsService.get_instance()
        user_cmd = service.create_command(
            name=name,
            description=description,
            icon=icon,
            category=category,
            show_on_home=show_on_home,
            content=prompt_template,
        )

        cmd = CommandDefinition(
            id=f"user-{user_cmd.name}",
            name=user_cmd.name,
            description=user_cmd.description,
            icon=user_cmd.icon,
            category=category,
            source=CommandSource.USER,
            action=CommandAction.PROMPT,
            prompt_template=prompt_template,
            show_on_home=show_on_home,
            show_in_slash=show_in_slash,
            sort_order=200,
            is_editable=True,
        )
        self._commands[cmd.id] = cmd
        logger.info(f"Commande utilisateur créée : {cmd.id}")
        return cmd

    async def update_user_command(
        self,
        command_id: str,
        name: str | None = None,
        description: str | None = None,
        icon: str | None = None,
        category: str | None = None,
        prompt_template: str | None = None,
        show_on_home: bool | None = None,
        show_in_slash: bool | None = None,
    ) -> CommandDefinition | None:
        """Met à jour une commande utilisateur."""
        cmd = self._commands.get(command_id)
        if not cmd or cmd.source != CommandSource.USER:
            return None

        # Extraire le nom original
        original_name = cmd.name

        service = UserCommandsService.get_instance()
        updated = service.update_command(
            name=original_name,
            description=description,
            category=category,
            icon=icon,
            show_on_home=show_on_home,
            content=prompt_template,
        )
        if not updated:
            return None

        # Mettre à jour le registre
        if name is not None:
            cmd.name = name
        if description is not None:
            cmd.description = description
        if icon is not None:
            cmd.icon = icon
        if category is not None:
            cmd.category = category
        if prompt_template is not None:
            cmd.prompt_template = prompt_template
        if show_on_home is not None:
            cmd.show_on_home = show_on_home
        if show_in_slash is not None:
            cmd.show_in_slash = show_in_slash

        logger.info(f"Commande utilisateur mise à jour : {command_id}")
        return cmd

    async def delete_user_command(self, command_id: str) -> bool:
        """Supprime une commande utilisateur."""
        cmd = self._commands.get(command_id)
        if not cmd or cmd.source != CommandSource.USER:
            return False

        service = UserCommandsService.get_instance()
        deleted = service.delete_command(cmd.name)
        if deleted:
            del self._commands[command_id]
            logger.info(f"Commande utilisateur supprimée : {command_id}")
        return deleted


def get_command_registry() -> CommandRegistry:
    """Récupère l'instance singleton du registre de commandes."""
    return CommandRegistry.get_instance()


async def init_command_registry() -> None:
    """Initialise le registre de commandes au démarrage."""
    registry = get_command_registry()
    await registry.init()
