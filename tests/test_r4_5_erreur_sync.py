"""#104 : l'erreur de synchronisation doit guider le testeur sans OAuth."""
import pytest

from tests.test_r4_3_caldav import serveur_caldav, setup  # noqa: F401


@pytest.mark.asyncio
async def test_erreur_caldav_explique_la_marche_a_suivre(client, db_session, serveur_caldav):  # noqa: F811
    await setup(client)
    serveur_caldav[1]['erreur'] = True
    reponse = await client.post('/api/calendar/sync')
    assert reponse.status_code == 502, reponse.text
    detail = reponse.json().get('detail') or reponse.json()['message']
    assert detail.startswith('Synchronisation CalDAV impossible.')
    assert 'Ouvre Agenda' in detail
    assert "mot de passe d'application" in detail
    assert 'relance la synchronisation' in detail
    assert 'inattendue' not in detail
    assert 'panne du serveur factice' not in detail
