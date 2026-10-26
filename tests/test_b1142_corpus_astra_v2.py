"""Phrases professionnelles légitimes, exercées par la véritable écriture mémoire."""
import pytest
from app.models.entities import MemoryCard, MemoryCardUse
from app.services import memory_cards as service
from sqlmodel import select

from tests.test_b1142_polarite_memoire import creer

CAS = [
    ('plus_01', 'Le client souhaite une offre plus détaillée', 'Le client souhaite une offre détaillée'),
    ('plus_02', 'La cliente demande un devis plus précis', 'La cliente demande un devis précis'),
    ('plus_03', 'Notre équipe recherche un outil plus simple', 'Notre équipe recherche un outil simple'),
    ('plus_04', 'Le service souhaite une réponse plus rapide', 'Le service souhaite une réponse rapide'),
    ('plus_05', 'Le client demande des délais plus courts', 'Le client demande des délais courts'),
    ('plus_06', 'Nadia veut des rapports plus lisibles', 'Nadia veut des rapports lisibles'),
    ('plus_07', 'Le client veut davantage de détails en plus', 'Le client veut des détails'),
    ('plus_08', 'La cliente veut de plus en plus de précisions', 'La cliente veut des précisions'),
    ('plus_09', 'Le service demande plus de brochures', 'Le service demande des brochures'),
    ('plus_10', 'Lina souhaite le plus de détails possible', 'Lina souhaite des détails'),
    ('sans_01', 'Le contrat est sans aucun doute valide', 'Le contrat est valide'),
    ('sans_02', 'Sophie transmet le contrat sans attendre', 'Sophie transmet le contrat'),
    ('sans_03', 'Sans attendre, Sophie transmet le contrat', 'Sophie transmet le contrat sans attendre'),
    ('sans_04', 'Marc transmet les pièces sans tarder', 'Marc transmet les pièces'),
    ('sans_05', 'Le service accepte sans réserve le devis', 'Le service accepte le devis sans réserve'),
    ('sans_06', 'Les dossiers sont tous archivés sans exception', 'Les dossiers sont tous archivés'),
    ('sans_07', 'Le règlement sera transmis sans délai', 'Le règlement sera transmis'),
    ('sans_08', 'Camille valide sans hésiter la proposition', 'Camille valide la proposition sans hésiter'),
    ('sans_09', 'Le client répond sans faute lundi', 'Le client répond lundi'),
    ('sans_10', 'La responsable valide le budget sans aucun doute', 'La responsable valide le budget'),
    ('citation_01', 'Le guide cite « jamais » dans la rubrique sécurité', 'Le guide cite « jamais »'),
    ('citation_02', 'La cliente écrit « jamais » dans sa réponse', 'La cliente écrit « jamais »'),
    ('citation_03', 'La charte contient le mot « jamais »', 'La charte contient le mot « jamais »'),
    ('citation_04', 'Le titre du document est « Jamais sans accord »', 'Le titre du document est « Jamais sans accord »'),
    ('citation_05', 'Le manuel précise « Ne jamais transmettre les tarifs »', 'Le manuel précise « Ne jamais transmettre les tarifs »'),
    ('citation_06', 'Le guide cite « jamais » dans la rubrique sécurité', 'Dans la rubrique sécurité, le guide cite « jamais »'),
    ('citation_07', 'Le client utilise « jamais » pour qualifier ce délai', 'Le client utilise « jamais »'),
    ('citation_08', 'La mention « sans engagement » figure sur le devis', 'La mention « sans engagement » figure sur le devis'),
    ('citation_09', 'Le document porte le titre « Un pas vers demain »', 'Le document porte le titre « Un pas vers demain »'),
    ('citation_10', 'La consigne est « Ne jamais partager le dossier »', 'La consigne est « Ne jamais partager le dossier »'),
    ('negation_01', 'Le client ne travaille pas le dimanche', 'Le dimanche, le client ne travaille pas'),
    ('negation_02', 'Nadia ne répond jamais le samedi', 'Le samedi, Nadia ne répond jamais'),
    ('negation_03', 'Le client ne veut pas recevoir de devis papier', 'Le client ne veut pas de devis papier'),
    ('negation_04', 'Le service ne veut plus recevoir de catalogue', 'Le service ne veut plus de catalogue'),
    ('negation_05', 'La cliente ne veut jamais recevoir de courrier papier', 'La cliente ne veut jamais de courrier papier'),
    ('negation_06', 'Paul ne voyage pas en décembre', 'En décembre, Paul ne voyage pas'),
    ('negation_07', 'Aucun acompte ne sera demandé', 'Aucun acompte ne sera demandé'),
    ('negation_08', 'La prestation ne comprend pas le transport', 'La prestation ne comprend pas le transport'),
    ('negation_09', 'La cliente ne commande plus de brochures', 'La cliente ne commande plus de brochures'),
    ('negation_10', 'Le client ne livre jamais le lundi', 'Le client ne livre jamais le lundi'),
    ('reformulation_01', 'Le client ne répond pas. Le client répond uniquement par courrier.', 'Le client répond uniquement par courrier'),
    ('reformulation_02', 'Luc ne valide pas le devis. Léa valide le devis.', 'Léa valide le devis'),
    ('reformulation_03', 'Paul ne facture pas le transport. Luc facture le transport.', 'Luc facture le transport'),
    ('reformulation_04', 'Le client ne souhaite pas de facture papier. Le service archive la facture papier.', 'Le service archive la facture papier'),
    ('reformulation_05', 'Nadia ne travaille pas dimanche. Nadia travaille lundi.', 'Nadia travaille lundi'),
    ('reformulation_06', 'Le client ne veut pas de supplément. Le supplément reste optionnel.', 'Le supplément reste optionnel'),
    ('reformulation_07', 'La réunion est prévue mardi à Lyon', 'La réunion est prévue à Lyon mardi'),
    ('reformulation_08', 'Le devis de Zoé atteint 12\u202f500 euros', 'Le devis de Zoé atteint 12 500 euros'),
    ('reformulation_09', 'Élodie valide le budget. Le budget concerne le projet Rhône.', 'Élodie valide le budget'),
    ('reformulation_10', 'Le délai est fixé à quinze jours', 'Le délai est fixé à quinze jours'),
    ('ordinaire_01', 'Le rendez-vous est confirmé vendredi', 'Le rendez-vous est confirmé vendredi'),
    ('ordinaire_02', 'La facture est payable à trente jours', 'La facture est payable à trente jours'),
    ('ordinaire_03', 'Le contact préfère les échanges par courriel', 'Le contact préfère les échanges par courriel'),
    ('ordinaire_04', 'La livraison est prévue à Grenoble', 'La livraison est prévue à Grenoble'),
    ('ordinaire_05', 'La réunion commence à neuf heures', 'La réunion commence à neuf heures'),
    ('ordinaire_06', 'Le budget prévu atteint 7 200 euros', 'Le budget prévu atteint 7\u00a0200 euros'),
    ('ordinaire_07', 'Le devis comprend la pose et le transport', 'Le devis comprend la pose et le transport'),
    ('ordinaire_08', 'Amélie prépare le dossier de clôture', 'Amélie prépare le dossier de clôture'),
    ('ordinaire_09', 'Le client souhaite une présentation en français', 'Le client souhaite une présentation en français'),
    ('ordinaire_10', 'La décision est reportée au prochain comité', 'La décision est reportée au prochain comité'),
]

@pytest.mark.parametrize('identifiant,source,contenu', CAS, ids=[c[0] for c in CAS])
async def test_fiche_legitime_acceptee(db_session, identifiant, source, contenu):
    try:
        fiche = await creer(db_session, source, contenu)
    except service.RefusMemoire as exc:
        assert not (await db_session.execute(select(MemoryCard))).scalars().all()
        assert not (await db_session.execute(select(MemoryCardUse))).scalars().all()
        pytest.fail(f'{identifiant}: {source!r} -> {contenu!r}: {exc}; détail={exc.detail}')
    assert fiche['receipt']['operation'] == 'creation'
    assert (await db_session.execute(select(MemoryCard))).scalars().one().content == contenu
    assert len((await db_session.execute(select(MemoryCardUse))).scalars().all()) == 1
