"""
THÉRÈSE v2 - Installed Tool Skill

Skill qui exécute un outil pré-installé (pas de génération LLM).
Les outils sont des scripts Python validés une seule fois et stockés dans ~/.therese/tools/.
"""

import json
import logging
from pathlib import Path
from typing import Any

from app.services.skills.base import (
    BaseSkill,
    FileFormat,
    InputField,
    SkillOutputType,
    SkillParams,
    SkillResult,
)
from app.services.skills.code_executor import execute_sandboxed

logger = logging.getLogger(__name__)


class InstalledToolSkill(BaseSkill):
    """Skill qui exécute un outil pré-installé (pas de génération LLM)."""

    output_type = SkillOutputType.FILE

    def __init__(self, tool_dir: Path, output_dir: Path):
        """
        Initialise un outil installé depuis son répertoire.

        Args:
            tool_dir: Chemin vers le répertoire de l'outil (~/.therese/tools/{tool_id}/)
            output_dir: Répertoire de sortie des fichiers générés
        """
        self.tool_dir = tool_dir
        self._manifest = json.loads((tool_dir / "manifest.json").read_text(encoding="utf-8"))
        self._tool_code = (tool_dir / "tool.py").read_text(encoding="utf-8")

        # Metadata depuis le manifest
        self.skill_id = f"tool:{self._manifest['id']}"
        self.name = self._manifest.get("name", self._manifest["id"])
        self.description = self._manifest.get("description", "")

        # Format de sortie
        format_str = self._manifest.get("output_format", "xlsx")
        try:
            self.output_format = FileFormat(format_str)
        except ValueError:
            self.output_format = FileFormat.MD

        super().__init__(output_dir)

    @property
    def manifest(self) -> dict[str, Any]:
        """Retourne le manifest de l'outil."""
        return self._manifest

    @property
    def tool_id(self) -> str:
        """ID de l'outil (sans le préfixe 'tool:')."""
        return self._manifest["id"]

    @property
    def version(self) -> str:
        """Version de l'outil."""
        return self._manifest.get("version", "1.0.0")

    def get_input_schema(self) -> dict[str, InputField]:
        """Génère dynamiquement le schema d'entrée depuis manifest.inputs."""
        schema: dict[str, InputField] = {}
        for inp in self._manifest.get("inputs", []):
            schema[inp["name"]] = InputField(
                type=inp.get("type", "text"),
                label=inp.get("label", inp["name"]),
                placeholder=inp.get("placeholder", ""),
                required=inp.get("required", False),
                options=inp.get("options", []),
                default=inp.get("default"),
                help_text=inp.get("help_text"),
            )
        return schema

    def get_system_prompt_addition(self) -> str:
        """
        Instructions pour le LLM quand cet outil est utilisé.

        Le LLM n'a pas besoin de générer du code - il génère un JSON
        avec les paramètres d'entrée, et l'outil fait le reste.
        """
        inputs_desc = []
        for inp in self._manifest.get("inputs", []):
            req = " (requis)" if inp.get("required") else ""
            inputs_desc.append(f'  - {inp["name"]}: {inp.get("label", inp["name"])}{req}')

        inputs_text = "\n".join(inputs_desc) if inputs_desc else "  (aucun paramètre)"

        return f"""
Tu utilises l'outil installé "{self.name}" ({self._manifest['id']}).
Cet outil génère un fichier .{self.output_format.value}.
NE génère PAS de code Python. Génère un JSON avec les paramètres suivants :
{inputs_text}

Réponds UNIQUEMENT avec un bloc JSON valide (pas de ```json, juste le JSON brut).
"""

    async def execute(self, params: SkillParams) -> SkillResult:
        """
        Exécute le script tool.py dans le sandbox existant.

        Les données sont passées via le namespace (params.metadata contient
        les inputs utilisateur + données propriétaires).

        Args:
            params: Paramètres de génération

        Returns:
            Résultat avec chemin vers le fichier généré
        """
        file_id = self.generate_file_id()
        output_path = self.get_output_path(file_id, params.title)

        # Préparer le code avec injection des paramètres
        # Le tool.py attend : output_path, title, params (dict), SYNOPTIA_COLORS
        params_json = json.dumps(params.metadata, ensure_ascii=False, default=str)
        wrapper_code = f"""
# Paramètres injectés
import json
params = json.loads({params_json!r})

# Code de l'outil installé
{self._tool_code}
"""

        try:
            logger.info(
                f"[{self.skill_id}] Exécution outil installé "
                f"v{self.version}..."
            )
            await execute_sandboxed(
                code=wrapper_code,
                output_path=str(output_path),
                title=params.title,
                format_type=self.output_format.value,
            )

            if output_path.exists() and output_path.stat().st_size > 0:
                file_size = output_path.stat().st_size
                logger.info(
                    f"[{self.skill_id}] Outil exécuté avec succès : "
                    f"{output_path} ({file_size} bytes)"
                )
                return SkillResult(
                    file_id=file_id,
                    file_path=output_path,
                    file_name=output_path.name,
                    file_size=file_size,
                    mime_type=self.get_mime_type(),
                    format=self.output_format,
                )
            else:
                raise RuntimeError(
                    f"L'outil {self.skill_id} n'a pas généré de fichier"
                )
        except Exception as e:
            logger.error(f"[{self.skill_id}] Erreur exécution : {e}")
            raise

    def get_test_fixture(self) -> dict[str, Any] | None:
        """Charge le test fixture si disponible."""
        fixture_path = self.tool_dir / "test_fixture.json"
        if fixture_path.exists():
            return json.loads(fixture_path.read_text(encoding="utf-8"))
        return None

    def to_dict(self) -> dict[str, Any]:
        """Sérialise l'outil pour l'API."""
        return {
            "id": self.tool_id,
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "output_format": self.output_format.value,
            "inputs": self._manifest.get("inputs", []),
            "source_model": self._manifest.get("source_model", ""),
            "created_at": self._manifest.get("created_at", ""),
            "generation_attempts": self._manifest.get("generation_attempts", 0),
        }
