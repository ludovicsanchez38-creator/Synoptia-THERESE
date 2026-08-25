"""
THÉRÈSE v2 - LLM Provider Base Module

Shared types and ABC for all LLM providers.
Sprint 2 - PERF-2.1: Extracted from monolithic llm.py
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, AsyncGenerator, Literal

import httpx

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    ANTHROPIC = "anthropic"
    MISTRAL = "mistral"
    OLLAMA = "ollama"
    OPENAI = "openai"
    GEMINI = "gemini"
    GROK = "grok"
    OPENROUTER = "openrouter"
    PERPLEXITY = "perplexity"
    DEEPSEEK = "deepseek"
    INFOMANIAK = "infomaniak"
    # Ajoutés le 24/08/2026. Tous compatibles OpenAI, confirmé en documentation
    # officielle : ils héritent donc de la boucle d'outils sans la réécrire.
    GLM = "glm"
    KIMI = "kimi"
    QWEN = "qwen"
    MINIMAX = "minimax"


def adresse_fournisseur_valide(adresse: str) -> bool:
    """Une adresse de fournisseur exploitable, pas juste un préfixe plausible.

    Revue dette 0.43.4 (deux passes) : startswith("http://") laissait passer
    « http:// » tout seul, un hôte avec espace et « https://javascript:… » ;
    puis la validation ne vivait que dans la route POST /llm alors que le
    démarrage et les agents relisent la préférence par un autre chemin. D'où
    ce module neutre : tout lecteur ou écrivain d'adresse applique LA même
    règle. urlsplit + hostname + port tranchent ; le moindre blanc disqualifie.
    """
    from urllib.parse import urlsplit

    if any(c.isspace() for c in adresse):
        return False
    try:
        morceaux = urlsplit(adresse)
        if morceaux.scheme not in ("http", "https"):
            return False
        if not morceaux.hostname:
            return False
        morceaux.port  # noqa: B018 - lève ValueError sur un port imparsable
    except ValueError:
        return False
    return True


@dataclass
class LLMConfig:
    """LLM configuration."""

    provider: LLMProvider
    model: str
    max_tokens: int = 4096
    temperature: float = 0.7
    context_window: int = 128000
    api_key: str | None = None
    base_url: str | None = None
    # Effort de raisonnement (chantier 10/07/2026) : None = Auto (rien
    # d'envoye, defaut serveur). Valeurs normalisees low/medium/high/max.
    effort: str | None = None
    # 0.48 : la valeur REELLEMENT emise, resolue par le catalogue a la
    # CONSTRUCTION (resoudre_effort est ainsi appele par tout chemin de
    # creation - helper, config par defaut, POST /config/llm, replis -
    # sans qu'aucun site ne puisse l'oublier). Les providers emettent ce
    # champ dans leur syntaxe, sans table locale.
    effort_resolu: str | None = None

    def __post_init__(self) -> None:
        # Import local : modeles_catalogue importe LLMProvider d'ici -
        # l'import module-niveau serait un cycle.
        from app.services.modeles_catalogue import resoudre_effort

        self.effort_resolu = resoudre_effort(
            self.model, self.effort, self.provider.value
        )


@dataclass
class Message:
    """Chat message."""

    role: Literal["user", "assistant", "system"]
    content: str


@dataclass
class ToolCall:
    """A tool call from the LLM."""
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ToolResult:
    """Result of a tool execution to send back to the LLM."""
    tool_call_id: str
    result: Any
    is_error: bool = False


@dataclass
class ToolTurn:
    """Un tour d'outils complet (texte assistant + appels + résultats).

    Les continuations multi-tours doivent REJOUER les tours précédents dans
    le contexte envoyé au modèle, sinon il re-demande les mêmes outils en
    boucle puis invente une explication d'échec (bug lcjp 11/06/2026).
    """
    assistant_content: str
    # 0.48 (Mistral reasoning) : le content BRUT du tour (liste de chunks,
    # thinking compris) quand le fournisseur l'exige au rejeu. None pour
    # tous les autres providers.
    tool_calls: list[ToolCall]
    tool_results: list[ToolResult]
    assistant_content_brut: Any | None = None


@dataclass
class StreamEvent:
    """An event from the LLM stream."""
    type: Literal["text", "tool_call", "done", "error"]
    content: str | None = None
    tool_call: ToolCall | None = None
    stop_reason: str | None = None
    # Usage réel du provider (event type="done"), quand disponible. None si le
    # provider ne l'a pas encore fourni : l'appelant retombe alors sur
    # l'estimation ~2 tokens/mot (cf chat.py/board.py).
    input_tokens: int | None = None
    output_tokens: int | None = None
    # 0.48 (Mistral reasoning) : le content brut du tour, posé sur
    # l'évènement tool_call quand le tour était en chunks - transporté
    # par chat.py jusqu'au ToolTurn du rejeu.
    assistant_content_brut: Any | None = None


class BaseProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: LLMConfig, client: httpx.AsyncClient):
        self.config = config
        self.client = client

    @abstractmethod
    async def stream(
        self,
        system_prompt: str | None,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Stream response from the LLM.

        Args:
            system_prompt: System prompt
            messages: Messages in provider-native format
            tools: Optional tools definitions

        Yields:
            StreamEvent objects
        """
        pass

    @abstractmethod
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
        """
        Continue streaming after tool execution.

        Args:
            system_prompt: System prompt
            messages: Messages before tool calls
            assistant_content: Text generated before tool calls
            tool_calls: The tool calls that were made
            tool_results: Results of those tool calls
            tools: Tools to make available
            prior_turns: Tours d'outils PRÉCÉDENTS de la même réponse, à
                rejouer dans l'ordre avant le tour courant (multi-tours)

        Yields:
            StreamEvent objects
        """
        pass

    @staticmethod
    def _append_openai_tool_turn(
        messages: list[dict[str, Any]],
        assistant_content: str,
        tool_calls: list[ToolCall],
        tool_results: list[ToolResult],
        assistant_content_brut: Any | None = None,
    ) -> None:
        """Ajoute un tour d'outils au format OpenAI-compatible (in place).

        Un message assistant portant les tool_calls (arguments en chaîne
        JSON), puis un message role="tool" par résultat (tool_call_id).
        Partagé par OpenAI/Grok/Mistral/DeepSeek/Infomaniak/OpenRouter/
        Perplexity.
        """
        messages.append({
            "role": "assistant",
            # BUG-108 (lcjp, 12/06/2026) : Mistral rejette en 400 un message
            # assistant ayant à la fois un content NON vide ET des tool_calls
            # (le modèle écrivait du texte avant l'appel d'outil → 400 → résultat
            # read_emails perdu → boucle « Max tool iterations »). Un message
            # porteur de tool_calls ne transporte donc jamais de texte : on force
            # `None` (valeur canonique OpenAI/litellm pour un message tool-call,
            # déjà envoyée par l'ancien code quand le texte était vide, donc
            # éprouvée côté Mistral). Le texte pré-appel reste affiché/streamé à
            # l'utilisateur. Couvre aussi OpenRouter/Infomaniak routant vers Mistral.
            #
            # 0.48 : EXCEPTION documentée - en mode reasoning, Mistral rend le
            # content en LISTE de chunks et sa doc exige de rejouer le message
            # assistant COMPLET en multi-tours. Seule une LISTE se rejoue ;
            # une string reste None (BUG-108 préservé).
            "content": (
                assistant_content_brut
                if isinstance(assistant_content_brut, list)
                and assistant_content_brut
                else None
            ),
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

    def _parse_sse_line(self, line: str) -> dict | None:
        """Parse an SSE data line to JSON."""
        if line.startswith("data: "):
            data = line[6:]
            if data.strip() == "[DONE]":
                return None
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return None
        return None
