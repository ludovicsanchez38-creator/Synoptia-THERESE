"""Complément : extraction fidèle via l'outil natif, bornes et annulation."""
import pytest
from app.models.entities import Conversation, MemoryCard, MemoryCardUse, Message
from app.services import memory_card_tools as outil
from sqlmodel import select

CAS = [
    ('comparatif_apres_negation', 'Le client ne veut pas de papier, mais souhaite plus de documents numériques.', 'Le client souhaite plus de documents numériques'),
    ('comparatif_reordonne', 'Élodie demande un devis plus précis pour lundi', 'Pour lundi, Élodie demande un devis plus précis'),
    ('sans_expression', 'Sans hésiter, Camille valide le devis', 'Camille valide le devis sans hésiter'),
    ('jamais_cite', 'Le guide cite « jamais » dans la rubrique sécurité', 'Le guide cite « jamais »'),
    ('negation_reformulee', 'Le client ne travaille pas le dimanche', 'Le dimanche, le client ne travaille pas'),
    ('fait_distinct', 'Luc ne valide pas le devis. Léa valide le devis.', 'Léa valide le devis'),
]

async def appeler(session, source, contenu, **kwargs):
    conversation = Conversation(title='Suivi professionnel')
    session.add(conversation)
    await session.commit()
    session.add(Message(conversation_id=conversation.id, role='user', content=source))
    await session.commit()
    return await outil.executer_outil({'kind':'fait','subject':'client','title':'Client','content':contenu}, scope='global', scope_id=None, conversation_id=conversation.id, **kwargs)

@pytest.mark.parametrize('nom,source,contenu', CAS, ids=[c[0] for c in CAS])
async def test_outil_natif_accepte_la_fiche_legitime(db_session, nom, source, contenu):
    resultat = await appeler(db_session, source, contenu)
    assert resultat.get('success'), resultat
    assert resultat.get('receipt')
    assert (await db_session.execute(select(MemoryCard))).scalars().one().content == contenu

@pytest.mark.parametrize('nom,source,contenu', [
    ('vide', '', ''),
    ('contenu_trop_long', 'Le dossier est prêt. ' * 100, 'Le dossier est prêt. ' * 100),
])
async def test_bornes_refusees_sans_ecriture(db_session, nom, source, contenu):
    resultat = await appeler(db_session, source, contenu)
    assert not resultat['success']
    assert not (await db_session.execute(select(MemoryCard))).scalars().all()
    assert not (await db_session.execute(select(MemoryCardUse))).scalars().all()

async def test_annulation_sans_ecriture(db_session):
    class Annulation:
        def annulation_observee(self):
            return True
    resultat = await appeler(db_session, 'Le devis est accepté', 'Le devis est accepté', contexte=Annulation())
    assert not resultat['success']
    assert not (await db_session.execute(select(MemoryCard))).scalars().all()
    assert not (await db_session.execute(select(MemoryCardUse))).scalars().all()

async def test_message_long_fiche_courte_sans_invention(db_session):
    source = 'La réunion est confirmée. ' * 4000
    resultat = await appeler(db_session, source, 'La réunion est confirmée')
    assert resultat['success'] and resultat['receipt']


@pytest.mark.parametrize('inverse', [False, True])
@pytest.mark.parametrize('correction', [False, True])
async def test_reformulation_negative_avec_raison_affirmative(db_session, inverse, correction):
    from tests.test_b1142_polarite_champs import ecrire_decision

    contenu, raison = 'Le dimanche, le client ne travaille pas', 'Le suivi reste disponible'
    ancien = ('Le client ne travaille pas le dimanche', raison)
    if inverse:
        contenu, raison = raison, contenu
        ancien = ancien[::-1]
    await ecrire_decision(
        db_session, 'Le client ne travaille pas le dimanche. Le suivi reste disponible.',
        contenu, raison, ancienne=ancien if correction else None,
    )
