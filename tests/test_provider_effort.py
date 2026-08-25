"""
Chantier effort (10/07/2026 soir, validé Ludo) - reasoning effort par provider.

THÉRÈSE n'envoyait aucun effort : tous les modèles tournaient au défaut
serveur. Nouveau champ LLMConfig.effort (None = Auto = rien d'envoyé),
traduit par provider et envoyé UNIQUEMENT aux modèles dont le support est
VÉRIFIÉ (sources du 10/07/2026) :
- Anthropic `output_config.effort` low/medium/high/max : Fable 5, Sonnet 5,
  Sonnet 4.6, Opus 4.5+ - PAS Haiku (erreur API).
- OpenAI `reasoning_effort` : vérifié sur GPT-5.6 (none->max). Les 5.5/5.4 ne
  sont PAS sourcés ce soir -> rien d'envoyé (dette documentée).
- xAI `reasoning_effort` low/medium/high (défaut high) : grok-4.5 -> Maximal
  plafonné à high.
- Ollama `think` : niveaux low/medium/high (max non standardisé, gpt-oss le
  refuse) -> plafonné à high ; les modèles non-thinking renvoient une erreur,
  gérée par retry sans think côté stream (testé séparément).
"""
import httpx
import pytest
from app.services.llm import LLMConfig, LLMProvider
from app.services.providers.anthropic import AnthropicProvider
from app.services.providers.grok import GrokProvider
from app.services.providers.ollama import OllamaProvider
from app.services.providers.openai import OpenAIProvider

MSGS = [{"role": "user", "content": "salut"}]


def _config(provider: LLMProvider, model: str, effort: str | None) -> LLMConfig:
    return LLMConfig(provider, model, api_key="test", effort=effort)


class TestAnthropicEffort:
    def _body(self, model: str, effort: str | None):
        provider = AnthropicProvider(
            _config(LLMProvider.ANTHROPIC, model, effort), httpx.AsyncClient()
        )
        return provider._build_request_body("sys", MSGS, None)

    @pytest.mark.parametrize(
        "model",
        ["claude-fable-5", "claude-sonnet-5", "claude-sonnet-4-6", "claude-opus-4-8"],
    )
    def test_effort_envoye_sur_les_modeles_supportes(self, model):
        body = self._body(model, "high")
        assert body["output_config"] == {"effort": "high"}

    def test_effort_max_transmis_tel_quel(self):
        assert self._body("claude-fable-5", "max")["output_config"] == {"effort": "max"}

    def test_pas_d_effort_sur_haiku(self):
        # L'API renvoie une erreur si effort est envoyé à Haiku 4.5.
        assert "output_config" not in self._body("claude-haiku-4-5-20251001", "high")

    def test_auto_n_envoie_rien(self):
        assert "output_config" not in self._body("claude-fable-5", None)


class TestOpenAIEffort:
    def _body(self, model: str, effort: str | None):
        provider = OpenAIProvider(
            _config(LLMProvider.OPENAI, model, effort), httpx.AsyncClient()
        )
        return provider._build_request_body(MSGS, None)

    @pytest.mark.parametrize("model", ["gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"])
    def test_effort_envoye_sur_gpt56(self, model):
        assert self._body(model, "medium")["reasoning_effort"] == "medium"

    def test_max_transmis_sur_gpt56(self):
        assert self._body("gpt-5.6-sol", "max")["reasoning_effort"] == "max"

    def test_pas_d_effort_sur_gpt55_non_source(self):
        # Support non vérifié sur 5.5 le 10/07 -> rien d'envoyé (dette).
        assert "reasoning_effort" not in self._body("gpt-5.5", "high")

    def test_auto_n_envoie_rien(self):
        assert "reasoning_effort" not in self._body("gpt-5.6-sol", None)


class TestGrokEffort:
    def _body(self, model: str, effort: str | None):
        provider = GrokProvider(
            _config(LLMProvider.GROK, model, effort), httpx.AsyncClient()
        )
        return provider._build_request_body(MSGS, None)

    def test_effort_envoye_sur_grok45(self):
        assert self._body("grok-4.5", "medium")["reasoning_effort"] == "medium"

    def test_max_plafonne_a_high(self):
        # xAI n'expose que low/medium/high (défaut high).
        assert self._body("grok-4.5", "max")["reasoning_effort"] == "high"

    def test_pas_d_effort_sur_grok43_non_source(self):
        assert "reasoning_effort" not in self._body("grok-4.3", "high")


class TestEffortEndpoints:
    """POST /api/config/llm accepte effort et le persiste ; GET le restitue."""

    @pytest.mark.asyncio
    async def test_post_effort_puis_get(self, client):
        resp = await client.post(
            "/api/config/llm",
            json={"provider": "anthropic", "model": "claude-fable-5", "effort": "high"},
        )
        assert resp.status_code == 200
        assert resp.json()["effort"] == "high"

        resp = await client.get("/api/config/llm")
        assert resp.json()["effort"] == "high"

    @pytest.mark.asyncio
    async def test_effort_auto_equivaut_a_rien(self, client):
        resp = await client.post(
            "/api/config/llm",
            json={"provider": "anthropic", "model": "claude-fable-5", "effort": "auto"},
        )
        assert resp.status_code == 200
        assert resp.json()["effort"] is None

    @pytest.mark.asyncio
    async def test_effort_invalide_422(self, client):
        resp = await client.post(
            "/api/config/llm",
            json={"provider": "anthropic", "model": "claude-fable-5", "effort": "turbo"},
        )
        assert resp.status_code == 422


