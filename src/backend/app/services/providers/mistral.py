"""
THÉRÈSE v2 - Mistral Provider

Mistral API streaming implementation.
Sprint 2 - PERF-2.1: Extracted from monolithic llm.py

API Mistral = compatible OpenAI : meme protocole de streaming des tool_calls
(arguments envoyes en chunks, accumules par index) et meme boucle de
continuation (message assistant avec tool_calls + messages role=tool, puis
re-stream). Cette implementation est alignee sur openai.py.
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

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"


class MistralProvider(BaseProvider):
    """Mistral API provider."""

    def _build_request_body(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> dict:
        request_body: dict = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": messages,
            "stream": True,
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
        """Stream from Mistral API avec support des outils.

        Les tool_calls sont streames par fragments (id/nom dans un chunk,
        arguments en plusieurs morceaux) : on les accumule par index puis on
        les emet completement a la fin (finish_reason == "tool_calls"), avec un
        StreamEvent done stop_reason="tool_calls" pour que l'orchestrateur
        execute les outils PUIS rappelle continue_with_tool_results. Sans ca,
        Mistral renvoyait une reponse vide des qu'un outil etait sollicite
        (CRM, generation Word, synthese board).
        """
        request_body = self._build_request_body(messages, tools)
        done_emitted = False

        try:
            async with self.client.stream(
                "POST",
                MISTRAL_API_URL,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                json=request_body,
            ) as response:
                response.raise_for_status()

                # tool_calls en cours de construction, indexes par position
                tool_calls: dict[int, dict] = {}

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        if not done_emitted:
                            yield StreamEvent(type="done", stop_reason="end_turn")
                            done_emitted = True
                        break
                    try:
                        event = json.loads(data)
                    except json.JSONDecodeError:
                        continue

                    choices = event.get("choices", [])
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})
                    finish_reason = choices[0].get("finish_reason")

                    # Texte
                    if content := delta.get("content"):
                        yield StreamEvent(type="text", content=content)

                    # Fragments de tool_calls (accumulation par index)
                    if tool_call_deltas := delta.get("tool_calls"):
                        for tc_delta in tool_call_deltas:
                            idx = tc_delta.get("index", 0)
                            if idx not in tool_calls:
                                tool_calls[idx] = {"id": tc_delta.get("id", ""), "name": "", "arguments": ""}
                            if tc_delta.get("id"):
                                tool_calls[idx]["id"] = tc_delta["id"]
                            if func := tc_delta.get("function"):
                                if name := func.get("name"):
                                    tool_calls[idx]["name"] = name
                                if args := func.get("arguments"):
                                    tool_calls[idx]["arguments"] += args

                    # Fin de tour
                    if finish_reason == "tool_calls" or (finish_reason and tool_calls):
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
                        yield StreamEvent(type="done", stop_reason="tool_calls")
                        done_emitted = True
                        break
                    elif finish_reason:
                        yield StreamEvent(type="done", stop_reason="end_turn")
                        done_emitted = True
                        break

            # Filet : si le flux se termine sans finish_reason explicite
            if not done_emitted:
                yield StreamEvent(type="done", stop_reason="end_turn")

        except httpx.HTTPStatusError as e:
            logger.error(f"Mistral API error: {e.response.status_code}")
            yield StreamEvent(type="error", content=f"API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Mistral streaming error: {e}")
            yield StreamEvent(type="error", content=str(e))

    async def continue_with_tool_results(
        self,
        system_prompt: str | None,
        messages: list[dict],
        assistant_content: str,
        tool_calls: list[ToolCall],
        tool_results: list[ToolResult],
        tools: list[dict] | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Renvoie les resultats d'outils a Mistral et re-stream la reponse finale.

        Format OpenAI-compatible : un message assistant portant les tool_calls,
        puis un message role="tool" par resultat (tool_call_id + content).
        """
        messages = list(messages)  # copie

        messages.append({
            "role": "assistant",
            "content": assistant_content or None,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments) if tc.arguments else "{}",
                    },
                }
                for tc in tool_calls
            ],
        })

        for tr in tool_results:
            result_content = tr.result
            if isinstance(result_content, dict):
                result_content = json.dumps(result_content)
            elif not isinstance(result_content, str):
                result_content = str(result_content)
            messages.append({
                "role": "tool",
                "tool_call_id": tr.tool_call_id,
                "content": result_content,
            })

        async for event in self.stream(system_prompt, messages, tools):
            yield event
