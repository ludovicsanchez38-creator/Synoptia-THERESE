"""B-966 et B-967 (cycle 11, 23/09/2026) : routage des modèles des agents.

B-966 (sécurité, ATTÉNUÉ, décision en attente) : `_get_llm_for_model` testait
« / » (OpenRouter) avant « : » (Ollama), puis, si Ollama ne répondait pas, les
préfixes cloud. Un modèle local au format Hugging Face d'Ollama (`hf.co/…:Q4`)
partait chez OpenRouter dès qu'une clé existait, et `qwen3.5:9b` (local) chez
Qwen cloud quand Ollama était arrêté. Ces deux cas sont fermés ; les autres
(noms locaux sans « hf.co/ » hors catalogue, bascule du disjoncteur vers un
cloud) demandent de conserver le fournisseur avec le modèle : non testés ici.

B-967 : `codestral-2508` et `deepseek-v4-*`, proposés par l'Atelier, ne
correspondaient à aucun préfixe et retombaient en silence sur le modèle
principal. Le catalogue AVAILABLE_MODELS connaît pourtant leur fournisseur.
"""

from __future__ import annotations

import pytest
from app.services import llm as module_llm
from app.services.agents.runtime import _get_llm_for_model

PRINCIPAL = object()


@pytest.fixture
def fournisseurs(monkeypatch):
    """Tous les fournisseurs configurés sauf ceux de `indisponibles`."""
    demandes: list[str] = []
    indisponibles: set[str] = set()

    def service(provider_name, model_override=None):
        demandes.append(provider_name)
        return None if provider_name in indisponibles else ("service", provider_name, model_override)

    monkeypatch.setattr(module_llm, "get_llm_service_for_provider", service)
    monkeypatch.setattr(module_llm, "get_llm_service", lambda *a, **k: PRINCIPAL)
    return demandes, indisponibles


@pytest.mark.parametrize(
    "modele",
    ["hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF:Q4_K_M", "qwen3.5:9b"],
)
def test_b966_un_modele_local_reste_local(fournisseurs, modele):
    demandes, _ = fournisseurs
    assert _get_llm_for_model(modele) == ("service", "ollama", modele)
    assert demandes == ["ollama"]


def test_b966_ollama_arrete_ne_bascule_pas_vers_un_cloud_homonyme(fournisseurs):
    demandes, indisponibles = fournisseurs
    indisponibles.add("ollama")
    assert _get_llm_for_model("qwen3.5:9b") is PRINCIPAL
    assert "qwen" not in demandes and "openrouter" not in demandes, demandes


@pytest.mark.parametrize(
    ("modele", "fournisseur"),
    [
        ("meta-llama/llama-3.1-8b-instruct:free", "openrouter"),
        # Huitième revue Codex (R-6) : variante et preset OpenRouter combinés.
        ("anthropic/claude-sonnet-4-6:nitro@preset/revue", "openrouter"),
        ("anthropic/claude-opus-5", "openrouter"),
        ("nvidia/nemotron-3-super-120b-a12b", "openrouter"),
        ("claude-opus-5", "anthropic"),
        ("qwen3.8-max", "qwen"),
        ("MiniMax-M3", "minimax"),
    ],
)
def test_b966_les_identifiants_cloud_gardent_leur_fournisseur(fournisseurs, modele, fournisseur):
    assert _get_llm_for_model(modele) == ("service", fournisseur, modele)


@pytest.mark.parametrize(
    ("modele", "fournisseur"),
    [("codestral-2508", "mistral"), ("deepseek-v4-pro", "deepseek"), ("deepseek-v4-flash", "deepseek")],
)
def test_b967_le_catalogue_des_agents_donne_le_fournisseur(fournisseurs, modele, fournisseur):
    assert _get_llm_for_model(modele) == ("service", fournisseur, modele)
