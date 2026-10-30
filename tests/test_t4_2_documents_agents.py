"""La boucle réelle des agents garde la finalité documents jusqu'à l'envoi."""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.services.agents.config import AgentConfig
from app.services.agents.runtime import AgentRuntime
from app.services.consentements import enregistrer_accord, verifier_envoi_llm
from app.services.context import ContextWindow
from app.services.providers.base import LLMConfig, LLMProvider


@pytest.mark.parametrize('outil', ['read_file', 'search_codebase', 'git_diff', 'run_command', 'list_directory', 'git_status'])
@pytest.mark.parametrize('accord', ['absent', 'autre', 'retire_avant', 'retire_apres', 'actif', 'local'])
async def test_documents_dans_la_boucle(client, monkeypatch, outil, accord):
    config = LLMConfig(LLMProvider.OLLAMA if accord == 'local' else LLMProvider.OPENAI,
                       'modele', base_url='http://127.0.0.1:11434')
    enregistrer_accord('llm', 'openai', True, '3', [])
    if accord == 'autre':
        enregistrer_accord('documents', 'anthropic', True, '3', [])
    if accord in ('retire_avant', 'retire_apres', 'actif'):
        enregistrer_accord('documents', 'openai', True, '3', [])
    if accord == 'retire_avant':
        enregistrer_accord('documents', 'openai', False, '3', [])
    envois = []

    async def stream(context, **kwargs):
        verifier_envoi_llm(config, context)
        envois.append(' '.join(m.content for m in context.messages))
        if len(envois) == 1:
            yield SimpleNamespace(type='tool_call', tool_call=SimpleNamespace(id='t1', name=outil, arguments={}))
        else:
            yield SimpleNamespace(type='text', content='Terminé')

    service = SimpleNamespace(config=config, prepare_context=lambda messages, **kw: ContextWindow(list(messages)),
                              stream_response_with_tools=stream)
    monkeypatch.setattr('app.services.agents.runtime._get_llm_for_model', lambda _: service)
    lecture = AsyncMock(return_value='CONTENU_DOCUMENT_FICTIF')
    executor = SimpleNamespace(**{outil: lecture})
    runtime = AgentRuntime(AgentConfig(id='test', name='Test', description='Test', system_prompt='Aide.',
                                      default_model='gpt-test', max_iterations=3), executor,
                           [{'function': {'name': outil}}])
    events = []
    async for event in runtime.run('Aide-moi'):
        events.append(event)
        if event.type == 'tool_result' and accord == 'retire_apres':
            enregistrer_accord('documents', 'openai', False, '3', [])
    if accord in ('actif', 'local'):
        assert len(envois) == 2
        assert 'CONTENU_DOCUMENT_FICTIF' in envois[1]
    else:
        assert all('CONTENU_DOCUMENT_FICTIF' not in e for e in envois)
        if accord != 'retire_apres':
            lecture.assert_not_called()
        assert any('documents' in (e.content + (e.tool_result or '')) for e in events)
