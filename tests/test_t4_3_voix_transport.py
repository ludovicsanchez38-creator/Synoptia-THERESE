"""La voix cloud revérifie l'accord après lecture audio et préparation HTTP."""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.services.consentements import enregistrer_accord
from app.services.error_handler import ErreurPourEcran


@pytest.mark.parametrize('moment', ['lecture', 'client'])
async def test_retrait_voix_avant_transport(client, monkeypatch, moment):
    from app.routers import voice

    enregistrer_accord('voice', 'groq', True, '3', [])
    transport = AsyncMock(return_value=SimpleNamespace(status_code=200, json=lambda: {'text': 'Fictif'}))

    async def lire():
        if moment == 'lecture':
            enregistrer_accord('voice', 'groq', False, '3', [])
        return b'audio fictif'

    async def preparer():
        if moment == 'client':
            enregistrer_accord('voice', 'groq', False, '3', [])
        return SimpleNamespace(post=transport)

    monkeypatch.setattr(voice, '_get_groq_api_key', AsyncMock(return_value='factice'))
    monkeypatch.setattr(voice, 'get_http_client', preparer)
    erreur = None
    try:
        await voice.transcribe_audio(SimpleNamespace(read=lire, filename='test.webm', content_type='audio/webm'), None)
    except ErreurPourEcran as exc:
        erreur = str(exc)
    transport.assert_not_called()
    assert erreur and 'accord' in erreur
