"""B-1115 : une correction réussie ne s'affiche plus précédée d'un refus.

Relance du 23/10 (Sonnet 5.5, code C19-E, journal du moteur) : Sonnet modifie la
fiche avec une raison non sourcée (refus et détail), puis reprend sans raison
quatre secondes plus tard (reçu, version 2). La bulle commençait par « Cette
fiche doit reprendre uniquement une information donnée dans ton message. » au-
dessus de « C'est mis à jour ». Le refus d'une modification est lu tout de suite
par le modèle et n'est affiché qu'en fin de tour, si la fiche n'a pas été écrite.
"""
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.routers import chat
from app.services import memory_card_tools
from app.services.providers.base import StreamEvent, ToolCall

REFUS = "Cette fiche doit reprendre uniquement une information donnée dans ton message."


async def _jouer(db_session, monkeypatch, resultats, appels, suite=("C'est mis à jour.",), relance=None):
    monkeypatch.setattr(memory_card_tools, "executer_outil", AsyncMock(side_effect=resultats))
    monkeypatch.setattr(chat, "_perimetre_de_conversation", AsyncMock(return_value=("global", None)))
    recus = []

    class Modele:
        async def continue_with_tool_results(self, *args, **kwargs):
            recus.append(kwargs.get("tool_results") or args)
            if relance and len(recus) == 1:
                # Le modèle lit le refus et reprend avec un nouvel appel.
                yield StreamEvent(type="tool_call", tool_call=ToolCall(id="reprise", name="upsert_memory_card",
                                                                       arguments=relance))
                yield StreamEvent(type="done", stop_reason="tool_use")
                return
            for fragment in suite:
                yield StreamEvent(type="text", content=fragment)
            yield StreamEvent(type="done", stop_reason="end_turn")

    chunks = [json.loads(c.removeprefix("data: ")) async for c in chat._execute_tools_and_continue(
        Modele(), None, context=SimpleNamespace(memory_cards_enabled=True), assistant_content="",
        tool_calls=[ToolCall(id=f"fiche-{i}", name="upsert_memory_card", arguments=a) for i, a in enumerate(appels)],
        tools=[memory_card_tools.MEMORY_CARD_TOOL], conversation_id="conv-factice", session=db_session,
        remaining_iterations=3,
    )]
    return "".join(c.get("content", "") for c in chunks if c["type"] == "text"), chunks, recus


async def test_refus_apres_ecriture_de_la_meme_fiche_non_affiche(db_session, monkeypatch):
    texte, chunks, recus = await _jouer(db_session, monkeypatch, [
        {"success": True, "receipt": {"id": "f1", "version": 2, "operation": "modification"}},
        {"success": False, "message": REFUS, "card_id": None},
    ], [{"id": "f1", "version": 1, "content": "a"}, {"id": "f1", "version": 1, "content": "a", "reason": "b"}],
        suite=(REFUS[:30], REFUS[30:], " C'est mis à jour."))
    assert REFUS not in texte
    assert texte.strip() == "C'est mis à jour."
    assert [c["receipt"]["id"] for c in chunks if c["type"] == "memory_receipt"] == ["f1"]
    # Le modèle a bien reçu le refus du second appel.
    assert REFUS in json.dumps(recus, default=str, ensure_ascii=False)


async def test_refus_d_une_autre_fiche_reste_affiche(db_session, monkeypatch):
    texte, _, _ = await _jouer(db_session, monkeypatch, [
        {"success": True, "receipt": {"id": "f1", "version": 2, "operation": "modification"}},
        {"success": False, "message": REFUS, "card_id": None},
    ], [{"id": "f1", "version": 1, "content": "a"}, {"id": "f2", "version": 1, "content": "b"}])
    assert texte.count(REFUS) == 1


async def test_refus_puis_reprise_reussie_au_tour_suivant_non_affiche(db_session, monkeypatch):
    # L'ordre observé le 23/10 : refus, le modèle relit le détail, reprend, reçu.
    texte, chunks, recus = await _jouer(db_session, monkeypatch, [
        {"success": False, "message": REFUS, "card_id": None, "detail": "Sans source : « utilisateur »."},
        {"success": True, "receipt": {"id": "f1", "version": 2, "operation": "modification"}},
    ], [{"id": "f1", "version": 1, "content": "a", "reason": "b"}], relance={"id": "f1", "version": 1, "content": "a"},
        suite=(REFUS, " C'est mis à jour."))
    assert REFUS not in texte
    assert texte.strip() == "C'est mis à jour."
    assert [c["receipt"]["id"] for c in chunks if c["type"] == "memory_receipt"] == ["f1"]
    assert "utilisateur" in json.dumps(recus, default=str, ensure_ascii=False)


async def test_refus_dans_le_meme_appel_puis_ecriture_non_affiche(db_session, monkeypatch):
    texte, _, _ = await _jouer(db_session, monkeypatch, [
        {"success": False, "message": REFUS, "card_id": None},
        {"success": True, "receipt": {"id": "f1", "version": 2, "operation": "modification"}},
    ], [{"id": "f1", "version": 1, "content": "a", "reason": "b"}, {"id": "f1", "version": 1, "content": "a"}])
    assert REFUS not in texte


async def test_refus_d_une_modification_jamais_ecrite_affiche_une_fois_en_fin(db_session, monkeypatch):
    texte, _, _ = await _jouer(db_session, monkeypatch, [
        {"success": False, "message": REFUS, "card_id": None},
    ], [{"id": "f1", "version": 1, "content": "a", "reason": "b"}], suite=(REFUS, " Je n'ai pas pu la modifier."))
    assert texte.count(REFUS) == 1
    assert texte.index("Je n'ai pas pu") < texte.index(REFUS)


async def test_refus_d_une_creation_reste_immediat(db_session, monkeypatch):
    texte, _, _ = await _jouer(db_session, monkeypatch, [
        {"success": False, "message": REFUS, "card_id": None},
    ], [{"content": "a"}], suite=(" Je n'ai rien retenu.",))
    assert texte.count(REFUS) == 1
    assert texte.index(REFUS) < texte.index("Je n'ai rien retenu")
