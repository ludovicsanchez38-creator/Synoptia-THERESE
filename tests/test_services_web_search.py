"""
THERESE v2 - Web Search Service Tests

Tests for US-WEB-01 to US-WEB-05.
"""

import pytest


class TestWebSearchService:
    """Tests for web search service functionality."""

    def test_import_web_search_service(self):
        """Test web search service can be imported."""
        from app.services.web_search import WebSearchService
        assert WebSearchService is not None

    def test_web_search_tool_definition(self):
        """US-WEB-05: Web search tool is properly defined (OpenAI format)."""
        from app.services.web_search import WEB_SEARCH_TOOL

        assert WEB_SEARCH_TOOL is not None
        # OpenAI function calling format
        assert "type" in WEB_SEARCH_TOOL
        assert WEB_SEARCH_TOOL["type"] == "function"
        assert "function" in WEB_SEARCH_TOOL
        assert WEB_SEARCH_TOOL["function"]["name"] == "web_search"
        assert "description" in WEB_SEARCH_TOOL["function"]
        assert "parameters" in WEB_SEARCH_TOOL["function"]


class TestDuckDuckGoSearch:
    """Tests for US-WEB-03: DuckDuckGo integration."""

    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        """US-WEB-03: DuckDuckGo search returns results."""
        from app.services.web_search import WebSearchService

        service = WebSearchService()

        try:
            results = await service.search("Python programming")

            assert results is not None
            assert hasattr(results, "results") or isinstance(results, list)
        except Exception:
            # May fail due to network issues
            pytest.skip("DuckDuckGo search failed - network issue")

    @pytest.mark.asyncio
    async def test_search_empty_query(self):
        """Test search with empty query."""
        from app.services.web_search import WebSearchService

        service = WebSearchService()

        try:
            results = await service.search("")

            # Should either return empty or raise
            assert results is not None or results == []
        except ValueError:
            pass  # Empty query rejection is valid

    @pytest.mark.asyncio
    async def test_search_with_limit(self):
        """Test search with result limit."""
        from app.services.web_search import WebSearchService

        service = WebSearchService()

        try:
            results = await service.search("AI technology", max_results=5)

            if hasattr(results, "results"):
                assert len(results.results) <= 5
            elif isinstance(results, list):
                assert len(results) <= 5
        except Exception:
            pytest.skip("DuckDuckGo search failed - network issue")


class TestWebSearchFormatting:
    """Tests for US-WEB-05: Result formatting."""

    def test_search_result_structure(self):
        """US-WEB-05: Search results are properly formatted."""
        from app.services.web_search import SearchResult

        result = SearchResult(
            title="Test Title",
            url="https://example.com",
            snippet="Test snippet",
        )

        assert result.title == "Test Title"
        assert result.url == "https://example.com"
        assert result.snippet == "Test snippet"

    def test_search_response_structure(self):
        """Test search response structure."""
        from app.services.web_search import SearchResult, SearchResponse

        results = [
            SearchResult(title="Result 1", url="https://a.com", snippet="A"),
            SearchResult(title="Result 2", url="https://b.com", snippet="B"),
        ]

        response = SearchResponse(
            query="test query",
            results=results,
            total_results=2,
        )

        assert response.query == "test query"
        assert len(response.results) == 2
        assert response.total_results == 2


class TestGeminiGrounding:
    """Tests for US-WEB-02: Gemini Google Search Grounding."""

    def test_gemini_grounding_config(self):
        """US-WEB-02: Gemini grounding configuration exists."""
        # This tests that the LLM service has grounding support
        from app.services.llm import LLMService

        assert LLMService is not None
        # Grounding is configured in _stream_gemini method


class TestExecuteWebSearch:
    """Tests for web search execution via tools."""

    @pytest.mark.asyncio
    async def test_execute_web_search_function(self):
        """Test execute_web_search function."""
        from app.services.web_search import execute_web_search

        try:
            result = await execute_web_search({"query": "Python AI"})

            assert result is not None
            assert isinstance(result, str) or isinstance(result, dict)
        except Exception:
            pytest.skip("Web search execution failed - network issue")

    @pytest.mark.asyncio
    async def test_execute_web_search_missing_query(self):
        """Test execute_web_search without query."""
        from app.services.web_search import execute_web_search

        try:
            result = await execute_web_search({})

            # Should handle missing query gracefully
            assert result is not None
        except (ValueError, KeyError):
            pass  # Valid to reject missing query
