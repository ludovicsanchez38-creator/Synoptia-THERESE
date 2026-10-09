"""Claude et Gemini n'envoient pas plus que le plafond publié.

Le catalogue dit 128 000 pour les Claude récents et 65 536 pour
Gemini 3.8 Flash. Une configuration plus haute doit être bornée.
"""

from __future__ import annotations

import httpx
import pytest
from app.services.providers.anthropic import AnthropicProvider
from app.services.providers.base import LLMConfig, LLMProvider
from app.services.providers.gemini import GeminiProvider


def _corps_claude(modele: str, max_tokens: int) -> dict:
    config = LLMConfig(
        LLMProvider.ANTHROPIC, modele, api_key="k", max_tokens=max_tokens,
    )
    return AnthropicProvider(config, httpx.AsyncClient())._build_request_body(
        "sys", [{"role": "user", "content": "salut"}], None,
    )


class TestPlafondSortiePublie:
    @pytest.mark.parametrize(
        "modele",
        ["claude-fable-5-1", "claude-sonnet-5-5", "claude-haiku-5-5"],
    )
    def test_claude_borne_une_demande_au_dessus_de_128000(self, modele: str):
        config = LLMConfig(
            LLMProvider.ANTHROPIC, modele, api_key="k", max_tokens=200_000,
        )
        assert config.max_tokens == 200_000
        assert _corps_claude(modele, 200_000)["max_tokens"] == 128_000
        assert _corps_claude(modele, 1_000)["max_tokens"] == 1_000

    def test_gemini_38_borne_une_demande_au_dessus_de_65536(self):
        config = LLMConfig(
            LLMProvider.GEMINI, "gemini-3.8-flash", api_key="g", max_tokens=200_000,
        )
        assert config.max_tokens == 200_000
        corps = GeminiProvider(config, httpx.AsyncClient())._build_request_body(
            [], None, None,
        )
        assert corps["generationConfig"]["maxOutputTokens"] == 65_536
        sous = LLMConfig(
            LLMProvider.GEMINI, "gemini-3.8-flash", api_key="g", max_tokens=1_000,
        )
        corps_sous = GeminiProvider(sous, httpx.AsyncClient())._build_request_body(
            [], None, None,
        )
        assert corps_sous["generationConfig"]["maxOutputTokens"] == 1_000
