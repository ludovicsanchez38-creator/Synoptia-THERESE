import pytest


@pytest.mark.asyncio
async def test_suppression_decrit_ce_qui_reste(client):
    result = (await client.delete('/api/data/all?confirm=true')).json()
    texte = result['message'] + ' ' + result['note']
    assert 'conformément au RGPD' not in texte
    for mot in ('base locale', 'journaux techniques', 'noms', 'adresses', 'hors du dossier'):
        assert mot in texte
