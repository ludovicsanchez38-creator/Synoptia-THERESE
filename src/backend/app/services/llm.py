"""
THÉRÈSE v2 - LLM Service (Facade)

Handles LLM interactions with context management.
Supports Claude, OpenAI, Gemini, Mistral, Grok, and Ollama.

Sprint 2 - PERF-2.1: Refactored to use modular providers.
"""

import logging
import os
from pathlib import Path
from typing import AsyncGenerator

from app.services.context import ContextWindow

# Re-export types for backward compatibility
from app.services.providers import (
    AnthropicProvider,
    GeminiProvider,
    GrokProvider,
    LLMConfig,
    LLMProvider,
    Message,
    MistralProvider,
    OllamaProvider,
    OpenAIProvider,
    OpenRouterProvider,
    StreamEvent,
    ToolCall,
    ToolResult,
)

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# API Key Cache
# -----------------------------------------------------------------------------

_api_key_cache: dict[str, str | None] = {}
_api_key_cache_loaded: bool = False


async def load_api_key_cache() -> None:
    """Load all API keys from DB into memory cache."""
    global _api_key_cache, _api_key_cache_loaded

    try:
        from app.config import settings
        from app.services.encryption import get_encryption_service
        from sqlalchemy import create_engine, text

        engine = create_engine(f"sqlite:///{settings.db_path}")
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT key, value FROM preferences WHERE key LIKE :pattern"),
                {"pattern": "%api_key%"}
            )
            rows = result.fetchall()

            encryption = get_encryption_service()
            for row in rows:
                pref_key = row[0]
                value = row[1]
                if value:
                    if encryption.is_encrypted(value):
                        try:
                            value = encryption.decrypt(value)
                        except Exception:
                            logger.warning(f"Decryption failed for {pref_key}, skipping")
                            continue
                    _api_key_cache[pref_key] = value

        _api_key_cache_loaded = True
        logger.info(f"API key cache loaded: {len(_api_key_cache)} key(s)")

    except Exception as e:
        logger.warning(f"Could not load API key cache: {e}")


def invalidate_api_key_cache() -> None:
    """Invalidate API key cache (call after updates)."""
    global _api_key_cache_loaded
    _api_key_cache_loaded = False
    _api_key_cache.clear()


def _get_api_key_from_db(provider: str) -> str | None:
    """Load API key from database or cache."""
    if _api_key_cache_loaded:
        return _api_key_cache.get(f"{provider}_api_key")

    # Fallback: direct DB read via asyncio.to_thread pour ne pas bloquer l'event loop
    try:
        import asyncio

        def _sync_read_key():
            from app.config import settings
            from app.services.encryption import get_encryption_service
            from sqlalchemy import create_engine, text

            engine = create_engine(f"sqlite:///{settings.db_path}")
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT value FROM preferences WHERE key = :key"),
                    {"key": f"{provider}_api_key"}
                )
                row = result.fetchone()
                if row and row[0]:
                    value = row[0]
                    encryption = get_encryption_service()
                    if encryption.is_encrypted(value):
                        try:
                            value = encryption.decrypt(value)
                        except Exception as dec_err:
                            logger.error(f"Failed to decrypt {provider} API key: {dec_err}")
                            return None
                    return value
            return None

        # Si on est déjà dans un event loop, utiliser to_thread.
        # Sinon (appel sync), exécuter directement.
        try:
            asyncio.get_running_loop()
            # On ne peut pas await dans une fonction sync, donc on exécute en sync
            # Ce fallback est rarement appelé (le cache est normalement chargé)
            return _sync_read_key()
        except RuntimeError:
            return _sync_read_key()
    except Exception as e:
        logger.debug(f"Could not load {provider} API key: {e}")

    return None


# -----------------------------------------------------------------------------
# THERESE.md Loading
# -----------------------------------------------------------------------------

_therese_md_content: str | None = None
_therese_md_loaded: bool = False


def load_therese_md() -> str | None:
    """Load THERESE.md from standard locations."""
    global _therese_md_content, _therese_md_loaded

    if _therese_md_loaded:
        return _therese_md_content

    search_paths = [
        Path.home() / ".therese" / "THERESE.md",
        Path.home() / "THERESE.md",
    ]

    for path in search_paths:
        if path.exists() and path.is_file():
            try:
                content = path.read_text(encoding="utf-8")
                _therese_md_content = content
                _therese_md_loaded = True
                logger.info(f"Loaded THERESE.md from {path}")
                return content
            except Exception as e:
                logger.warning(f"Failed to read THERESE.md: {e}")

    _therese_md_loaded = True
    return None


