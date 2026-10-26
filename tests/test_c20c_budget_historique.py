"""B-1119 : le texte du flux survit au refus de budget et au rechargement."""
import json
from types import SimpleNamespace

import pytest
from app.models.database import get_session_context
from app.models.entities import Message
from app.routers import chat
from app.services.context import ContextWindow
from app.services.providers.base import LLMProvider, StreamEvent, ToolCall
from sqlmodel import select

REFUS = 'Cette fiche doit reprendre uniquement une information donnée dans ton message.'


async def _rejouer(client, monkeypatch, texte, *, refus_memoire=False, profondeur=1, repetitions=1):
    controles = []
    avant_erreur = []

    def controler(*args, **kwargs):
        controles.append(None)
        return {'allowed': len(controles) <= profondeur, 'warnings': [], 'errors': ['Budget atteint.']}

    class Modele:
        config = SimpleNamespace(model='modele-factice', provider=LLMProvider.ANTHROPIC)
        continuations = 0

        def prepare_context(self, messages, memory_context=None):
            return ContextWindow(messages=messages, system_prompt='', max_tokens=8000)

        async def stream_response_with_tools(self, context, tools=None):
            yield StreamEvent(type='text', content=texte)
            yield self.appel()
            yield StreamEvent(type='done', stop_reason='tool_use', input_tokens=20, output_tokens=5)

        def appel(self):
            return StreamEvent(type='tool_call', tool_call=ToolCall(
                id=f'appel-{self.continuations}', name='upsert_memory_card' if refus_memoire else 'list_tasks',
                arguments={'kind': 'fait', 'subject': 'livraison', 'title': 'Livraison',
                           'content': 'Livraison à Bordeaux'} if refus_memoire else {},
            ))

        async def continue_with_tool_results(self, *args, **kwargs):
            self.continuations += 1
            assert self.continuations < profondeur, 'Le modèle ne doit plus être appelé après le refus.'
            yield StreamEvent(type='text', content=f' Suite {self.continuations}.')
            yield self.appel()
            yield StreamEvent(type='done', stop_reason='tool_use', input_tokens=20, output_tokens=5)

    original = chat._do_stream_response

    async def observer(*args, **kwargs):
        async for morceau in original(*args, **kwargs):
            evenement = json.loads(morceau.removeprefix('data: '))
            if evenement['type'] == 'error':
                # Lecture séparée AVANT la remise du terminal au client.
                async with get_session_context() as session:
                    avant_erreur.append((await session.execute(select(Message).where(
                        Message.role == 'assistant',
                    ))).scalars().all())
            yield morceau

    async def outil(*args, **kwargs):
        return '[]'

    modele = Modele()
    monkeypatch.setattr(chat, 'get_llm_service', lambda: modele)
    monkeypatch.setattr(chat, '_controle_du_prompt', controler)
    monkeypatch.setattr(chat, 'execute_workspace_tool', outil)
    monkeypatch.setattr(chat, '_do_stream_response', observer)
    conversation_id = None
    for tour in range(repetitions):
        controles.clear()
        modele.continuations = 0
        reponse = await client.post('/api/chat/send', json={
            'message': 'Livraison à Lyon', 'stream': True, 'conversation_id': conversation_id,
        })
        assert reponse.status_code == 200, reponse.text
        evenements = [json.loads(ligne.removeprefix('data: ')) for ligne in reponse.text.splitlines()
                      if ligne.startswith('data: ')]
        conversation_id = next(e['conversation_id'] for e in evenements if e.get('conversation_id'))
        assert evenements[-1]['type'] == 'error'
        assert 'Budget atteint.' in evenements[-1]['content']
        assert not any(e['type'] == 'done' for e in evenements)
        affiche = ''.join(e.get('content') or '' for e in evenements if e['type'] == 'text')
        assert texte in affiche
        if refus_memoire:
            assert affiche.count(REFUS) == 1
        recharge = await client.get(f'/api/chat/conversations/{conversation_id}/messages')
        assert recharge.status_code == 200
        assistants = [m for m in recharge.json() if m['role'] == 'assistant']
        assert len(assistants) == tour + 1
        assert assistants[-1]['content'] == affiche
        assert len(avant_erreur[-1]) == tour + 1
        assert avant_erreur[-1][-1].content == affiche
        assert modele.continuations == profondeur - 1


@pytest.mark.parametrize('refus_memoire', [False, True])
async def test_texte_sauve_avant_erreur_et_recharge(client, monkeypatch, refus_memoire):
    await _rejouer(client, monkeypatch, 'Je vérifie la livraison. ', refus_memoire=refus_memoire)


async def test_budget_refuse_au_troisieme_tour_d_outils(client, monkeypatch):
    await _rejouer(client, monkeypatch, 'Je consulte les tâches.', profondeur=3)


# Dix entrées inventées après le correctif, avec des profondeurs différentes.
@pytest.mark.parametrize(('texte', 'refus_memoire', 'profondeur', 'repetitions'), [
    ('Le devis attend une signature.', False, 1, 1),
    ('Échéance : mardi à 09 h 15.', False, 2, 1),
    ('**Dossier Aubépine** : je poursuis.', True, 1, 1),
    ('Deux étapes :\n1. Lire\n2. Vérifier\n', False, 3, 1),
    ('Le client dit « à bientôt ». ', True, 2, 1),
    ('Montant annoncé : 1\u202f250 €.', False, 2, 1),
    ('Je cherche le fichier `plan.pdf`.', False, 1, 1),
    ('La modification reste à vérifier.\n\n', True, 3, 1),
    ('Réponse brève : oui.', True, 1, 1),
    ('Même réponse au tour suivant.', False, 1, 2),
])
async def test_rejeu_apres_correctif(client, monkeypatch, texte, refus_memoire, profondeur, repetitions):
    await _rejouer(client, monkeypatch, texte, refus_memoire=refus_memoire,
                  profondeur=profondeur, repetitions=repetitions)
