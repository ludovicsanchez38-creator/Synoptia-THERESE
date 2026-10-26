"""Revue Grok 0.81 : un refus de budget après un outil qui a écrit un fichier.

Le refus de B-1119 sortait avant le drain des cartes (B-147) et avant le
suivi de la dépense : un fichier écrit restait sans carte pour l'ouvrir, et
les jetons consommés par le tour n'étaient comptés nulle part.

Les cartes se vérifient en appel direct du producteur, comme les tests B-147 :
derrière la route HTTP, chaque pas du producteur tourne dans sa propre tâche
et la collecte du tour ne le suit pas (generate_document n'écrit d'ailleurs
plus pendant le flux, il attend sa confirmation). La dépense se vérifie aussi
par la route HTTP, le chemin réel.
"""
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.models.entities import Conversation, Message
from app.routers import chat
from app.services import workspace_tools
from app.services.context import ContextWindow
from app.services.providers.base import LLMProvider, StreamEvent, ToolCall
from sqlmodel import select


class _Suivi:
    """Laisse passer le vrai suivi et garde chaque enregistrement."""

    def __init__(self, reel):
        self._reel = reel
        self.enregistrements = []

    def record_usage(self, **kwargs):
        self.enregistrements.append(kwargs)
        return self._reel.record_usage(**kwargs)

    def __getattr__(self, nom):
        return getattr(self._reel, nom)


async def _rejouer(client, monkeypatch, *, texte, fichiers, profondeur=1, usage=(20, 5), session=None):
    controles = []

    def controler(*args, **kwargs):
        controles.append(None)
        return {'allowed': len(controles) <= profondeur, 'warnings': [], 'errors': ['Budget atteint.']}

    entree, sortie = usage

    class Modele:
        config = SimpleNamespace(model='modele-factice', provider=LLMProvider.ANTHROPIC)
        continuations = 0

        def prepare_context(self, messages, memory_context=None):
            return ContextWindow(messages=messages, system_prompt='', max_tokens=8000)

        async def stream_response_with_tools(self, context, tools=None):
            if texte:
                yield StreamEvent(type='text', content=texte)
            yield self.appel()
            yield StreamEvent(type='done', stop_reason='tool_use', input_tokens=entree, output_tokens=sortie)

        def appel(self):
            return StreamEvent(type='tool_call', tool_call=ToolCall(
                id=f'appel-{self.continuations}', name='list_tasks', arguments={},
            ))

        async def continue_with_tool_results(self, *args, **kwargs):
            self.continuations += 1
            assert self.continuations < profondeur, 'Le modèle ne doit plus être appelé après le refus.'
            yield StreamEvent(type='text', content=f' Suite {self.continuations}.')
            yield self.appel()
            yield StreamEvent(type='done', stop_reason='tool_use', input_tokens=entree, output_tokens=sortie)

    restants = list(fichiers)

    async def outil(*args, **kwargs):
        # Le fichier est écrit par l'outil, comme generate_document : la
        # carte attend dans le seau du tour.
        if restants:
            workspace_tools.record_generated_file(restants.pop(0))
        return '[]'

    suivi = _Suivi(chat.get_token_tracker())
    monkeypatch.setattr(chat, 'get_llm_service', lambda: Modele())
    monkeypatch.setattr(chat, '_controle_du_prompt', controler)
    monkeypatch.setattr(chat, 'execute_workspace_tool', outil)
    monkeypatch.setattr(chat, 'get_token_tracker', lambda: suivi)

    if session is not None:
        # Appel direct du producteur (harnais des tests B-147).
        conversation = Conversation(title='courrier')
        session.add(conversation)
        await session.commit()
        monkeypatch.setattr(chat, '_get_memory_context', AsyncMock(return_value=''))
        brut = ''
        async for morceau in chat._do_stream_response(conversation.id, 'Fais-moi le courrier en PDF', session):
            brut += morceau
        evenements = [json.loads(bloc.strip().removeprefix('data: ')) for bloc in brut.split('\n\n')
                      if bloc.strip().startswith('data: ')]
        lignes = (await session.execute(
            select(Message).where(Message.conversation_id == conversation.id, Message.role == 'assistant')
        )).scalars().all()
        assistants = [{'content': m.content, 'extra_data': m.extra_data} for m in lignes]
        return evenements, assistants, suivi

    reponse = await client.post('/api/chat/send', json={'message': 'Fais-moi le courrier en PDF', 'stream': True})
    assert reponse.status_code == 200, reponse.text
    evenements = [json.loads(ligne.removeprefix('data: ')) for ligne in reponse.text.splitlines()
                  if ligne.startswith('data: ')]
    conversation_id = next(e['conversation_id'] for e in evenements if e.get('conversation_id'))
    recharge = await client.get(f'/api/chat/conversations/{conversation_id}/messages')
    assert recharge.status_code == 200
    assistants = [m for m in recharge.json() if m['role'] == 'assistant']
    return evenements, assistants, suivi


