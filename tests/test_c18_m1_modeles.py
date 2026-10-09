"""Lot M1 (cycle 18, 9 octobre 2026) : modèles ajoutés, têtes inchangées.

Les chiffres viennent des fiches citées dans
docs/plans/2026-10-09-c18-m1-modeles.md. Aucun appel réseau.
"""

import httpx
import pytest
from app.services.modeles_catalogue import (
    fenetre_de_contexte,
    modeles_ordonnes,
    resoudre_effort,
)
from app.services.providers.anthropic import AnthropicProvider
from app.services.providers.base import LLMConfig, LLMProvider, ToolCall, ToolResult
from app.services.providers.gemini import GeminiProvider
from app.services.providers.grok import GrokProvider
from app.services.providers.mistral import MistralProvider
from app.services.token_tracker import TOKEN_PRICES, TokenTracker

from tests.test_anthropic_blocs_de_reflexion import _flux, _outil, _reflexion, _sse
from tests.test_provider_tools import _collect, _FakeClient

# Listes servies AVANT ce lot. Chacune doit rester, dans le même ordre relatif.
ANCIENS = {
    "anthropic": (
        "claude-opus-5-5",
        "claude-fable-5",
        "claude-opus-5",
        "claude-sonnet-5",
        "claude-haiku-4-5-20251001",
        "claude-opus-4-8",
        "claude-opus-4-7",
        "claude-opus-4-6",
        "claude-sonnet-4-6",
    ),
    "grok": (
        "grok-4.6",
        "grok-4.5",
        "grok-4.3",
        "grok-4.20-0309-reasoning",
        "grok-4.20-0309-non-reasoning",
    ),
    "gemini": (
        "gemini-3.7-flash",
        "gemini-3.1-pro-preview",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-2.5-pro",
        "gemini-2.5-flash",
    ),
    "mistral": (
        "mistral-medium-3-5",
        "mistral-medium-latest",
        "mistral-large-latest",
        "mistral-large-2512",
        "mistral-small-2603",
        "codestral-2508",
        "ministral-8b-2512",
        "ministral-3b-2512",
    ),
}

TETES = {
    "anthropic": "claude-opus-5-5",
    "openai": "gpt-6-sol",
    "gemini": "gemini-3.7-flash",
    "mistral": "mistral-medium-3-5",
    "grok": "grok-4.6",
}

ORDRE = {
    "anthropic": (
        "claude-opus-5-5",
        "claude-fable-5-1",
        "claude-fable-5",
        "claude-opus-5",
        "claude-sonnet-5-5",
        "claude-sonnet-5",
        "claude-haiku-5-5",
        "claude-haiku-4-5-20251001",
        "claude-opus-4-8",
        "claude-opus-4-7",
        "claude-opus-4-6",
        "claude-sonnet-4-6",
    ),
    "grok": (
        "grok-4.6",
        "grok-4.7",
        "grok-4.5",
        "grok-4.3",
        "grok-4.20-0309-reasoning",
        "grok-4.20-0309-non-reasoning",
    ),
    "gemini": (
        "gemini-3.7-flash",
        "gemini-3.8-flash",
        "gemini-3.1-pro-preview",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-2.5-pro",
        "gemini-2.5-flash",
    ),
    "mistral": (
        "mistral-medium-3-5",
        "mistral-large-4",
        "mistral-medium-latest",
        "mistral-large-latest",
        "mistral-large-2512",
        "mistral-small-2603",
        "codestral-2508",
        "ministral-8b-2512",
        "ministral-3b-2512",
    ),
}

TARIFS = {
    "claude-fable-5-1": {"input": 10.00, "output": 50.00},
    "claude-sonnet-5-5": {"input": 2.00, "output": 10.00},
    "claude-haiku-5-5": {"input": 0.10, "output": 0.50},
    "grok-4.7": {"input": 2.00, "output": 6.00},
    "mistral-large-4": {"input": 1.36, "output": 4.18},
    "gemini-3.8-flash": {"input": 0.75, "output": 3.75},
}

OUTIL = [{
    "type": "function",
    "function": {"name": "lire", "description": "lit", "parameters": {"type": "object", "properties": {}}},
}]


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient()


