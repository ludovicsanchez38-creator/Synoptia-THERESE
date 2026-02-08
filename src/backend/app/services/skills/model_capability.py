"""
THÉRÈSE v2 - Détection capacité modèle pour Skills

Détermine si un modèle LLM est capable de générer du code Python fiable
(python-docx, python-pptx, openpyxl) ou s'il doit utiliser du Markdown.
"""

from app.services.providers.base import LLMProvider

# Modèles capables de générer du code Python fiable pour les skills FILE.
# "*" = tous les modèles du provider sont capables.
# Sinon, on vérifie si un des patterns est contenu dans le nom du modèle.
CODE_CAPABLE_MODELS: dict[LLMProvider, set[str]] = {
    LLMProvider.ANTHROPIC: {"*"},          # Tous les Claude (Opus, Sonnet, Haiku)
    LLMProvider.OPENAI: {"*"},             # Tous les GPT / o-series
    LLMProvider.GEMINI: {"pro"},           # Gemini Pro oui, Flash non
    LLMProvider.MISTRAL: {"large", "codestral"},  # Large et Codestral oui, Small non
    LLMProvider.GROK: {"*"},               # Grok-3/4
    LLMProvider.OLLAMA: set(),             # Aucun Ollama fiable pour du code python-docx
}


def get_model_capability(provider: LLMProvider, model: str) -> str:
    """
    Détermine la capacité d'un modèle : code Python ou Markdown.

    Args:
        provider: Provider LLM (anthropic, openai, gemini, etc.)
        model: Identifiant du modèle (ex: "gemini-3-flash-preview")

    Returns:
        "code" si le modèle peut générer du code Python fiable,
        "markdown" sinon.
    """
    patterns = CODE_CAPABLE_MODELS.get(provider, set())

    # Wildcard : tous les modèles du provider sont capables
    if "*" in patterns:
        return "code"

    # Vérifier si un des patterns matche dans le nom du modèle
    model_lower = model.lower()
    for pattern in patterns:
        if pattern in model_lower:
            return "code"

    return "markdown"
