"""Une image jointe réclame l'accord documents dans les deux routes du chat."""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.services.consentements import enregistrer_accord
from app.services.llm import LLMConfig, LLMProvider, LLMService
from app.services.providers.base import StreamEvent


@pytest.mark.parametrize('stream', [False, True])
@pytest.mark.parametrize('accord', ['absent', 'retire', 'retire_pendant', 'actif'])
async def test_image_seule_passe_par_la_garde_documents(client, monkeypatch, tmp_path, stream, accord):
    from app.routers import chat

    image = tmp_path / 'image-fictive.png'
    image.write_bytes(b'\x89PNG\r\n\x1a\n')
    enregistrer_accord('llm', 'openai', True, '3', [])
    if accord != 'absent':
        enregistrer_accord('documents', 'openai', True, '3', [])
    if accord == 'retire':
        enregistrer_accord('documents', 'openai', False, '3', [])
    envois = []

    async def transport(*args, **kwargs):
        envois.append(args)
        yield StreamEvent(type='text', content='Image reçue')

    service = LLMService(LLMConfig(LLMProvider.OPENAI, 'modele-fictif', api_key='factice'))
    service._provider = SimpleNamespace(stream=transport)
    service._ensure_provider = AsyncMock()
    if accord == 'retire_pendant':
        preparer = service.prepare_context

        def retrait_avant_envoi(*args, **kwargs):
            context = preparer(*args, **kwargs)
            enregistrer_accord('documents', 'openai', False, '3', [])
            return context

        monkeypatch.setattr(service, 'prepare_context', retrait_avant_envoi)
    monkeypatch.setattr(chat, 'get_llm_service', lambda: service)
    response = await client.post('/api/chat/send', json={
        'message': 'Observe cette image', 'file_paths': [str(image)],
        'include_memory': False, 'stream': stream,
    })
    if accord == 'actif':
        assert envois, response.text
        assert 'image_url' in str(envois)
    else:
        assert not envois, 'Image transmise sans accord documents'
        assert 'documents' in response.text, response.text


async def test_garde_centrale_detecte_image_sans_drapeau(client):
    from app.services.consentements import verifier_envoi_llm
    from app.services.context import ContextWindow
    from app.services.error_handler import ErreurPourEcran
    from app.services.providers.base import ImageJointe, Message

    enregistrer_accord('llm', 'openai', True, '3', [])
    context = ContextWindow(messages=[Message(role='user', content='', images=[
        ImageJointe(media_type='image/png', donnees_base64='fictif'),
    ])])
    with pytest.raises(ErreurPourEcran, match='documents'):
        verifier_envoi_llm(LLMConfig(LLMProvider.OPENAI, 'modele'), context)
