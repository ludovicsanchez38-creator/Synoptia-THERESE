"""La destination aval inconnue interdit tout envoi OpenClaw."""
from unittest.mock import AsyncMock, Mock

import pytest
from app.models.database import get_sync_session
from app.models.entities_agents import AgentSession
from app.services.consentements import enregistrer_accord


@pytest.mark.parametrize('accords', ['absents', 'retires', 'tous'])
@pytest.mark.parametrize('route', ['dispatch', 'send'])
async def test_routes_fermees(client, monkeypatch, accords, route):
    from app.services import openclaw_bridge as bridge

    for purpose in ('llm', 'documents', 'images', 'board', 'voice'):
        for provider in ('openai', 'gemini', 'anthropic', 'openclaw'):
            if accords != 'absents':
                enregistrer_accord(purpose, provider, True, '3', [])
            if accords == 'retires':
                enregistrer_accord(purpose, provider, False, '3', [])
    spawn = AsyncMock(return_value={'session_id': 'fictive'})
    send = AsyncMock(return_value={'content': 'fictif'})
    check = AsyncMock(return_value=True)
    monkeypatch.setattr(bridge, 'spawn_session', spawn)
    monkeypatch.setattr(bridge, 'send_message', send)
    monkeypatch.setattr(bridge, 'check_connection', check)
    with get_sync_session() as session:
        session.add(AgentSession(id='session-fictive', agent_name='test', instruction='fictif',
                                 status='running', openclaw_session_id='aval-fictif'))
        session.commit()
    path, body = (('/dispatch', {'instruction': 'SECRET_FICTIF', 'agent_name': 'test'}) if route == 'dispatch'
                  else ('/sessions/session-fictive/send', {'content': 'SECRET_FICTIF'}))
    response = await client.post('/api/agents' + path, json=body)
    assert response.status_code == 403
    assert 'destination' in response.text and 'Tu' in response.text
    spawn.assert_not_called()
    send.assert_not_called()
    check.assert_not_called()


@pytest.mark.parametrize('fonction', ['spawn_session', 'send_message'])
async def test_passerelle_elle_meme_fermee(monkeypatch, fonction):
    from app.services import openclaw_bridge as bridge

    transport = Mock(side_effect=AssertionError('Passerelle appelée'))
    monkeypatch.setattr(bridge, '_client', transport)
    result = await getattr(bridge, fonction)('fictif', 'SECRET_FICTIF')
    assert 'destination' in result['error']
    transport.assert_not_called()
