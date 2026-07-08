"""
THÉRÈSE v2 - Gemini Provider

Google Gemini API streaming implementation.
Sprint 2 - PERF-2.1: Extracted from monolithic llm.py
"""

import json
import logging
import re
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

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# Préfixe des ids synthétisés : Gemini < 3 n'envoie pas d'id de functionCall,
# on en fabrique un pour corréler les résultats. On ne le renvoie PAS dans le
# functionResponse (la doc impose de renvoyer l'id exact UNIQUEMENT s'il vient
# du modèle).
_SYNTHETIC_ID_PREFIX = "gemini-call-"


# Revue adversariale US-009 : le champ `parameters` de l'API v1beta est un
# proto Schema (sous-ensemble OpenAPI) qui REJETTE les clés inconnues avec un
# 400 sur toute la requête. Les inputSchema MCP contiennent couramment
# $schema, additionalProperties, anyOf, default... -> whitelist récursive.
_GEMINI_SCHEMA_KEYS = {
    "type", "description", "properties", "required", "enum", "items",
    "nullable", "format", "minimum", "maximum", "minItems", "maxItems",
}


def _sanitize_schema(schema: dict) -> dict:
    """Ne garde que les clés du proto Schema Gemini, récursivement."""
    cleaned: dict = {}
    for key, value in schema.items():
        if key not in _GEMINI_SCHEMA_KEYS:
            continue
        if key == "properties" and isinstance(value, dict):
            cleaned[key] = {
                name: _sanitize_schema(sub) if isinstance(sub, dict) else sub
                for name, sub in value.items()
            }
        elif key == "items" and isinstance(value, dict):
            cleaned[key] = _sanitize_schema(value)
        else:
            cleaned[key] = value
    return cleaned


# L'API Gemini impose sur functionDeclaration.name : commencer par une lettre
# ou un underscore, puis [A-Za-z0-9_.:-], 128 caractères max. Les noms d'outils
# MCP (serveur__outil, parfois avec /, espaces, ou un chiffre en tête) violent
# souvent cette règle -> 400 "Invalid function name" sur TOUTE la requête, donc
# plus aucune réponse Gemini.
_INVALID_NAME_CHAR = re.compile(r"[^A-Za-z0-9_.:-]")


def _sanitize_function_name(name: str) -> str:
    """Rend un nom d'outil conforme à la contrainte Gemini (cf. ci-dessus).

    Déterministe : la même entrée donne toujours la même sortie, ce qui permet
    de re-sanitiser un nom à la continuation sans table de correspondance.
    """
    if not name:
        return "_"
    cleaned = _INVALID_NAME_CHAR.sub("_", name)
    if not (cleaned[0].isalpha() or cleaned[0] == "_"):
        cleaned = "_" + cleaned
    return cleaned[:128]


def _build_name_map(tools: list[dict]) -> dict[str, str]:
    """nom sanitisé -> nom réel, pour ré-associer le functionCall renvoyé par
    Gemini à l'outil enregistré (qui porte son nom d'origine)."""
    mapping: dict[str, str] = {}
    for tool in tools:
        raw = (tool.get("function", tool) or {}).get("name", "")
        if raw:
            mapping[_sanitize_function_name(raw)] = raw
    return mapping


def _tools_to_function_declarations(tools: list[dict]) -> list[dict]:
    """US-009 : convertit les tools format OpenAI vers functionDeclarations.

    Les NOMS sont sanitisés (contrainte Gemini, bug #2) et les schémas
    (memory/workspace tools, mais aussi inputSchema MCP arbitraires) vers le
    sous-ensemble proto Schema accepté par l'API.
    """
    declarations = []
    for tool in tools:
        func = tool.get("function", tool)
        decl: dict = {"name": _sanitize_function_name(func.get("name", ""))}
        if func.get("description"):
            decl["description"] = func["description"]
        if isinstance(func.get("parameters"), dict):
            decl["parameters"] = _sanitize_schema(func["parameters"])
        declarations.append(decl)
    return declarations


def _message_has_payload(msg: dict) -> bool:
    """Un message Gemini est exploitable s'il a du texte non vide OU un
    functionCall/functionResponse (US-009 : l'ancien filtre texte-seulement
    aurait jeté les tours d'outils de la continuation)."""
    for part in msg.get("parts") or []:
        if part.get("text", "").strip():
            return True
        if "functionCall" in part or "functionResponse" in part:
            return True
    return False


