"""Une limite de requêtes ne prouve pas que la clé est valide."""

import httpx
import pytest
from app.services.verification_cle import message_verification, verifier_cle


@pytest.mark.asyncio
async def test_limite_ne_presente_pas_la_cle_comme_acceptee():
    transport = httpx.MockTransport(lambda _: httpx.Response(429))
    async with httpx.AsyncClient(transport=transport) as client:
        etat = await verifier_cle('openai', 'valeur-fictive', client)
    assert etat == 'limite'
    message = message_verification(etat, 'Fournisseur fictif')
    assert 'acceptée' not in message
    assert 'vérifi' in message.lower()
