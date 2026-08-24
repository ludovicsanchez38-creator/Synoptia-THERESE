"""THÉRÈSE v2 — Fournisseur MiniMax.

API compatible OpenAI, avec prise en charge des outils par le paramètre `tools`.

PIÈGE À CONNAÎTRE : la casse des identifiants compte. C'est `MiniMax-M3`, avec
deux majuscules et un M majuscule après le tiret. Passer `minimax-m3` fait
échouer la requête. Les identifiants en minuscules qu'on croise dans la
bibliothèque Ollama désignent l'offre Ollama Cloud, pas cette API.

Adresse relevée le 24/08/2026 : https://api.minimax.io/v1
"""

import logging

from .openai import OpenAIProvider

logger = logging.getLogger(__name__)

MINIMAX_API_URL = "https://api.minimax.io/v1/chat/completions"


class MiniMaxProvider(OpenAIProvider):
    """Fournisseur MiniMax, compatible OpenAI, outils inclus."""

    API_URL = MINIMAX_API_URL
