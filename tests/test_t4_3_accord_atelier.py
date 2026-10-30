"""L'Atelier prépare l'accord pour la destination réelle, sans envoyer la mission."""
from types import SimpleNamespace

import pytest
from app.services.llm import LLMConfig, LLMProvider


@pytest.mark.parametrize('provider,adresse,destination', [
    (LLMProvider.OPENAI, None, 'openai'),
    (LLMProvider.OLLAMA, 'http://127.0.0.1:11434', None),
    (LLMProvider.OLLAMA, 'http://192.0.2.10:11434', 'ollama-cloud'),
])
async def test_preparation_accord_destination_effective(client, monkeypatch, provider, adresse, destination):
    from app.services.agents import runtime
    config = LLMConfig(provider, 'modele-test', base_url=adresse)
    monkeypatch.setattr(runtime, '_get_llm_for_model', lambda _: SimpleNamespace(config=config))
    response = await client.get('/api/agents/profiles/researcher/consent?model=modele-test')
    assert response.status_code == 200, response.text
    assert response.json()['provider'] == destination
    assert response.json()['purposes'] == (['llm', 'documents'] if destination else [])
    if adresse and destination:
        assert adresse in response.json()['label']


async def test_accords_acquittes_par_api_depuis_base_vierge(client, monkeypatch):
    from app.services.agents import runtime
    config = LLMConfig(LLMProvider.OPENAI, 'modele-test')
    monkeypatch.setattr(runtime, '_get_llm_for_model', lambda _: SimpleNamespace(config=config))
    url = '/api/agents/profiles/researcher/consent?model=modele-test'
    assert (await client.get(url)).json()['granted_purposes'] == []
    for purpose, attendus in [('llm', ['llm']), ('documents', ['llm', 'documents'])]:
        response = await client.post('/api/consents', json={
            'purpose': purpose, 'provider': 'openai', 'granted': True, 'text_version': '3',
            'data_categories': ['message saisi', 'fichiers'],
        })
        assert response.status_code == 200
        assert (await client.get(url)).json()['granted_purposes'] == attendus
    await client.post('/api/consents', json={
        'purpose': 'documents', 'provider': 'openai', 'granted': False, 'text_version': '3',
    })
    assert (await client.get(url)).json()['granted_purposes'] == ['llm']
