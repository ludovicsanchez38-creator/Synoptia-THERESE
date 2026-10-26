"""B-1142 : une frontière de champ ne prolonge pas une proposition."""
import pytest
from app.models.entities import Conversation, MemoryCard, MemoryCardUse, Message
from app.services import memory_cards as service
from sqlmodel import select


async def ecrire_decision(session, source, contenu, raison, ancienne=None):
    conv = Conversation(title="Décision")
    session.add(conv)
    await session.commit()
    donnees = {"kind": "decision", "subject": "decision", "title": "Décision",
               "content": contenu, "reason": raison}
    if ancienne:
        fiche = await service.ecrire(donnees | {"content": ancienne[0], "reason": ancienne[1]})
        stockee = await session.get(MemoryCard, fiche["id"])
        stockee.protected = False
        await session.commit()
        donnees |= {"id": fiche["id"], "version": fiche["version"]}
    message = Message(conversation_id=conv.id, role="user", content=source)
    session.add(message)
    await session.commit()
    fiche = await service.ecrire(donnees, automatique=True,
                                conversation_id=conv.id, message_id=message.id)
    assert fiche["content"] == contenu and fiche["reason"] == raison
    recus = (await session.execute(select(MemoryCardUse))).scalars().all()
    assert len(recus) == 1 and recus[0].card_id == fiche["id"]
    assert fiche["receipt"]["operation"] == ("modification" if ancienne else "creation")
    return fiche


@pytest.mark.parametrize("inverse", [False, True])
async def test_contenu_et_raison_ont_des_polarites_separees(db_session, inverse):
    contenu, raison = "Paul ne vient pas", "Paul travaille dimanche"
    if inverse:
        contenu, raison = raison, contenu
    await ecrire_decision(db_session, "Paul ne vient pas. Paul travaille dimanche.", contenu, raison)


@pytest.mark.parametrize("inverse", [False, True])
async def test_ancienne_fiche_garde_aussi_ses_frontieres(db_session, inverse):
    contenu, raison = "Paul ne vient pas", "Paul travaille dimanche"
    nouveau_contenu, nouvelle_raison = contenu, "Travail dimanche"
    if inverse:
        contenu, raison = raison, contenu
        nouveau_contenu, nouvelle_raison = nouvelle_raison, nouveau_contenu
    await ecrire_decision(db_session, "Travail dimanche", nouveau_contenu, nouvelle_raison,
                         ancienne=(contenu, raison))


# Dix entrées nouvelles, écrites après la séparation des champs.
@pytest.mark.parametrize("source,contenu,raison,ancienne,accepte", [
    ("Anna ne part plus. Anna garde la boutique.", "Anna ne part plus", "Anna garde la boutique", None, True),
    ("Boris ne livre jamais. Boris travaille ici.", "Boris ne livre jamais", "Boris travaille ici", None, True),
    ("Chloé téléphone. Chloé ne vient pas.", "Chloé téléphone", "Chloé ne vient pas", None, True),
    ("David ne répond pas. David ne vient plus.", "David ne répond pas", "David ne vient plus", None, True),
    ("Enzo vient. Enzo ne travaille jamais.", "Enzo vient", "Enzo ne travaille jamais", None, True),
    ("Travail samedi", "Fanny ne vient pas", "Travail samedi", ("Fanny ne vient pas", "Fanny travaille dimanche"), True),
    ("Travail mardi", "Gaby ne sort plus", "Travail mardi", ("Gaby ne sort plus", "Gaby travaille lundi"), True),
    ("Hélène vient. Hélène travaille lundi.", "Hélène ne vient pas", "Hélène travaille lundi", None, False),
    ("Ivan ne vient pas. Ivan travaille jeudi.", "Ivan vient", "Ivan travaille jeudi", None, False),
    ("Jade travaille lundi", "Jade vient", "Jade travaille lundi", ("Jade ne vient pas", "Jade travaille mardi"), False),
])
async def test_rejeu_astra_champs(db_session, source, contenu, raison, ancienne, accepte):
    if accepte:
        await ecrire_decision(db_session, source, contenu, raison, ancienne)
    else:
        with pytest.raises(service.RefusMemoire, match="uniquement une information"):
            await ecrire_decision(db_session, source, contenu, raison, ancienne)
        assert not (await db_session.execute(select(MemoryCardUse))).scalars().all()
        db_session.expire_all()
        fiches = (await db_session.execute(select(MemoryCard))).scalars().all()
        assert len(fiches) == int(ancienne is not None)
        if ancienne:
            assert (fiches[0].content, fiches[0].reason, fiches[0].version) == (*ancienne, 1)
