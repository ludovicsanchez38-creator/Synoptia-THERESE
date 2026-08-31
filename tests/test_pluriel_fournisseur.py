"""Finding 5 (revue 30/08) : la réponse vient du repli, le badge dit le premier.

Le circuit breaker bascule Anthropic → OpenAI, restaure le singleton, et
chat.py lit alors le fournisseur du sélecteur. Une clé « effacée » restait
dans le cache et servait encore de repli.
"""

from __future__ import annotations

import pytest
from app.services.providers.base import LLMConfig, LLMProvider, StreamEvent


@pytest.mark.asyncio
async def test_apres_bascule_l_attribution_est_celle_du_repli(monkeypatch):
    from app.services.llm import LLMService

    choisi = LLMConfig(provider=LLMProvider.ANTHROPIC, model="claude-sonnet-4-6")
    repli = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4.1")
    service = LLMService(choisi)

    monkeypatch.setattr(service, "_resolve_with_circuit_breaker", lambda: repli)

    async def faux_ensure():
        service._provider = type("P", (), {})()

        async def stream(*_a, **_k):
            yield StreamEvent(type="text", content="ok")
            yield StreamEvent(type="done")

        service._provider.stream = stream

    monkeypatch.setattr(service, "_ensure_provider", faux_ensure)

    from app.services.context import ContextWindow
    from app.services.providers.base import Message as LLMMessage

    contexte = ContextWindow(
        messages=[LLMMessage(role="user", content="ping")],
        system_prompt="sys",
        max_tokens=1000,
    )
    async for _ in service.stream_response_with_tools(contexte):
        pass

    assert service.config.provider == LLMProvider.ANTHROPIC
    assert service.fournisseur_effectif == "openai"
    assert service.modele_effectif == "gpt-4.1"


def test_delete_api_key_invalide_cache_et_singleton():
    """Même invalidation que POST /api-key : sinon une clé effacée reste un repli."""
    from pathlib import Path

    source = Path("src/backend/app/routers/config.py").read_text(encoding="utf-8")
    debut = source.index("async def delete_api_key")
    fin = source.index("\n@router.", debut + 1)
    corps = source[debut:fin]
    assert "invalidate_api_key_cache" in corps
    assert "invalidate_llm_service" in corps or "_llm_service = None" in corps
