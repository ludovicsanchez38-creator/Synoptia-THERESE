"""Les SDK images et Fal vérifient aussi l'accord après leur préparation."""
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from app.services.consentements import enregistrer_accord
from app.services.image_generator import ImageGeneratorService, ImageProvider


@pytest.mark.parametrize('provider', list(ImageProvider))
async def test_retrait_images_avant_transport(client, monkeypatch, tmp_path, provider):
    from app.services import image_generator

    enregistrer_accord('images', provider.value, True, '3', [])
    envoi = Mock(side_effect=RuntimeError('Transport fictif appelé'))
    envoi_async = AsyncMock(side_effect=RuntimeError('Transport fictif appelé'))
    monkeypatch.setattr(image_generator, '_get_api_key_from_db', lambda _: 'factice')
    monkeypatch.setitem(sys.modules, 'openai', SimpleNamespace(
        OpenAI=lambda **kw: SimpleNamespace(images=SimpleNamespace(generate=envoi))))
    genai = SimpleNamespace(Client=lambda **kw: SimpleNamespace(models=SimpleNamespace(generate_content=envoi)),
                            types=SimpleNamespace(GenerateContentConfig=lambda **kw: kw, ImageConfig=lambda **kw: kw))
    import google
    monkeypatch.setattr(google, 'genai', genai, raising=False)
    monkeypatch.setitem(sys.modules, 'google.genai', genai)

    async def thread(fn, *args, **kwargs):
        enregistrer_accord('images', provider.value, False, '3', [])
        return fn(*args, **kwargs)

    async def preparer():
        enregistrer_accord('images', provider.value, False, '3', [])
        return SimpleNamespace(post=envoi_async)

    monkeypatch.setattr(image_generator.asyncio, 'to_thread', thread)
    monkeypatch.setattr('app.services.http_client.get_http_client', preparer)
    erreur = None
    try:
        await ImageGeneratorService(tmp_path).generate('Prompt fictif', provider)
    except Exception as exc:
        erreur = str(exc)
    envoi.assert_not_called()
    envoi_async.assert_not_called()
    assert erreur and 'accord' in erreur
