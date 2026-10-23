"""B-1104 : provenance cumulée, sans élargir aux autres fiches."""
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.models.entities import Conversation, Message
from app.services import memory_cards as service


async def corriger(db_session, fournisseur="Naccanset", jour="lundi", invention=""):
    conv = Conversation(title="Chantier Chonloumi")
    db_session.add(conv)
    await db_session.commit()
    source = Message(conversation_id=conv.id, role="user",
                     content=f"Chantier Chonloumi : bois de Rarelbrou, livraison le {jour}.")
    db_session.add(source)
    await db_session.commit()
    donnees = {"kind": "fait", "subject": "chantier", "title": "Chonloumi", "content": source.content}
    fiche = await service.ecrire(donnees, automatique=True, conversation_id=conv.id, message_id=source.id)
    correction = Message(conversation_id=conv.id, role="user",
                         content=f"Correction Chonloumi : bois de {fournisseur}.")
    db_session.add(correction)
    await db_session.commit()
    resultat = await service.ecrire({"id": fiche["id"], "version": 1,
                                    "content": f"Chantier Chonloumi : bois de {fournisseur}, livraison le {jour}.{invention}"},
                                   automatique=True, conversation_id=conv.id, message_id=correction.id)
    assert resultat["version"] == 2
    assert fournisseur in resultat["content"] and jour in resultat["content"]
    return resultat


async def test_correction_conserve_un_fait_preexistant(db_session):
    await corriger(db_session)


@pytest.mark.parametrize("invention", [" Livraison gratuite.", " Délai garanti de 48 heures."])
async def test_fait_absent_des_deux_sources_refuse(db_session, invention):
    with pytest.raises(service.RefusMemoire, match="uniquement une information"):
        await corriger(db_session, invention=invention)


@pytest.mark.parametrize("fournisseur,jour", [
    ("BoisAzur", "mardi"), ("Sylviane", "mercredi"), ("Valdor", "jeudi"),
    ("Arboria", "vendredi"), ("Cimebleue", "samedi"), ("Montclair", "dimanche"),
    ("Norois", "mardi"), ("Boisclair", "jeudi"), ("Tremblay", "vendredi"), ("Vallon", "samedi"),
])
async def test_rejeu_corrections(db_session, fournisseur, jour):
    await corriger(db_session, fournisseur, jour)


@pytest.mark.parametrize("nombre", [1, 2])
async def test_refus_de_fiche_non_repete_par_la_continuation(db_session, monkeypatch, nombre):
    from app.routers import chat
    from app.services import memory_card_tools
    from app.services.providers.base import StreamEvent, ToolCall

    refus = "Cette fiche doit reprendre uniquement une information donnée dans ton message."
    monkeypatch.setattr(memory_card_tools, "executer_outil", AsyncMock(return_value={"success": False, "message": refus}))
    monkeypatch.setattr(chat, "_perimetre_de_conversation", AsyncMock(return_value=("global", None)))
    suites = []

    class Modele:
        async def continue_with_tool_results(self, *args, **kwargs):
            suites.append(True)
            yield StreamEvent(type="text", content=refus)
            yield StreamEvent(type="done", stop_reason="end_turn")

    chunks = [json.loads(c.removeprefix("data: ")) async for c in chat._execute_tools_and_continue(
        Modele(), None, context=SimpleNamespace(memory_cards_enabled=True), assistant_content="",
        tool_calls=[ToolCall(id=f"fiche-{i}", name="upsert_memory_card", arguments={}) for i in range(nombre)],
        tools=[memory_card_tools.MEMORY_CARD_TOOL], conversation_id="conv-factice", session=db_session,
        remaining_iterations=3,
    )]
    texte = "".join(c.get("content", "") for c in chunks if c["type"] == "text")
    assert texte.count(refus) == 1
    assert suites == [True]


async def appliquer_correction(db_session, contenu, message, **changements):
    conv = Conversation(title="Livraison")
    db_session.add(conv)
    await db_session.commit()
    fiche = await service.ecrire({"kind": "fait", "subject": "livraison", "title": "Livraison", "content": contenu})
    source = Message(conversation_id=conv.id, role="user", content=message)
    db_session.add(source)
    await db_session.commit()
    # Fiche non protégée pour isoler la vérification de provenance automatique.
    from app.models.entities import MemoryCard
    stockee = await db_session.get(MemoryCard, fiche["id"])
    stockee.protected = False
    await db_session.commit()
    return await service.ecrire({"id": fiche["id"], "version": 1, **changements},
                               automatique=True, conversation_id=conv.id, message_id=source.id)


