"""P-122 (Ludo, 25/09/2026, « Il faut rajouter opus 5.5 et gpt 6 sol et luna au fait
partout ») : Claude Opus 5.5, GPT-6 Sol et GPT-6 Luna entrent dans THÉRÈSE.

Relevé aux sources le 25/09/2026 :
- platform.claude.com/docs/en/about-claude/models/overview : `claude-opus-5-5`,
  4 $ / 20 $ par million, contexte 1 M, sortie 128 k, « start with Claude Opus 5.5
  for most workloads » ;
- platform.claude.com/docs/en/build-with-claude/effort : les cinq niveaux (low,
  medium, high, xhigh, max), défaut medium ;
- platform.claude.com/docs/en/models/opus-5-5/migration-guide : réflexion toujours
  active (rejeu des blocs, B-1364), temperature/top_p/top_k refusés ;
- developers.openai.com/api/docs/models : `gpt-6-sol` (« complex coding and agentic
  workflows ») et `gpt-6-luna` (« most efficient »), contexte 1,05 M, sortie 128 k,
  effort none, low, medium, high, xhigh, max ;
- developers.openai.com/api/docs/pricing : gpt-6-sol 2 $ / 10 $, gpt-6-luna 0,10 $ /
  0,50 $ (standard, contexte court).

Choix éditorial (contrat du catalogue : la tête est le modèle recommandé, la
puissance maximale juste après) : Opus 5.5 prend la tête d'Anthropic, GPT-6 Sol
celle d'OpenAI ; Fable 5 et GPT-6 Astra restent deuxièmes.
"""

from __future__ import annotations

import json
import pathlib

import pytest

RACINE = pathlib.Path(__file__).resolve().parent.parent
NIVEAUX = ("low", "medium", "high", "xhigh", "max")


def test_opus_5_5_prend_la_tete_d_anthropic_avec_sa_fiche():
    from app.services.modeles_catalogue import (
        CATALOGUE,
        fenetre_de_contexte,
        max_tokens_recommande,
        resoudre_effort,
    )

    anthropic = CATALOGUE["anthropic"]
    assert anthropic.modeles[0] == "claude-opus-5-5"
    assert anthropic.modeles[1] == "claude-fable-5", "la puissance maximale juste après"
    assert "claude-opus-5" in anthropic.modeles, "ajouter n'est pas remplacer"
    for effort in NIVEAUX:
        assert resoudre_effort("claude-opus-5-5", effort, "anthropic") == effort, effort
    assert max_tokens_recommande("claude-opus-5-5") == 64000
    assert fenetre_de_contexte("anthropic", "claude-opus-5-5") == 1_000_000


@pytest.mark.parametrize("modele", ["gpt-6-sol", "gpt-6-luna"])
def test_gpt_6_sol_et_luna_sont_au_catalogue_openai(modele):
    from app.services.modeles_catalogue import CATALOGUE, fenetre_de_contexte, resoudre_effort
    from app.services.providers.openai import _uses_max_completion_tokens

    assert modele in CATALOGUE["openai"].modeles
    for effort in ("none", *NIVEAUX):
        assert resoudre_effort(modele, effort, "openai") == effort, effort
    assert fenetre_de_contexte("openai", modele) == 1_050_000
    assert _uses_max_completion_tokens(modele) is True


def test_gpt_6_sol_prend_la_tete_d_openai_astra_reste_deuxieme():
    from app.services.modeles_catalogue import CATALOGUE

    openai = CATALOGUE["openai"]
    assert openai.modeles[:3] == ("gpt-6-sol", "gpt-6-astra", "gpt-6-luna")
    assert "gpt-5.6-sol" in openai.modeles, "ajouter n'est pas remplacer"


def test_les_trois_modeles_ont_leur_tarif():
    from app.services.token_tracker import TOKEN_PRICES

    assert TOKEN_PRICES["claude-opus-5-5"] == {"input": 4.00, "output": 20.00}
    assert TOKEN_PRICES["gpt-6-sol"] == {"input": 2.00, "output": 10.00}
    assert TOKEN_PRICES["gpt-6-luna"] == {"input": 0.10, "output": 0.50}


def test_opus_5_5_ne_recoit_jamais_de_temperature():
    from app.services.providers.anthropic import AnthropicProvider
    from app.services.providers.base import LLMConfig, LLMProvider

    from tests.test_provider_tools import _FakeClient

    fournisseur = AnthropicProvider(
        LLMConfig(provider=LLMProvider.ANTHROPIC, model="claude-opus-5-5", api_key="k"),
        client=_FakeClient([]),
    )
    corps = fournisseur._build_request_body("system", [{"role": "user", "content": "?"}], None)
    assert "temperature" not in corps and "top_p" not in corps and "top_k" not in corps
    assert "thinking" not in corps, "Opus 5.5 réfléchit toujours ; « disabled » serait un 400"


def test_les_temoins_d_effort_openai_connaissent_gpt_6_sol_et_luna():
    temoins = json.loads((RACINE / "src/frontend/src/lib/effortOpenAI.temoins.json").read_text(encoding="utf-8"))
    for modele in ("gpt-6-sol", "gpt-6-luna"):
        assert temoins["temoins"].get(modele) is True, modele
        assert modele in temoins["effort_transmis_sans_outils"], modele


def test_l_atelier_propose_les_trois_modeles():
    from app.services.agents.config import AVAILABLE_MODELS

    par_id = {m["id"]: m for m in AVAILABLE_MODELS}
    assert par_id["claude-opus-5-5"]["provider"] == "anthropic"
    assert par_id["claude-opus-5-5"].get("recommended") is True
    assert par_id["gpt-6-sol"]["provider"] == "openai"
    assert par_id["gpt-6-luna"]["provider"] == "openai"
    assert sum(1 for m in AVAILABLE_MODELS if m.get("recommended")) == 1