def reload_therese_md() -> str | None:
    """Force reload of THERESE.md."""
    global _therese_md_content, _therese_md_loaded
    _therese_md_content = None
    _therese_md_loaded = False
    return load_therese_md()


# -----------------------------------------------------------------------------
# LLM Service (Facade)
# -----------------------------------------------------------------------------

class LLMService:
    """Service for LLM interactions."""

    DEFAULT_SYSTEM_PROMPT_TEMPLATE = """Tu es THÉRÈSE, une assistante IA souveraine française.

## Utilisateur
{user_identity}

## Ton rôle
Tu aides les entrepreneurs et TPE avec leurs tâches quotidiennes.
Tu es efficace, professionnelle et tu utilises un français naturel et fluide.

## Style de réponse
- Réponds de manière concise et directe. Va droit au but.
- N'utilise PAS de tableaux markdown sauf si l'utilisateur le demande explicitement.
- Privilégie les listes à puces ou le texte simple pour les récapitulatifs.
- Pas d'emojis de statut, pas de dashboards non sollicités.
- Si tu fais un récap en fin de réponse, utilise des listes à puces simples.

## Mémoire persistante
Tu as accès à une mémoire persistante contenant les contacts et projets de l'utilisateur.
{therese_md}"""

    DEFAULT_SYSTEM_PROMPT_NO_PROFILE = """Tu es THÉRÈSE, une assistante IA souveraine française.
Tu aides les entrepreneurs et TPE avec leurs tâches quotidiennes.

## Style de réponse
- Réponds de manière concise et directe. Va droit au but.
- N'utilise PAS de tableaux markdown sauf si l'utilisateur le demande explicitement.
- Privilégie les listes à puces ou le texte simple pour les récapitulatifs.
- Pas d'emojis de statut, pas de dashboards non sollicités.
{therese_md}"""

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or self._default_config()
        self._provider = None

    def _get_system_prompt_with_identity(self) -> str:
        """Get system prompt with user identity injected."""
        from app.services.user_profile import get_cached_profile

        profile = get_cached_profile()
        therese_md = load_therese_md()
        therese_md_section = ""
        if therese_md:
            content = therese_md[:10000]
            if len(therese_md) > 10000:
                content += "\n\n[... tronqué ...]"
            therese_md_section = f"\n\n## Instructions THERESE.md:\n{content}"

        if not profile or not profile.name:
            return self.DEFAULT_SYSTEM_PROMPT_NO_PROFILE.format(therese_md=therese_md_section)

        return self.DEFAULT_SYSTEM_PROMPT_TEMPLATE.format(
            user_identity=profile.format_for_llm(),
            therese_md=therese_md_section
        )

    def _default_config(self) -> LLMConfig:
        """Get default configuration from user preferences."""
        # Read user-selected provider/model from preferences
        selected_provider = None
        selected_model = None
        try:
            from app.config import settings
            from sqlalchemy import create_engine, text

            engine = create_engine(f"sqlite:///{settings.db_path}")
            with engine.connect() as conn:
                for key in ("llm_provider", "llm_model"):
                    result = conn.execute(
                        text("SELECT value FROM preferences WHERE key = :key"),
                        {"key": key},
                    )
                    row = result.fetchone()
                    if row and row[0]:
                        if key == "llm_provider":
                            selected_provider = row[0]
                        else:
                            selected_model = row[0]
        except Exception as e:
            logger.debug(f"Could not read LLM preferences: {e}")

        # Provider configs: (enum, default_model, context_window)
        provider_configs = {
            "anthropic": (LLMProvider.ANTHROPIC, "claude-opus-4-6", 200000),
            "openai": (LLMProvider.OPENAI, "gpt-5.2", 200000),
            "gemini": (LLMProvider.GEMINI, "gemini-3-pro-preview", 1000000),
            "mistral": (LLMProvider.MISTRAL, "mistral-large-latest", 256000),
            "grok": (LLMProvider.GROK, "grok-4", 131072),
            "openrouter": (LLMProvider.OPENROUTER, "anthropic/claude-sonnet-4-5", 200000),
            "ollama": (LLMProvider.OLLAMA, "mistral-nemo", 32000),
        }

        # If user selected a provider, use it
        if selected_provider and selected_provider in provider_configs:
            provider_enum, default_model, ctx_window = provider_configs[selected_provider]
            model = selected_model or default_model

            if selected_provider == "ollama":
                return LLMConfig(provider_enum, model, base_url="http://localhost:11434", context_window=ctx_window)

            api_key = _get_api_key_from_db(selected_provider)
            if not api_key:
                env_map = {
                    "anthropic": "ANTHROPIC_API_KEY",
                    "openai": "OPENAI_API_KEY",
                    "gemini": "GEMINI_API_KEY",
                    "mistral": "MISTRAL_API_KEY",
                    "grok": "XAI_API_KEY",
                    "openrouter": "OPENROUTER_API_KEY",
                }
                api_key = os.getenv(env_map.get(selected_provider, ""))

            if api_key:
                return LLMConfig(provider_enum, model, api_key=api_key, context_window=ctx_window)

            logger.warning(f"Selected provider {selected_provider} has no API key, falling back")

        # Fallback: first provider with a valid key
        anthropic_key = _get_api_key_from_db("anthropic") or os.getenv("ANTHROPIC_API_KEY")
        openai_key = _get_api_key_from_db("openai") or os.getenv("OPENAI_API_KEY")
        gemini_key = _get_api_key_from_db("gemini") or os.getenv("GEMINI_API_KEY")
        mistral_key = _get_api_key_from_db("mistral") or os.getenv("MISTRAL_API_KEY")

        if anthropic_key:
            return LLMConfig(LLMProvider.ANTHROPIC, "claude-opus-4-6", api_key=anthropic_key, context_window=200000)
        elif openai_key:
            return LLMConfig(LLMProvider.OPENAI, "gpt-5.2", api_key=openai_key, context_window=200000)
        elif gemini_key:
            return LLMConfig(LLMProvider.GEMINI, "gemini-3-pro-preview", api_key=gemini_key, context_window=1000000)
        elif mistral_key:
            return LLMConfig(LLMProvider.MISTRAL, "mistral-large-latest", api_key=mistral_key, context_window=256000)
        else:
            return LLMConfig(LLMProvider.OLLAMA, "mistral-nemo", base_url="http://localhost:11434", context_window=32000)

    async def _get_client(self):
        """Get shared HTTP client from global pool."""
        from app.services.http_client import get_http_client
        return await get_http_client()

    def _get_provider(self):
        """Get or create provider instance."""
        if self._provider is None:
            # Will be lazily initialized
            pass
        return self._provider

    async def _ensure_provider(self):
        """Ensure provider is initialized."""
        if self._provider is None:
            client = await self._get_client()
            provider_map = {
                LLMProvider.ANTHROPIC: AnthropicProvider,
                LLMProvider.OPENAI: OpenAIProvider,
                LLMProvider.GEMINI: GeminiProvider,
                LLMProvider.MISTRAL: MistralProvider,
                LLMProvider.GROK: GrokProvider,
                LLMProvider.OPENROUTER: OpenRouterProvider,
                LLMProvider.OLLAMA: OllamaProvider,
            }
            provider_class = provider_map.get(self.config.provider)
            if provider_class:
                self._provider = provider_class(self.config, client)

    def prepare_context(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
        memory_context: str | None = None,
    ) -> ContextWindow:
        """Prepare context window."""
        full_system = system_prompt or self._get_system_prompt_with_identity()
        if memory_context:
            full_system += f"\n\n## Contexte mémoire:\n{memory_context}"

        max_msg_tokens = self.config.context_window - 4096
        context = ContextWindow(
            messages=messages.copy(),
            system_prompt=full_system,
            max_tokens=max_msg_tokens,
        )
        return context.trim_to_fit()

    async def stream_response(
        self,
        context: ContextWindow,
        tools: list[dict] | None = None,
        enable_grounding: bool = True,
    ) -> AsyncGenerator[str, None]:
        """Stream response (text only, backward compat)."""
        async for event in self.stream_response_with_tools(context, tools, enable_grounding=enable_grounding):
            if event.type == "text" and event.content:
                yield event.content

    async def stream_response_with_tools(
        self,
        context: ContextWindow,
        tools: list[dict] | None = None,
        enable_grounding: bool = True,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Stream response with tool support."""
        await self._ensure_provider()

        # Convert context to provider format
        if self.config.provider == LLMProvider.ANTHROPIC:
            system_prompt, messages = context.to_anthropic_format()
        elif self.config.provider == LLMProvider.GEMINI:
            system_prompt, messages = context.to_gemini_format()
        else:
            messages = context.to_openai_format()
            system_prompt = context.system_prompt

        # Pass enable_grounding to Gemini provider
        if self.config.provider == LLMProvider.GEMINI:
            async for event in self._provider.stream(system_prompt, messages, tools, enable_grounding=enable_grounding):
                yield event
        else:
            async for event in self._provider.stream(system_prompt, messages, tools):
                yield event

    async def continue_with_tool_results(
        self,
        context: ContextWindow,
        assistant_content: str,
        tool_calls: list[ToolCall],
        tool_results: list[ToolResult],
        tools: list[dict] | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Continue after tool execution."""
        await self._ensure_provider()

        if self.config.provider == LLMProvider.ANTHROPIC:
            system_prompt, messages = context.to_anthropic_format()
        elif self.config.provider == LLMProvider.GEMINI:
            system_prompt, messages = context.to_gemini_format()
        else:
            messages = context.to_openai_format()
            system_prompt = context.system_prompt

        async for event in self._provider.continue_with_tool_results(
            system_prompt, messages, assistant_content, tool_calls, tool_results, tools
        ):
            yield event

    async def generate_content(
        self,
        prompt: str,
        context: dict | None = None,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Generate complete content (non-streaming).

        Grounding is disabled for content generation (skills, documents)
        to avoid Gemini searching instead of generating structured content.

        Args:
            prompt: Le prompt utilisateur
            context: Contexte optionnel (clé-valeur)
            system_prompt: System prompt personnalisé
            max_tokens: Limite de tokens en sortie (défaut: config du provider)
        """
        messages = [Message(role="user", content=prompt)]
        effective_system = system_prompt or self._get_system_prompt_with_identity()

        if context:
            context_str = "\n".join(f"- {k}: {v}" for k, v in context.items())
            effective_system += f"\n\n## Contexte:\n{context_str}"

        # Thread-safety : copier la config si on doit overrider max_tokens
        # pour ne pas muter l'état partagé entre requêtes concurrentes.
        original_config = self.config
        if max_tokens and max_tokens > self.config.max_tokens:
            from dataclasses import replace
            self.config = replace(self.config, max_tokens=max_tokens)

        ctx = self.prepare_context(messages=messages, system_prompt=effective_system)
        content_parts = []
        errors = []
        try:
            async for event in self.stream_response_with_tools(ctx, enable_grounding=False):
                if event.type == "text" and event.content:
                    content_parts.append(event.content)
                elif event.type == "error":
                    errors.append(event.content or "Unknown error")
        finally:
            self.config = original_config

        if not content_parts and errors:
            raise RuntimeError(f"Erreur LLM lors de la génération : {'; '.join(errors)}")

        return "".join(content_parts)

    async def close(self):
        """Close method (no-op, client managed globally)."""
        # Client is now managed by http_client module
        pass


# -----------------------------------------------------------------------------
# Global Instance
# -----------------------------------------------------------------------------

_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    """Get global LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def invalidate_llm_service() -> None:
    """Reset LLM service singleton (call after provider/model change)."""
    global _llm_service
    _llm_service = None


def get_llm_service_for_provider(provider_name: str) -> LLMService | None:
    """Get LLM service for a specific provider if configured."""
    provider_name = provider_name.lower()

    provider_configs = {
        "anthropic": (LLMProvider.ANTHROPIC, "claude-opus-4-6", "ANTHROPIC_API_KEY", 200000),
        "openai": (LLMProvider.OPENAI, "gpt-5.2", "OPENAI_API_KEY", 200000),
        "gemini": (LLMProvider.GEMINI, "gemini-3-pro-preview", ["GEMINI_API_KEY", "GOOGLE_API_KEY"], 1000000),
        "mistral": (LLMProvider.MISTRAL, "mistral-large-latest", "MISTRAL_API_KEY", 256000),
        "grok": (LLMProvider.GROK, "grok-4", "XAI_API_KEY", 131072),
        "openrouter": (LLMProvider.OPENROUTER, "anthropic/claude-sonnet-4-5", "OPENROUTER_API_KEY", 200000),
        "ollama": (LLMProvider.OLLAMA, "mistral-nemo", None, 32000),
    }

    if provider_name not in provider_configs:
        return None

    provider, model, env_vars, context_window = provider_configs[provider_name]

    api_key = None
    if env_vars:
        api_key = _get_api_key_from_db(provider_name)
        if not api_key:
            if isinstance(env_vars, str):
                env_vars = [env_vars]
            for env_var in env_vars:
                api_key = os.getenv(env_var)
                if api_key:
                    break

        if not api_key:
            return None

    base_url = "http://localhost:11434" if provider_name == "ollama" else None

    config = LLMConfig(
        provider=provider,
        model=model,
        api_key=api_key,
        base_url=base_url,
        context_window=context_window,
    )

    return LLMService(config)
