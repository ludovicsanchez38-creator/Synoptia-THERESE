"""
THÉRÈSE v2 - Skills Registry

Gestionnaire de skills avec découverte automatique et exécution.
"""

import logging
import re
from pathlib import Path
from typing import Optional

from app.config import settings
from app.services.skills.base import (
    BaseSkill,
    FileFormat,
    SkillExecuteRequest,
    SkillExecuteResponse,
    SkillParams,
    SkillResult,
)

logger = logging.getLogger(__name__)


class SkillsRegistry:
    """
    Registre central des skills.

    Gère l'enregistrement, la découverte et l'exécution des skills.
    """

    def __init__(self):
        self._skills: dict[str, BaseSkill] = {}
        self._output_dir = Path(settings.data_dir) / "outputs"
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def register(self, skill: BaseSkill) -> None:
        """
        Enregistre un skill dans le registre.

        Args:
            skill: Instance du skill à enregistrer
        """
        if skill.skill_id in self._skills:
            logger.warning(f"Skill {skill.skill_id} already registered, overwriting")

        self._skills[skill.skill_id] = skill
        logger.info(f"Registered skill: {skill.skill_id} ({skill.name})")

    def get(self, skill_id: str) -> Optional[BaseSkill]:
        """
        Récupère un skill par son ID.

        Args:
            skill_id: Identifiant du skill

        Returns:
            Instance du skill ou None si non trouvé
        """
        return self._skills.get(skill_id)

    def list_skills(self) -> list[dict]:
        """
        Liste tous les skills enregistrés.

        Returns:
            Liste des métadonnées des skills
        """
        return [
            {
                "skill_id": skill.skill_id,
                "name": skill.name,
                "description": skill.description,
                "format": skill.output_format.value,
            }
            for skill in self._skills.values()
        ]

    async def execute(
        self,
        skill_id: str,
        request: SkillExecuteRequest,
        llm_content: str,
    ) -> SkillExecuteResponse:
        """
        Exécute un skill et génère un fichier.

        Args:
            skill_id: Identifiant du skill
            request: Requête d'exécution
            llm_content: Contenu généré par le LLM

        Returns:
            Réponse avec URL de téléchargement ou erreur
        """
        skill = self.get(skill_id)
        if not skill:
            return SkillExecuteResponse(
                success=False,
                download_url="",
                error=f"Skill '{skill_id}' not found",
            )

        try:
            # Préparer les paramètres
            # Priorité : titre explicite > titre dans le contenu LLM > titre du prompt
            title = (
                request.title
                or self._extract_title_from_content(llm_content)
                or self._extract_title(request.prompt)
            )
            params = SkillParams(
                title=title,
                content=llm_content,
                template=request.template,
                metadata=request.context,
            )

            # Exécuter le skill
            result: SkillResult = await skill.execute(params)

            # Construire l'URL de téléchargement
            download_url = f"/api/skills/download/{result.file_id}"

            # Enregistrer le fichier dans le cache pour téléchargement
            self._file_cache[result.file_id] = result

            return SkillExecuteResponse(
                success=True,
                file_id=result.file_id,
                file_name=result.file_name,
                file_size=result.file_size,
                download_url=download_url,
                preview=llm_content[:500] + "..." if len(llm_content) > 500 else llm_content,
            )

        except Exception as e:
            logger.exception(f"Error executing skill {skill_id}")
            return SkillExecuteResponse(
                success=False,
                download_url="",
                error=str(e),
            )

    def get_file(self, file_id: str) -> Optional[SkillResult]:
        """
        Récupère les informations d'un fichier généré.

        Args:
            file_id: Identifiant du fichier

        Returns:
            Résultat du skill ou None
        """
        return self._file_cache.get(file_id)

    def _extract_title_from_content(self, llm_content: str) -> str | None:
        """
        Extrait un titre depuis le contenu généré par le LLM.

        Cherche dans l'ordre :
        1. Un heading Markdown (# Titre)
        2. Un doc.add_heading("...", level=0) dans le code Python
        3. Une variable title = "..." dans le code Python

        Args:
            llm_content: Contenu généré par le LLM

        Returns:
            Titre extrait ou None
        """
        if not llm_content:
            return None

        # Titres génériques à ignorer
        generic_titles = {
            "document", "titre", "title", "données", "configuration",
            "couleurs", "couleurs synoptia", "mise en page",
            "configuration des marges", "styles", "template",
            "document word", "présentation", "tableur",
        }

        def _is_good_title(t: str) -> bool:
            """Vérifie qu'un titre est exploitable (pas générique, pas une variable)."""
            if not t or t.lower() in generic_titles:
                return False
            if t.startswith("{") or t.startswith("f\"") or t == "title":
                return False
            return True

        # 1. Chercher doc.add_heading("...", level=0 ou 1) dans le code Python
        # C'est la source la plus fiable pour le titre du document
        heading_code = re.search(
            r'add_heading\(\s*["\'](.+?)["\']\s*,\s*level\s*=\s*[01]\s*\)',
            llm_content,
        )
        if heading_code and _is_good_title(heading_code.group(1).strip()):
            return heading_code.group(1).strip()[:50]

        # 2. Chercher le premier heading Markdown (# Titre)
        heading_match = re.search(r'^#\s+(.+)$', llm_content, re.MULTILINE)
        if heading_match and _is_good_title(heading_match.group(1).strip()):
            return heading_match.group(1).strip()[:50]

        # 3. Chercher title = "..." dans le code Python
        title_var = re.search(
            r'\btitle\s*=\s*["\'](.+?)["\']',
            llm_content,
        )
        if title_var and _is_good_title(title_var.group(1).strip()):
            return title_var.group(1).strip()[:50]

        return None

    def _extract_title(self, prompt: str) -> str:
        """
        Extrait un titre du prompt utilisateur.

        Args:
            prompt: Prompt utilisateur

        Returns:
            Titre extrait ou première ligne tronquée
        """
        lines = prompt.strip().split('\n')
        first_line = lines[0] if lines else prompt

        # Préfixes français courants
        prefixes_fr = [
            "Crée ", "Rédige ", "Génère ", "Conçois ",
            "Fais ", "Prépare ", "Produis ", "Écris ",
            "Compose ", "Élabore ", "Construis ", "Développe ",
            "Planifie ", "Organise ", "Analyse ",
        ]
        # Préfixes anglais courants
        prefixes_en = [
            "Create ", "Write ", "Generate ", "Make ", "Build ",
            "Prepare ", "Produce ", "Draft ", "Design ",
        ]

        for prefix in prefixes_fr + prefixes_en:
            if first_line.lower().startswith(prefix.lower()):
                subject = first_line[len(prefix):].strip()
                # Prendre jusqu'au premier point ou les 50 premiers caractères
                subject = subject.split('.')[0][:50]
                if subject:
                    return subject

        # Chercher un pattern "champ: valeur" (inputs dynamiques)
        # Ex: "sujet: Proposition commerciale" → "Proposition commerciale"
        # Ex: "prompt: Parle moi de X" → "Parle moi de X"
        field_match = re.match(r'^[\w]+\s*:\s*(.+)', first_line, re.IGNORECASE)
        if field_match:
            value = field_match.group(1).strip()[:50]
            if value:
                return value

        # Fallback : première ligne du prompt tronquée à 50 caractères
        fallback = first_line.strip()[:50]
        return fallback if fallback else "Document"

    @property
    def _file_cache(self) -> dict[str, SkillResult]:
        """Cache des fichiers générés (simple en mémoire pour le MVP)."""
        if not hasattr(self, "_cached_files"):
            self._cached_files: dict[str, SkillResult] = {}
        return self._cached_files

    @property
    def output_dir(self) -> Path:
        """Répertoire de sortie des fichiers."""
        return self._output_dir


