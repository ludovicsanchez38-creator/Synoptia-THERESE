"""B-1104 (suite) et B-1114 : une correction de fiche par le chat aboutit.

Relance instrumentée du 23/10 (Sonnet 5.5, arguments lus dans les réponses de
l'API) : Sonnet ajoutait à la raison des mots absents des deux sources
(« Correction donnée par Camille », « et non plus Verzanma »). Le refus ne
disait pas lesquels, et trois essais échouaient de la même façon. Un autre
passage créait une seconde fiche `correction` sans id : l'ancienne scierie
restait active à côté de la nouvelle.
"""
import json

import pytest
from app.models.entities import Conversation, MemoryCard, Message
from app.services import memory_card_tools

MESSAGE = "Retiens ceci pour la suite : pour le chantier Sacducbi, le bois vient de la scierie Verzanma, et la livraison se fait toujours le lundi."
CORRECTION = "Correction pour le chantier Sacducbi : le bois viendra désormais de la scierie Louvelset. Mets ta mémoire à jour."
FICHE = {"kind": "fait", "subject": "Chantier Sacducbi", "title": "Chantier Sacducbi : approvisionnement bois et livraison",
         "content": "Pour le chantier Sacducbi, le bois vient de la scierie Verzanma. La livraison se fait toujours le lundi."}


async def _fiche_puis_correction(db_session):
    conv = Conversation(title="Sacducbi")
    db_session.add(conv)
    await db_session.commit()
    db_session.add(Message(conversation_id=conv.id, role="user", content=MESSAGE))
    await db_session.commit()
    creation = await memory_card_tools.executer_outil(dict(FICHE), scope="global", scope_id=None, conversation_id=conv.id)
    assert creation["success"], creation
    db_session.add(Message(conversation_id=conv.id, role="user", content=CORRECTION))
    await db_session.commit()
    return conv.id, creation["receipt"]["id"]


async def _corriger(conversation_id, fiche_id, **champs):
    return await memory_card_tools.executer_outil(
        {"id": fiche_id, "version": 1, "kind": "correction", "subject": "Chantier Sacducbi", **champs},
        scope="global", scope_id=None, conversation_id=conversation_id)


async def test_le_refus_nomme_les_mots_sans_source_pour_le_modele(db_session):
    conv, fiche = await _fiche_puis_correction(db_session)
    refus = await _corriger(conv, fiche, title="Chantier Sacducbi : approvisionnement bois",
                            content="Pour le chantier Sacducbi, le bois viendra désormais de la scierie Louvelset.",
                            reason="Correction donnée par Camille.")
    assert not refus["success"]
    # Le message affiché reste le même d'un essai à l'autre (une seule bulle) ;
    # le détail, lu par le modèle dans le résultat de l'outil, dit quoi retirer.
    assert refus["message"] == "Cette fiche doit reprendre uniquement une information donnée dans ton message."
    assert "« Camille »" in refus["detail"] and "« donnée »" in refus["detail"]
    assert "Louvelset" not in refus["detail"]
    assert json.loads(memory_card_tools.texte_resultat(refus))["detail"] == refus["detail"]


async def test_le_refus_nomme_une_negation_ajoutee(db_session):
    conv, fiche = await _fiche_puis_correction(db_session)
    refus = await _corriger(conv, fiche, title="Chantier Sacducbi",
                            content="Pour le chantier Sacducbi, le bois vient désormais de la scierie Louvelset "
                                    "(et non plus Verzanma). La livraison se fait toujours le lundi.")
    assert not refus["success"]
    assert "« non »" in refus["detail"]
    assert "« plus Verzanma »" in refus["detail"]


async def test_le_nombre_sans_source_est_nomme(db_session):
    conv, fiche = await _fiche_puis_correction(db_session)
    refus = await _corriger(conv, fiche, title="Chantier Sacducbi",
                            content="Pour le chantier Sacducbi, le bois viendra désormais de la scierie Louvelset, 12 palettes.")
    assert not refus["success"]
    assert "« 12 »" in refus["detail"] and "« palettes »" in refus["detail"]


async def test_le_detail_reste_borne(db_session):
    conv, fiche = await _fiche_puis_correction(db_session)
    refus = await _corriger(conv, fiche, title="Chantier Sacducbi",
                            content="Louvelset " + " ".join(f"mot{i}inventé" for i in range(30)))
    assert not refus["success"]
    assert refus["detail"].count("«") == 8
    assert "»…" in refus["detail"]


async def test_l_essai_suivant_sans_les_mots_nommes_aboutit(db_session):
    conv, fiche = await _fiche_puis_correction(db_session)
    refus = await _corriger(conv, fiche, title="Chantier Sacducbi : approvisionnement bois et livraison",
                            content="Pour le chantier Sacducbi, le bois vient désormais de la scierie Louvelset "
                                    "(et non plus Verzanma). La livraison se fait toujours le lundi.",
                            reason="Correction donnée par Camille : changement de scierie pour le chantier Sacducbi.")
    assert not refus["success"]
    reussite = await _corriger(conv, fiche, title="Chantier Sacducbi : approvisionnement bois et livraison",
                               content="Pour le chantier Sacducbi, le bois vient désormais de la scierie Louvelset. "
                                       "La livraison se fait toujours le lundi.")
    assert reussite["success"], reussite
    stockee = await db_session.get(MemoryCard, fiche)
    await db_session.refresh(stockee)
    assert "Louvelset" in stockee.content and "Verzanma" not in stockee.content and stockee.version == 2


