"""B-1157 : une panne ne prouve ni une absence de résultats ni une clé invalide."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.services import deep_research as module
from app.services.web_search import RechercheWebRefusee


async def rechercher(monkeypatch, reponses):
    requetes = [f"Axe {i}" for i in range(len(reponses))]
    monkeypatch.setattr(module, "decompose_question", AsyncMock(return_value=requetes))
    service = SimpleNamespace(search=AsyncMock(side_effect=reponses))
    monkeypatch.setattr(module, "get_web_search_service", lambda: service)
    async def synthese(*args, **kwargs):
        yield "Synthèse simulée"

    llm = SimpleNamespace(prepare_context=lambda messages: messages, stream_response=synthese)
    return [event async for event in module.deep_research("Question locale", llm)]


@pytest.mark.parametrize("reponses,attendu", [
    ([RuntimeError("Panne factice")], "n'a pas pu aboutir"),
    ([SimpleNamespace(results=[])], "Aucun résultat"),
])
async def test_distingue_panne_et_absence_de_resultats(monkeypatch, reponses, attendu):
    events = await rechercher(monkeypatch, reponses)
    assert events[-1].type == "error"
    assert attendu in events[-1].content
    assert "Brave" not in events[-1].content
    assert "clé" not in events[-1].content


VIDE = SimpleNamespace(results=[])
SOURCE = SimpleNamespace(results=[SimpleNamespace(
    title="Source locale", url="https://example.invalid/source", snippet="Extrait simulé",
)])


@pytest.mark.parametrize("reponses,type_final,texte", [
    ([TimeoutError("Délai dépassé")], "error", "n'a pas pu aboutir"),
    ([ConnectionError("Connexion coupée")], "error", "n'a pas pu aboutir"),
    ([OSError("Réseau inaccessible")], "error", "n'a pas pu aboutir"),
    ([ValueError("Réponse illisible")], "error", "n'a pas pu aboutir"),
    ([KeyError("Champ absent")], "error", "n'a pas pu aboutir"),
    ([VIDE, VIDE], "error", "Aucun résultat"),
    ([VIDE, TimeoutError("Deuxième axe indisponible")], "error", "n'a pas pu aboutir"),
    ([ConnectionError("Premier axe indisponible"), VIDE], "error", "n'a pas pu aboutir"),
    ([RechercheWebRefusee("Préférence locale")], "error", "Recherche web coupée"),
    ([SOURCE, TimeoutError("Axe complémentaire indisponible")], "done", "Synthèse simulée"),
])
async def test_dix_rejeux_apres_correctif(monkeypatch, reponses, type_final, texte):
    events = await rechercher(monkeypatch, reponses)
    assert events[-1].type == type_final
    assert texte in events[-1].content
    assert "Brave" not in events[-1].content
    if type_final == "done":
        assert len(events[-1].sources) == 1
