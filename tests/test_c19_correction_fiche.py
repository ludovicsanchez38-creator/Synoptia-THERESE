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
    assert suites == []
