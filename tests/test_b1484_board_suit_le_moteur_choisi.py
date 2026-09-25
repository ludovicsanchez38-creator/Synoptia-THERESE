"""B-1484 : le Board cherchait toujours chez DuckDuckGo.

Le chat, la recherche approfondie et les agents passent par
get_web_search_service(), qui respecte le moteur choisi dans Paramètres
(Brave si une clé est saisie, SearXNG si une adresse est donnée, DuckDuckGo
sinon). Le Board instanciait WebSearchService() en direct : une question
stratégique partait chez DuckDuckGo même quand l'utilisateur avait branché
son SearXNG pour que ses recherches ne sortent pas.
"""

import pytest


@pytest.fixture
def searxng_choisi():
    from app.services import web_search

    precedent = web_search._searxng_url_cache
    web_search._searxng_url_cache = "http://127.0.0.1:9/"
    web_search._searxng_service = None
    yield
    web_search._searxng_url_cache = precedent
    web_search._searxng_service = None


async def test_le_board_cherche_avec_searxng_quand_il_est_choisi(searxng_choisi, monkeypatch):
    from app.services import web_search
    from app.services.board import BoardService

    monkeypatch.setattr(web_search, "_get_brave_api_key", lambda: None)
    moteurs_appeles: list[str] = []

    async def recherche_searxng(self, query, max_results=5, **_):
        moteurs_appeles.append("searxng")
        return web_search.SearchResponse(query=query, results=[], total_results=0)

    async def recherche_duckduckgo(self, query, max_results=5, **_):
        moteurs_appeles.append("duckduckgo")
        return web_search.SearchResponse(query=query, results=[], total_results=0)

    monkeypatch.setattr(web_search.SearXNGService, "search", recherche_searxng)
    monkeypatch.setattr(web_search.WebSearchService, "search", recherche_duckduckgo)

    board = BoardService()
    await board._search_web_for_context("Faut-il ouvrir un second atelier ?")

    assert moteurs_appeles == ["searxng"]
