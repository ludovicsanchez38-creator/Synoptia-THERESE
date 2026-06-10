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

# US-009 (revue adversariale) : cache de capacité par modèle. Une fois qu'un
# modèle a répondu « does not support tools », on n'envoie plus de tools pour
# lui (évite un aller-retour 400 + retry à CHAQUE message). Process-local,
# se vide au redémarrage (un modèle re-pullé peut gagner le support).
_MODELS_WITHOUT_TOOLS: set[str] = set()

# Sentinelle interne : « ce modèle ne supporte pas les tools, rejouer sans »
_TOOLS_UNSUPPORTED = StreamEvent(type="error", content="__ollama_tools_unsupported__")


class OllamaProvider(BaseProvider):
    """Local Ollama API provider."""

    async def stream(
        self,
        system_prompt: str | None,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Stream from local Ollama.

        US-009 + revue adversariale : le chat fournit TOUJOURS des tools, mais
        beaucoup de modèles Ollama (gemma3, deepseek-r1...) ne les supportent
        pas et renvoient un 400 avant de streamer. Sans dégradation gracieuse,
        le chat TEXTE devenait inutilisable sur ces modèles. Ici : 400
        « does not support tools » -> on prévient une fois, on mémorise, et on
        rejoue la requête SANS tools (le chat texte fonctionne).
        """
        base_url = (self.config.base_url or "http://localhost:11434").rstrip("/")
        model = self.config.model

        # Construire la liste de messages avec le system prompt en premier
        # /api/chat attend le system prompt comme message role="system",
        # pas comme champ top-level (contrairement à /api/generate)
        chat_messages: list[dict] = []
        if system_prompt:
            chat_messages.append({"role": "system", "content": system_prompt})
        chat_messages.extend(m for m in messages if m.get("role") != "system")

        # BUG-048 : transmettre num_predict + num_ctx pour les skills Office
        # (certains modèles Ollama ont des défauts trop petits : 128 tokens)
        ollama_options: dict = {
            "num_predict": self.config.max_tokens,
            # BUG-052 : cap à 8192 pour éviter l'OOM sur les machines <8 Go RAM
            # Ollama respecte le context_window réel du modèle si inférieur
            "num_ctx": min(max(self.config.context_window, 2048), 8192),
        }

        request_body: dict = {
            "model": model,
            "messages": chat_messages,
            "stream": True,
            "options": ollama_options,
        }
        # US-009 : /api/chat accepte les tools au format OpenAI (type=function)
        if tools and model not in _MODELS_WITHOUT_TOOLS:
            request_body["tools"] = tools

        tools_rejected = False
        async for event in self._stream_request(base_url, model, request_body):
            if event is _TOOLS_UNSUPPORTED:
                tools_rejected = True
                break
            yield event

        if not tools_rejected:
            return

        # Dégradation gracieuse : prévenir (une fois) puis rejouer sans tools.
        _MODELS_WITHOUT_TOOLS.add(model)
        request_body.pop("tools", None)
        yield StreamEvent(
            type="text",
            content=(
                f"*(Le modèle {model} ne gère pas les outils - création de "
                "contacts, calendrier, documents. Je réponds en texte seulement ; "
                "pour les actions, installe un modèle compatible comme qwen3, "
                "llama3.1 ou mistral.)*\n\n"
            ),
        )
        async for event in self._stream_request(base_url, model, request_body):
            if event is _TOOLS_UNSUPPORTED:
                # Sans tools dans la requête, ce signal n'a plus de sens
                yield StreamEvent(
                    type="error",
                    content=f"Erreur Ollama inattendue avec le modèle '{model}'.",
                )
                return
            yield event

    async def _stream_request(
        self,
        base_url: str,
        model: str,
        request_body: dict,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Une requête /api/chat streamée, avec gestion d'erreur HONNÊTE.

        Revue adversariale US-009 : raise_for_status() + e.response.json()
        était du code mort sur une réponse streaming (le body n'est jamais lu
        avant la levée -> httpx.ResponseNotRead -> l'utilisateur recevait le
        HTTP 400 brut). Pattern correct (cf. gemini.py) : tester status_code
        DANS le async with et lire le body via aread() avant de router.
        """
        try:
            async with self.client.stream(
                "POST",
                f"{base_url}/api/chat",
                json=request_body,
                # BUG-050 : pas de timeout de lecture pour les providers locaux
                # Les skills Office sur machines lentes (Pentium G620) peuvent dépasser 120s
                # L'AbortController frontend + bouton Stop gèrent déjà l'annulation utilisateur
                # connect=5s pour détecter rapidement si Ollama n'est pas démarré
                timeout=httpx.Timeout(connect=5.0, read=None, write=None, pool=5.0),
            ) as response:
                if response.status_code != 200:
                    error_body = await response.aread()
                    detail = ""
                    try:
                        detail = json.loads(error_body.decode()).get("error", "")
                    except Exception:
                        detail = error_body.decode(errors="replace")[:300]
                    status = response.status_code
                    logger.error(f"Ollama HTTP {status}: {detail}")

                    if "does not support tools" in detail.lower() and "tools" in request_body:
                        yield _TOOLS_UNSUPPORTED
                        return
                    if status == 404:
                        yield StreamEvent(
                            type="error",
                            content=(
                                f"Le modèle '{model}' n'est pas installé dans Ollama. "
                                f"Lance 'ollama pull {model}' dans un terminal pour l'installer."
                            ),
                        )
                        return
                    if status == 500:
                        # BUG-052 : message spécifique si problème de mémoire
                        ram_hint = ""
                        if (
                            "out of memory" in detail.lower()
                            or "num_ctx" in detail.lower()
                            or "alloc" in detail.lower()
                        ):
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
                        return
                    yield StreamEvent(
                        type="error",
                        content=f"Erreur Ollama (HTTP {status}): {detail}",
                    )
                    return

                has_content = False
                has_tool_calls = False
                tool_call_index = 0
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
                            message = event.get("message", {})
                            # US-009 : tool_calls natifs Ollama. Les arguments
                            # arrivent déjà en objet JSON (pas une chaîne).
                            # Ollama ne fournit pas d'id -> on en synthétise un
                            # pour corréler les résultats dans la boucle d'outils.
                            for tc in message.get("tool_calls") or []:
                                func = tc.get("function", {})
                                name = func.get("name")
                                if not name:
                                    continue
                                arguments = func.get("arguments")
                                if isinstance(arguments, str):
                                    try:
                                        arguments = json.loads(arguments)
                                    except json.JSONDecodeError:
                                        arguments = {}
                                has_tool_calls = True
                                yield StreamEvent(
                                    type="tool_call",
                                    tool_call=ToolCall(
                                        id=f"ollama-call-{tool_call_index}",
                                        name=name,
                                        arguments=arguments or {},
                                    ),
                                )
                                tool_call_index += 1
                            # Extraire le contenu - accepter aussi les chaînes vides
                            # (certains modèles comme gemma3:1b envoient du contenu vide)
                            content = message.get("content")
                            if content is not None and content != "":
                                has_content = True
                                yield StreamEvent(type="text", content=content)
                        except json.JSONDecodeError:
                            continue

                if not has_content and not has_tool_calls:
                    logger.warning(f"Ollama ({model}): réponse vide, aucun contenu reçu")
                    yield StreamEvent(
                        type="error",
                        content=(
                            f"Ollama n'a renvoyé aucun contenu pour le modèle '{model}'. "
                            "Ollama est peut-être gelé ou surchargé - essaie de le relancer."
                        ),
                    )
                    return

            yield StreamEvent(
                type="done",
                stop_reason="tool_calls" if has_tool_calls else "end_turn",
            )

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
        """US-009 : continuation après exécution des outils (format Ollama).

        Format officiel /api/chat : le message assistant rejoue les tool_calls
        (arguments en objet), puis chaque résultat est un message
        {"role": "tool", "content": ..., "tool_name": <nom>} - Ollama corrèle
        par nom, pas par id (il n'en fournit pas).
        """
        messages = list(messages)

        assistant_message: dict = {
            "role": "assistant",
            "content": assistant_content or "",
            "tool_calls": [
                {"function": {"name": tc.name, "arguments": tc.arguments or {}}}
                for tc in tool_calls
            ],
        }
        messages.append(assistant_message)

        name_by_id = {tc.id: tc.name for tc in tool_calls}
        for tr in tool_results:
            result_content = tr.result
            if isinstance(result_content, dict):
                result_content = json.dumps(result_content)
            elif not isinstance(result_content, str):
                result_content = str(result_content)
            messages.append({
                "role": "tool",
                "content": result_content,
                "tool_name": name_by_id.get(tr.tool_call_id, ""),
            })

        async for event in self.stream(system_prompt, messages, tools):
            yield event
