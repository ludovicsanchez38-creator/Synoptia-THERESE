"""THÉRÈSE v2 — Fournisseur Kimi (Moonshot AI).

« Kimi API is compatible with the OpenAI API format », dit sa documentation :
les SDK OpenAI Python et Node l'appellent tels quels. D'où l'héritage, qui
apporte la boucle d'outils, le rejeu des tours et la mesure des jetons.

Adresse relevée le 24/08/2026 sur platform.kimi.ai/docs/guide/quick-start.
Note : platform.moonshot.ai redirige en 301 vers platform.kimi.ai. La plateforme
chinoise platform.moonshot.cn n'a pas été vérifiée et peut différer.

Kimi K3 offre un million de jetons de contexte, ce qui en fait un candidat
sérieux pour les longs documents.
"""

import logging

from .openai import OpenAIProvider

logger = logging.getLogger(__name__)

KIMI_API_URL = "https://api.moonshot.ai/v1/chat/completions"


class KimiProvider(OpenAIProvider):
    """Fournisseur Kimi de Moonshot AI, compatible OpenAI, outils inclus."""

    API_URL = KIMI_API_URL
