"""
Lot modèles 10/07/2026 - paramètres de sampling conditionnels chez Anthropic.

Les modèles Anthropic récents (Fable 5, Sonnet 5, Opus 4.7/4.8) REFUSENT les
paramètres de sampling : envoyer `temperature` retourne un 400. Le provider
les envoyait inconditionnellement -> sélectionner un de ces modèles cassait
le chat (bug latent : Opus 4.8 était déjà au catalogue). Les modèles plus
anciens (Sonnet 4.6, Haiku 4.5...) les acceptent toujours.

Vérifié le 10/07/2026 contre la référence API Anthropic (skill claude-api) :
« Sampling parameters (temperature, top_p, top_k) are also removed and will
400 » sur Fable 5 / Opus 4.8 / 4.7 / Sonnet 5.
"""
import httpx
import pytest
from app.services.llm import LLMConfig, LLMProvider
from app.services.providers.anthropic import AnthropicProvider


def _provider(model: str) -> AnthropicProvider:
    config = LLMConfig(LLMProvider.ANTHROPIC, model, api_key="sk-ant-test")
    # Client jamais utilisé : on ne teste que la construction du payload.
    return AnthropicProvider(config, httpx.AsyncClient())


@pytest.mark.parametrize(
    "model",
    ["claude-fable-5", "claude-opus-4-8", "claude-opus-4-7", "claude-sonnet-5"],
)
def test_pas_de_temperature_sur_les_modeles_recents(model):
    body = _provider(model)._build_request_body(
        system_prompt="sys", messages=[{"role": "user", "content": "salut"}],
        anthropic_tools=None,
    )
    assert "temperature" not in body, f"{model} refuse temperature (400 API)"
    assert body["model"] == model
    assert body["stream"] is True


@pytest.mark.parametrize(
    "model",
    ["claude-sonnet-4-6", "claude-haiku-4-5-20251001", "claude-opus-4-6"],
)
def test_temperature_conservee_sur_les_modeles_qui_l_acceptent(model):
    body = _provider(model)._build_request_body(
        system_prompt="sys", messages=[{"role": "user", "content": "salut"}],
        anthropic_tools=None,
    )
    assert "temperature" in body
