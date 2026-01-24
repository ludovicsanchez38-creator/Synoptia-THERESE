"""
THERESE v2 - Performance Tests

Tests for US-PERF-01 to US-PERF-05.
"""

import pytest
import time
from httpx import AsyncClient


class TestStreamingMetrics:
    """Tests for US-PERF-01: First token latency tracking."""

    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, async_client: AsyncClient):
        """Test getting performance metrics."""
        response = await async_client.get("/api/perf/metrics")
        assert response.status_code == 200

        data = response.json()
        assert "total_requests" in data
        assert "avg_first_token_ms" in data
        assert "meets_sla" in data

    @pytest.mark.asyncio
    async def test_get_recent_metrics(self, async_client: AsyncClient):
        """Test getting recent streaming metrics."""
        response = await async_client.get("/api/perf/metrics/recent?limit=10")
        assert response.status_code == 200

        data = response.json()
        assert "metrics" in data
        assert "count" in data


class TestConversationPagination:
    """Tests for US-PERF-02: Progressive loading."""

    @pytest.mark.asyncio
    async def test_get_conversations_count(self, async_client: AsyncClient):
        """Test getting total conversation count."""
        response = await async_client.get("/api/perf/conversations/count")
        assert response.status_code == 200

        data = response.json()
        assert "total" in data
        assert isinstance(data["total"], int)

    @pytest.mark.asyncio
    async def test_list_conversations_pagination(self, async_client: AsyncClient):
        """Test conversations list with pagination."""
        # Get first page
        response = await async_client.get("/api/chat/conversations?limit=10&offset=0")
        assert response.status_code == 200

        # Get second page
        response = await async_client.get("/api/chat/conversations?limit=10&offset=10")
        assert response.status_code == 200


class TestMemoryManagement:
    """Tests for US-PERF-03: Memory leak prevention."""

    @pytest.mark.asyncio
    async def test_get_memory_stats(self, async_client: AsyncClient):
        """Test getting memory statistics."""
        response = await async_client.get("/api/perf/memory")
        assert response.status_code == 200

        data = response.json()
        assert "uptime_hours" in data
        assert "gc_stats" in data
        assert "last_cleanup_ago_minutes" in data

    @pytest.mark.asyncio
    async def test_trigger_cleanup(self, async_client: AsyncClient):
        """Test triggering memory cleanup."""
        response = await async_client.post("/api/perf/memory/cleanup")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "results" in data
        assert "stats" in data


class TestSearchOptimization:
    """Tests for US-PERF-04: Fast search on 1000+ conversations."""

    @pytest.mark.asyncio
    async def test_search_conversations(self, async_client: AsyncClient):
        """Test fast conversation search."""
        response = await async_client.get("/api/perf/conversations/search?q=test")
        assert response.status_code == 200

        data = response.json()
        assert "results" in data
        assert "source" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_search_requires_query(self, async_client: AsyncClient):
        """Test search requires a query parameter."""
        response = await async_client.get("/api/perf/conversations/search")
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_reindex_conversations(self, async_client: AsyncClient):
        """Test rebuilding search index."""
        response = await async_client.post("/api/perf/conversations/reindex")
        assert response.status_code == 200

        data = response.json()
        assert "indexed" in data
        assert "stats" in data


class TestPowerOptimization:
    """Tests for US-PERF-05: Battery optimization."""

    @pytest.mark.asyncio
    async def test_get_power_settings(self, async_client: AsyncClient):
        """Test getting power settings."""
        response = await async_client.get("/api/perf/power")
        assert response.status_code == 200

        data = response.json()
        assert "health_check_interval" in data
        assert "battery_saver_mode" in data
        assert "reduce_animations" in data

    @pytest.mark.asyncio
    async def test_update_power_settings(self, async_client: AsyncClient):
        """Test updating power settings."""
        response = await async_client.post(
            "/api/perf/power",
            params={"health_check_interval": 60},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["health_check_interval"] == 60

    @pytest.mark.asyncio
    async def test_enable_battery_saver(self, async_client: AsyncClient):
        """Test enabling battery saver mode."""
        response = await async_client.post(
            "/api/perf/power/battery-saver?enabled=true"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["battery_saver_enabled"] is True
        assert data["settings"]["battery_saver_mode"] is True
        assert data["settings"]["health_check_interval"] == 120  # Extended

    @pytest.mark.asyncio
    async def test_disable_battery_saver(self, async_client: AsyncClient):
        """Test disabling battery saver mode."""
        response = await async_client.post(
            "/api/perf/power/battery-saver?enabled=false"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["battery_saver_enabled"] is False
        assert data["settings"]["battery_saver_mode"] is False


class TestPerformanceStatus:
    """Tests for combined performance status."""

    @pytest.mark.asyncio
    async def test_get_performance_status(self, async_client: AsyncClient):
        """Test getting combined performance status."""
        response = await async_client.get("/api/perf/status")
        assert response.status_code == 200

        data = response.json()
        assert "streaming" in data
        assert "memory" in data
        assert "search_index" in data
        assert "power" in data
        assert "conversations_total" in data


class TestSearchIndexUnit:
    """Unit tests for search index functionality."""

    def test_search_index_basic(self):
        """Test basic search index operations."""
        from app.services.performance import SearchIndex

        index = SearchIndex()

        # Index some conversations
        index.index_conversation("conv1", "Meeting with client")
        index.index_conversation("conv2", "Project planning session")
        index.index_conversation("conv3", "Client feedback review")

        # Search
        results = index.search("client")
        assert len(results) == 2
        assert any(r[0] == "conv1" for r in results)
        assert any(r[0] == "conv3" for r in results)

    def test_search_index_prefix_match(self):
        """Test prefix matching in search."""
        from app.services.performance import SearchIndex

        index = SearchIndex()
        index.index_conversation("conv1", "Development tasks")
        index.index_conversation("conv2", "Developer meeting")

        # Search with prefix
        results = index.search("dev")
        assert len(results) == 2

    def test_search_index_stats(self):
        """Test getting index stats."""
        from app.services.performance import SearchIndex

        index = SearchIndex()
        index.index_conversation("conv1", "Test conversation")

        stats = index.get_stats()
        assert stats["indexed_conversations"] == 1
        assert stats["unique_words"] > 0


class TestPerformanceMonitorUnit:
    """Unit tests for performance monitor."""

    def test_streaming_metrics(self):
        """Test streaming metrics recording."""
        from app.services.performance import StreamingMetrics

        metrics = StreamingMetrics(
            conversation_id="test-conv",
            provider="anthropic",
            model="claude-4",
        )

        # Simulate streaming
        time.sleep(0.01)  # Small delay
        latency = metrics.record_first_token()
        assert latency > 0
        assert latency < 1000  # Less than 1 second

        # record_first_token() doesn't count as a token, only record_token() does
        metrics.record_token()
        metrics.record_token()

        summary = metrics.finish()
        assert summary["total_tokens"] == 2
        assert summary["first_token_ms"] > 0
        assert summary["provider"] == "anthropic"

    def test_performance_monitor_singleton(self):
        """Test performance monitor is singleton."""
        from app.services.performance import get_performance_monitor

        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()
        assert monitor1 is monitor2

    def test_performance_monitor_stats(self):
        """Test getting performance stats."""
        from app.services.performance import get_performance_monitor

        monitor = get_performance_monitor()
        stats = monitor.get_stats()

        assert "total_requests" in stats
        assert "avg_first_token_ms" in stats
        assert "meets_sla" in stats
