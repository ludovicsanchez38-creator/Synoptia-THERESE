"""R3 : contexte utilisateur complet, y compris après le caractère 2000."""
import pytest
from app.services.user_profile import UserProfile

from tests.test_r2_3_outil import fournisseur  # noqa: F401

CONTEXTE = 'Règle 1 : tutoyer.\n' + 'Projet fictif. ' * 155 + '\nRègle 3 : préfixe LOUTRE-VIOLETTE.'


def test_format_profil_integral():
    assert CONTEXTE.index('Règle 3') > 2000
    assert CONTEXTE in UserProfile(name='Camille Fictive', context=CONTEXTE).format_for_llm()


@pytest.mark.asyncio
async def test_profil_integral_dans_charge_du_routeur(client, db_session, fournisseur):  # noqa: F811
    reponse = await client.post('/api/config/profile', json={'name': 'Camille Fictive',
        'location': 'Bretagne fictive', 'context': CONTEXTE})
    assert reponse.status_code == 200
    assert (await client.get('/api/config/profile')).json()['context'] == CONTEXTE
    await client.post('/api/chat/send', json={'message': 'Cite la règle 3', 'stream': True})
    systeme = fournisseur[2][-1]['system']
    assert CONTEXTE in systeme
    assert 'Camille Fictive' in systeme and 'Bretagne fictive' in systeme
