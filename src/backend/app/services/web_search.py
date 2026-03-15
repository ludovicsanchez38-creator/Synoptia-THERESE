"""
THÉRÈSE v2 - Web Search Service

Provides web search capabilities for LLMs.
Supports Brave Search (with API key) and DuckDuckGo (free fallback).
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single search result."""
    title: str
    url: str
    snippet: str
    source: str = "duckduckgo"


@dataclass
class SearchResponse:
    """Response from a web search."""
    query: str
    results: list[SearchResult]
    total_results: int


class BraveSearchService:
    """
    Web search service using Brave Search API.

    Requires a Brave Search API key (https://brave.com/search/api/).
    Free tier : 2 000 requêtes/mois.
    """

    BRAVE_API_URL = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=15.0,
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip",
                    "X-Subscription-Token": self._api_key,
                },
            )
        return self._client

    async def search(
        self,
        query: str,
        max_results: int = 5,
        region: str = "fr",
    ) -> SearchResponse:
        """
        Search the web using Brave Search API.

        Args:
            query: Search query
            max_results: Maximum number of results (default 5)
            region: Country code (default fr)

        Returns:
            SearchResponse with results
        """
        client = await self._get_client()

        try:
            response = await client.get(
                self.BRAVE_API_URL,
                params={
                    "q": query,
                    "count": max_results,
                    "country": region,
                    "search_lang": "fr",
                    "text_decorations": False,
                },
            )
            response.raise_for_status()
            data = response.json()

            results: list[SearchResult] = []
            for item in data.get("web", {}).get("results", [])[:max_results]:
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("description", ""),
                    source="brave",
                ))

            return SearchResponse(
                query=query,
                results=results,
                total_results=len(results),
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"Brave Search error: {e.response.status_code}")
            return SearchResponse(query=query, results=[], total_results=0)
        except Exception as e:
            logger.error(f"Brave Search error: {e}")
            return SearchResponse(query=query, results=[], total_results=0)

    def format_results_for_llm(self, response: SearchResponse) -> str:
        """Format search results as context for LLM."""
        if not response.results:
            return f"Aucun résultat trouvé pour: {response.query}"

        lines = [f"Résultats de recherche web pour: {response.query}\n"]

        for i, result in enumerate(response.results, 1):
            lines.append(f"{i}. **{result.title}**")
            lines.append(f"   URL: {result.url}")
            if result.snippet:
                lines.append(f"   {result.snippet}")
            lines.append("")

        return "\n".join(lines)

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


class WebSearchService:
    """
    Web search service using DuckDuckGo.

    DuckDuckGo HTML search is free and doesn't require an API key.
    """

    DUCKDUCKGO_URL = "https://html.duckduckgo.com/html/"
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={"User-Agent": self.USER_AGENT},
                follow_redirects=True,
            )
        return self._client

    async def search(
        self,
        query: str,
        max_results: int = 5,
        region: str = "fr-fr",
    ) -> SearchResponse:
        """
        Search the web using DuckDuckGo.

        Args:
            query: Search query
            max_results: Maximum number of results to return (default 5)
            region: Region for search results (default fr-fr for French)

        Returns:
            SearchResponse with results
        """
        client = await self._get_client()

        try:
            response = await client.post(
                self.DUCKDUCKGO_URL,
                data={
                    "q": query,
                    "kl": region,
                    "df": "",  # Date filter (empty = all time)
                },
            )
            response.raise_for_status()
            html = response.text

            # Parse results from HTML
            results = self._parse_html_results(html, max_results)

            return SearchResponse(
                query=query,
                results=results,
                total_results=len(results),
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"DuckDuckGo search error: {e.response.status_code}")
            return SearchResponse(query=query, results=[], total_results=0)
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return SearchResponse(query=query, results=[], total_results=0)

    def _parse_html_results(self, html: str, max_results: int) -> list[SearchResult]:
        """Parse search results from DuckDuckGo HTML response."""
        results = []

        # Alternative pattern for result links
        link_pattern = r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
        snippet_pattern = r'<a[^>]*class="result__snippet"[^>]*>([^<]*(?:<[^>]*>[^<]*</[^>]*>)*[^<]*)</a>'

        # Find all links and snippets
        links = re.findall(link_pattern, html)
        snippets = re.findall(snippet_pattern, html)

        for i, (url, title) in enumerate(links[:max_results]):
            # Clean up URL (DuckDuckGo sometimes wraps URLs)
            if "uddg=" in url:
                # Extract actual URL from DuckDuckGo redirect
                url_match = re.search(r'uddg=([^&]+)', url)
                if url_match:
                    from urllib.parse import unquote
                    url = unquote(url_match.group(1))

            # Get corresponding snippet
            snippet = ""
            if i < len(snippets):
                snippet = re.sub(r'<[^>]+>', '', snippets[i])  # Remove HTML tags
                snippet = snippet.strip()

            # Clean title
            title = re.sub(r'<[^>]+>', '', title).strip()

            if title and url:
                results.append(SearchResult(
                    title=title,
                    url=url,
                    snippet=snippet,
                    source="duckduckgo",
                ))

        return results

    def format_results_for_llm(self, response: SearchResponse) -> str:
        """Format search results as context for LLM."""
        if not response.results:
            return f"Aucun résultat trouvé pour: {response.query}"

        lines = [f"Résultats de recherche web pour: {response.query}\n"]

        for i, result in enumerate(response.results, 1):
            lines.append(f"{i}. **{result.title}**")
            lines.append(f"   URL: {result.url}")
            if result.snippet:
                lines.append(f"   {result.snippet}")
            lines.append("")

        return "\n".join(lines)

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# ============================================================
# SearXNG Service (méta-moteur auto-hébergeable)
# ============================================================


