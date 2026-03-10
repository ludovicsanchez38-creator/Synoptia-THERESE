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

            # BUG-048 : transmettre num_predict + num_ctx pour les skills Office
            # (certains modèles Ollama ont des défauts trop petits : 128 tokens)
            ollama_options: dict = {
                "num_predict": self.config.max_tokens,
                # BUG-052 : cap à 8192 pour éviter l'OOM sur les machines <8 Go RAM
                # Ollama respecte le context_window réel du modèle si inférieur
                "num_ctx": min(max(self.config.context_window, 2048), 8192),
            }

            async with self.client.stream(
                "POST",
                f"{base_url}/api/chat",
                json={
                    "model": model,
                    "messages": chat_messages,
                    "stream": True,
                    "options": ollama_options,
                },
                # BUG-050 : pas de timeout de lecture pour les providers locaux
                # Les skills Office sur machines lentes (Pentium G620) peuvent dépasser 120s
                # L'AbortController frontend + bouton Stop gèrent déjà l'annulation utilisateur
                # connect=5s pour détecter rapidement si Ollama n'est pas démarré
                timeout=httpx.Timeout(connect=5.0, read=None, write=None, pool=5.0),
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
                    yield StreamEvent(
                        type="error",
                        content=(
                            f"Ollama n'a renvoyé aucun contenu pour le modèle '{model}'. "
                            "Ollama est peut-être gelé ou surchargé - essaie de le relancer."
                        ),
                    )
                    return

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
        # Note : httpx.ReadTimeout ne peut pas être levé avec read=None (timeout désactivé)
        # Le catch ReadTimeout a été retiré — l'arrêt de génération se fait via AbortController
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
            elif status == 500:
                # BUG-052 : message spécifique si problème de mémoire
                ram_hint = ""
                if "out of memory" in detail.lower() or "num_ctx" in detail.lower() or "alloc" in detail.lower():
                    ram_hint = (
                        " Ta machine n'a probablement pas assez de RAM pour ce modèle. "
                        "Essaie un modèle plus léger (ex: qwen3:1.7b, gemma3:1b)."
                    )
                yield StreamEvent(
                    type="error",
                    content=(
                        f"Ollama a rencontré une erreur interne (HTTP 500).{ram_hint} "
                        f"Détail : {detail}"
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
