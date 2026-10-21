"""R2-2 : corpus fictif et refus déterministes, sans fournisseur."""
import asyncio
import json

import pytest
from app.models.entities import Conversation, Message, Project
from app.services import memory_cards as service

# Corpus local v1 : aucune donnée réelle.
SENSIBLES = [
    'Mon mot de passe est Factice!2026', 'password = Factice!2026',
    'api_key = fausse', 'sk-test-0123456789abcdefghijklmnop',
    'Bearer jetonFictif0123456789012345', 'ghp_0123456789abcdefghijklmnopqrstuv',
    '4111 1111 1111 1111', 'FR76 3000 6000 0112 3456 7890 189',
    'Il souffre de diabète', 'Rendez-vous oncologue chaque semaine',
    'Son origine ethnique est fictive', 'Née de parents de race fictive',
    'Il vote pour le parti fictif', 'Il colle des affiches électorales pour ce parti',
    'Sa religion est fictive', 'Elle prie chaque dimanche à la messe',
    'Il est syndiqué', 'Elle cotise à la CGT',
    'Son profil génétique est fictif', 'Son ADN porte cette mutation',
    'Son empreinte biométrique identifie le client', 'Reconnaissance faciale du client',
    'Son orientation sexuelle est fictive', 'Il vit une relation homosexuelle',
    'Convictions philosophiques du client', 'Il adhère à une école de pensée philosophique',
    'ｍｏｔ ｄｅ ｐａｓｓｅ Factice!2026', 'c\u200blé A\u200bPI fausse',
    'mot-de-passe fictif', 'IBAN : F R 7 6 3 0 0 0 6 0 0 0 0 1 1 2 3 4 5 6 7 8 9 0 1 8 9',
]
ADMISSIBLES = ['SIRET 12345678901234', 'Demande un acompte de 30 %.',
               'Délai de paiement de 30 jours.', 'Préfère des phrases courtes.']


def donnees(**kwargs):
    return {'kind': 'preference', 'subject': 'rédaction', 'title': 'Rédaction',
            'content': 'Préfère des phrases courtes.'} | kwargs


async def source(db_session, contenu='Préfère des phrases courtes.', projet=None):
    conv = Conversation(title='Source factice', project_id=projet)
    db_session.add(conv)
    await db_session.commit()
    msg = Message(conversation_id=conv.id, role='user', content=contenu)
    db_session.add(msg)
    await db_session.commit()
    return {'automatique': True, 'conversation_id': conv.id, 'message_id': msg.id,
            'scope': 'project' if projet else 'global', 'scope_id': projet}


@pytest.mark.asyncio
async def test_corpus_creation_edition_sur_les_trois_champs(db_session):
    for champ in ('title', 'content', 'reason'):
        for valeur in SENSIBLES:
            with pytest.raises(service.RefusMemoire) as refus:
                await service.ecrire(donnees(**{champ: valeur}))
            assert valeur not in str(refus.value)
    for index, valeur in enumerate(ADMISSIBLES):
        fiche = await service.ecrire(donnees(subject=f'admissible {index}', content=valeur))
        for champ in ('title', 'content', 'reason'):
            for sensible in SENSIBLES:
                with pytest.raises(service.RefusMemoire):
                    await service.ecrire({'id': fiche['id'], 'version': fiche['version'], champ: sensible})


@pytest.mark.asyncio
async def test_correction_et_paraphrases_independantes_du_type(db_session):
    origine = await source(db_session)
    fiche = await service.ecrire(donnees(), **origine)
    corrigee = await service.ecrire({'id': fiche['id'], 'version': 1, 'content': 'Préfère les listes.'})
    assert corrigee['protected']
    for valeurs in [donnees(subject='paraphrase'), donnees(kind='fait', subject='autre titre'),
                    {'id': fiche['id'], 'version': 2, 'content': 'Préfère des phrases courtes.'}]:
        with pytest.raises(service.RefusMemoire) as refus:
            await service.ecrire(valeurs, **origine)
        assert refus.value.card_id == fiche['id']
    await service.rendre_la_main(fiche['id'], 2)
    nouveau = await source(db_session, 'Préfère des phrases courtes et simples.')
    suite = await service.ecrire({'id': fiche['id'], 'version': 3, 'content': 'Préfère des phrases courtes et simples.'}, **nouveau)
    assert suite['protected']  # même type preference, mise à jour chat protégée


@pytest.mark.asyncio
async def test_correction_chat_de_fait_et_rejeu_efface(db_session):
    origine = await source(db_session, 'En fait, corrige : délai de paiement de 30 jours.')
    fiche = await service.ecrire(donnees(kind='fait', content='Délai de paiement de 30 jours.'), **origine)
    assert fiche['protected']
    rejouee = await service.ecrire(donnees(kind='fait', content='Délai de paiement de 30 jours.'), **origine)
    assert rejouee['id'] == fiche['id']
    await service.effacer(fiche['id'], 1)
    with pytest.raises(service.RefusMemoire):
        await service.ecrire(donnees(kind='fait', content='Délai de paiement de 30 jours.'), **origine)
    with pytest.raises(service.RefusMemoire):
        await service.ecrire(donnees(subject='reformulation', content='Paiement de 30 jours.'), **origine)
    assert not await service.lire_pour_chat('paiement', 'global', None)


@pytest.mark.asyncio
async def test_matrice_recouvrement_global_a_b(db_session):
    a, b = Project(name='A'), Project(name='B')
    db_session.add_all([a, b])
    await db_session.commit()
    origine_a = await source(db_session, projet=a.id)
    origine_b = await source(db_session, projet=b.id)
    globale = await service.ecrire(donnees(kind='correction'))
    for origine in (origine_a, origine_b):
        with pytest.raises(service.RefusMemoire):
            await service.ecrire(donnees(subject='autre'), **origine)
    await service.effacer(globale['id'], 1)
    protegee_a = await service.ecrire(donnees(kind='correction', scope='project', scope_id=a.id, project_id=a.id))
    with pytest.raises(service.RefusMemoire):
        await service.ecrire(donnees(subject='autre'), **origine_a)
    fiche_b = await service.ecrire(donnees(subject='autre'), **origine_b)
    assert fiche_b['scope_id'] == b.id
    origine_globale = await source(db_session)
    with pytest.raises(service.RefusMemoire):
        await service.ecrire(donnees(subject='sans liens'), **origine_globale)
    assert protegee_a['protected']


@pytest.mark.asyncio
async def test_suspension_et_concurrence_versions(db_session):
    from app.services.memory_tools import creations_du_chat_suspendues
    async with creations_du_chat_suspendues():
        with pytest.raises(service.RefusMemoire):
            await service.ecrire(donnees())
    fiche = await service.ecrire(donnees())
    resultats = await asyncio.gather(*[
        service.ecrire({'id': fiche['id'], 'version': 1, 'content': contenu})
        for contenu in ('Version A', 'Version B')], return_exceptions=True)
    assert sum(isinstance(r, service.RefusMemoire) for r in resultats) == 1
    assert sum(isinstance(r, dict) for r in resultats) == 1


def test_noms_communs_de_secrets_et_valeurs_isolees_du_corpus():
    from app.services.memory_card_security import contient_sensible
    for valeur in ['crm_access_token', 'smtp_passwd', 'AKIAABCDEFGHIJKLMNOP',
                    'AIzaFauxJetonSansValeurDeVingtCaracteres',
                    'eyJfauxheader.abcdefghijklmno.abcdefghijklmnop']:
        assert contient_sensible(valeur)
    assert not contient_sensible('SIRET fictif 12345678901237')
