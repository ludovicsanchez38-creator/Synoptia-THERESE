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
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from .base import StreamEvent
from .openai import OpenAIProvider

logger = logging.getLogger(__name__)

GROK_API_URL = "https://api.x.ai/v1/chat/completions"


class GrokProvider(OpenAIProvider):
    """xAI Grok API provider (OpenAI-compatible, outils inclus)."""

    API_URL = GROK_API_URL

    async def _stream_request(
        self, request_body: dict[str, Any]
    ) -> AsyncGenerator[StreamEvent, None]:
        """Repli 0.48 : conflit de doc sur reasoning_effort=xhigh (grok-4.6).

        Si l'API refuse le paramètre par un 400 AVANT tout event, UNE
        seconde tentative part avec le corps copié sans le champ. Après un
        début de flux, jamais de rejeu (duplication interdite) : l'erreur
        suit la voie normale.
        """
        emis = 0
        try:
            async for event in super()._stream_request(request_body):
                emis += 1
                yield event
        except httpx.HTTPStatusError as e:
            if (
                emis == 0
                and e.response.status_code == 400
                and "reasoning_effort" in request_body
            ):
                logger.warning(
                    "Grok a refusé reasoning_effort=%s (400) : "
                    "seconde tentative sans le paramètre",
                    request_body["reasoning_effort"],
                )
                corps = {
                    k: v for k, v in request_body.items()
                    if k != "reasoning_effort"
                }
                async for event in super()._stream_request(corps):
                    yield event
            else:
                raise
