"""R3-1 : sélection et ordre prouvés sur le payload du routeur de chat."""
import json
from datetime import UTC, datetime, timedelta

import pytest
from app.models.entities import Contact, Conversation, MemoryCard, Message, Project
from app.services import memory_cards

from tests.test_r2_3_outil import fournisseur  # noqa: F401


@pytest.mark.asyncio
@pytest.mark.parametrize('kind', ['fait', 'decision'])
async def test_liens_mots_avant_dernier_message_date_et_uuid(client, db_session, fournisseur, kind):
    a, b = Project(name='Dossier A'), Project(name='Dossier B')
    db_session.add_all([a, b])
    await db_session.commit()
    personne = Contact(first_name='Cliente', scope='project', scope_id=a.id)
    autre = Contact(first_name='Autre', scope='project', scope_id=b.id)
    conv = Conversation(title='Conversation neuve', project_id=a.id)
    db_session.add_all([personne, autre, conv])
    await db_session.commit()
    db_session.add(Message(conversation_id=conv.id, role='user', content='Parlons zéphyr.'))
    db_session.add(Message(conversation_id=conv.id, role='assistant', content='Entendu.'))
    await db_session.commit()
    async def fiche(sujet, **liens):
        return await memory_cards.ecrire({'kind': kind, 'subject': sujet, 'title': sujet,
            'content': 'Accord annuel.', 'reason': 'Validation commune.' if kind == 'decision' else '', **liens})
    contact = await fiche('contact', contact_id=personne.id)
    portee = await fiche('portée', scope='project', scope_id=a.id)  # écriture sans project_id
    projet = await fiche('projet', project_id=a.id)
    mots = await fiche('zéphyr')
    interdit = await fiche('zéphyr interdit', contact_id=autre.id)
    sans_lien = await fiche('invisible')
    date = datetime(2026, 10, 21, tzinfo=UTC)
    for f in (contact, portee, projet, mots):
        ligne = await db_session.get(MemoryCard, f['id'])
        ligne.updated_at = date + (timedelta(seconds=1) if f == contact else timedelta())
        db_session.add(ligne)
    await db_session.commit()
    reponse = await client.post('/api/chat/send', json={'conversation_id': conv.id,
        'message': 'Bonjour', 'stream': True})
    assert reponse.status_code == 200
    systeme = fournisseur[2][-1]['system']
    for f in (contact, portee, projet, mots):
        assert f['id'] in systeme, (f['title'], reponse.text)
    for f in (interdit, sans_lien):
        assert f['id'] not in systeme
    # Liens avant mots seuls ; date décroissante, puis UUID croissant à égalité.
    ordre = [contact['id'], *sorted([portee['id'], projet['id']]), mots['id']]
    assert sorted(ordre, key=systeme.index) == ordre
    # Le mot n'est pas dans la dernière demande utilisateur du payload.
    derniers = [m for m in fournisseur[2][-1]['messages'] if m['role'] == 'user']
    assert derniers[-1]['content'] == 'Bonjour'
    assert 'zéphyr' in json.dumps(derniers[:-1], ensure_ascii=False)
