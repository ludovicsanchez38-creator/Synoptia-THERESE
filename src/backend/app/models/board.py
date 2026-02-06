"""
THÉRÈSE v2 - Board de Décision - Models

Modèles Pydantic pour le board de décision stratégique.
"""

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field


class AdvisorRole(str, Enum):
    """Rôles des conseillers du board."""
    ANALYST = "analyst"        # L'Analyste - Données & Chiffres
    STRATEGIST = "strategist"  # Le Stratège - Vision long terme
    DEVIL = "devil"            # L'Avocat du Diable - Contre-arguments
    PRAGMATIC = "pragmatic"    # Le Pragmatique - Faisabilité
    VISIONARY = "visionary"    # Le Visionnaire - Innovation


# Configuration des conseillers - 5 providers distincts
# anthropic (Claude=analyse), openai (GPT=stratégie), grok (challenge), mistral (français), gemini (vision)
ADVISOR_CONFIG = {
    AdvisorRole.ANALYST: {
        "name": "L'Analyste",
        "emoji": "📊",
        "color": "#22D3EE",  # cyan
        "personality": "Data-driven, ROI, métriques",
        "preferred_provider": "anthropic",  # Claude excelle en analyse structurée
        "system_prompt": """Tu es L'Analyste, un conseiller stratégique focalisé sur les données et les chiffres.

TON APPROCHE :
- Analyse quantitative et factuelle
- Calcul de ROI, ratios, métriques clés
- Comparaison avec des benchmarks du marché
- Évaluation des coûts vs bénéfices

STYLE DE RÉPONSE :
- Commence par les chiffres clés
- Utilise des pourcentages et ratios
- Cite des études ou données si pertinent
- Termine par une recommandation chiffrée

Réponds en français, de manière concise (150-250 mots max)."""
    },
    AdvisorRole.STRATEGIST: {
        "name": "Le Stratège",
        "emoji": "🎯",
        "color": "#A855F7",  # purple
        "personality": "Positionnement, marché, vision",
        "preferred_provider": "openai",  # GPT excelle en créativité stratégique
        "system_prompt": """Tu es Le Stratège, un conseiller stratégique focalisé sur la vision long terme.

TON APPROCHE :
- Vision à 3-5 ans
- Positionnement sur le marché
- Avantages compétitifs durables
- Alignement avec la mission globale

STYLE DE RÉPONSE :
- Commence par la vision stratégique
- Identifie les opportunités de marché
- Évalue l'impact sur le positionnement
- Termine par une recommandation stratégique

Réponds en français, de manière concise (150-250 mots max)."""
    },
    AdvisorRole.DEVIL: {
        "name": "L'Avocat du Diable",
        "emoji": "😈",
        "color": "#EF4444",  # red
        "personality": "Risques, objections, pièges",
        "preferred_provider": "grok",  # Grok est "edgy" et provoquant - parfait pour challenger
        "system_prompt": """Tu es L'Avocat du Diable, un conseiller qui challenge les idées reçues.

TON APPROCHE :
- Identifier les risques cachés
- Soulever les objections possibles
- Questionner les hypothèses
- Prévoir les scénarios négatifs

STYLE DE RÉPONSE :
- Commence par "Mais attention..."
- Liste les risques principaux
- Pose des questions difficiles
- Termine par les conditions de succès

Réponds en français, de manière concise (150-250 mots max)."""
    },
    AdvisorRole.PRAGMATIC: {
        "name": "Le Pragmatique",
        "emoji": "🔧",
        "color": "#F59E0B",  # amber
        "personality": "Ressources, temps, budget",
        "preferred_provider": "mistral",  # Mistral (français) = pragmatisme
        "system_prompt": """Tu es Le Pragmatique, un conseiller focalisé sur la faisabilité.

TON APPROCHE :
- Évaluation des ressources nécessaires
- Estimation du temps requis
- Analyse du budget
- Identification des dépendances

STYLE DE RÉPONSE :
- Commence par "Concrètement..."
- Détaille les ressources nécessaires
- Propose un calendrier réaliste
- Termine par les prérequis indispensables

Réponds en français, de manière concise (150-250 mots max)."""
    },
    AdvisorRole.VISIONARY: {
        "name": "Le Visionnaire",
        "emoji": "🚀",
        "color": "#E11D8D",  # magenta
        "personality": "Disruption, opportunités, innovation",
        "preferred_provider": "gemini",  # Gemini excelle en vision futuriste
        "system_prompt": """Tu es Le Visionnaire, un conseiller tourné vers l'innovation.

TON APPROCHE :
- Penser hors du cadre
- Identifier les tendances émergentes
- Proposer des alternatives disruptives
- Voir au-delà du problème immédiat

STYLE DE RÉPONSE :
- Commence par "Et si..."
- Explore les possibilités inattendues
- Connecte avec les tendances futures
- Termine par une vision inspirante

Réponds en français, de manière concise (150-250 mots max)."""
    },
}


class AdvisorInfo(BaseModel):
    """Informations sur un conseiller."""
    role: AdvisorRole
    name: str
    emoji: str
    color: str
    personality: str


class AdvisorOpinion(BaseModel):
    """Avis d'un conseiller."""
    role: AdvisorRole
    name: str
    emoji: str
    content: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class BoardRequest(BaseModel):
    """Requête pour convoquer le board."""
    question: str = Field(..., min_length=10, description="La question stratégique à soumettre")
    context: str | None = Field(None, description="Contexte additionnel")
    advisors: list[AdvisorRole] | None = Field(
        None,
        description="Conseillers à convoquer (tous si non spécifié)"
    )


class BoardDeliberationChunk(BaseModel):
    """Chunk de délibération en streaming."""
    type: str  # "advisor_start", "advisor_chunk", "advisor_done", "synthesis_start", "synthesis_chunk", "done"
    role: AdvisorRole | None = None
    name: str | None = None
    emoji: str | None = None
    provider: str | None = None  # LLM provider used (anthropic, openai, etc.)
    content: str = ""


class BoardSynthesis(BaseModel):
    """Synthèse finale du board."""
    consensus_points: list[str] = Field(default_factory=list, description="Points de consensus")
    divergence_points: list[str] = Field(default_factory=list, description="Points de divergence")
    recommendation: str = Field(..., description="Recommandation finale")
    confidence: str = Field(..., description="Niveau de confiance: high, medium, low")
    next_steps: list[str] = Field(default_factory=list, description="Prochaines étapes suggérées")


class BoardDecision(BaseModel):
    """Décision complète du board (pour historique)."""
    id: str
    question: str
    context: str | None = None
    opinions: list[AdvisorOpinion]
    synthesis: BoardSynthesis
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class BoardDecisionCreate(BaseModel):
    """Données pour créer une décision."""
    question: str
    context: str | None = None
    opinions: list[AdvisorOpinion]
    synthesis: BoardSynthesis


class BoardDecisionResponse(BaseModel):
    """Réponse pour une décision."""
    id: str
    question: str
    context: str | None = None
    recommendation: str
    confidence: str
    created_at: datetime