class TestOllamaEffort:
    def _body(self, effort: str | None):
        config = LLMConfig(LLMProvider.OLLAMA, "qwen3:8b", effort=effort)
        provider = OllamaProvider(config, httpx.AsyncClient())
        return provider._build_request_body("sys", MSGS, None)

    def test_effort_envoye_en_think(self):
        assert self._body("medium")["think"] == "medium"

    def test_max_plafonne_a_high(self):
        # « max » non standardisé côté Ollama (gpt-oss le refuse).
        assert self._body("max")["think"] == "high"

    def test_auto_n_envoie_rien(self):
        assert "think" not in self._body(None)


# ============================================================
# Jalon 0.48 (brique 2 du lot A1) : le catalogue est la SEULE source de
# la politique d'effort - resoudre_effort() est appelé par CONSTRUCTION
# de LLMConfig, les providers émettent config.effort_resolu dans leur
# syntaxe, sans table locale.
# ============================================================


class TestLaResolutionParConstruction:
    def test_construire_une_config_resout_l_effort(self):
        config = LLMConfig(
            LLMProvider.OPENAI, "gpt-5.6-sol", api_key="t", effort="max"
        )
        assert config.effort_resolu == "max"

    def test_gpt55_ne_resout_rien(self):
        config = LLMConfig(
            LLMProvider.OPENAI, "gpt-5.5", api_key="t", effort="max"
        )
        assert config.effort_resolu is None

    def test_sans_effort_demande_rien(self):
        config = LLMConfig(LLMProvider.OPENAI, "gpt-5.6-sol", api_key="t")
        assert config.effort_resolu is None


class TestGrok46XHigh:
    def _body(self, model: str, effort: str | None):
        provider = GrokProvider(
            _config(LLMProvider.GROK, model, effort), httpx.AsyncClient()
        )
        return provider._build_request_body(MSGS, None)

    def test_max_devient_xhigh_sur_grok_46(self):
        """xhigh existe depuis grok-4.6 (high n'est que le DÉFAUT)."""
        assert self._body("grok-4.6", "max")["reasoning_effort"] == "xhigh"

    def test_grok_45_reste_plafonne_a_high(self):
        assert self._body("grok-4.5", "max")["reasoning_effort"] == "high"

    def test_grok_43_ne_recoit_rien(self):
        assert "reasoning_effort" not in self._body("grok-4.3", "max")


class TestOpus5:
    def _body(self, model: str, effort: str | None):
        provider = AnthropicProvider(
            _config(LLMProvider.ANTHROPIC, model, effort), httpx.AsyncClient()
        )
        return provider._build_request_body("sys", MSGS, None)

    def test_opus_5_recoit_l_effort_max(self):
        body = self._body("claude-opus-5", "max")
        assert body["output_config"] == {"effort": "max"}

    def test_opus_5_sans_sampling(self):
        """Doc extended-thinking-models : temperature refusée par Opus 5."""
        body = self._body("claude-opus-5", "max")
        assert "temperature" not in body


class TestGeminiThinkingLevel:
    def _body(self, model: str, effort: str | None):
        from app.services.providers.gemini import GeminiProvider

        provider = GeminiProvider(
            _config(LLMProvider.GEMINI, model, effort), httpx.AsyncClient()
        )
        return provider._build_request_body(MSGS, None, None)

    def test_max_devient_high_majuscule_sur_37_flash(self):
        body = self._body("gemini-3.7-flash", "max")
        assert (
            body["generationConfig"]["thinkingConfig"]["thinkingLevel"] == "HIGH"
        )

    def test_jamais_combine_a_thinking_budget(self):
        body = self._body("gemini-3.7-flash", "max")
        assert "thinkingBudget" not in body["generationConfig"].get(
            "thinkingConfig", {}
        )

    def test_les_2x_ne_recoivent_rien(self):
        """thinkingLevel sur un modèle < 3 = erreur API."""
        body = self._body("gemini-2.5-pro", "max")
        assert "thinkingConfig" not in body.get("generationConfig", {})


class TestMistralReasoningEffort:
    def _body(self, model: str, effort: str | None):
        from app.services.providers.mistral import MistralProvider

        provider = MistralProvider(
            _config(LLMProvider.MISTRAL, model, effort), httpx.AsyncClient()
        )
        return provider._build_request_body(MSGS, None)

    def test_max_devient_high_sur_medium_35(self):
        assert self._body("mistral-medium-3-5", "max")["reasoning_effort"] == "high"

    def test_les_autres_mistral_ne_recoivent_rien(self):
        assert "reasoning_effort" not in self._body("mistral-small-2603", "max")


class TestLeReglageAChaud:
    @pytest.mark.asyncio
    async def test_post_config_puis_chat_immediat_porte_l_effort(
        self, client, monkeypatch
    ):
        """Design 0.48 : POST /config/llm installe la config à chaud - le
        chat qui suit immédiatement doit émettre l'effort résolu, sans
        redémarrage."""
        import app.services.llm as llm_module

        reponse = await client.post("/api/config/llm", json={
            "provider": "openai",
            "model": "gpt-5.6-sol",
            "api_key": "sk-test-effort",
            "effort": "max",
        })
        assert reponse.status_code == 200, reponse.text

        config = llm_module._llm_service.config
        assert config.effort_resolu == "max", (
            "la config installée à chaud n'est pas passée par le résolveur"
        )
