"""B-1115 : le refus d'une modification de fiche s'annonce comme une tentative.

Relance du 23/10 (Sonnet 5.5, journal du moteur) : Sonnet modifie la fiche avec
une raison non sourcée (refus et détail), puis reprend sans raison quatre
secondes plus tard (reçu, version 2). La bulle commençait par « Cette fiche doit
reprendre uniquement une information donnée dans ton message. » au-dessus de
« C'est mis à jour ». Trois essais de report du refus en fin de tour ont été
refusés par Astra (refus perdu sur une erreur, une exception, une annulation) :
le refus reste affiché tout de suite, annoncé comme une tentative.
"""
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.routers import chat
from app.services import memory_card_tools
from app.services.providers.base import StreamEvent, ToolCall, ToolResult

REFUS = "Cette fiche doit reprendre uniquement une information donnée dans ton message."
TENTATIVE = "Tentative de modification refusée : cette fiche doit reprendre uniquement une information donnée dans ton message."
MODIFICATION = {"id": "f1", "version": 1, "content": "a", "reason": "b"}


async def _flux(db_session, monkeypatch, resultats, appels, modele=None, contexte=None, suite=("C'est mis à jour.",),
                relance=None):
    monkeypatch.setattr(memory_card_tools, "executer_outil", AsyncMock(side_effect=resultats))
    monkeypatch.setattr(chat, "_perimetre_de_conversation", AsyncMock(return_value=("global", None)))
    recus = []

    class Modele:
        async def continue_with_tool_results(self, *args, **kwargs):
            recus.append((args, kwargs))
            if relance and len(recus) == 1:
                # Le modèle lit le refus et reprend avec un nouvel appel.
                yield StreamEvent(type="tool_call", tool_call=ToolCall(id="reprise", name="upsert_memory_card",
                                                                       arguments=relance))
                yield StreamEvent(type="done", stop_reason="tool_use")
                return
            for fragment in suite:
                yield StreamEvent(type="text", content=fragment)
            yield StreamEvent(type="done", stop_reason="end_turn")

    morceaux = []
    try:
        async for c in chat._execute_tools_and_continue(
            modele or Modele(), None, context=SimpleNamespace(memory_cards_enabled=True), assistant_content="",
            tool_calls=[ToolCall(id=f"fiche-{i}", name="upsert_memory_card", arguments=a) for i, a in enumerate(appels)],
            tools=[memory_card_tools.MEMORY_CARD_TOOL], conversation_id="conv-factice", session=db_session,
            remaining_iterations=3, contexte=contexte,
        ):
            morceaux.append(json.loads(c.removeprefix("data: ")))
    except RuntimeError as erreur:
        morceaux.append({"type": "exception", "content": str(erreur)})
    return morceaux, recus


def _texte(morceaux):
    return "".join(m.get("content", "") for m in morceaux if m["type"] == "text")


def _lus(recus):
    vus = []

    def fouiller(objet):
        if isinstance(objet, ToolResult):
            vus.append(objet)
        elif isinstance(objet, (list, tuple)):
            for element in objet:
                fouiller(element)
        elif isinstance(objet, dict):
            for element in objet.values():
                fouiller(element)
    fouiller(recus)
    return vus


async def test_refus_d_une_modification_annonce_une_tentative(db_session, monkeypatch):
    morceaux, _ = await _flux(db_session, monkeypatch, [{"success": False, "message": REFUS, "card_id": None}],
                              [MODIFICATION], suite=(" Je n'ai pas pu la modifier.",))
    texte = _texte(morceaux)
    assert texte.count(TENTATIVE) == 1
    assert texte.index(TENTATIVE) < texte.index("Je n'ai pas pu")


async def test_tentative_refusee_puis_reprise_reussie(db_session, monkeypatch):
    # L'ordre observé le 23/10 : refus, le modèle relit le détail, reprend, reçu.
    morceaux, recus = await _flux(db_session, monkeypatch, [
        {"success": False, "message": REFUS, "card_id": None, "detail": "Sans source : « utilisateur »."},
        {"success": True, "receipt": {"id": "f1", "version": 2, "operation": "modification"}},
    ], [MODIFICATION], relance={"id": "f1", "version": 1, "content": "a"}, suite=(REFUS, " C'est mis à jour."))
    texte = _texte(morceaux)
    # La tentative est annoncée une fois ; la reprise verbatim du modèle est retirée.
    assert texte.count(TENTATIVE) == 1 and texte.count(REFUS) == 0
    assert texte.strip().endswith("C'est mis à jour.")
    assert [m["receipt"]["id"] for m in morceaux if m["type"] == "memory_receipt"] == ["f1"]
    assert "utilisateur" in _lus(recus)[0].result


