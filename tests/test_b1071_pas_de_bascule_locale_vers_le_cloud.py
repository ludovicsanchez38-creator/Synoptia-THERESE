"""B-1071 (lecteur E de la carte c12) : l'onglet Modèles promet « En local,
rien ne quitte ton ordinateur ». Avec Ollama comme fournisseur principal,
deux échecs ouvraient son disjoncteur et le service principal (chat,
documents, e-mails) basculait en silence sur le premier fournisseur en ligne
dont une clé est enregistrée. Un fournisseur local ne bascule jamais vers
un service en ligne ; l'échec remonte.
"""

from __future__ import annotations

import pytest
from app.services import llm as module_llm
from app.services.circuit_breaker import get_circuit_breaker
from app.services.llm import LLMService
from app.services.providers import LLMConfig, LLMProvider


@pytest.fixture(autouse=True)
def _disjoncteur_propre():
    get_circuit_breaker().reset()
    yield
    get_circuit_breaker().reset()


@pytest.fixture
def cles_en_ligne(monkeypatch):
    monkeypatch.setattr(module_llm, "_get_api_key_from_db", lambda nom: "cle-" + nom if nom in ("anthropic", "openai") else None)


def _ouvrir_le_disjoncteur(fournisseur: str) -> None:
    cb = get_circuit_breaker()
    for _ in range(5):
        cb.record_failure(fournisseur, "Impossible de se connecter")
    assert not cb.is_available(fournisseur)


def test_ollama_indisponible_ne_bascule_pas_vers_un_service_en_ligne(cles_en_ligne):
    service = LLMService(LLMConfig(provider=LLMProvider.OLLAMA, model="qwen3:8b", api_key=None, base_url="http://127.0.0.1:1"))
    _ouvrir_le_disjoncteur("ollama")
    config = service._resolve_with_circuit_breaker()
    assert config.provider == LLMProvider.OLLAMA, f"bascule vers {config.provider}"


def test_un_service_en_ligne_garde_son_repli(cles_en_ligne):
    service = LLMService(LLMConfig(provider=LLMProvider.ANTHROPIC, model="claude-opus-5", api_key="cle-anthropic", base_url=None))
    _ouvrir_le_disjoncteur("anthropic")
    config = service._resolve_with_circuit_breaker()
    assert config.provider == LLMProvider.OPENAI
