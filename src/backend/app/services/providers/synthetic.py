"""API Chat Completions de Synthetic.

Documentation et base annoncée : https://dev.synthetic.new/docs/api/overview
"""

import re

from .openai import OpenAIProvider

SYNTHETIC_BASE_URL = "https://api.synthetic.new/openai/v1"
SYNTHETIC_MODELS_URL = f"{SYNTHETIC_BASE_URL}/models"
_IDENTIFIANT = re.compile(r"(?:fast:)?(?:hf:[^/:\s]+/[^/:\s]+|syn:[^:\s]+:[^/:\s]+|infinite:[^:\s]+:[^/:\s]+)")


def est_identifiant_synthetic(identifiant: str) -> bool:
    """Reconnaît les espaces de noms du fournisseur avant le routage par ponctuation."""
    return _IDENTIFIANT.fullmatch(identifiant) is not None


class SyntheticProvider(OpenAIProvider):
    """Fournisseur compatible OpenAI avec flux et outils."""

    API_URL = f"{SYNTHETIC_BASE_URL}/chat/completions"
