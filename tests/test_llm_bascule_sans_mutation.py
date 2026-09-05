"""B-488 (05/09/2026) : le service LLM est un singleton ; la bascule du
disjoncteur et l'override de max_tokens MUTAIENT sa configuration partagée.
Un flux B démarré pendant qu'un flux A avait basculé (anthropic -> ollama)
lisait la config de repli, et l'étiquette « fournisseur effectif » mentait.
La bascule est désormais locale à l'appel.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services.llm import LLMService
from app.services.providers.base import LLMConfig, LLMProvider, StreamEvent


class _Fournisseur:
    def __init__(self, nom: str, journal: list, service: LLMService, config_initiale: LLMConfig):
        self.nom, self.journal, self.service, self.config_initiale = nom, journal, service, config_initiale

    async def stream(self, system_prompt, messages, tools=None, **kwargs):
        # Observé PENDANT le flux : la config partagée ne doit pas avoir bougé.
        self.journal.append((self.nom, self.service.config is self.config_initiale))
        yield StreamEvent(type="text", content=f"réponse de {self.nom}")


@pytest.mark.asyncio
async def test_la_bascule_du_disjoncteur_ne_mute_pas_la_config_partagee():
    principale = LLMConfig(LLMProvider.ANTHROPIC, "claude-test", api_key="x", context_window=8000)
    repli = LLMConfig(LLMProvider.OLLAMA, "gemma-test", base_url="http://127.0.0.1:9", context_window=8000)
    service = LLMService(principale)
    journal: list = []
    primaire = _Fournisseur("primaire", journal, service, principale)
    service._provider = primaire
    service._ensure_provider = AsyncMock()
    service._resolve_with_circuit_breaker = lambda: repli

    async def provider_pour(config):
        assert config is repli
        return _Fournisseur("repli", journal, service, principale)

    service._provider_pour = provider_pour

    contexte = MagicMock()
    contexte.system_prompt = ""
    contexte.to_openai_format.return_value = []
    contexte.to_anthropic_format.return_value = ("", [])

    events = [e async for e in service.stream_response_with_tools(contexte, tools=None)]

    assert [e.content for e in events if e.type == "text"] == ["réponse de repli"]
    assert journal == [("repli", True)], "la config partagée a été mutée pendant le flux"
    assert service.config is principale
    assert service._provider is primaire, "le fournisseur partagé a été remplacé"
    assert service.fournisseur_effectif == "ollama"


@pytest.mark.asyncio
async def test_generate_content_n_ecrit_pas_max_tokens_dans_la_config_partagee(monkeypatch):
    principale = LLMConfig(LLMProvider.ANTHROPIC, "claude-test", api_key="x", context_window=8000, max_tokens=100)
    service = LLMService(principale)
    vus: list[int] = []

    async def faux_stream(context, tools=None, enable_grounding=True, config=None):
        vus.append((config or service.config).max_tokens)
        yield StreamEvent(type="text", content="ok")

    monkeypatch.setattr(service, "stream_response_with_tools", faux_stream)
    monkeypatch.setattr(service, "_get_system_prompt_with_identity", lambda: "sys")

    texte = await service.generate_content(prompt="bonjour", max_tokens=4000)

    assert texte == "ok"
    assert vus == [4000], "l'override n'est pas arrivé au flux"
    assert service.config.max_tokens == 100, "max_tokens a été écrit dans la config partagée"
