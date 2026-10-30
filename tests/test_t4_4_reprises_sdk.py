"""Les vrais SDK images repassent par la garde à chaque tentative HTTP."""
import base64
from unittest.mock import Mock

import httpx
import pytest
from app.services.consentements import accord_valide, enregistrer_accord
from app.services.image_generator import ImageGeneratorService, ImageProvider
from PIL import Image


@pytest.mark.parametrize('provider', [ImageProvider.OPENAI, ImageProvider.GEMINI])
@pytest.mark.parametrize('edition', [False, True])
@pytest.mark.parametrize('retrait', [True, False])
async def test_reprise_sdk_reel(client, monkeypatch, tmp_path, provider, edition, retrait):
    from app.services import image_generator

    enregistrer_accord('images', provider.value, True, '3', [])
    monkeypatch.setattr(image_generator, '_get_api_key_from_db', lambda _: 'factice')
    # Les SDK, leur sérialisation et leurs reprises restent réels.
    # Seul le transport réseau est remplacé, en dessous du transport gardé.
    envois = []

    def repondre(request):
        envois.append((request.content, accord_valide('images', provider.value)))
        if len(envois) == 1:
            if retrait:
                enregistrer_accord('images', provider.value, False, '3', [])
            return httpx.Response(429, headers={'retry-after-ms': '1'}, json={
                'error': {'code': 429, 'message': 'Reprise fictive', 'status': 'RESOURCE_EXHAUSTED'},
            })
        image = base64.b64encode(b'image fictive').decode()
        data = ({'data': [{'b64_json': image}]} if provider == ImageProvider.OPENAI else
                {'candidates': [{'content': {'parts': [{'inlineData': {'data': image, 'mimeType': 'image/png'}}]}}]})
        return httpx.Response(200, json=data)

    transport = httpx.MockTransport(repondre)
    monkeypatch.setattr(httpx.HTTPTransport, 'handle_request', lambda self, request: transport.handle_request(request))
    # Gemini sans HttpRetryOptions n'a qu'une tentative dans la version installée.
    # Activer ses reprises natives éprouve aussi une évolution de ce défaut.
    from google import genai
    from google.genai import types
    original = genai.Client

    def gemini(**kwargs):
        options = kwargs.pop('http_options', None) or types.HttpOptions()
        options.retry_options = types.HttpRetryOptions(attempts=3, initial_delay=0.001, max_delay=0.001, jitter=0.001)
        return original(**kwargs, http_options=options)

    monkeypatch.setattr(genai, 'Client', gemini)
    service = ImageGeneratorService(tmp_path)
    service._save_image = Mock(return_value='image enregistrée')
    reference = tmp_path / 'reference.png'
    Image.new('RGB', (2, 2)).save(reference)
    erreur = None
    try:
        await service.generate('PROMPT_FICTIF', provider, reference_image_path=str(reference) if edition else None)
    except Exception as exc:
        erreur = str(exc)
    assert len(envois) == (1 if retrait else 2)
    assert all(accord for _, accord in envois)
    if retrait:
        assert erreur and 'accord' in erreur and 'images' in erreur
        service._save_image.assert_not_called()
    else:
        assert erreur is None
        service._save_image.assert_called_once()
