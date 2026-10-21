"""Fermeture du noyau : loquets réels, rollback et absence de clair après le chat."""
import asyncio
from pathlib import Path

import pytest
from app.models.entities import MemoryCard, Message
from app.services import memory_cards as service, memory_tools
from sqlalchemy import delete
from sqlmodel import select

from tests.test_r2_3_outil import action, fournisseur  # noqa: F401


@pytest.mark.asyncio
async def test_purge_entre_entree_et_inscription_du_geste_refuse_le_retard(db_session, monkeypatch):
    entree, autoriser = asyncio.Event(), asyncio.Event()
    original = memory_tools._proteger_le_geste
    async def retarder(coro):
        entree.set()
        await autoriser.wait()
        return await original(coro)
    monkeypatch.setattr(memory_tools, '_proteger_le_geste', retarder)
    tache = asyncio.create_task(service.ecrire(action()))
    await entree.wait()
    async with memory_tools.creations_du_chat_suspendues():
        await memory_tools.attendre_les_gestes_de_creation()
    autoriser.set()
    with pytest.raises(service.RefusMemoire):
        await tache
    assert not (await service.lister())['items']


@pytest.mark.asyncio
async def test_purge_attend_le_commit_du_geste_puis_efface(db_session, monkeypatch):
    entree, autoriser = asyncio.Event(), asyncio.Event()
    original = service._ecrire
    async def retarder(*args, **kwargs):
        entree.set()
        await autoriser.wait()
        return await original(*args, **kwargs)
    monkeypatch.setattr(service, '_ecrire', retarder)
    tache = asyncio.create_task(service.ecrire(action()))
    await entree.wait()
    async with memory_tools.creations_du_chat_suspendues():
        attente = asyncio.create_task(memory_tools.attendre_les_gestes_de_creation())
        await asyncio.sleep(0)
        assert not attente.done()
        autoriser.set()
        await tache
        await attente
        async with service.get_session_context() as session:
            await session.execute(delete(MemoryCard))
    assert not (await service.lister())['items']


@pytest.mark.asyncio
async def test_rollback_ne_laisse_ni_fiche_ni_recu(client, db_session, fournisseur, monkeypatch):
    original = service._ecrire
    async def echouer(*args, **kwargs):
        await original(*args, **kwargs)
        raise service.RefusMemoire('Échec factice avant commit.')
    monkeypatch.setattr(service, '_ecrire', echouer)
    fournisseur[1].append(action())
    rep = await client.post('/api/chat/send', json={'message': 'Préfère des phrases courtes.', 'stream': True})
    assert 'memory_receipt' not in rep.text
    assert not (await service.lister())['items']
    for msg in (await db_session.execute(select(Message))).scalars():
        assert 'memory_receipts' not in (msg.extra_data or '')


@pytest.mark.asyncio
async def test_aucun_clair_dans_le_dossier_de_donnees_apres_ecriture_chat(client, db_session, fournisseur):
    from app.config import settings
    sentinelle = 'SENTINELLE_MEMOIRE_CHIFFREE préfère les listes.'
    fournisseur[1].append(action(content=sentinelle))
    rep = await client.post('/api/chat/send', json={'message': sentinelle, 'stream': True})
    assert 'memory_receipt' in rep.text
    assert (await service.lister())['total'] == 1
    for fichier in Path(settings.data_dir).rglob('*'):
        if fichier.is_file():
            assert b'SENTINELLE_MEMOIRE_CHIFFREE' not in fichier.read_bytes(), fichier.name


@pytest.mark.asyncio
async def test_un_rejeu_ne_contourne_pas_un_changement_de_dossier(db_session):
    from app.models.entities import Project
    from tests.test_r2_2_protection import source
    a, b = Project(name='A'), Project(name='B')
    db_session.add_all([a, b])
    await db_session.commit()
    origine = await source(db_session, projet=a.id)
    await service.ecrire(action(), **origine)
    with pytest.raises(service.RefusMemoire):
        await service.ecrire(action(), **(origine | {'scope_id': b.id}))


@pytest.mark.asyncio
async def test_arret_observe_avant_commit_annule_la_fiche(db_session, monkeypatch):
    from app.services.contexte_execution import ContexteExecution
    contexte = ContexteExecution()
    original = service._ecrire
    async def arreter(*args, **kwargs):
        resultat = await original(*args, **kwargs)
        contexte.demander_arret()
        return resultat
    monkeypatch.setattr(service, '_ecrire', arreter)
    with pytest.raises(service.RefusMemoire):
        await service.ecrire(action(), contexte=contexte)
    assert not (await service.lister())['items']


@pytest.mark.asyncio
async def test_contact_exporte_et_efface_aussi_les_fiches_de_son_dossier(client, db_session):
    from app.models.entities import Contact, Project
    personne = Contact(first_name='Cliente factice')
    db_session.add(personne)
    await db_session.commit()
    projet = Project(name='Dossier', contact_id=personne.id)
    db_session.add(projet)
    await db_session.commit()
    fiche = await service.ecrire(action() | {'scope': 'project', 'scope_id': projet.id})
    rep = await client.get(f'/api/rgpd/export/{personne.id}')
    assert fiche['id'] in {f['id'] for f in rep.json()['memory_cards']}
    assert (await client.delete(f'/api/memory/contacts/{personne.id}')).status_code == 200
    assert not (await service.lister())['items']


@pytest.mark.asyncio
async def test_source_ancienne_accessible_depuis_la_fiche(client, db_session):
    from datetime import UTC, datetime, timedelta
    from app.models.entities import Conversation
    conv = Conversation(title='Ancien échange')
    db_session.add(conv)
    await db_session.commit()
    date = datetime(2026, 1, 1, tzinfo=UTC)
    messages = [Message(id=f'source-{i:04}', conversation_id=conv.id, role='user', content=f'Tour {i}',
                        created_at=date + timedelta(seconds=i)) for i in range(110)]
    db_session.add_all(messages)
    await db_session.commit()
    rep = await client.get(f'/api/chat/conversations/{conv.id}/messages')
    assert 'source-0000' not in {m['id'] for m in rep.json()}
    rep = await client.get(f'/api/chat/conversations/{conv.id}/messages?around_message_id=source-0000')
    assert [m['id'] for m in rep.json()] == ['source-0000']