class SearXNGService:
    """
    Web search service using a SearXNG instance.

    SearXNG est un méta-moteur open source auto-hébergeable.
    Aucune clé API requise - juste l'URL de l'instance.
    """

    def __init__(self, instance_url: str):
        self._instance_url = instance_url.rstrip("/")
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=15.0)
        return self._client

    async def search(self, query: str, max_results: int = 5, region: str = "fr") -> SearchResponse:
        """Search using SearXNG JSON API."""
        client = await self._get_client()

        try:
            response = await client.get(
                f"{self._instance_url}/search",
                params={
                    "q": query,
                    "format": "json",
                    "language": region,
                    "categories": "general",
                    "pageno": 1,
                },
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", [])[:max_results]:
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                    source="searxng",
                ))

            return SearchResponse(
                query=query,
                results=results,
                total_results=data.get("number_of_results", len(results)),
            )

        except Exception as e:
            logger.error(f"SearXNG search error: {e}")
            return SearchResponse(query=query, results=[], total_results=0)

    def format_results_for_llm(self, response: SearchResponse) -> str:
        """Format search results for LLM consumption."""
        if not response.results:
            return f"Aucun résultat trouvé pour : {response.query}"

        parts = [f"Résultats de recherche pour : {response.query}\n"]
        for i, r in enumerate(response.results, 1):
            parts.append(f"{i}. {r.title}\n   URL: {r.url}\n   {r.snippet}\n")
        return "\n".join(parts)

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None


# Global instances
_web_search_service: WebSearchService | None = None
_brave_search_service: BraveSearchService | None = None
_searxng_service: SearXNGService | None = None


def get_web_search_service() -> WebSearchService | BraveSearchService | SearXNGService:
    """
    Get the global web search service instance.

    Priorité : Brave Search (si clé API) > SearXNG (si URL configurée) > DuckDuckGo (fallback).
    """
    global _web_search_service, _brave_search_service, _searxng_service

    # 1. Brave Search (si clé API configurée)
    brave_key = _get_brave_api_key()
    if brave_key:
        if _brave_search_service is None:
            _brave_search_service = BraveSearchService(brave_key)
            logger.info("Brave Search API activé")
        return _brave_search_service

    # 2. SearXNG (si URL configurée)
    searxng_url = _get_searxng_url()
    if searxng_url:
        if _searxng_service is None:
            _searxng_service = SearXNGService(searxng_url)
            logger.info(f"SearXNG activé : {searxng_url}")
        return _searxng_service

    # 3. Fallback DuckDuckGo
    if _web_search_service is None:
        _web_search_service = WebSearchService()
    return _web_search_service


_brave_api_key_cache: str | None = None


