"""
THÉRÈSE v2 - Tool Installer

Boucle generate-test-fix pour créer et installer un outil.
Le LLM génère un script Python, THÉRÈSE le valide (sandbox + test fixture),
et l'installe dans ~/.therese/tools/.
"""

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import settings
from app.services.skills.code_executor import (
    CodeExecutionError,
    execute_sandboxed,
    validate_code,
)

logger = logging.getLogger(__name__)


@dataclass
class ToolInstallResult:
    """Résultat de l'installation d'un outil."""
    success: bool
    tool_id: str | None = None
    tool_dir: str | None = None
    error: str | None = None
    attempts: int = 0
    model_used: str | None = None


class ToolInstaller:
    """
    Boucle generate-test-fix pour créer et installer un outil.

    Workflow :
    1. Demande au LLM de générer le script
    2. Valide avec le sandbox
    3. Teste avec le test_fixture
    4. Si échec : renvoie l'erreur au LLM, retry (max 3)
    5. Si 3 échecs : escalade vers modèle supérieur
    6. Si succès : installe dans ~/.therese/tools/
    """

    MAX_ATTEMPTS = 3
    ESCALATION_MODELS = ["claude-sonnet-4-6", "claude-opus-4-6"]

    def __init__(self):
        self._tools_dir = Path(settings.data_dir) / "tools"
        self._tools_dir.mkdir(parents=True, exist_ok=True)

    @property
    def tools_dir(self) -> Path:
        """Répertoire des outils installés."""
        return self._tools_dir

    async def install_tool(
        self,
        tool_id: str,
        name: str,
        description: str,
        output_format: str,
        code: str,
        inputs: list[dict[str, Any]] | None = None,
        test_input: dict[str, Any] | None = None,
        model: str | None = None,
    ) -> ToolInstallResult:
        """
        Valide et installe un script Python comme outil.

        Pour la V3, le code est fourni directement (pas de génération LLM).
        La boucle generate-test-fix sera ajoutée en V4 quand le LLM
        génèrera le code automatiquement.

        Args:
            tool_id: Identifiant unique de l'outil (slug)
            name: Nom de l'outil
            description: Description de l'outil
            output_format: Format de sortie (xlsx, docx, pptx)
            code: Script Python à installer
            inputs: Schema des entrées (liste de InputField dicts)
            test_input: Données de test pour validation
            model: Modèle source (informatif)

        Returns:
            ToolInstallResult avec succès/erreur
        """
        tool_dir = self._tools_dir / tool_id

        # 1. Valider la sécurité du code
        is_valid, error_msg = validate_code(code)
        if not is_valid:
            return ToolInstallResult(
                success=False,
                error=f"Validation code échouée : {error_msg}",
                attempts=1,
            )

        # 2. Tester dans le sandbox
        import tempfile
        test_output = Path(tempfile.mktemp(suffix=f".{output_format}"))
        try:
            # Préparer le code de test avec les paramètres fictifs
            test_params = test_input or {}
            params_json = json.dumps(test_params, ensure_ascii=False, default=str)
            test_code = f"""
import json
params = json.loads({params_json!r})
{code}
"""
            await execute_sandboxed(
                code=test_code,
                output_path=str(test_output),
                title="Test Installation",
                format_type=output_format,
            )

            # Vérifier que le fichier a été créé
            if not test_output.exists() or test_output.stat().st_size == 0:
                return ToolInstallResult(
                    success=False,
                    error="Le script n'a pas généré de fichier de sortie",
                    attempts=1,
                )

            logger.info(
                f"Test sandbox réussi pour {tool_id} "
                f"({test_output.stat().st_size} bytes)"
            )

        except CodeExecutionError as e:
            return ToolInstallResult(
                success=False,
                error=f"Échec sandbox : {e}",
                attempts=1,
            )
        except Exception as e:
            return ToolInstallResult(
                success=False,
                error=f"Erreur inattendue : {e}",
                attempts=1,
            )
        finally:
            # Nettoyer le fichier de test
            if test_output.exists():
                test_output.unlink()

        # 3. Installer dans ~/.therese/tools/{tool_id}/
        tool_dir.mkdir(parents=True, exist_ok=True)

        # Écrire le manifest
        manifest = {
            "id": tool_id,
            "name": name,
            "description": description,
            "version": "1.0.0",
            "created_at": datetime.now(UTC).isoformat(),
            "source_model": model or "manual",
            "generation_attempts": 1,
            "output_format": output_format,
            "inputs": inputs or [],
            "data_params": [],
            "test_fixture": "test_fixture.json",
        }
        (tool_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # Écrire le script
        (tool_dir / "tool.py").write_text(code, encoding="utf-8")

        # Écrire le test fixture
        fixture = {
            "input": test_input or {},
            "expected": {"file_exists": True},
        }
        (tool_dir / "test_fixture.json").write_text(
            json.dumps(fixture, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        logger.info(f"Outil {tool_id} installé dans {tool_dir}")

        return ToolInstallResult(
            success=True,
            tool_id=tool_id,
            tool_dir=str(tool_dir),
            attempts=1,
            model_used=model,
        )

    async def uninstall_tool(self, tool_id: str) -> bool:
        """
        Désinstalle un outil.

        Args:
            tool_id: Identifiant de l'outil

        Returns:
            True si désinstallé, False si non trouvé
        """
        tool_dir = self._tools_dir / tool_id
        if not tool_dir.exists():
            return False

        # Supprimer le répertoire et son contenu
        import shutil
        shutil.rmtree(tool_dir)
        logger.info(f"Outil {tool_id} désinstallé")
        return True

    async def test_tool(
        self,
        tool_id: str,
        test_input: dict[str, Any] | None = None,
    ) -> tuple[bool, str]:
        """
        Re-teste un outil existant.

        Args:
            tool_id: Identifiant de l'outil
            test_input: Données de test (ou depuis le test_fixture)

        Returns:
            Tuple (succès, message)
        """
        tool_dir = self._tools_dir / tool_id
        if not tool_dir.exists():
            return False, f"Outil {tool_id} non trouvé"

        manifest = json.loads((tool_dir / "manifest.json").read_text(encoding="utf-8"))
        code = (tool_dir / "tool.py").read_text(encoding="utf-8")
        output_format = manifest.get("output_format", "xlsx")

        # Charger le test_input depuis le fixture si non fourni
        if test_input is None:
            fixture_path = tool_dir / "test_fixture.json"
            if fixture_path.exists():
                fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
                test_input = fixture.get("input", {})
            else:
                test_input = {}

        import tempfile
        test_output = Path(tempfile.mktemp(suffix=f".{output_format}"))
        try:
            params_json = json.dumps(test_input, ensure_ascii=False, default=str)
            test_code = f"""
import json
params = json.loads({params_json!r})
{code}
"""
            await execute_sandboxed(
                code=test_code,
                output_path=str(test_output),
                title="Test Outil",
                format_type=output_format,
            )

            if test_output.exists() and test_output.stat().st_size > 0:
                size = test_output.stat().st_size
                return True, f"Test réussi ({size} bytes)"
            else:
                return False, "Le script n'a pas généré de fichier"

        except Exception as e:
            return False, f"Échec : {e}"
        finally:
            if test_output.exists():
                test_output.unlink()


# Singleton
_installer: ToolInstaller | None = None


def get_tool_installer() -> ToolInstaller:
    """Récupère l'instance singleton du ToolInstaller."""
    global _installer
    if _installer is None:
        _installer = ToolInstaller()
    return _installer
