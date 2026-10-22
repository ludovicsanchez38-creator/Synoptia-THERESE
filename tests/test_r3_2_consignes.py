"""R3 : le payload du chat reflète les consignes enregistrées sans redémarrage."""
import pytest
from app.services import llm

from tests.test_r2_3_outil import fournisseur  # noqa: F401


@pytest.mark.asyncio
async def test_enregistrement_therese_md_recharge_le_chat(client, db_session, fournisseur, monkeypatch):  # noqa: F811
    monkeypatch.setattr(llm, '_therese_md_content', 'Ancien témoin FICTIF-ANCIEN')
    monkeypatch.setattr(llm, '_therese_md_loaded', True)
    assert 'FICTIF-ANCIEN' in llm.load_therese_md()
    texte = 'Consigne fictive : le témoin est FICTIF-NOUVEAU.'
    reponse = await client.post('/api/config/therese-md', json={'content': texte})
    assert reponse.status_code == 200
    assert (await client.get('/api/config/therese-md')).json()['content'] == texte
    await client.post('/api/chat/send', json={'message': 'Bonjour', 'stream': True})
    systeme = fournisseur[2][-1]['system']
    assert texte in systeme
    assert 'FICTIF-ANCIEN' not in systeme
    # Une suppression depuis l'application ne garde pas davantage l'ancien cache.
    await client.post('/api/config/therese-md', json={'content': ''})
    await client.post('/api/chat/send', json={'message': 'Bonjour', 'stream': True})
    assert 'FICTIF-NOUVEAU' not in fournisseur[2][-1]['system']