@pytest.mark.parametrize("contenu,changements", [
    ("Livraison le lundi sous 30 jours", {"content": "Livraison le mardi sous 90 jours"}),
    ("La livraison n'est pas gratuite", {"content": "La livraison est gratuite le mardi"}),
    ("Livraison le lundi sous 30 jours", {"title": "Livraison sous 90 jours", "content": "Livraison le mardi sous 30 jours"}),
])
async def test_contre_exemples_astra_refuses(db_session, contenu, changements):
    with pytest.raises(service.RefusMemoire, match="uniquement une information"):
        await appliquer_correction(db_session, contenu, "Correction : livraison le mardi", **changements)


async def test_correction_affirmant_le_contraire_acceptee(db_session):
    fiche = await appliquer_correction(db_session, "La livraison n'est pas gratuite",
                                      "Correction : la livraison est désormais gratuite",
                                      content="La livraison est gratuite")
    assert fiche["content"] == "La livraison est gratuite"


async def test_refus_memoire_conserve_la_reponse_a_une_autre_demande(db_session, monkeypatch):
    from app.routers import chat
    from app.services import memory_card_tools
    from app.services.providers.base import StreamEvent, ToolCall

    refus = "Cette fiche doit reprendre uniquement une information donnée dans ton message."
    monkeypatch.setattr(memory_card_tools, "executer_outil", AsyncMock(return_value={"success": False, "message": refus}))
    monkeypatch.setattr(chat, "_perimetre_de_conversation", AsyncMock(return_value=("global", None)))

    class Modele:
        async def continue_with_tool_results(self, *args, **kwargs):
            for fragment in [refus[:24], refus[24:], "\nPour ton autre question : 7 × 8 = 56."]:
                yield StreamEvent(type="text", content=fragment)
            yield StreamEvent(type="done", stop_reason="end_turn")

    chunks = [json.loads(c.removeprefix("data: ")) async for c in chat._execute_tools_and_continue(
        Modele(), None, context=SimpleNamespace(memory_cards_enabled=True), assistant_content="",
        tool_calls=[ToolCall(id="fiche", name="upsert_memory_card", arguments={})],
        tools=[memory_card_tools.MEMORY_CARD_TOOL], conversation_id="conv-factice", session=db_session,
        remaining_iterations=3,
    )]
    texte = "".join(c.get("content", "") for c in chunks if c["type"] == "text")
    assert "7 × 8 = 56" in texte
    assert texte.count(refus) == 1


@pytest.mark.parametrize("titre", ["Fournisseur de bois", "Livraison gratuite"])
async def test_titre_reste_un_resume_libre(db_session, titre):
    fiche = await appliquer_correction(db_session, "Le bois viendra de la scierie Rarelbrou",
                                      "Correction : le bois viendra de la scierie Naccanset",
                                      title=titre, content="Le bois viendra de la scierie Naccanset")
    assert fiche["title"] == titre


async def test_nombre_du_titre_donne_dans_le_message_accepte(db_session):
    fiche = await appliquer_correction(db_session, "Livraison sous 30 jours",
                                      "Correction : livraison sous 9 jours",
                                      title="Livraison sous 9 jours", content="Livraison sous 9 jours")
    assert fiche["title"] == "Livraison sous 9 jours"


@pytest.mark.parametrize("contenu,changements", [
    ("La livraison est gratuite", {"content": "La livraison n'est pas gratuite le mardi"}),
    ("Livraison : tarif 30,50 euros", {"content": "Livraison le mardi : tarif 50,30 euros"}),
    ("Livraison : tarif 30,50 euros", {"title": "Tarif 50,30 euros", "content": "Livraison le mardi : tarif 30,50 euros"}),
    ("Livraison : tarif 1.5 euros", {"reason": "Tarif 5.1 euros", "content": "Livraison le mardi : tarif 1.5 euros"}),
    ("Livraison : tarif 7 500 euros", {"content": "Livraison le mardi : tarif 500 7 euros"}),
])
async def test_reprise3_inventions_nombres_et_polarite_refusees(db_session, contenu, changements):
    with pytest.raises(service.RefusMemoire, match="uniquement une information"):
        await appliquer_correction(db_session, contenu, "Correction : livraison le mardi", **changements)


@pytest.mark.parametrize("contenu,message,proposition", [
    ("Il n'y a pas de livraison", "Correction : la livraison est disponible", "La livraison est disponible"),
    ("La livraison est disponible", "Correction : il n'y a pas de livraison", "Il n'y a pas de livraison"),
    ("Sans de l'or", "Correction : or disponible", "Or disponible"),
    ("Livraison : tarif 30,50 euros", "Correction : tarif 50,30 euros", "Livraison : tarif 50,30 euros"),
    ("Livraison : tarif 7 500 euros", "Correction : livraison le mardi", "Livraison le mardi : tarif 7 500 euros"),
])
async def test_reprise3_corrections_explicites_acceptees(db_session, contenu, message, proposition):
    fiche = await appliquer_correction(db_session, contenu, message, content=proposition)
    assert fiche["content"] == proposition
