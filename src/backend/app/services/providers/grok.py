"""
THÉRÈSE v2 - Grok Provider

xAI Grok API streaming implementation (OpenAI-compatible).
Sprint 2 - PERF-2.1: Extracted from monolithic llm.py
US-009 : boucle d'outils complète héritée d'OpenAIProvider.

L'API xAI (/v1/chat/completions) est OpenAI-compatible, y compris le function
calling (tools, tool_calls, finish_reason="tool_calls", messages role="tool").
Particularité documentée : en streaming, le tool call arrive ENTIER dans un
seul chunk - le parseur OpenAI (accumulation par index) gère ce cas tel quel.
Avant US-009, ce provider ignorait les tools et la continuation était un stub :
« crée un contact » répondait en texte sans jamais créer le contact.
"""

import logging

from .openai import OpenAIProvider

logger = logging.getLogger(__name__)

GROK_API_URL = "https://api.x.ai/v1/chat/completions"


class GrokProvider(OpenAIProvider):
    """xAI Grok API provider (OpenAI-compatible, outils inclus)."""

    API_URL = GROK_API_URL
