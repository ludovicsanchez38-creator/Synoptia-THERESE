"""Preuve HTTP de relecture entre conversations, sans substituer le sélecteur."""
import json

import pytest
from app.models.entities import Conversation
from app.services import llm, memory_cards
from app.services.providers.base import LLMProvider

from tests.test_r2_3_outil import action, fournisseur  # noqa: F401


@pytest.mark.asyncio
@pytest.mark.parametrize('provider', ['ollama', 'openai', 'anthropic'])
@pytest.mark.parametrize('stream', [True, False])
async def test_ecriture_a_puis_charge_reelle_b_et_effacement(client, db_session, fournisseur, provider, stream):
    fournisseur[1].append(action())
    tour1 = await client.post('/api/chat/send', json={'message': 'Préfère des phrases courtes.', 'stream': True})
    assert tour1.status_code == 200
    fiche = (await memory_cards.lister())['items'][0]
    b = Conversation(title='Autre conversation')
    db_session.add(b)
    await db_session.commit()
    fournisseur[0].config = llm.LLMConfig(LLMProvider(provider), 'modele-factice', context_window=128000)
    demande = {'conversation_id': b.id, 'message': 'Aide-moi à rédiger.', 'stream': stream,
               'memory_card_grants': [f'llm:{provider}']}
    tour2 = await client.post('/api/chat/send', json=demande)
    assert tour2.status_code == 200, tour2.text
    charge = fournisseur[2][-1]
    complet = json.dumps(charge, ensure_ascii=False)
    assert fiche['content'] in complet
    assert fiche['id'] in complet
    # Aucune histoire de A ne doit être copiée dans les tours de B.
    messages_non_systeme = [m for m in charge['messages'] if m.get('role') != 'system']
    assert fiche['content'] not in json.dumps(messages_non_systeme, ensure_ascii=False)
    await memory_cards.effacer(fiche['id'], fiche['version'])
    rep = await client.post('/api/chat/send', json=demande)
    assert rep.status_code == 200
    assert fiche['content'] not in json.dumps(fournisseur[2][-1], ensure_ascii=False)
    assert fiche['id'] not in json.dumps(fournisseur[2][-1], ensure_ascii=False)


@pytest.mark.asyncio
async def test_correction_utilisateur_resiste_au_chat_et_seule_valeur_corrigee_relue(client, db_session, fournisseur):
    fournisseur[1].append(action())
    await client.post('/api/chat/send', json={'message': 'Préfère des phrases courtes.', 'stream': True})
    fiche = (await memory_cards.lister())['items'][0]
    await memory_cards.ecrire({'id': fiche['id'], 'version': 1, 'content': 'Préfère les listes.'})
    fournisseur[1].append(action(subject='autre formulation'))
    tentative = await client.post('/api/chat/send', json={'message': 'Préfère des phrases courtes.', 'stream': True})
    assert 'Cette fiche est protégée' in tentative.text
    rep = await client.post('/api/chat/send', json={'message': 'Aide-moi à rédiger.', 'stream': True})
    assert rep.status_code == 200
    complet = json.dumps(fournisseur[2][-1], ensure_ascii=False)
    assert 'Préfère les listes.' in complet
    assert 'Préfère des phrases courtes.' not in complet
    assert (await memory_cards.lister())['total'] == 1


@pytest.mark.asyncio
@pytest.mark.parametrize('message', ['Mon mot de passe est Factice!2026', 'Ma clé API est sk-test-factice123456', 'Il souffre de diabète'])
async def test_aucun_rappel_sensible_dans_un_autre_chat(client, db_session, fournisseur, message):
    fournisseur[1].append(action(content=message))
    await client.post('/api/chat/send', json={'message': message, 'stream': True})
    assert not (await memory_cards.lister())['items']
    await client.post('/api/chat/send', json={'message': 'Que sais-tu de ma façon de travailler ?', 'stream': True})
    assert message not in json.dumps(fournisseur[2][-1], ensure_ascii=False)


