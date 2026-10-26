"""B-1157 : une panne ne prouve ni une absence de résultats ni une clé invalide."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from app.services import deep_research as module
from app.services import web_search
from app.services.web_search import RechercheWebRefusee, SearchResponse, SearchResult


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
    ([SearchResponse(query="Vide", results=[], total_results=0)], "Aucun résultat"),
])
async def test_distingue_panne_et_absence_de_resultats(monkeypatch, reponses, attendu):
    events = await rechercher(monkeypatch, reponses)
    assert events[-1].type == "error"
    assert attendu in events[-1].content
    assert "Brave" not in events[-1].content
    assert "clé" not in events[-1].content


VIDE = SearchResponse(query="Vide", results=[], total_results=0)
SOURCE = SearchResponse(query="Source", total_results=1, results=[SearchResult(
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


async def test_panne_reseau_du_vrai_service(monkeypatch):
    service = web_search.WebSearchService()
    client = SimpleNamespace(post=AsyncMock(side_effect=httpx.ConnectError("Panne simulée")))
    monkeypatch.setattr(service, "_get_client", AsyncMock(return_value=client))
    monkeypatch.setattr(web_search, "verifier_autorisation_recherche", lambda: None)
    monkeypatch.setattr(module, "get_web_search_service", lambda: service)
    monkeypatch.setattr(module, "decompose_question", AsyncMock(return_value=["Question locale"]))
    events = [event async for event in module.deep_research("Question locale", SimpleNamespace())]
    assert events[-1].type == "error"
    assert events[-1].content == "La recherche web n'a pas pu aboutir. Réessaie plus tard."
    client.post.assert_awaited_once()


HTML_VIDE = '<div class="no-results">No results.</div>'
HTML_SOURCE = '<div class="result"><a class="result__a" href="https://example.invalid/source">Source</a><a class="result__snippet">Extrait</a></div>'


@pytest.mark.parametrize("reponses,type_final,texte", [
    ([httpx.ReadTimeout("Lecture simulée")], "error", "n'a pas pu aboutir"),
    ([httpx.ConnectTimeout("Connexion simulée")], "error", "n'a pas pu aboutir"),
    ([httpx.RemoteProtocolError("Protocole simulé")], "error", "n'a pas pu aboutir"),
    ([(503, "")], "error", "n'a pas pu aboutir"),
    ([(429, "")], "error", "n'a pas pu aboutir"),
    ([(200, "<html>Page inconnue</html>")], "error", "n'a pas pu aboutir"),
    ([(200, HTML_VIDE)], "error", "Aucun résultat"),
    ([(200, HTML_VIDE), (502, "")], "error", "n'a pas pu aboutir"),
    ([(503, ""), (200, HTML_SOURCE)], "done", "Synthèse simulée"),
    ([(200, HTML_SOURCE), (503, "")], "done", "Synthèse simulée"),
])
async def test_dix_rejeux_indisponible_apres_astra(monkeypatch, reponses, type_final, texte):
    reponses_http = iter(reponses)

    def transport(request):
        reponse = next(reponses_http)
        if isinstance(reponse, Exception):
            raise reponse
        statut, html = reponse
        return httpx.Response(statut, text=html)

    async def synthese(*args, **kwargs):
        yield "Synthèse simulée"

    service = web_search.WebSearchService()
    monkeypatch.setattr(web_search, "verifier_autorisation_recherche", lambda: None)
    monkeypatch.setattr(module, "get_web_search_service", lambda: service)
    monkeypatch.setattr(module, "decompose_question", AsyncMock(return_value=[
        f"Axe {i}" for i in range(len(reponses))
    ]))
    llm = SimpleNamespace(prepare_context=lambda messages: messages, stream_response=synthese)
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        monkeypatch.setattr(service, "_get_client", AsyncMock(return_value=client))
        events = [event async for event in module.deep_research("Question locale", llm)]
    assert events[-1].type == type_final
    assert texte in events[-1].content
    if type_final == "done":
        assert len(events[-1].sources) == 1
