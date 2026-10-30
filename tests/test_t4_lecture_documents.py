"""Aucun accès disque ni nom révélé sans accord pour le destinataire réel."""
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.services.memory_tools import execute_memory_tool


@pytest.mark.asyncio
@pytest.mark.parametrize('provider,model,url,grants', [
    ('openai', 'modele', None, []),
    ('openai', 'modele', None, ['documents:anthropic']),
    ('ollama', 'modele:cloud', None, []),
    ('ollama', 'modele', 'https://distant.invalid', []),
])
async def test_lecture_refusee_avant_la_base(provider, model, url, grants):
    session = AsyncMock()
    config = SimpleNamespace(provider=SimpleNamespace(value=provider), model=model, base_url=url)
    resultat = await execute_memory_tool('read_file', {'file_id': 'document-prive'}, session,
                                        llm_config=config, document_grants=grants)
    assert json.loads(resultat) == {'found': False, 'message': 'Lecture de document non autorisée pour ce service d’IA.'}
    session.execute.assert_not_called()


@pytest.mark.asyncio
async def test_absence_de_destination_refuse_la_lecture():
    session = AsyncMock()
    resultat = await execute_memory_tool('read_file', {'file_id': 'document-prive'}, session)
    assert json.loads(resultat)['found'] is False
    session.execute.assert_not_called()
