"""
THERESE v2 - User Commands Service

Gestion des commandes utilisateur personnalisees.
Stockage : ~/.therese/commands/user/*.md (YAML frontmatter + contenu)
"""

import json
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
        category: str = "production",
        icon: str = "",
        show_on_home: bool = True,
        show_in_slash: bool = True,
        content: str = "",
        created_at: str | None = None,
        updated_at: str | None = None,
    ):
        self.name = name
        self.description = description
        self.category = category
        self.icon = icon
        self.show_on_home = show_on_home
        # B-254 : le drapeau ne vivait qu'en memoire ; un redemarrage le
        # remettait a True. Il suit desormais `show_on_home`, de la creation au
        # frontmatter et retour.
        self.show_in_slash = show_in_slash
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
            "show_in_slash": self.show_in_slash,
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
            "show_in_slash": self.show_in_slash,
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

        # B-484 (05/09/2026) : le nom du fichier est l'identité de la commande.
        # Un frontmatter divergent la rendait introuvable (chemin dérivé du
        # nom lu, fichier rangé sous l'autre nom).
        return cls(
            name=name,
            description=frontmatter.get("description", ""),
            category=frontmatter.get("category", "production"),
            icon=frontmatter.get("icon", ""),
            show_on_home=frontmatter.get("show_on_home", True),
            show_in_slash=frontmatter.get("show_in_slash", True),
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
        category: str = "production",
        icon: str = "",
        show_on_home: bool = True,
        show_in_slash: bool = True,
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
            show_in_slash=show_in_slash,
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
        show_in_slash: bool | None = None,
        content: str | None = None,
        new_name: str | None = None,
    ) -> UserCommand | None:
        """Met a jour une commande existante.

        B-515 (05/09/2026) : un renommage ne renommait que la copie en
        mémoire du registre ; le fichier gardait l'ancien nom et le nouveau
        partait au redémarrage. Le fichier est renommé ici.
        """
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
        if show_in_slash is not None:
            cmd.show_in_slash = show_in_slash
        if content is not None:
            cmd.content = content

        cmd.updated_at = datetime.now().isoformat()

        filepath = self._command_path(name)
        if new_name and new_name != name:
            nouveau = self._command_path(new_name)
            if nouveau.exists():
                raise ValueError(f"Une commande « {new_name} » existe déjà.")
            cmd.name = nouveau.stem
            nouveau.write_text(cmd.to_markdown(), encoding="utf-8")
            filepath.unlink(missing_ok=True)
            logger.info(f"Renamed user command: {name} -> {cmd.name}")
            return cmd
        filepath.write_text(cmd.to_markdown(), encoding="utf-8")
        logger.info(f"Updated user command: {name}")
        return cmd

    def delete_command(self, name: str) -> bool:
        """Archive une commande dans la Corbeille, avec un repli local réversible."""
        filepath = self._command_path(name)
        if not filepath.exists():
            return False

        trash_dir = Path.home() / ".Trash"
        fallback_dir = self._commands_dir / ".trash"

        def available_destination(directory: Path) -> Path:
            destination = directory / filepath.name
            if not destination.exists():
                return destination
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            return directory / f"{filepath.stem}-{timestamp}{filepath.suffix}"

        try:
            if not trash_dir.exists():
                raise OSError("La Corbeille système n'est pas disponible")
            destination = available_destination(trash_dir)
            shutil.move(str(filepath), str(destination))
            # B-465 (05/09/2026) : le dépôt en Corbeille est noté, sans quoi la
            # purge RGPD ne pouvait pas le retrouver et le texte de
            # l'utilisatrice survivait à « toutes mes données ».
            self._noter_depot_en_corbeille(destination)
        except OSError as exc:
            fallback_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(filepath), str(available_destination(fallback_dir)))
            logger.warning("System trash unavailable, command archived locally: %s", exc)

        logger.info(f"Deleted user command: {name}")
        return True

    def _index_corbeille(self) -> Path:
        return self._commands_dir / ".corbeille.json"

    def _depots_en_corbeille(self) -> list[str]:
        index = self._index_corbeille()
        if not index.exists():
            return []
        try:
            charge = json.loads(index.read_text(encoding="utf-8"))
            return [str(x) for x in charge] if isinstance(charge, list) else []
        except (OSError, ValueError):
            return []

    def _noter_depot_en_corbeille(self, destination: Path) -> None:
        depots = self._depots_en_corbeille()
        depots.append(str(destination))
        self._index_corbeille().write_text(json.dumps(depots, ensure_ascii=False), encoding="utf-8")

    def purger_tout(self) -> int:
        """Efface DÉFINITIVEMENT toutes les commandes utilisateur (RGPD Art. 17).

        B-193 : ces fichiers contiennent du texte rédigé par l'utilisateur et
        vivent hors des tables balayées par « supprimer toutes mes données ».
        On ne passe pas par `delete_command`, qui ARCHIVE dans la Corbeille :
        un effacement demandé au titre du droit à l'oubli ne doit rien laisser
        ailleurs, repli local `.trash` compris.
        """
        if not self._commands_dir.exists():
            return 0

        efface = 0
        for filepath in self._commands_dir.glob("*.md"):
            filepath.unlink(missing_ok=True)
            efface += 1

        repli = self._commands_dir / ".trash"
        if repli.exists():
            shutil.rmtree(repli, ignore_errors=True)

        # B-465 : les commandes archivées dans la Corbeille système partent aussi.
        for depot in self._depots_en_corbeille():
            try:
                Path(depot).unlink(missing_ok=True)
                efface += 1
            except OSError as exc:
                logger.warning("Dépôt en Corbeille non effacé : %s (%s)", depot, exc)
        self._index_corbeille().unlink(missing_ok=True)

        logger.info("Purge RGPD : %d commande(s) utilisateur effacée(s)", efface)
        return efface