def _fichier(nom):
    return {
        'skill_id': None, 'file_id': f'f-{nom}', 'file_name': nom, 'file_size': 4096,
        'download_url': f'/api/skills/files/f-{nom}', 'format': nom.rsplit('.', 1)[-1],
        'local_dir': '/tmp',
    }


def _cartes_persistees(assistant):
    extra = assistant.get('extra_data')
    if isinstance(extra, str):
        extra = json.loads(extra)
    return [f['file_name'] for f in (extra or {}).get('skill_files') or []]


async def test_le_pdf_garde_sa_carte_et_la_depense_est_comptee(client, db_session, monkeypatch):
    evenements, assistants, suivi = await _rejouer(
        client, monkeypatch, texte='Je prépare le courrier. ', fichiers=[_fichier('courrier.pdf')],
        session=db_session,
    )
    types = [e['type'] for e in evenements]
    assert types[-1] == 'error'
    assert 'skill_file' in types, 'la carte du PDF déjà écrit doit précéder le refus'
    assert types.index('skill_file') < len(types) - 1
    assert len(assistants) == 1
    assert _cartes_persistees(assistants[0]) == ['courrier.pdf'], 'la carte doit survivre au rechargement'
    assert len(suivi.enregistrements) == 1, 'la dépense du tour refusé doit être comptée une fois'
    assert suivi.enregistrements[0]['input_tokens'] == 20
    assert suivi.enregistrements[0]['output_tokens'] == 5


async def test_sans_texte_le_fichier_seul_garde_un_message(client, db_session, monkeypatch):
    evenements, assistants, suivi = await _rejouer(
        client, monkeypatch, texte='', fichiers=[_fichier('note.pdf')], session=db_session,
    )
    assert evenements[-1]['type'] == 'error'
    assert len(assistants) == 1, 'sans texte, le message porte la carte et le motif du refus'
    assert _cartes_persistees(assistants[0]) == ['note.pdf']
    assert 'Budget atteint.' in assistants[0]['content']
    assert len(suivi.enregistrements) == 1


async def test_sans_fichier_le_refus_reste_celui_de_b1119(client, monkeypatch):
    evenements, assistants, suivi = await _rejouer(
        client, monkeypatch, texte='Je consulte les tâches. ', fichiers=[],
    )
    assert 'skill_file' not in [e['type'] for e in evenements]
    assert len(assistants) == 1
    assert _cartes_persistees(assistants[0]) == []
    assert len(suivi.enregistrements) == 1


async def test_sans_texte_ni_fichier_aucun_message_mais_la_depense(client, monkeypatch):
    _, assistants, suivi = await _rejouer(client, monkeypatch, texte='', fichiers=[])
    assert assistants == []
    assert len(suivi.enregistrements) == 1


# Dix entrées inventées après le correctif : profondeurs, noms, nombre de
# fichiers et usages différents.
@pytest.mark.parametrize(('texte', 'noms', 'profondeur', 'usage'), [
    ('Voici le devis. ', ['devis-aubepine.pdf'], 1, (120, 40)),
    ('', ['compte-rendu.docx'], 2, (5, 1)),
    ('Deux pièces :', ['lettre.pdf', 'annexe.pdf'], 2, (300, 90)),
    ('Échéancier prêt.', ['echeancier.xlsx'], 3, (64, 64)),
    ('**Note** jointe.', ['note de cadrage.pdf'], 1, (1, 1)),
    ('Je génère…', ['courrier-été.pdf'], 2, (999, 3)),
    ('Montant : 1 250 €.', ['facture-proforma.pdf'], 1, (42, 7)),
    ('', ['a.pdf', 'b.pdf', 'c.pdf'], 3, (10, 10)),
    ('Le plan suit.\n\n', ['plan.pptx'], 1, (77, 12)),
    ('Réponse brève.', ['brief.pdf'], 2, (2000, 500)),
])
async def test_rejeu_apres_correctif(client, db_session, monkeypatch, texte, noms, profondeur, usage):
    evenements, assistants, suivi = await _rejouer(
        client, monkeypatch, texte=texte, fichiers=[_fichier(n) for n in noms],
        profondeur=profondeur, usage=usage, session=db_session,
    )
    assert evenements[-1]['type'] == 'error'
    cartes = [e['skill_file']['file_name'] for e in evenements if e['type'] == 'skill_file']
    assert cartes == noms[:profondeur], cartes
    assert len(assistants) == 1
    assert _cartes_persistees(assistants[0]) == noms[:profondeur]
    assert len(suivi.enregistrements) == 1
    assert suivi.enregistrements[0]['input_tokens'] == usage[0] * profondeur


async def test_par_la_route_la_depense_du_tour_refuse_est_comptee(client, monkeypatch):
    """Chemin réel : la route HTTP, sans fichier (rien n'écrit pendant le flux)."""
    _, assistants, suivi = await _rejouer(
        client, monkeypatch, texte='Je consulte les tâches. ', fichiers=[], profondeur=2, usage=(30, 9),
    )
    assert len(assistants) == 1
    assert len(suivi.enregistrements) == 1
    assert suivi.enregistrements[0]['input_tokens'] == 60
    assert suivi.enregistrements[0]['output_tokens'] == 18
