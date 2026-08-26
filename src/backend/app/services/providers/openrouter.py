"""
THÉRÈSE v2 - OpenRouter Provider

OpenRouter API streaming implementation (OpenAI-compatible).
Accès unifié à 200+ modèles LLM via https://openrouter.ai/api/v1.
"""

import json
import logging
from typing import Any, AsyncGenerator

import httpx

from .base import (
    BaseProvider,
    StreamEvent,
    ToolCall,
    ToolResult,
    ToolTurn,
)

logger = logging.getLogger(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


def _message_erreur_sse(code: int | None, error_type: str | None) -> str:
    """Traduit une erreur SSE OpenRouter en message CLASSÉ, sans son corps.

    Deux exigences opposées, toutes deux obligatoires :

    - le `message` du fournisseur ne doit jamais atteindre l'écran (il peut
      porter un chemin local ou un fragment de clé) ;
    - la CLASSE de l'erreur doit y arriver intacte, sinon `_is_provider_outage`
      ne reconnaît rien et le circuit breaker cesse de compter les pannes.

    La passe 7 des 0.48.x avait satisfait la première en cassant la seconde :
    tout devenait « Le service OpenRouter a signalé une erreur. », qu'aucun
    marqueur ne reconnaît. Le vocabulaire ci-dessous est celui du chemin HTTP
    du même fournisseur, et « API error: {code} » est la forme que le circuit
    breaker sait lire pour les 5xx (même contrat que Gemini).
    """
    marqueur = (error_type or "").lower()
    if code == 401 or "auth" in marqueur or "key" in marqueur:
        return "Clé API OpenRouter invalide ou expirée."
    if code == 402 or "credit" in marqueur or "insufficient" in marqueur:
        return "Crédit OpenRouter insuffisant. Recharge ton compte sur openrouter.ai."
    if code == 429 or "rate_limit" in marqueur:
        return "Trop de requêtes OpenRouter. Patiente quelques secondes."
    if code is not None and code >= 500:
        return f"Le service OpenRouter est momentanément indisponible (API error: {code})."
    if code is not None:
        # Erreur de requête : basculer de fournisseur n'aiderait pas, donc
        # aucun marqueur de panne ici - c'est délibéré.
        return f"OpenRouter a refusé la requête ({code})."
    return "OpenRouter a signalé une erreur pendant la réponse."


class OpenRouterProvider(BaseProvider):
    """OpenRouter API provider (OpenAI-compatible, 200+ modèles)."""

    def _build_request_body(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> dict[str, Any]:
        """Build request body (OpenAI-compatible format)."""
        request_body: dict[str, Any] = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": messages,
            "stream": True,
            # Usage réel (dette 14/06/2026) : sans ce flag, le chunk usage final
            # n'est pas envoyé du tout par l'API en streaming.
            "stream_options": {"include_usage": True},
        }

        if tools:
            request_body["tools"] = tools
            request_body["tool_choice"] = "auto"

        return request_body

    async def stream(
        self,
        system_prompt: str | None,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Stream from OpenRouter API with tool support."""
        request_body = self._build_request_body(messages, tools)

        try:
            async with self.client.stream(
                "POST",
                OPENROUTER_API_URL,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://synoptia.fr",
                    "X-Title": "THERESE",
                },
                json=request_body,
            ) as response:
                response.raise_for_status()

                # Track tool calls being built
                tool_calls: dict[int, dict] = {}
                has_content = False
                # Usage réel (dette 14/06/2026) : le chunk usage (stream_options.
                # include_usage) arrive APRÈS le chunk finish_reason, choices vide.
                # On mémorise stop_reason et on n'émet "done" qu'à la toute fin
                # (chunk usage ou [DONE]) pour ne pas le manquer.
                pending_stop_reason: str | None = None
                input_tokens: int | None = None
                output_tokens: int | None = None
                # Garde de robustesse : si la connexion se coupe après
                # finish_reason mais avant [DONE]/le chunk usage, il faut
                # quand même émettre "done" (sinon chat.py reste bloqué en
                # attente indéfiniment de ce signal). Couvre aussi le cas
                # erreur SSE explicite (pas de filet à ajouter après une
                # erreur déjà émise).
                stream_finished = False

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            if not has_content and not tool_calls:
                                logger.warning("OpenRouter: réponse vide (aucun contenu reçu)")
                                yield StreamEvent(
                                    type="error",
                                    content="Le modèle n'a produit aucune réponse. "
                                    "Essayez un autre modèle ou vérifiez votre clé API OpenRouter.",
                                )
                            else:
                                yield StreamEvent(
                                    type="done",
                                    stop_reason=pending_stop_reason or "stop",
                                    input_tokens=input_tokens,
                                    output_tokens=output_tokens,
                                )
                            stream_finished = True
                            break
                        try:
                            event = json.loads(data)
                            if usage := event.get("usage"):
                                input_tokens = usage.get("prompt_tokens", input_tokens)
                                output_tokens = usage.get("completion_tokens", output_tokens)

                            # OpenRouter peut renvoyer une erreur dans le flux SSE
                            if "error" in event:
                                err = event["error"]
                                est_dict = isinstance(err, dict)
                                err_msg = err.get("message", str(err)) if est_dict else str(err)
                                code = err.get("code") if est_dict else None
                                error_type = None
                                if est_dict and isinstance(err.get("metadata"), dict):
                                    error_type = err["metadata"].get("error_type")
                                # Le message du fournisseur peut porter un
                                # chemin local ou un identifiant : il reste au
                                # LOG. Seule sa CLASSE va à l'écran.
                                logger.error(f"OpenRouter SSE error: {err_msg}")
                                yield StreamEvent(
                                    type="error",
                                    content=_message_erreur_sse(
                                        code if isinstance(code, int) else None,
                                        error_type if isinstance(error_type, str) else None,
                                    ),
                                )
                                stream_finished = True
                                break

                            choices = event.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                finish_reason = choices[0].get("finish_reason")

                                # Handle text content
                                if content := delta.get("content"):
                                    has_content = True
                                    yield StreamEvent(type="text", content=content)

                                # Handle tool calls
                                if tool_call_deltas := delta.get("tool_calls"):
                                    for tc_delta in tool_call_deltas:
                                        idx = tc_delta.get("index", 0)

                                        if idx not in tool_calls:
                                            tool_calls[idx] = {
                                                "id": tc_delta.get("id", ""),
                                                "name": "",
                                                "arguments": "",
                                            }

                                        if func := tc_delta.get("function"):
                                            if name := func.get("name"):
                                                tool_calls[idx]["name"] = name
                                            if args := func.get("arguments"):
                                                tool_calls[idx]["arguments"] += args

                                # Check if done
                                if finish_reason == "tool_calls":
                                    for tc in tool_calls.values():
                                        try:
                                            arguments = json.loads(tc["arguments"]) if tc["arguments"] else {}
                                        except json.JSONDecodeError:
                                            arguments = {}

                                        yield StreamEvent(
                                            type="tool_call",
                                            tool_call=ToolCall(
                                                id=tc["id"],
                                                name=tc["name"],
                                                arguments=arguments,
                                            ),
                                        )
                                    pending_stop_reason = "tool_calls"

                                elif finish_reason == "stop":
                                    pending_stop_reason = "stop"

                                elif finish_reason == "length":
                                    if not has_content:
                                        logger.warning("OpenRouter: finish_reason=length sans contenu (budget tokens épuisé par le raisonnement)")
                                        yield StreamEvent(
                                            type="error",
                                            content="Le modèle a épuisé son budget de tokens sans produire de réponse visible. "
                                            "Essayez avec un prompt plus court ou augmentez max_tokens.",
                                        )
                                    else:
                                        pending_stop_reason = "length"

                                elif finish_reason == "content_filter":
                                    logger.warning("OpenRouter: réponse filtrée par le modèle")
                                    yield StreamEvent(
                                        type="error",
                                        content="Le modèle a filtré la réponse (content_filter). "
                                        "Reformule ton message ou essaie un autre modèle.",
                                    )

                        except json.JSONDecodeError:
                            continue

            # Filet : le flux s'est terminé sans jamais voir [DONE] ni erreur
            # SSE explicite (coupure après finish_reason, ou pas de
            # finish_reason explicite du tout).
            if not stream_finished:
                if not has_content and not tool_calls:
                    logger.warning("OpenRouter: réponse vide (flux coupé sans contenu)")
                    yield StreamEvent(
                        type="error",
                        content="Le modèle n'a produit aucune réponse. "
                        "Essayez un autre modèle ou vérifiez votre clé API OpenRouter.",
                    )
                else:
                    yield StreamEvent(
                        type="done",
                        stop_reason=pending_stop_reason or "stop",
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                    )

        except httpx.HTTPStatusError as http_error:
            response = http_error.response
            status = response.status_code
            error_body = ""
            try:
                error_body = response.text
            except Exception as body_err:
                logger.debug("Impossible de lire le body erreur OpenRouter: %s", body_err)
            logger.error(f"OpenRouter API error: {status} - {error_body}")

            # BUG-openrouter-403 : parser le body JSON pour un message d'erreur lisible
            api_error_msg = ""
            try:
                if error_body:
                    err_json = json.loads(error_body)
                    err_obj = err_json.get("error", {})
                    api_error_msg = err_obj.get("message", "") if isinstance(err_obj, dict) else str(err_obj)
            except (json.JSONDecodeError, AttributeError):
                pass
            # Borne la longueur pour éviter de flooder l'UI avec un message très long
            api_error_msg = api_error_msg[:200]

            if status == 401:
                yield StreamEvent(type="error", content="Clé API OpenRouter invalide ou expirée.")
            elif status == 402:
                yield StreamEvent(type="error", content="Crédit OpenRouter insuffisant. Recharge ton compte sur openrouter.ai.")
            elif status == 403:
                # 403 = pas de crédits, compte suspendu, ou clé sans permission
                if api_error_msg:
                    yield StreamEvent(
                        type="error",
                        content="OpenRouter a refusé la requête (403). "
                        "Vérifie tes crédits sur openrouter.ai/settings/billing ou choisis un modèle gratuit (:free).",
                    )
                else:
                    yield StreamEvent(
                        type="error",
                        content="OpenRouter : accès refusé (403). Crédits insuffisants ou clé sans permission. "
                        "Recharge ton compte sur openrouter.ai/settings/billing ou choisis un modèle gratuit (:free).",
                    )
            elif status == 429:
                yield StreamEvent(type="error", content="Trop de requêtes OpenRouter. Patiente quelques secondes.")
            else:
                if api_error_msg:
                    yield StreamEvent(type="error", content=f"Erreur API OpenRouter ({status})")
                else:
                    yield StreamEvent(type="error", content=f"Erreur API OpenRouter ({status})")
        except Exception as e:
            logger.error(f"OpenRouter streaming error: {e}")
            # Revue 0.48 p2 (F1) : jamais str(e) brut dans un évènement
            # relayé à l'écran - le détail vit dans le log ci-dessus. La forme
            # dit la CLASSE d'erreur : une panne de transport ouvre le circuit
            # (_is_provider_outage matche « réseau »), un bug local jamais.
            if isinstance(e, httpx.TransportError):
                yield StreamEvent(
                    type="error",
                    content=f"Erreur réseau vers le service d'IA ({type(e).__name__})",
                )
            else:
                yield StreamEvent(
                    type="error",
                    content=f"Erreur interne du service d'IA ({type(e).__name__})",
                )

    async def continue_with_tool_results(
        self,
        system_prompt: str | None,
        messages: list[dict],
        assistant_content: str,
        tool_calls: list[ToolCall],
        tool_results: list[ToolResult],
        tools: list[dict] | None = None,
        prior_turns: list[ToolTurn] | None = None,
        assistant_content_brut: "list[Any] | None" = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Continue OpenRouter conversation with tool results."""
        messages = list(messages)  # copie
        # Multi-tours (bug lcjp 11/06/2026) : rejouer les tours précédents
        # avant le tour courant, sinon le modèle re-demande le même outil.
        for turn in prior_turns or []:
            self._append_openai_tool_turn(
                messages, turn.assistant_content, turn.tool_calls, turn.tool_results
            )
        self._append_openai_tool_turn(messages, assistant_content, tool_calls, tool_results)

        async for event in self.stream(system_prompt, messages, tools):
            yield event
