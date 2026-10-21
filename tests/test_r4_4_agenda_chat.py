"""#104 : le fournisseur factice capture le retour réel de l'outil agenda."""
from copy import deepcopy

import pytest
from app.models.entities import Calendar
from app.services.providers.base import LLMConfig, LLMProvider, StreamEvent, ToolCall

from tests.test_r2_3_outil import fournisseur  # noqa: F401
from tests.test_r4_3_caldav import serveur_caldav, setup  # noqa: F401


@pytest.mark.asyncio
@pytest.mark.parametrize('etat', ['absent', 'jamais', 'echec', 'vide_local'])
async def test_retour_outil_interdit_les_inventions(client, db_session, fournisseur, etat):
    if etat != 'absent':
        cal = Calendar(id='r4-agenda', summary='Agenda fictif', provider='local' if etat == 'vide_local' else 'caldav',
            remote_id='r4-distant', sync_status='error' if etat == 'echec' else 'idle',
            last_sync_error='panne factice' if etat == 'echec' else None,
            caldav_url='http://127.0.0.1:9/', caldav_username='fictif', caldav_password='fictif')
        db_session.add(cal)
        await db_session.commit()
    captures = []
    class Factice:
        async def stream(self, system_prompt, messages, tools=None, **kwargs):
            yield StreamEvent(type='tool_call', tool_call=ToolCall(id='r4-appel', name='list_calendar_events', arguments={'days': 1}))
            yield StreamEvent(type='done', stop_reason='tool_calls')
        async def continue_with_tool_results(self, system_prompt, messages, assistant_content, tool_calls, tool_results, *args, **kwargs):
            captures.extend(deepcopy(tool_results))
            yield StreamEvent(type='text', content='Je ne peux pas confirmer ton agenda. Ouvre Agenda pour le synchroniser.')
            yield StreamEvent(type='done', stop_reason='end_turn')
    fournisseur[0].config = LLMConfig(LLMProvider.OPENAI, 'factice', context_window=128000)
    fournisseur[0]._provider = Factice()
    demande = {'message': 'Quel est mon agenda du jour ?', 'stream': True}
    if etat != 'absent':
        demande['calendar_id'] = 'r4-agenda'
    rep = await client.post('/api/chat/send', json=demande)
    assert rep.status_code == 200, rep.text
    assert captures, rep.text
    resultat = str(captures[0].result).lower()
    assert "n'invente aucun" in resultat
    if etat == 'echec':
        assert 'dernière synchronisation a échoué' in resultat
    else:
        assert 'aucun calendrier synchronisé' in resultat
    if etat != 'vide_local':
        assert 'aucun evenement dans' not in resultat
    assert '09:00' not in rep.text


@pytest.mark.asyncio
async def test_echec_sync_est_enregistre_pour_le_chat(client, db_session, serveur_caldav):
    identifiant = await setup(client)
    serveur_caldav[1]['erreur'] = True
    reponse = await client.post('/api/calendar/sync')
    assert reponse.status_code >= 400
    calendrier = await db_session.get(Calendar, identifiant)
    await db_session.refresh(calendrier)
    assert calendrier.sync_status == 'error'
    assert 'synchronisation a échoué' in calendrier.last_sync_error
    assert calendrier.synced_at is None