async def test_refus_d_une_creation_reste_tel_quel(db_session, monkeypatch):
    morceaux, _ = await _flux(db_session, monkeypatch, [{"success": False, "message": REFUS, "card_id": None}],
                              [{"content": "a"}], suite=(" Je n'ai rien retenu.",))
    texte = _texte(morceaux)
    assert texte.count(REFUS) == 1 and "Tentative" not in texte


async def test_le_modele_recoit_le_detail_et_la_fiche_visee(db_session, monkeypatch):
    # Astra c19e v1 : la boucle remplaçait le résultat refusé par « Error: message » ;
    # le détail (mots sans source, id et version de la fiche) n'arrivait pas au modèle.
    _, recus = await _flux(db_session, monkeypatch, [
        {"success": False, "message": REFUS, "card_id": "f9", "detail": "Fiche « Livraison » : id f9, version 3."},
    ], [{"kind": "correction", "subject": "livraison", "title": "t", "content": "c"}])
    (lu,) = _lus(recus)
    assert lu.is_error
    contenu = json.loads(lu.result)
    assert contenu["detail"] == "Fiche « Livraison » : id f9, version 3."
    assert contenu["card_id"] == "f9" and contenu["message"] == REFUS


# Garde-fous de la revue Astra c19e v2 et v3 : le refus est affiché avant toute
# interruption du tour, puisqu'il part dès que l'outil répond.
REFUS_MODIF = [{"success": False, "message": REFUS, "card_id": None}]


def _position(morceaux, predicat):
    return next(i for i, m in enumerate(morceaux) if predicat(m))


def _est_tentative(m):
    return m["type"] == "text" and TENTATIVE in m.get("content", "")


async def test_refus_avant_l_erreur_du_fournisseur(db_session, monkeypatch):
    class Modele:
        async def continue_with_tool_results(self, *args, **kwargs):
            yield StreamEvent(type="text", content="Je mets ta mémoire à jour.")
            yield StreamEvent(type="error", content="Overloaded (529)")

    morceaux, _ = await _flux(db_session, monkeypatch, list(REFUS_MODIF), [MODIFICATION], modele=Modele())
    assert _position(morceaux, _est_tentative) < _position(morceaux, lambda m: m["type"] == "error")


async def test_refus_avant_l_exception_de_la_suite(db_session, monkeypatch):
    class Modele:
        async def continue_with_tool_results(self, *args, **kwargs):
            yield StreamEvent(type="text", content="Je mets ta mémoire à jour.")
            raise RuntimeError("coupure")

    morceaux, _ = await _flux(db_session, monkeypatch, list(REFUS_MODIF), [MODIFICATION], modele=Modele())
    assert morceaux[-1] == {"type": "exception", "content": "coupure"}
    assert any(_est_tentative(m) for m in morceaux[:-1])


async def test_refus_avant_le_budget_refuse(db_session, monkeypatch):
    monkeypatch.setattr(chat, "_controle_du_prompt", lambda *a, **k: {"allowed": False, "errors": ["Budget atteint."]})

    class Modele:
        async def continue_with_tool_results(self, *args, **kwargs):
            raise AssertionError("aucune suite attendue")
            yield  # pragma: no cover

    morceaux, _ = await _flux(db_session, monkeypatch, list(REFUS_MODIF), [MODIFICATION], modele=Modele())
    assert _position(morceaux, _est_tentative) < _position(morceaux, lambda m: m["type"] == "error")


async def test_refus_affiche_avant_une_annulation(db_session, monkeypatch):
    etat = {"annule": False}

    async def refuser_puis_annuler(*args, **kwargs):
        etat["annule"] = True
        return dict(REFUS_MODIF[0])

    class Modele:
        async def continue_with_tool_results(self, *args, **kwargs):
            raise AssertionError("aucune suite après une annulation")
            yield  # pragma: no cover

    contexte = SimpleNamespace(annulation_observee=lambda: etat["annule"])
    morceaux, _ = await _flux(db_session, monkeypatch, refuser_puis_annuler, [MODIFICATION], modele=Modele(),
                              contexte=contexte)
    assert sum(_est_tentative(m) for m in morceaux) == 1
