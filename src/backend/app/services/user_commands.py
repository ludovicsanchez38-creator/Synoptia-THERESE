"""
THERESE v2 - User Commands Service

Gestion des commandes utilisateur personnalisees.
Stockage : ~/.therese/commands/user/*.md (YAML frontmatter + contenu)
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml
from app.config import settings

logger = logging.getLogger(__name__)


class UserCommand:
    """Represente une commande utilisateur."""

    def __init__(
        self,
        name: str,
        description: str = "",
        category: str = "general",
        icon: str = "",
        show_on_home: bool = False,
        content: str = "",
        created_at: str | None = None,
        updated_at: str | None = None,
    ):
        self.name = name
        self.description = description
        self.category = category
        self.icon = icon
        self.show_on_home = show_on_home
        self.content = content
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or self.created_at

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "icon": self.icon,
            "show_on_home": self.show_on_home,
            "content": self.content,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_markdown(self) -> str:
        """Serialize vers fichier markdown avec YAML frontmatter."""
        frontmatter = {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "icon": self.icon,
            "show_on_home": self.show_on_home,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        yaml_str = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
        return f"---\n{yaml_str}---\n{self.content}"

    @classmethod
    def from_markdown(cls, text: str, filename: str) -> "UserCommand":
        """Parse un fichier markdown avec YAML frontmatter."""
        name = filename.replace(".md", "")

        if not text.startswith("---"):
            return cls(name=name, content=text)

        parts = text.split("---", 2)
        if len(parts) < 3:
            return cls(name=name, content=text)

        try:
            frontmatter = yaml.safe_load(parts[1]) or {}
        except yaml.YAMLError:
            frontmatter = {}

        content = parts[2].lstrip("\n")

        return cls(
            name=frontmatter.get("name", name),
            description=frontmatter.get("description", ""),
            category=frontmatter.get("category", "general"),
            icon=frontmatter.get("icon", ""),
            show_on_home=frontmatter.get("show_on_home", False),
            content=content,
            created_at=frontmatter.get("created_at"),
            updated_at=frontmatter.get("updated_at"),
        )


class UserCommandsService:
    """Service singleton pour gerer les commandes utilisateur."""

    _instance: Optional["UserCommandsService"] = None

    def __init__(self):
        self._commands_dir = Path(settings.data_dir) / "commands" / "user"
        self._commands_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_instance(cls) -> "UserCommandsService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _command_path(self, name: str) -> Path:
        """Chemin du fichier de commande."""
        safe_name = name.replace("/", "-").replace("\\", "-").replace(" ", "-")
        return self._commands_dir / f"{safe_name}.md"

    def list_commands(self) -> list[UserCommand]:
        """Liste toutes les commandes utilisateur."""
        commands = []
        if not self._commands_dir.exists():
            return commands

        for filepath in sorted(self._commands_dir.glob("*.md")):
            try:
                text = filepath.read_text(encoding="utf-8")
                cmd = UserCommand.from_markdown(text, filepath.name)
                commands.append(cmd)
            except Exception as e:
                logger.warning(f"Failed to parse command file {filepath}: {e}")

        return commands

    def get_command(self, name: str) -> UserCommand | None:
        """Recupere une commande par son nom."""
        filepath = self._command_path(name)
        if not filepath.exists():
            return None

        text = filepath.read_text(encoding="utf-8")
        return UserCommand.from_markdown(text, filepath.name)

    def create_command(
        self,
        name: str,
        description: str = "",
        category: str = "general",
        icon: str = "",
        show_on_home: bool = False,
        content: str = "",
    ) -> UserCommand:
        """Cree une nouvelle commande."""
        filepath = self._command_path(name)
        if filepath.exists():
            raise ValueError(f"La commande '{name}' existe deja")

        cmd = UserCommand(
            name=name,
            description=description,
            category=category,
            icon=icon,
            show_on_home=show_on_home,
            content=content,
        )

        filepath.write_text(cmd.to_markdown(), encoding="utf-8")
        logger.info(f"Created user command: {name}")
        return cmd

    def update_command(
        self,
        name: str,
        description: str | None = None,
        category: str | None = None,
        icon: str | None = None,
        show_on_home: bool | None = None,
        content: str | None = None,
    ) -> UserCommand | None:
        """Met a jour une commande existante."""
        cmd = self.get_command(name)
        if not cmd:
            return None

        if description is not None:
            cmd.description = description
        if category is not None:
            cmd.category = category
        if icon is not None:
            cmd.icon = icon
        if show_on_home is not None:
            cmd.show_on_home = show_on_home
        if content is not None:
            cmd.content = content

        cmd.updated_at = datetime.now().isoformat()

        filepath = self._command_path(name)
        filepath.write_text(cmd.to_markdown(), encoding="utf-8")
        logger.info(f"Updated user command: {name}")
        return cmd

    def delete_command(self, name: str) -> bool:
        """Supprime une commande (deplace vers ~/.Trash)."""
        filepath = self._command_path(name)
        if not filepath.exists():
            return False

        trash_dir = Path.home() / ".Trash"
        if trash_dir.exists():
            shutil.move(str(filepath), str(trash_dir / filepath.name))
        else:
            filepath.unlink()

        logger.info(f"Deleted user command: {name}")
        return True
