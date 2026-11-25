"""L'appel Anthropic d'extraction de fond entre dans le coût quotidien."""

from unittest.mock import AsyncMock

import pytest
from app.models.entities import Conversation, Message
from app.routers.chat import _extract_entities_background
from app.services.llm import LLMService
from app.services.providers.anthropic import AnthropicProvider
from app.services.providers.base import LLMConfig, LLMProvider

from tests.test_anthropic_blocs_de_reflexion import _texte
from tests.test_c5_anthropic_cout_cache import _couts_enregistres, _reponse
from tests.test_provider_tools import _FakeClient


@pytest.mark.asyncio
@pytest.mark.parametrize("sortie", ['{"contacts": [], "projects": []}', "JSON illisible"])
async def test_compte_l_extraction_meme_sans_entite_retenue(db_session, monkeypatch, sortie):
    conversation = Conversation(title="Compte démo")
    db_session.add(conversation)
    await db_session.flush()
    reponse = Message(
        conversation_id=conversation.id, role="assistant", content="Quatre.",
        extra_data='{"provenance_documents": "sans_document"}',
    )
    db_session.add(reponse)
    await db_session.commit()
    config = LLMConfig(LLMProvider.ANTHROPIC, "claude-sonnet-5-5", api_key="factice")
    transport = _FakeClient(responses=[_reponse(_texte(0, sortie), {
        "input_tokens": 40, "cache_creation_input_tokens": 897, "cache_read_input_tokens": 0,
        "cache_creation": {"ephemeral_5m_input_tokens": 897, "ephemeral_1h_input_tokens": 0},
    }, 75)])
    service = LLMService(config)
    service._provider = AnthropicProvider(config, client=transport)
    monkeypatch.setattr(service, "_ensure_provider", AsyncMock())
    monkeypatch.setattr(service, "_resolve_with_circuit_breaker", lambda: config)
    monkeypatch.setattr(
        "app.services.consentements.accord_valide",
        lambda purpose, provider, categories=(): purpose == "llm" and provider == "anthropic",
    )
    enregistrements = _couts_enregistres(monkeypatch, "app.services.entity_extractor")

    await _extract_entities_background(
        "Combien font deux plus deux ?", conversation.id, reponse.id, service,
    )

    assert len(transport.requests) == 1
    assert len(enregistrements) == 1
    usage = enregistrements[0]
    assert usage.conversation_id == conversation.id
    assert (usage.input_tokens, usage.output_tokens) == (937, 75)
    assert usage.cost_eur == pytest.approx(0.0030725)