def _garder_ordre(liste: list[str], anciens: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(modele for modele in liste if modele in anciens)


class TestCatalogueM1:
    def test_tetes_inchangees_et_anciens_conserves_dans_le_meme_ordre(self):
        for fournisseur, tete in TETES.items():
            liste = modeles_ordonnes(fournisseur)
            assert liste[0] == tete
            assert len(liste) == len(set(liste))
        for fournisseur, anciens in ANCIENS.items():
            assert _garder_ordre(modeles_ordonnes(fournisseur), anciens) == anciens

    def test_les_nouveaux_identifiants_prennent_la_place_prevue(self):
        for fournisseur, attendu in ORDRE.items():
            assert tuple(modeles_ordonnes(fournisseur)) == attendu
        grok = modeles_ordonnes("grok")
        assert "grok-4.7-fast" not in grok
        assert "mistral-large-4-0" not in modeles_ordonnes("mistral")

    def test_fenetres_et_plafonds_documentes(self):
        for modele in ("claude-fable-5-1", "claude-sonnet-5-5", "claude-haiku-5-5"):
            assert fenetre_de_contexte("anthropic", modele) == 1_000_000
            config = LLMConfig(LLMProvider.ANTHROPIC, modele)
            assert config.max_tokens == 128_000
        assert fenetre_de_contexte("anthropic", "claude-haiku-4-5-20251001") == 200_000
        assert LLMConfig(LLMProvider.ANTHROPIC, "claude-opus-5-5").max_tokens == 64_000

        assert fenetre_de_contexte("grok", "grok-4.7") == 500_000
        assert fenetre_de_contexte("grok", "grok-4.6") == 131_072
        assert LLMConfig(LLMProvider.GROK, "grok-4.7").max_tokens == 4096

        assert fenetre_de_contexte("mistral", "mistral-large-4") == 1_000_000
        assert fenetre_de_contexte("mistral", "mistral-medium-3-5") == 256_000
        assert LLMConfig(LLMProvider.MISTRAL, "mistral-large-4").max_tokens == 4096

        assert fenetre_de_contexte("gemini", "gemini-3.8-flash") == 1_048_576
        assert fenetre_de_contexte("gemini", "gemini-3.7-flash") == 1_000_000
        assert LLMConfig(LLMProvider.GEMINI, "gemini-3.8-flash").max_tokens == 65_536

    def test_efforts_traduits_sans_rien_inventer(self):
        for modele in ("claude-fable-5-1", "claude-sonnet-5-5", "claude-haiku-5-5"):
            assert resoudre_effort(modele, "xhigh") == "xhigh"
            assert resoudre_effort(modele, "max") == "max"
            assert resoudre_effort(modele, None) is None
        # Fable 5 garde sa table sans xhigh (hors demande).
        assert resoudre_effort("claude-fable-5", "xhigh") is None
        assert resoudre_effort("grok-4.7", "max") == "xhigh"
        assert resoudre_effort("grok-4.7", "high") == "high"
        assert resoudre_effort("gemini-3.8-flash", "max", "gemini") == "HIGH"
        assert resoudre_effort("gemini-3.8-flash", "minimal", "gemini") is None
        assert "mistral-large-4" in modeles_ordonnes("mistral")
        assert resoudre_effort("mistral-large-4", "high", "mistral") is None


class TestTarifsM1:
    def test_les_prix_documentes_ne_sont_ni_absents_ni_nuls(self):
        traceur = object.__new__(TokenTracker)
        for modele, prix in TARIFS.items():
            assert TOKEN_PRICES.get(modele) == prix
            assert traceur.tarif_connu(modele) is True
            cout = traceur.estimate_cost(modele, 1_000_000, 1_000_000)
            assert cout == pytest.approx(prix["input"] + prix["output"])
            assert cout > 0


def test_grok_47_envoie_leffort_xhigh_et_les_outils():
    config = LLMConfig(LLMProvider.GROK, "grok-4.7", api_key="x", effort="max")
    corps = GrokProvider(config, _client())._build_request_body(
        [{"role": "user", "content": "salut"}],
        tools=OUTIL,
    )
    assert corps["model"] == "grok-4.7"
    assert corps["reasoning_effort"] == "xhigh"
    assert corps["tools"] == OUTIL
    assert corps["tool_choice"] == "auto"
    assert corps["temperature"] == 0.7


def test_gemini_38_envoie_le_niveau_sans_temperature_ni_minimal():
    config = LLMConfig(LLMProvider.GEMINI, "gemini-3.8-flash", api_key="g", effort="max")
    corps = GeminiProvider(config, _client())._build_request_body([], None, None)
    assert corps["generationConfig"]["thinkingConfig"] == {"thinkingLevel": "HIGH"}
    assert "temperature" not in corps["generationConfig"]
    assert corps["generationConfig"]["maxOutputTokens"] == 65_536
    assert "MINIMAL" not in str(corps)


def test_mistral_large_4_n_envoie_pas_deffort():
    assert "mistral-large-4" in modeles_ordonnes("mistral")
    config = LLMConfig(LLMProvider.MISTRAL, "mistral-large-4", api_key="m", effort="high")
    corps = MistralProvider(config, _client())._build_request_body(
        [{"role": "user", "content": "salut"}],
    )
    assert "reasoning_effort" not in corps
    assert corps["model"] == "mistral-large-4"


def test_sonnet_55_envoie_leffort_sans_echantillonnage_ni_tool_choice():
    config = LLMConfig(LLMProvider.ANTHROPIC, "claude-sonnet-5-5", api_key="k", effort="high")
    corps = AnthropicProvider(config, _client())._build_request_body(
        "sys", [{"role": "user", "content": "salut"}], OUTIL,
    )
    assert corps["output_config"] == {"effort": "high"}
    assert "temperature" not in corps
    assert "top_p" not in corps
    assert "top_k" not in corps
    assert "tool_choice" not in corps
    assert "thinking" not in corps
    assert corps["max_tokens"] == 128_000


@pytest.mark.asyncio
async def test_sonnet_55_rejoue_un_bloc_de_reflexion_entre_deux_outils():
    client = _FakeClient(_flux(
        _reflexion(0, "sig-a", "je cherche"),
        _outil(1, "tu_1", "lire", {"id": "1"}),
        _reflexion(2, "sig-b"),
        _outil(3, "tu_2", "ecrire", {"id": "2"}),
    ))
    config = LLMConfig(LLMProvider.ANTHROPIC, "claude-sonnet-5-5", api_key="k", effort="high")
    evenements = await _collect(
        AnthropicProvider(config, client).stream("sys", [{"role": "user", "content": "?"}], None)
    )
    appels = [e for e in evenements if e.type == "tool_call"]
    assert len(appels) == 2
    brut = appels[-1].assistant_content_brut
    assert [bloc["type"] for bloc in brut] == ["thinking", "tool_use", "thinking", "tool_use"]
    assert brut[2] == {"type": "thinking", "thinking": "", "signature": "sig-b"}
    assert not any(e.type == "text" and "je cherche" in (e.content or "") for e in evenements)

    suite = _FakeClient([_sse({"type": "message_stop"})])
    await _collect(AnthropicProvider(config, suite).continue_with_tool_results(
        "sys",
        [{"role": "user", "content": "?"}],
        assistant_content="",
        tool_calls=[
            ToolCall(id="tu_1", name="lire", arguments={"id": "1"}),
            ToolCall(id="tu_2", name="ecrire", arguments={"id": "2"}),
        ],
        tool_results=[
            ToolResult(tool_call_id="tu_1", result="ok"),
            ToolResult(tool_call_id="tu_2", result="ok"),
        ],
        tools=None,
        assistant_content_brut=brut,
    ))
    renvoye = suite.last_request["json"]
    assert "temperature" not in renvoye
    assert "top_p" not in renvoye
    assert "top_k" not in renvoye
    assert "tool_choice" not in renvoye
    assert renvoye["output_config"] == {"effort": "high"}
    assistant = [m for m in renvoye["messages"] if m["role"] == "assistant"][-1]
    assert assistant["content"] == brut


def test_les_agents_recoivent_les_modeles_a_outils_documentes():
    from app.services.agents.config import AVAILABLE_MODELS, AgentConfig

    par_id = {m["id"]: m for m in AVAILABLE_MODELS}
    for identifiant in (
        "claude-fable-5-1",
        "claude-sonnet-5-5",
        "claude-haiku-5-5",
        "grok-4.7",
        "gemini-3.8-flash",
    ):
        assert identifiant in par_id
        assert par_id[identifiant].get("recommended") is not True
    assert "mistral-large-4" not in par_id
    assert "grok-4.7-fast" not in par_id
    assert sum(1 for m in AVAILABLE_MODELS if m.get("recommended")) == 1
    assert AgentConfig(id="a", name="a", description="a").default_model == "claude-sonnet-4-6"