def _get_brave_api_key() -> str | None:
    """
    Récupère la clé API Brave Search.

    Vérifie : variable d'environnement > cache module.
    Le cache est alimenté par set_brave_api_key() lors de la config.
    """
    import os

    env_key = os.environ.get("BRAVE_API_KEY")
    if env_key:
        return env_key

    return _brave_api_key_cache


def set_brave_api_key(key: str | None) -> None:
    """
    Met à jour la clé API Brave Search en cache.

    Appelé lors du changement de clé API dans la config.
    Invalide le service Brave existant pour forcer la recréation.
    """
    global _brave_api_key_cache, _brave_search_service
    _brave_api_key_cache = key
    # Invalider le service pour qu'il soit recréé avec la nouvelle clé
    if _brave_search_service is not None:
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_brave_search_service.close())
        except RuntimeError:
            pass
        _brave_search_service = None


_searxng_url_cache: str | None = None


def _get_searxng_url() -> str | None:
    """Récupère l'URL SearXNG (env ou cache)."""
    import os

    env_url = os.environ.get("SEARXNG_URL")
    if env_url:
        return env_url

    return _searxng_url_cache


def set_searxng_url(url: str | None) -> None:
    """Met à jour l'URL SearXNG en cache."""
    global _searxng_url_cache, _searxng_service
    _searxng_url_cache = url
    if _searxng_service is not None:
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_searxng_service.close())
        except RuntimeError:
            pass
        _searxng_service = None


# Tool definition for LLM function calling
WEB_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Recherche sur le web pour trouver des informations actuelles. Utilise cette fonction quand l'utilisateur demande des informations récentes, des actualités, des données que tu ne connais pas, ou quand il te demande d'analyser un site web, une entreprise, un produit ou un service. Pour analyser un site, recherche son URL ou son nom.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "La requête de recherche (en français ou anglais)",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Nombre maximum de résultats (défaut: 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
}


async def execute_web_search(arguments: dict[str, Any]) -> str:
    """Execute a web search tool call."""
    query = arguments.get("query", "")
    max_results = arguments.get("max_results", 5)

    if not query:
        return "Erreur: requête de recherche vide"

    service = get_web_search_service()
    response = await service.search(query, max_results=max_results)
    return service.format_results_for_llm(response)


# Définition de l'outil browser pour le LLM (tool calling)
BROWSER_TOOL = {
    "type": "function",
    "function": {
        "name": "browser_navigate",
        "description": "Navigue sur une page web, extrait le contenu textuel et peut interagir avec la page. Utilise cette fonction quand l'utilisateur demande d'aller sur un site web spécifique, d'extraire des données d'une page, de remplir un formulaire, ou de chercher des informations sur un site précis.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "L'URL complète de la page web à visiter (ex: https://example.com)",
                },
                "action": {
                    "type": "string",
                    "enum": ["navigate", "extract", "click", "fill", "links", "screenshot"],
                    "description": "L'action à effectuer sur la page",
                    "default": "navigate",
                },
                "selector": {
                    "type": "string",
                    "description": "Sélecteur CSS pour cibler un élément (optionnel, pour click/fill/extract)",
                },
                "value": {
                    "type": "string",
                    "description": "Valeur à saisir dans un champ (pour l'action fill)",
                },
            },
            "required": ["url"],
        },
    },
}


async def execute_browser_action(arguments: dict[str, Any]) -> str:
    """Exécute une action browser via le browser agent."""
    from app.services.browser_agent import get_browser_agent

    agent = get_browser_agent()
    url = arguments.get("url", "")
    action = arguments.get("action", "navigate")
    selector = arguments.get("selector")
    value = arguments.get("value")

    # Pour navigate, on doit d'abord naviguer
    if action == "navigate" or not agent._page:
        result = await agent.navigate(url)
        if not result.success:
            return f"Erreur navigation : {result.error}"
        if action == "navigate":
            return f"Page chargée : {result.title}\n\nContenu :\n{result.content}"

    # Ensuite exécuter l'action demandée
    result = await agent.execute_action(action, {
        "selector": selector,
        "value": value,
    })

    if not result.success:
        return f"Erreur {action} : {result.error}"

    return result.content or f"Action {action} exécutée avec succès"
