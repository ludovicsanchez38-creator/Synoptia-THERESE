"""Le petit modèle doit recevoir une distinction explicite utilisateur/assistante."""
import pytest

from tests.test_r2_3_outil import fournisseur  # noqa: F401


@pytest.mark.asyncio
@pytest.mark.parametrize('nom', ['Élise Maquette', 'Noé Atelier'])
async def test_identite_et_regles_du_profil_desambiguees_dans_le_payload(client, db_session, fournisseur, nom):  # noqa: F811
    rep = await client.post('/api/config/profile', json={'name': nom,
        'context': 'Règle 3 : préfixe LOUTRE-VIOLETTE.'})
    assert rep.status_code == 200
    await client.post('/api/chat/send', json={'message': 'Qui suis-je ?', 'stream': True})
    systeme = fournisseur[2][-1]['system']
    assert f'Tu es {nom}' in systeme
    assert systeme.rfind(nom) > systeme.index('Honnêteté sur les données')
    assert 'règles numérotées de son profil' in systeme
    assert 'LOUTRE-VIOLETTE' in systeme
