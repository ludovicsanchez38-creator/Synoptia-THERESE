"""Le composeur reçoit la même classification que la garde moteur."""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.services.llm import LLMConfig, LLMProvider


@pytest.mark.parametrize('url,modele,attendu', [
    ('http://192.0.2.10:11434', 'llama3', 'ollama-cloud'),
    ('http://localhost:11434', 'llama3', None),
    ('http://127.0.0.1:11434', 'llama3', None),
    ('http://[::1]:11434', 'llama3', None),
    ('http://localhost:11434', 'modele:cloud', 'ollama-cloud'),
])
async def test_destination_publiee_pour_l_accord(client, monkeypatch, url, modele, attendu):
    from app.routers import config

    monkeypatch.setattr('app.services.llm.get_llm_service', lambda: SimpleNamespace(
        config=LLMConfig(LLMProvider.OLLAMA, modele, base_url=url)))
    monkeypatch.setattr(config, '_available_models_for', AsyncMock(return_value=[modele]))
    response = await client.get('/api/config/llm')
    assert response.status_code == 200
    assert response.json()['consent_provider'] == attendu
    if '192.0.2.10' in url:
        assert response.json()['consent_label'] == f'Serveur Ollama distant ({url})'
