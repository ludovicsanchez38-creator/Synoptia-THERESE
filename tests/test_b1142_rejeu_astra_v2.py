"""Trente entrées inventées après le premier vert de la reprise Astra v2."""
import pytest
from app.models.entities import MemoryCard, MemoryCardUse
from app.services import memory_cards as service
from sqlmodel import select

from tests.test_b1142_polarite_memoire import creer


@pytest.mark.parametrize('source,contenu,accepte', [
    ('Anaïs demande une réponse plus précise', 'Anaïs demande une réponse précise', True),
    ('Brice ne commande pas de papier, mais souhaite plus de cartes numériques', 'Brice souhaite plus de cartes numériques', True),
    ('Clément ne souhaite pas une offre plus chère', 'Clément ne souhaite pas une offre chère', True),
    ('Dina ne veut plus de papier, mais veut plus de fichiers', 'Dina veut plus de fichiers', True),
    ('Élise veut un devis plus détaillé lundi', 'Lundi, Élise veut un devis détaillé', True),
    ('Farah souhaite des plans plus lisibles', 'Farah souhaite des plans lisibles', True),
    ('Gaëtan ne souhaite pas de courrier et demande plus de plans', 'Gaëtan demande plus de plans', True),
    ('Hélène ne reçoit plus de prospectus', 'Hélène reçoit des prospectus', False),
    ('Iris réclame plus de photos', 'Iris ne réclame plus de photos', False),
    ('Joachim ne répond plus', 'Joachim répond', False),
])
async def test_dix_comparatifs_apres_correctif(db_session, source, contenu, accepte):
    await verifier(db_session, source, contenu, accepte)


@pytest.mark.parametrize('source,contenu,accepte', [
    ('Karim ne travaille pas le mardi', 'Le mardi, Karim ne travaille pas', True),
    ('Louise ne voyage jamais en février', 'En février, Louise ne voyage jamais', True),
    ('Malik ne veut pas recevoir de brochure', 'Malik ne veut pas de brochure', True),
    ('Nina ne veut plus recevoir de courrier', 'Nina ne veut plus de courrier', True),
    ('Omar ne veut jamais recevoir de facture papier', 'Omar ne veut jamais de facture papier', True),
    ('Le lexique cite “jamais” dans son introduction', 'Le lexique cite “jamais”', True),
    ('La notice cite « plus » dans le chapitre annexe', 'La notice cite « plus »', True),
    ('Le manuel cite "sans" dans le chapitre annexe', 'Le manuel cite "sans"', True),
    ('Le guide cite “jamais”. Pascal répond lundi.', 'Pascal ne répond jamais lundi', False),
    ('Quentin ne travaille pas le vendredi', 'Quentin travaille le vendredi', False),
])
async def test_dix_reformulations_et_citations_apres_correctif(db_session, source, contenu, accepte):
    await verifier(db_session, source, contenu, accepte)


@pytest.mark.parametrize('source,contenu,accepte', [
    ('Rania ne signe pas le contrat. Sofiane signe le contrat.', 'Sofiane signe le contrat', True),
    ('Tom ne livre jamais les colis. Uma livre les colis.', 'Uma livre les colis', True),
    ('Véra ne prépare plus le bilan. William prépare le bilan.', 'William prépare le bilan', True),
    ('Xavier ne facture pas les déplacements; Yasmina facture les déplacements.', 'Yasmina facture les déplacements', True),
    ('Zoé ne répond pas, mais Abel répond.', 'Abel répond', True),
    ('Béa ne réclame pas de facture. Le service archive la facture.', 'Le service archive la facture', True),
    ('Côme ne travaille pas dimanche. Côme travaille mardi.', 'Côme travaille mardi', True),
    ('Daphné ne veut pas de supplément. Le supplément reste facultatif.', 'Le supplément reste facultatif', True),
    ('Étienne ne valide pas le devis. Fatou valide le devis.', 'Étienne valide le devis. Fatou ne valide pas le devis.', False),
    ('Gilles ne veut pas recevoir de dossier. Hana classe le dossier.', 'Gilles veut un dossier', False),
])
async def test_dix_sujets_apres_correctif(db_session, source, contenu, accepte):
    await verifier(db_session, source, contenu, accepte)


async def verifier(session, source, contenu, accepte):
    if accepte:
        fiche = await creer(session, source, contenu)
        assert fiche['receipt']['operation'] == 'creation'
        assert (await session.execute(select(MemoryCard))).scalars().one().content == contenu
        assert len((await session.execute(select(MemoryCardUse))).scalars().all()) == 1
    else:
        with pytest.raises(service.RefusMemoire, match='uniquement une information'):
            await creer(session, source, contenu)
        assert not (await session.execute(select(MemoryCard))).scalars().all()
        assert not (await session.execute(select(MemoryCardUse))).scalars().all()
