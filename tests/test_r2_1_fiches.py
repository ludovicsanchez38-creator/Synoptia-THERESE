"""R2-1 : fiches SQL chiffrées et effacement dès leur introduction."""
import json
from pathlib import Path

import pytest
from app.models.entities import Contact, Conversation, Message, Project
from sqlmodel import select


async def ajouter(service, **kwargs):
    donnees = {'kind': 'preference', 'subject': 'rédaction', 'title': 'Rédaction',
               'content': 'Préfère des phrases courtes.'} | kwargs
    return await service.ecrire(donnees)


@pytest.mark.asyncio
async def test_fiche_version_archive_source_et_clair(db_session):
    from app.config import settings
    from app.models.entities import MemoryCard
    from app.services import memory_cards as service

    conv = Conversation(title='Source')
    db_session.add(conv)
    await db_session.commit()
    source = Message(conversation_id=conv.id, role='user', content='Préfère des phrases courtes.')
    db_session.add(source)
    await db_session.commit()
    fiche = await ajouter(service, conversation_id=conv.id, message_id=source.id,
                          content='SENTINELLE_R2_CHIFFREE_écriture')
    assert fiche['version'] == 1 and fiche['state'] == 'active'
    assert fiche['author'] == 'utilisateur'
    modifiee = await service.ecrire({'id': fiche['id'], 'version': 1, 'content': 'Texte corrigé.'})
    assert modifiee['version'] == 2 and modifiee['protected']
    with pytest.raises(service.RefusMemoire) as erreur:
        await service.ecrire({'id': fiche['id'], 'version': 1, 'content': 'Périmé.'})
    assert erreur.value.status == 409
    archivee = await service.ecrire({'id': fiche['id'], 'version': 2, 'state': 'archivee'})
    assert archivee['state'] == 'archivee'
    assert not await service.lire_pour_chat('phrases', 'global', None)
    for fichier in Path(settings.data_dir).rglob('*'):
        if fichier.is_file():
            assert b'SENTINELLE_R2_CHIFFREE' not in fichier.read_bytes(), fichier.name
    await db_session.delete(conv)
    await db_session.commit()
    async with service.get_session_context() as autre:
        ligne = await autre.get(MemoryCard, fiche['id'])
        assert ligne.conversation_id is None and ligne.message_id is None


@pytest.mark.asyncio
@pytest.mark.parametrize('cabinet', [False, True])
async def test_cloisons_et_liens_de_client(db_session, cabinet):
    from app.services import memory_cards as service
    from app.services.cloisonnement import poser_mode_cabinet

    a, b = Project(name='A'), Project(name='B')
    db_session.add_all([a, b])
    await db_session.commit()
    client = Contact(first_name='Client A', scope='project', scope_id=a.id)
    db_session.add(client)
    await db_session.commit()
    globale = await ajouter(service)
    fa = await ajouter(service, scope='project', scope_id=a.id, project_id=a.id)
    fb = await ajouter(service, scope='project', scope_id=b.id, project_id=b.id)
    liee = await ajouter(service, subject='façon client', contact_id=client.id)
    fait = await ajouter(service, kind='fait', subject='preuve cabinet', title='Orchidée', content='Orchidée globale.')
    conv = Conversation(title='Source dossier B', project_id=b.id)
    db_session.add(conv)
    await db_session.commit()
    source = Message(conversation_id=conv.id, role='user', content='autre')
    db_session.add(source)
    await db_session.commit()
    poser_mode_cabinet(cabinet)
    try:
        ids = lambda fiches: {f['id'] for f in fiches}
        assert ids(await service.lire_pour_chat('', 'global', None)) == {globale['id']} 
        assert ids(await service.lire_pour_chat('', 'project', b.id)) == {globale['id'], fb['id']}
        assert ids(await service.lire_pour_chat('', 'project', a.id)) == {globale['id'], fa['id'], liee['id']}
        assert ids(await service.lire_pour_chat('', 'all', None)) == {globale['id'], fa['id'], fb['id'], liee['id']}
        assert await service.lire_pour_chat('', 'inconnu', None) == []
        rappel = ids(await service.lire_pour_chat('orchidée', 'project', a.id))
        assert (fait['id'] in rappel) is (not cabinet)
        assert fait['id'] in ids(await service.lire_pour_chat('orchidée', 'global', None))
        with pytest.raises(service.RefusMemoire, match='hors du périmètre') as refus:
            await service.ecrire({'id': fa['id'], 'version': 1, 'content': 'autre'},
                automatique=True, scope='project', scope_id=b.id,
                conversation_id=conv.id, message_id=source.id)
        assert refus.value.status == 403
    finally:
        poser_mode_cabinet(None)


