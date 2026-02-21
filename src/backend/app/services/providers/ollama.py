"""
THÉRÈSE v2 - Ollama Provider

Local Ollama API streaming implementation.
Sprint 2 - PERF-2.1: Extracted from monolithic llm.py
BUG-040: Messages d'erreur lisibles (connexion, modèle introuvable, timeout)
"""

import json
import logging
from typing import AsyncGenerator

import httpx

from .base import (
    BaseProvider,
    StreamEvent,
    ToolCall,
    ToolResult,
)

logger = logging.getLogger(__name__)


class OllamaProvider(BaseProvider):
    """Local Ollama API provider."""

    async def stream(
        self,
        system_prompt: str | None,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Stream from local Ollama."""
        base_url = (self.config.base_url or "http://localhost:11434").rstrip("/")
        model = self.config.model

        try:
            # Construire la liste de messages avec le system prompt en premier
            # /api/chat attend le system prompt comme message role="system",
            # pas comme champ top-level (contrairement à /api/generate)
            chat_messages: list[dict] = []
            if system_prompt:
                chat_messages.append({"role": "system", "content": system_prompt})
            chat_messages.extend(
                m for m in messages if m.get("role") != "system"
            )

            async with self.client.stream(
                "POST",
                f"{base_url}/api/chat",
                json={
                    "model": model,
                    "messages": chat_messages,
                    "stream": True,
                },
                timeout=120.0,
            ) as response:
                response.raise_for_status()
                has_content = False
                async for line in response.aiter_lines():
                    if line:
                        try:
                            event = json.loads(line)
                            # Vérifier si Ollama renvoie une erreur dans le flux
                            if error_msg := event.get("error"):
                                yield StreamEvent(
                                    type="error",
                                    content=f"Ollama ({model}): {error_msg}",
                                )
                                return
                            # Extraire le contenu - accepter aussi les chaînes vides
                            # (certains modèles comme gemma3:1b envoient du contenu vide)
                            content = event.get("message", {}).get("content")
                            if content is not None and content != "":
                                has_content = True
                                yield StreamEvent(type="text", content=content)
                        except json.JSONDecodeError:
                            continue

                if not has_content:
                    logger.warning(f"Ollama ({model}): réponse vide, aucun contenu reçu")

            yield StreamEvent(type="done", stop_reason="end_turn")

        except httpx.ConnectError:
            logger.error(f"Ollama connexion impossible: {base_url}")
            yield StreamEvent(
                type="error",
                content=(
                    f"Impossible de se connecter à Ollama ({base_url}). "
                    "Vérifie qu'Ollama est lancé (ouvre un terminal et tape 'ollama serve')."
                ),
            )
        except httpx.ReadTimeout:
            logger.error(f"Ollama timeout pour le modèle {model}")
            yield StreamEvent(
                type="error",
                content=(
                    f"Ollama a mis trop de temps à répondre avec le modèle '{model}'. "
                    "Le modèle est peut-être trop lent ou surchargé. Réessaie ou choisis un modèle plus léger."
                ),
            )
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            try:
                body = e.response.json()
                detail = body.get("error", str(e))
            except Exception:
                detail = str(e)
            logger.error(f"Ollama HTTP {status}: {detail}")
            if status == 404:
                yield StreamEvent(
                    type="error",
                    content=(
                        f"Le modèle '{model}' n'est pas installé dans Ollama. "
                        f"Lance 'ollama pull {model}' dans un terminal pour l'installer."
                    ),
                )
            else:
                yield StreamEvent(
                    type="error",
                    content=f"Erreur Ollama (HTTP {status}): {detail}",
                )
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Ollama streaming error: {error_msg}")
            yield StreamEvent(
                type="error",
                content=(
                    f"Erreur Ollama: {error_msg}"
                    if error_msg
                    else "Erreur inattendue avec Ollama. Vérifie que le service est lancé."
                ),
            )

    async def continue_with_tool_results(
        self,
        system_prompt: str | None,
        messages: list[dict],
        assistant_content: str,
        tool_calls: list[ToolCall],
        tool_results: list[ToolResult],
        tools: list[dict] | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Ollama doesn't support tool calling in this implementation."""
        yield StreamEvent(type="done", stop_reason="end_turn")