# Singleton registry
_registry: Optional[SkillsRegistry] = None


def get_skills_registry() -> SkillsRegistry:
    """
    Récupère l'instance singleton du registre de skills.

    Returns:
        Instance du SkillsRegistry
    """
    global _registry
    if _registry is None:
        _registry = SkillsRegistry()
    return _registry


async def init_skills() -> None:
    """
    Initialise le système de skills.

    Charge et enregistre tous les skills disponibles.
    """
    from app.services.skills.docx_generator import DocxSkill
    from app.services.skills.pptx_generator import PptxSkill
    from app.services.skills.xlsx_generator import XlsxSkill
    from app.services.skills.text_skills import EmailProSkill, LinkedInPostSkill, ProposalSkill
    from app.services.skills.analysis_skills import (
        AnalyzeXlsxSkill,
        AnalyzePdfSkill,
        AnalyzeWebsiteSkill,
        MarketResearchSkill,
        AnalyzeAIToolSkill,
        ExplainConceptSkill,
        BestPracticesSkill,
    )
    from app.services.skills.planning_skills import (
        PlanMeetingSkill,
        PlanProjectSkill,
        PlanWeekSkill,
        PlanGoalsSkill,
        WorkflowSkill,
    )

    registry = get_skills_registry()

    # Enregistrer les skills FILE (génération de documents)
    registry.register(DocxSkill(registry.output_dir))
    registry.register(PptxSkill(registry.output_dir))
    registry.register(XlsxSkill(registry.output_dir))

    # Enregistrer les skills TEXT (génération de contenu textuel)
    registry.register(EmailProSkill(registry.output_dir))
    registry.register(LinkedInPostSkill(registry.output_dir))
    registry.register(ProposalSkill(registry.output_dir))

    # Enregistrer les skills ANALYSIS (compréhension)
    registry.register(AnalyzeXlsxSkill(registry.output_dir))
    registry.register(AnalyzePdfSkill(registry.output_dir))
    registry.register(AnalyzeWebsiteSkill(registry.output_dir))
    registry.register(MarketResearchSkill(registry.output_dir))
    registry.register(AnalyzeAIToolSkill(registry.output_dir))
    registry.register(ExplainConceptSkill(registry.output_dir))
    registry.register(BestPracticesSkill(registry.output_dir))

    # Enregistrer les skills PLANNING (organisation)
    registry.register(PlanMeetingSkill(registry.output_dir))
    registry.register(PlanProjectSkill(registry.output_dir))
    registry.register(PlanWeekSkill(registry.output_dir))
    registry.register(PlanGoalsSkill(registry.output_dir))
    registry.register(WorkflowSkill(registry.output_dir))

    logger.info(f"Initialized {len(registry.list_skills())} skills")


async def close_skills() -> None:
    """Ferme proprement le système de skills."""
    global _registry
    _registry = None
    logger.info("Skills system closed")
