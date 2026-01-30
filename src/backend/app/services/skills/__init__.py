"""
THÉRÈSE v2 - Skills Module

Système de skills pour génération de documents Office.
"""

from app.services.skills.base import (
    BaseSkill,
    FileFormat,
    SkillExecuteRequest,
    SkillExecuteResponse,
    SkillParams,
    SkillResult,
)
from app.services.skills.registry import (
    SkillsRegistry,
    close_skills,
    get_skills_registry,
    init_skills,
)

__all__ = [
    # Base classes
    "BaseSkill",
    "FileFormat",
    "SkillParams",
    "SkillResult",
    "SkillExecuteRequest",
    "SkillExecuteResponse",
    # Registry
    "SkillsRegistry",
    "get_skills_registry",
    "init_skills",
    "close_skills",
]
