"""Corpus lexical v1 : mots exacts, accents ; pas de lemmatisation implicite."""
import pytest
from app.models.entities import Project
from app.services import memory_cards as service


@pytest.mark.asyncio
async def test_corpus_ids_attendus_sans_resultat_interdit(db_session):
    a, b = Project(name='A'), Project(name='B')
    db_session.add_all([a, b])
    await db_session.commit()
    async def fiche(sujet, titre, contenu, **kw):
        return (await service.ecrire({'kind': 'fait', 'subject': sujet, 'title': titre, 'content': contenu} | kw))['id']
    ecole = await fiche('ecole', 'Devis ÉCOLE', 'Acompte convenu pour cette école.')
    delai = await fiche('delai', 'Paiement', 'Délai de paiement de trente jours.')
    dossier_a = await fiche('client', 'Homonyme école', 'Fait dossier A', scope='project', scope_id=a.id, project_id=a.id)
    dossier_b = await fiche('client', 'Homonyme école', 'Fait dossier B', scope='project', scope_id=b.id, project_id=b.id)
    corpus = [
        ('école', 'global', None, {ecole}), ('ＥＣＯＬＥ', 'global', None, {ecole}),
        ('delai', 'global', None, {delai}), ('écoles', 'global', None, set()),
        ('inconnu', 'global', None, set()), ('les des pour', 'global', None, set()),
        ('école', 'project', a.id, {ecole, dossier_a}),
        ('école', 'all', None, {ecole, dossier_a, dossier_b}),
        ('école', 'erreur', None, set()),
    ]
    for requete, scope, scope_id, attendus in corpus:
        assert {f['id'] for f in await service.lire_pour_chat(requete, scope, scope_id)} == attendus
