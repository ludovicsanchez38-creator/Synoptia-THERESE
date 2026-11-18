"""Le conseil affiché correspond au fournisseur qui a répondu."""

import httpx
import pytest
from app.services.verification_cle import message_verification, verifier_cle


@pytest.mark.asyncio
async def test_cle_sans_espace_ne_cite_pas_un_autre_fournisseur():
    transport = httpx.MockTransport(lambda _: httpx.Response(400, text='not scoped to a workspace'))
    async with httpx.AsyncClient(transport=transport) as client:
        etat = await verifier_cle('openai', 'valeur-fictive', client)
    assert etat == 'non_rattachee'
    message = message_verification(etat, 'OpenAI')
    assert 'OpenAI' in message
    assert 'Claude' not in message
    assert 'espace de travail' in message