@pytest.mark.asyncio
@pytest.mark.parametrize('action', ['contact', 'anonymisation', 'projet', 'purge'])
async def test_portabilite_et_effacement(client, db_session, action):
    from app.models.entities import MemoryCard
    from app.services import memory_cards as service

    personne = Contact(first_name='Cliente factice')
    db_session.add(personne)
    await db_session.commit()
    projet = Project(name='Dossier factice', contact_id=personne.id)
    db_session.add(projet)
    await db_session.commit()
    fiche = await ajouter(service, contact_id=personne.id, project_id=projet.id,
                          scope='project', scope_id=projet.id)
    export = await client.get('/api/data/export')
    assert fiche['id'] in {f['id'] for f in export.json()['memory_cards']}
    export_contact = await client.get(f'/api/rgpd/export/{personne.id}')
    assert fiche['id'] in {f['id'] for f in export_contact.json()['memory_cards']}
    if action == 'contact':
        rep = await client.delete(f'/api/memory/contacts/{personne.id}')
    elif action == 'anonymisation':
        rep = await client.post(f'/api/rgpd/anonymize/{personne.id}', json={})
    elif action == 'projet':
        ensemble = await client.get(f'/api/memory/projects/{projet.id}/ensemble')
        assert ensemble.json()['memory_cards']['total'] == 1
        rep = await client.delete(f'/api/memory/projects/{projet.id}')
    else:
        rep = await client.delete('/api/data/all', params={'confirm': 'true'})
    assert rep.status_code == 200, rep.text
    async with service.get_session_context() as autre:
        assert not (await autre.execute(select(MemoryCard))).scalars().all()
    assert not await service.lire_pour_chat('phrases', 'all', None)


def test_revision_chiffree_idempotente_et_contraintes(tmp_path):
    import importlib.util
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from app.models.database import db_connect
    from sqlalchemy import create_engine
    from sqlalchemy.exc import IntegrityError
    from sqlmodel import SQLModel

    chemin = tmp_path / 'ancienne.db'
    moteur = create_engine('sqlite://', creator=lambda: db_connect(chemin))
    try:
        with moteur.begin() as connexion:
            SQLModel.metadata.create_all(connexion, tables=[t for n, t in SQLModel.metadata.tables.items()
                if n not in ('memory_cards', 'memory_card_uses')])
            chemin_revision = Path(__file__).resolve().parents[1] / 'src/backend/alembic/versions/d0e1f2a3b4c5_memory_cards.py'
            spec = importlib.util.spec_from_file_location('revision_r2', chemin_revision)
            revision = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(revision)
            with Operations.context(MigrationContext.configure(connexion)):
                revision.upgrade()
                revision.upgrade()
            noms = {c['name'] for c in __import__('sqlalchemy').inspect(connexion).get_columns('memory_cards')}
            assert noms == set(SQLModel.metadata.tables['memory_cards'].columns.keys())
            with pytest.raises(IntegrityError):
                connexion.exec_driver_sql("INSERT INTO memory_cards(id,kind) VALUES ('invalide','sante')")
    finally:
        moteur.dispose()


@pytest.mark.asyncio
async def test_sauvegarde_chiffree_restaure_les_fiches(client, db_session):
    from app.config import settings
    from app.services import memory_cards as service

    fiche = await ajouter(service, content='SENTINELLE_R2_SAUVEGARDE')
    sauvegarde = await client.post('/api/data/backup', json={'password': 'Phrase-factice-R2-2026'})
    assert sauvegarde.status_code == 200, sauvegarde.text
    nom = sauvegarde.json()['backup_name']
    for fichier in Path(settings.data_dir).rglob('*'):
        if fichier.is_file():
            assert b'SENTINELLE_R2_SAUVEGARDE' not in fichier.read_bytes(), fichier.name
    await service.effacer(fiche['id'], 1)
    assert not await service.lire_pour_chat('', 'global', None)
    rep = await client.post(f'/api/data/restore/{nom}?confirm=true', json={'password': 'Phrase-factice-R2-2026'})
    assert rep.status_code == 200, rep.text
    assert (await service.lire_pour_chat('', 'global', None))[0]['id'] == fiche['id']