class GeminiProvider(BaseProvider):
    """Google Gemini API provider."""

    async def stream(
        self,
        system_prompt: str | None,
        messages: list[dict],
        tools: list[dict] | None = None,
        enable_grounding: bool = True,
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Stream from Google Gemini API with optional Google Search grounding.

        Args:
            system_prompt: System instruction
            messages: Messages in Gemini format (contents with parts)
            tools: Not used for Gemini (grounding instead)
            enable_grounding: Enable Google Search grounding (default True)
        """
        model = self.config.model
        url = f"{GEMINI_API_BASE}/{model}:streamGenerateContent"

        try:
            # Filter out empty messages (Gemini rejects empty parts)
            # US-009 : garder aussi les tours functionCall/functionResponse
            filtered_messages = [msg for msg in messages if _message_has_payload(msg)]

            if not filtered_messages:
                logger.error("Gemini: No valid messages to send")
                yield StreamEvent(type="error", content="Aucun message valide à envoyer")
                return

            request_body: dict[str, Any] = {
                "contents": filtered_messages,
                "generationConfig": {
                    "maxOutputTokens": self.config.max_tokens,
                    "temperature": self.config.temperature,
                },
            }

            # Add system instruction if present
            if system_prompt:
                request_body["systemInstruction"] = {
                    "parts": [{"text": system_prompt}]
                }

            # US-009 : function calling + grounding.
            # - tools fournis -> functionDeclarations (format officiel).
            # - google_search : seul Gemini 3 combine officiellement les
            #   outils intégrés avec le function calling ; sur 2.x, on écarte
            #   le grounding dès qu'il y a des functionDeclarations.
            declarations = _tools_to_function_declarations(tools) if tools else []
            # Table nom-sanitisé -> nom-réel pour ré-associer le functionCall
            # renvoyé par Gemini (qui voit les noms sanitisés) à l'outil réel.
            name_map = _build_name_map(tools) if tools else {}
            grounding_models = ["gemini-3", "gemini-2.5", "gemini-2.0"]
            grounding_ok = enable_grounding and any(model.startswith(m) for m in grounding_models)
            if declarations and grounding_ok and model.startswith("gemini-3"):
                request_body["tools"] = [{"google_search": {}, "functionDeclarations": declarations}]
                # Combiner built-in tools (google_search) + function calling sur Gemini 3
                # exige toolConfig.include_server_side_tool_invocations=true ET le mode
                # VALIDATED (le mode AUTO n'est PAS supporte avec ce flag). Sans ce bloc,
                # l'API renvoie 400 "Please enable tool_config.include_server_side_tool_invocations"
                # et le chat Gemini avec outils est mort (rapport Syn 14/06).
                # Source : ai.google.dev/gemini-api/docs/tool-combination (verifie 14/06/2026).
                request_body["toolConfig"] = {
                    "functionCallingConfig": {"mode": "VALIDATED"},
                    "include_server_side_tool_invocations": True,
                }
            elif declarations:
                request_body["tools"] = [{"functionDeclarations": declarations}]
            elif grounding_ok:
                request_body["tools"] = [{"google_search": {}}]

            logger.debug(f"Gemini request to {model}: {len(filtered_messages)} messages")

            async with self.client.stream(
                "POST",
                url,
                params={"key": self.config.api_key, "alt": "sse"},
                headers={"Content-Type": "application/json"},
                json=request_body,
            ) as response:
                if response.status_code != 200:
                    error_body = await response.aread()
                    error_text = error_body.decode()
                    logger.error(f"Gemini API {response.status_code}: {error_text}")
                    # Parse error message for user-friendly display
                    try:
                        error_json = json.loads(error_text)
                        error_msg = error_json.get("error", {}).get("message", error_text)
                    except json.JSONDecodeError:
                        error_msg = error_text[:200]
                    yield StreamEvent(type="error", content=f"Gemini: {error_msg}")
                    return
                has_tool_calls = False
                tool_call_index = 0
                # Usage réel (dette 14/06/2026) : usageMetadata est présent sur
                # chaque chunk avec des compteurs cumulatifs - on garde la
                # dernière valeur vue, utilisée au yield "done" final.
                input_tokens: int | None = None
                output_tokens: int | None = None
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if not data.strip():
                            continue
                        try:
                            event = json.loads(data)
                            if usage := event.get("usageMetadata"):
                                input_tokens = usage.get("promptTokenCount", input_tokens)
                                output_tokens = usage.get("candidatesTokenCount", output_tokens)
                            candidates = event.get("candidates", [])
                            if candidates:
                                content = candidates[0].get("content", {})
                                parts = content.get("parts", [])
                                for part in parts:
                                    if text := part.get("text"):
                                        yield StreamEvent(type="text", content=text)
                                    # US-009 : functionCall (arrive entier dans
                                    # un chunk, args déjà en objet JSON)
                                    if fc := part.get("functionCall"):
                                        raw_name = fc.get("name")
                                        if not raw_name:
                                            continue
                                        # Remapper le nom sanitisé vers le nom réel
                                        name = name_map.get(raw_name, raw_name)
                                        call_id = fc.get("id") or f"{_SYNTHETIC_ID_PREFIX}{tool_call_index}"
                                        has_tool_calls = True
                                        yield StreamEvent(
                                            type="tool_call",
                                            tool_call=ToolCall(
                                                id=call_id,
                                                name=name,
                                                arguments=fc.get("args") or {},
                                            ),
                                        )
                                        tool_call_index += 1
                                # Log grounding metadata if present
                                grounding = candidates[0].get("groundingMetadata")
                                if grounding:
                                    sources = grounding.get("webSearchQueries", [])
                                    if sources:
                                        logger.debug(f"Gemini grounding queries: {sources}")
                        except json.JSONDecodeError:
                            continue

            yield StreamEvent(
                type="done",
                stop_reason="tool_calls" if has_tool_calls else "end_turn",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

        except httpx.HTTPStatusError as e:
            error_body = e.response.text if hasattr(e.response, 'text') else str(e)
            logger.error(f"Gemini API error: {e.response.status_code} - {error_body}")
            yield StreamEvent(type="error", content=f"API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            yield StreamEvent(type="error", content=str(e))

    async def continue_with_tool_results(
        self,
        system_prompt: str | None,
        messages: list[dict],
        assistant_content: str,
        tool_calls: list[ToolCall],
        tool_results: list[ToolResult],
        tools: list[dict] | None = None,
        prior_turns: list[ToolTurn] | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """US-009 : continuation après exécution des outils (format Gemini).

        Tour "model" qui rejoue les functionCall, puis tour "user" avec un
        functionResponse {name, response} par résultat. L'id n'est renvoyé que
        s'il vient du modèle (Gemini 3) - jamais nos ids synthétiques.
        """
        contents = list(messages)
        # Multi-tours (bug lcjp 11/06/2026) : rejouer les tours précédents
        for turn in prior_turns or []:
            self._append_tool_turn(
                contents, turn.assistant_content, turn.tool_calls, turn.tool_results
            )
        self._append_tool_turn(contents, assistant_content, tool_calls, tool_results)

        async for event in self.stream(system_prompt, contents, tools, enable_grounding=False):
            yield event

    @staticmethod
    def _append_tool_turn(
        contents: list[dict[str, Any]],
        assistant_content: str,
        tool_calls: list[ToolCall],
        tool_results: list[ToolResult],
    ) -> None:
        """Ajoute un tour d'outils au format Gemini (functionCall/functionResponse)."""
        model_parts: list[dict] = []
        if assistant_content:
            model_parts.append({"text": assistant_content})
        for tc in tool_calls:
            # Nom re-sanitisé : il doit matcher les functionDeclarations
            # redéclarées (sanitisées), sinon Gemini ne corrèle pas le tour.
            fc: dict[str, Any] = {"name": _sanitize_function_name(tc.name), "args": tc.arguments or {}}
            if tc.id and not tc.id.startswith(_SYNTHETIC_ID_PREFIX):
                fc["id"] = tc.id
            model_parts.append({"functionCall": fc})
        contents.append({"role": "model", "parts": model_parts})

        calls_by_id = {tc.id: tc for tc in tool_calls}
        # Revue adversariale : sans ids (Gemini < 3), la corrélation est
        # positionnelle -> émettre les functionResponse dans l'ORDRE des
        # functionCall, pas dans l'ordre d'exécution (enforce_create_cap
        # déplace les appels bloqués en queue de tool_results).
        order = {tc.id: i for i, tc in enumerate(tool_calls)}
        sorted_results = sorted(
            tool_results, key=lambda tr: order.get(tr.tool_call_id, len(order))
        )
        response_parts: list[dict] = []
        for tr in sorted_results:
            tc = calls_by_id.get(tr.tool_call_id)
            fr: dict[str, Any] = {
                "name": _sanitize_function_name(tc.name) if tc else "",
                "response": {"result": tr.result},
            }
            if tc and tc.id and not tc.id.startswith(_SYNTHETIC_ID_PREFIX):
                fr["id"] = tc.id
            response_parts.append({"functionResponse": fr})
        contents.append({"role": "user", "parts": response_parts})
