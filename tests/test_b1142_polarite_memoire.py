"""B-1142 : les faits d'une fiche gardent la polarité de leur source."""
import pytest
from app.models.entities import Conversation, MemoryCard, MemoryCardUse, Message
from app.services import memory_cards as service
from sqlmodel import select

from tests.test_c19_correction_fiche import appliquer_correction


async def creer(session, message, contenu):
    conversation = Conversation(title="Polarité")
    session.add(conversation)
    await session.commit()
    source = Message(conversation_id=conversation.id, role="user", content=message)
    session.add(source)
    await session.commit()
    return await service.ecrire(
        {"kind": "fait", "subject": "client", "title": "Client", "content": contenu},
        automatique=True, conversation_id=conversation.id, message_id=source.id,
    )


@pytest.mark.parametrize("message,contenu", [
    ("Le client veut le devis papier", "Le client ne veut pas le devis papier"),
    ("Le client veut le devis papier", "Le client ne veut plus le devis papier"),
    ("Le client ne veut pas le devis papier", "Le client veut le devis papier"),
    ("Le client ne veut plus le devis papier", "Le client veut le devis papier"),
    ("Le client ne veut jamais le devis papier", "Le client veut le devis papier"),
    ("Le client ne veut aucun devis papier", "Le client veut le devis papier"),
    ("Le client ne répond pas", "Le client répond"),
    ("Le client répond", "Le client ne répond pas"),
])
async def test_creation_refuse_une_polarite_inversee(db_session, message, contenu):
    with pytest.raises(service.RefusMemoire, match="uniquement une information"):
        await creer(db_session, message, contenu)
    assert not (await db_session.execute(select(MemoryCard))).scalars().all()
    assert not (await db_session.execute(select(MemoryCardUse))).scalars().all()


@pytest.mark.parametrize("negatif", [
    "Le client ne veut pas le devis papier", "Le client ne veut plus le devis papier",
    "Le client ne veut jamais le devis papier", "Le client ne veut aucun devis papier",
])
@pytest.mark.parametrize("ajout", [True, False])
async def test_correction_refuse_une_polarite_absente_du_message(db_session, negatif, ajout):
    positif = "Le client veut le devis papier"
    ancien, contenu = (positif, negatif) if ajout else (negatif, positif)
    with pytest.raises(service.RefusMemoire, match="uniquement une information"):
        await appliquer_correction(db_session, ancien, ancien, content=contenu)


@pytest.mark.parametrize("espace", [" ", "\u00a0", "\u202f", "\u2009"])
async def test_nombre_garde_sa_valeur_avec_une_autre_espace(db_session, espace):
    fiche = await creer(db_session, f"Le devis vaut 12{espace}345 euros", "Le devis vaut 12 345 euros")
    assert fiche["receipt"]["operation"] == "creation"


@pytest.mark.parametrize("contenu", ["Le devis vaut 345 12 euros", "Le devis vaut 12 346 euros"])
async def test_nombre_modifie_reste_refuse(db_session, contenu):
    with pytest.raises(service.RefusMemoire, match="uniquement une information"):
        await creer(db_session, "Le devis vaut 12\u202f345 euros", contenu)


# Entrées inventées après le correctif, distinctes des reproductions.
@pytest.mark.parametrize("message,contenu,accepte", [
    ("Nora accepte les chèques", "Nora n'accepte pas les chèques", False),
    ("Basile ne commande plus de cuivre", "Basile commande du cuivre", False),
    ("Inès ne livre jamais le samedi", "Inès livre le samedi", False),
    ("Aucun acompte requis", "Un acompte requis", False),
    ("Leila ne voyage pas", "Leila voyage", False),
    ("Oscar téléphone", "Oscar ne téléphone plus", False),
    ("Maya ne demande pas de remise", "Maya ne demande pas de remise", True),
    ("Le budget atteint 84\u2009500 euros", "Le budget atteint 84\u00a0500 euros", True),
    ("La réserve mesure -2\u202f750 litres", "La réserve mesure 2 750 litres", False),
    ("Le colis pèse 16,25 kilos", "Le colis pèse 25,16 kilos", False),
])
async def test_rejeu_apres_correctif(db_session, message, contenu, accepte):
    if accepte:
        assert (await creer(db_session, message, contenu))["receipt"]
    else:
        with pytest.raises(service.RefusMemoire, match="uniquement une information"):
            await creer(db_session, message, contenu)


@pytest.mark.parametrize("message", [
    "Le client veut de plus en plus de détails",
    "Le client veut plus de détails",
    "Le client veut des détails en plus",
    "Le client veut le plus de détails",
])
async def test_plus_affirmatif_ne_cree_pas_de_negation(db_session, message):
    fiche = await creer(db_session, message, "Le client veut des détails")
    assert fiche["receipt"]["operation"] == "creation"


# Dix entrées inventées après le correctif des comparatifs.
@pytest.mark.parametrize("message,contenu,accepte", [
    ("Aline veut de plus en plus de photos", "Aline veut des photos", True),
    ("Bruno demande plus de cartes", "Bruno demande des cartes", True),
    ("Célia commande des boîtes en plus", "Célia commande des boîtes", True),
    ("Dario veut le plus de plans", "Dario veut des plans", True),
    ("Elsa veut des plans de plus en plus précis", "Elsa veut des plans précis", True),
    ("Farid ne veut plus de photos", "Farid veut des photos", False),
    ("Gaëlle n'imprime plus de cartes", "Gaëlle imprime des cartes", False),
    ("Hugo ne téléphone plus", "Hugo téléphone", False),
    ("Ida veut plus de plans", "Ida ne veut plus de plans", False),
    ("Joël ne veut plus de détails", "Joël ne veut plus de détails", True),
])
async def test_rejeu_astra_plus(db_session, message, contenu, accepte):
    await test_rejeu_apres_correctif(db_session, message, contenu, accepte)