@pytest.mark.asyncio
@pytest.mark.parametrize('provider,model,purpose,grants,autorise', [
    ('openai', 'factice', 'llm', [], False),
    ('openai', 'factice', 'llm', ['llm:openai'], True),
    ('openai', 'factice', 'documents', ['llm:openai'], False),
    ('openai', 'factice', 'documents', ['documents:openai'], True),
    ('ollama', 'factice:cloud', 'llm', [], False),
    ('ollama', 'factice:cloud', 'llm', ['llm:ollama-cloud'], True),
    ('ollama', 'factice', 'llm', [], True),
])
async def test_accord_destination_reelle_et_finalite(client, db_session, fournisseur, provider, model, purpose, grants, autorise):
    await memory_cards.ecrire(action())
    fournisseur[0].config = llm.LLMConfig(LLMProvider(provider), model, context_window=128000)
    avant = len(fournisseur[2])
    rep = await client.post('/api/chat/send', json={'message': 'Aide-moi à rédiger.', 'stream': True,
        'memory_card_grants': grants, 'memory_card_purpose': purpose})
    assert rep.status_code == 200
    assert (len(fournisseur[2]) > avant) == autorise
    # Révocation : le tour suivant doit réévaluer, sans garder un accord dans le contexte.
    if provider != 'ollama' or ':cloud' in model:
        avant = len(fournisseur[2])
        await client.post('/api/chat/send', json={'message': 'Autre demande.', 'stream': True, 'memory_card_grants': []})
        assert len(fournisseur[2]) == avant


@pytest.mark.asyncio
async def test_sans_fiche_ancien_accord_suffit_et_autres_consommateurs_restent_vides(client, db_session, fournisseur):
    fournisseur[0].config = llm.LLMConfig(LLMProvider.OPENAI, 'factice', context_window=128000)
    rep = await client.post('/api/chat/send', json={'message': 'Bonjour', 'stream': True})
    assert rep.status_code == 200 and len(fournisseur[2]) == 1
    fiche = await memory_cards.ecrire(action())
    # Voie commune utilisée hors chat : aucun attachement R2, identité réelle.
    resultat = await fournisseur[0].generate_content('Question hors chat')
    assert resultat
    assert fiche['id'] not in json.dumps(fournisseur[2][-1], ensure_ascii=False)
    assert fiche['content'] not in json.dumps(fournisseur[2][-1], ensure_ascii=False)


@pytest.mark.asyncio
async def test_repli_plus_petit_refuse_avant_fournisseur(client, db_session, fournisseur, monkeypatch):
    from unittest.mock import AsyncMock
    await memory_cards.ecrire(action(content='Préférence longue ' * 50))
    repli = llm.LLMConfig(LLMProvider.OPENAI, 'petit-factice', context_window=500)
    monkeypatch.setattr(fournisseur[0], '_resolve_with_circuit_breaker', lambda: repli)
    obtenir = AsyncMock()
    monkeypatch.setattr(fournisseur[0], '_provider_pour', obtenir)
    rep = await client.post('/api/chat/send', json={'message': 'Bonjour', 'stream': True, 'memory_card_grants': ['llm:openai']})
    assert rep.status_code == 200
    assert not fournisseur[2]
    obtenir.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize('stream', [True, False])
@pytest.mark.parametrize('taille', [4000, 30000])
async def test_document_long_ne_rabote_pas_la_demande_avant_la_reserve(client, db_session, fournisseur, monkeypatch, stream, taille):
    from unittest.mock import AsyncMock
    from app.routers import chat
    await memory_cards.ecrire(action())
    document = 'D' * 100000
    service = fournisseur[0]
    # Ancien prepare_context laisse environ 500 jetons à la demande, donc la coupe.
    # La réserve R2 doit repartir de la demande entière, avant cette coupe.
    fenetre_entree = len(service._get_system_prompt_with_identity() + '\n\n## Contexte mémoire:\n' + document) // 4 + 500
    service.config = llm.LLMConfig(LLMProvider.OLLAMA, 'factice', context_window=fenetre_entree + 4096)
    monkeypatch.setattr(chat, '_get_file_context', AsyncMock(return_value=(document, None)))
    demande = 'Q' * taille
    rep = await client.post('/api/chat/send', json={'message': demande, 'stream': stream,
        'disable_tools': True, 'file_paths': ['document-factice.txt']})
    assert rep.status_code == 200
    if taille == 30000:
        assert not fournisseur[2], 'La demande entière ne tient pas : aucun envoi partiel ne doit partir.'
    else:
        assert len(fournisseur[2]) == 1, rep.text
        user = [m for m in fournisseur[2][0]['messages'] if m.get('role') == 'user'][-1]
        assert user['content'] == demande
