"""B-1142 : sept inversions préexistantes et leurs témoins légitimes."""
import pytest
from app.models.entities import MemoryCard, MemoryCardUse
from app.services import memory_cards as service
from sqlmodel import select

from tests.test_b1142_polarite_memoire import creer
from tests.test_c19_correction_fiche import appliquer_correction

INVERSIONS = [
    ("Le client ne veut pas recevoir de devis papier", "Le client veut un devis papier"),
    ("Le client ne veut plus recevoir de devis papier", "Le client veut un devis papier"),
    ("Le client ne veut jamais recevoir de devis papier", "Le client veut un devis papier"),
    ("Le client ne veut aucun nouveau devis papier", "Le client veut un devis papier"),
    ("Le client ne répond pas, il préfère le courrier", "Le client répond"),
    ("Paul ne veut pas de devis. Luc veut un devis.", "Paul veut un devis. Luc ne veut pas de devis."),
    ("Le client veut un devis sans le moindre supplément", "Le client veut un devis avec supplément"),
]


@pytest.mark.parametrize("source,contenu", INVERSIONS)
async def test_inversions_astra_refusees_sans_fiche_ni_recu(db_session, source, contenu):
    with pytest.raises(service.RefusMemoire, match="uniquement une information"):
        await creer(db_session, source, contenu)
    assert not (await db_session.execute(select(MemoryCard))).scalars().all()
    assert not (await db_session.execute(select(MemoryCardUse))).scalars().all()


# Corpus légitime posé avant le correctif : mêmes objets, mais faits distincts.
@pytest.mark.parametrize("source,contenu", [
    ("Le client ne veut pas recevoir de devis papier. Le client classe le devis papier.", "Le client classe le devis papier"),
    ("Le client ne veut plus recevoir de devis papier. Le client archive le devis papier.", "Le client archive le devis papier"),
    ("Le client ne veut jamais recevoir de devis papier. Le client relit le devis papier.", "Le client relit le devis papier"),
    ("Le client ne veut aucun nouveau devis papier. Le client classe le devis papier.", "Le client classe le devis papier"),
    ("Paul ne répond pas, mais Luc répond.", "Luc répond"),
    ("Le client veut un devis sans le moindre supplément. Le supplément reste optionnel.", "Le supplément reste optionnel"),
    ("Le client veut un devis sans le moindre supplément", "Le client veut un devis"),
    ("Le client ne veut pas recevoir de devis papier", "Le client ne veut pas recevoir de devis papier"),
    ("Le client veut un devis sans le moindre supplément", "Le client veut un devis sans le moindre supplément"),
    ("Paul ne veut pas de devis. Luc veut un devis.", "Paul ne veut pas de devis. Luc veut un devis."),
])
async def test_faits_legitimes_restent_acceptes(db_session, source, contenu):
    assert (await creer(db_session, source, contenu))["receipt"]


@pytest.mark.parametrize("source,contenu", INVERSIONS[:4] + INVERSIONS[6:])
async def test_inversion_explicitement_corrigee_par_utilisateur(db_session, source, contenu):
    fiche = await appliquer_correction(db_session, source, contenu, content=contenu)
    assert fiche["receipt"]["operation"] == "modification"


# Dix entrées inventées après le correctif, dont des reprises partielles légitimes.
@pytest.mark.parametrize("source,contenu,accepte", [
    ("Ariane ne veut pas recevoir de catalogue papier", "Ariane veut un catalogue papier", False),
    ("Benoît ne veut plus recevoir de prospectus", "Benoît veut un prospectus", False),
    ("Cora ne veut jamais recevoir de courrier", "Cora veut du courrier", False),
    ("Denis ne veut aucun nouveau contrat", "Denis veut un contrat", False),
    ("Elsa veut une livraison sans le moindre supplément", "Elsa veut une livraison avec supplément", False),
    ("Farid ne répond pas, il voyage", "Farid répond", False),
    ("Gaëlle ne veut pas de remise. Hugo veut une remise.", "Gaëlle veut une remise. Hugo ne veut pas de remise.", False),
    ("Inès ne veut aucun nouveau dossier. Inès archive le dossier.", "Inès archive le dossier", True),
    ("Jules veut un devis sans le moindre supplément. Le supplément reste optionnel.", "Le supplément reste optionnel", True),
    ("Katia ne répond pas, mais Léo répond", "Léo répond", True),
])
async def test_rejeu_astra_inversions(db_session, source, contenu, accepte):
    if accepte:
        assert (await creer(db_session, source, contenu))["receipt"]
    else:
        await test_inversions_astra_refusees_sans_fiche_ni_recu(db_session, source, contenu)


@pytest.mark.parametrize("source,contenu", INVERSIONS)
async def test_correction_ne_peut_pas_inverser_la_source(db_session, source, contenu):
    with pytest.raises(service.RefusMemoire, match="uniquement une information"):
        await appliquer_correction(db_session, source, source, content=contenu)
    assert not (await db_session.execute(select(MemoryCardUse))).scalars().all()
    db_session.expire_all()
    fiche = (await db_session.execute(select(MemoryCard))).scalars().one()
    assert fiche.content == source and fiche.version == 1


async def test_source_recente_prime_sur_ancienne_affirmation(db_session):
    source = "Le client ne veut plus recevoir de devis papier"
    ancien = "Le client veut un devis papier"
    with pytest.raises(service.RefusMemoire, match="uniquement une information"):
        await appliquer_correction(db_session, ancien, source, content=ancien)
    assert not (await db_session.execute(select(MemoryCardUse))).scalars().all()