async def test_correction_sans_id_sur_un_sujet_couvert_renvoie_a_la_fiche(db_session):
    conv, fiche = await _fiche_puis_correction(db_session)
    refus = await memory_card_tools.executer_outil(
        {"kind": "correction", "subject": "chantier sacducbi", "title": "Sacducbi : scierie Louvelset",
         "content": "Pour le chantier Sacducbi, le bois viendra désormais de la scierie Louvelset."},
        scope="global", scope_id=None, conversation_id=conv)
    assert not refus["success"]
    assert refus["card_id"] == fiche
    assert fiche in refus["detail"] and "version 1" in refus["detail"]
    from sqlmodel import col, select
    actives = (await db_session.execute(select(MemoryCard).where(col(MemoryCard.state) == "active"))).scalars().all()
    assert [f.id for f in actives] == [fiche]


async def test_correction_sans_id_sur_un_sujet_nouveau_est_creee(db_session):
    conv, _ = await _fiche_puis_correction(db_session)
    db_session.add(Message(conversation_id=conv, role="user",
                           content="Correction pour le chantier Louvelset : la grue arrive désormais le mardi."))
    await db_session.commit()
    resultat = await memory_card_tools.executer_outil(
        {"kind": "correction", "subject": "Chantier Louvelset", "title": "Chantier Louvelset : grue",
         "content": "Pour le chantier Louvelset, la grue arrive désormais le mardi."},
        scope="global", scope_id=None, conversation_id=conv)
    assert resultat["success"], resultat


@pytest.mark.parametrize("kind", ["fait", "preference", "decision"])
async def test_les_autres_types_gardent_leur_regle(db_session, kind):
    conv, _ = await _fiche_puis_correction(db_session)
    resultat = await memory_card_tools.executer_outil(
        {"kind": kind, "subject": "Chantier Sacducbi", "title": "Sacducbi : scierie Louvelset",
         "content": "Pour le chantier Sacducbi, le bois viendra désormais de la scierie Louvelset."},
        scope="global", scope_id=None, conversation_id=conv)
    assert resultat.get("message") != "Cette correction doit modifier la fiche existante, pas en créer une seconde."
    if kind == "fait":
        # Même type, même sujet : le doublon existant donne désormais aussi l'id.
        assert "id " in resultat["detail"] and "version 1" in resultat["detail"]


async def _deux_clients(db_session, fiches_de):
    from app.models.entities import Contact
    alice, bernard = Contact(first_name="Alice"), Contact(first_name="Bernard")
    db_session.add_all([alice, bernard])
    await db_session.commit()
    conv = Conversation(title="Livraisons")
    db_session.add(conv)
    await db_session.commit()
    ids = {}
    for personne in fiches_de:
        contact = alice if personne == "Alice" else bernard
        db_session.add(Message(conversation_id=conv.id, role="user", content=f"Retiens : la livraison de {personne} se fait le lundi."))
        await db_session.commit()
        r = await memory_card_tools.executer_outil(
            {"kind": "fait", "subject": "livraison", "title": f"Livraison {personne}", "contact_id": contact.id,
             "content": f"La livraison de {personne} se fait le lundi."},
            scope="global", scope_id=None, conversation_id=conv.id)
        assert r["success"], r
        ids[personne] = r["receipt"]["id"]
    db_session.add(Message(conversation_id=conv.id, role="user",
                           content="Correction : la livraison de Bernard se fait désormais le mardi."))
    await db_session.commit()
    return conv.id, alice, bernard, ids


async def _corriger_livraison(conv, contact=None):
    return await memory_card_tools.executer_outil(
        {"kind": "correction", "subject": "livraison", "title": "Livraison Bernard",
         "content": "La livraison de Bernard se fait désormais le mardi.",
         **({"contact_id": contact.id} if contact else {})},
        scope="global", scope_id=None, conversation_id=conv)


async def test_correction_d_un_autre_contact_n_est_pas_renvoyee(db_session):
    # Astra c19e v1 : la fiche « livraison » d'Alice faisait refuser la correction de Bernard.
    conv, _, bernard, ids = await _deux_clients(db_session, ["Alice"])
    resultat = await _corriger_livraison(conv, bernard)
    assert resultat["success"], resultat
    alice = await db_session.get(MemoryCard, ids["Alice"])
    await db_session.refresh(alice)
    assert alice.content == "La livraison de Alice se fait le lundi." and alice.version == 1


async def test_correction_ambigue_n_est_pas_renvoyee(db_session):
    conv, _, _, _ = await _deux_clients(db_session, ["Alice", "Bernard"])
    resultat = await _corriger_livraison(conv)
    assert resultat["success"], resultat


async def test_correction_du_meme_contact_est_renvoyee_vers_sa_fiche(db_session):
    conv, _, bernard, ids = await _deux_clients(db_session, ["Alice", "Bernard"])
    refus = await _corriger_livraison(conv, bernard)
    assert not refus["success"]
    assert refus["card_id"] == ids["Bernard"]
