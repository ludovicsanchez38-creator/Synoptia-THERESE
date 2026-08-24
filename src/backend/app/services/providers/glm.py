"""THÉRÈSE v2 — Fournisseur GLM (Z.ai / Zhipu).

L'API Z.ai est compatible OpenAI, confirmé dans sa documentation : les SDK
OpenAI Python, JavaScript et Java l'appellent directement. GLM hérite donc du
fournisseur OpenAI, qui porte déjà la boucle d'outils complète, le rejeu des
tours précédents et la mesure réelle des jetons.

Cet héritage n'est pas un détail de forme. Avant qu'il ne soit posé pour Grok,
« crée un contact » répondait par du texte sans jamais créer le contact : le
fournisseur ignorait les outils et sa continuation était un simulacre.

Adresse relevée le 24/08/2026 sur docs.z.ai/api-reference/llm/chat-completion.
Il s'agit de la plateforme INTERNATIONALE (z.ai) et non de open.bigmodel.cn,
destinée à la Chine continentale, qui expose d'autres identifiants.
"""

import logging

from .openai import OpenAIProvider

logger = logging.getLogger(__name__)

GLM_API_URL = "https://api.z.ai/api/paas/v4/chat/completions"


class GLMProvider(OpenAIProvider):
    """Fournisseur GLM de Z.ai, compatible OpenAI, outils inclus."""

    API_URL = GLM_API_URL
