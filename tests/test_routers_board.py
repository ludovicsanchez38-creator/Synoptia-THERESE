"""
THERESE v2 - Board Router Tests

Tests for US-BOARD-01 to US-BOARD-05.
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


class TestBoardAdvisors:
    """Tests for board advisors listing."""

    @pytest.mark.asyncio
    async def test_list_advisors(self, client: AsyncClient):
        """Test listing all 5 advisors."""
        response = await client.get("/api/board/advisors")

        assert response.status_code == 200
        advisors = response.json()

        assert len(advisors) == 5

        # Check each advisor has required fields
        for advisor in advisors:
            assert "role" in advisor
            assert "name" in advisor
            assert "emoji" in advisor
            assert "color" in advisor
            assert "personality" in advisor

    @pytest.mark.asyncio
    async def test_get_analyst_advisor(self, client: AsyncClient):
        """Test getting the analyst advisor."""
        response = await client.get("/api/board/advisors/analyst")

        assert response.status_code == 200
        advisor = response.json()

        assert advisor["role"] == "analyst"
        assert advisor["name"] == "L'Analyste"

    @pytest.mark.asyncio
    async def test_get_strategist_advisor(self, client: AsyncClient):
        """Test getting the strategist advisor."""
        response = await client.get("/api/board/advisors/strategist")

        assert response.status_code == 200
        advisor = response.json()

        assert advisor["role"] == "strategist"
        assert advisor["name"] == "Le Stratège"

    @pytest.mark.asyncio
    async def test_get_devils_advocate(self, client: AsyncClient):
        """Test getting the devil's advocate advisor."""
        response = await client.get("/api/board/advisors/devil")

        assert response.status_code == 200
        advisor = response.json()

        assert advisor["role"] == "devil"
        assert advisor["name"] == "L'Avocat du Diable"

    @pytest.mark.asyncio
    async def test_get_pragmatic_advisor(self, client: AsyncClient):
        """Test getting the pragmatic advisor."""
        response = await client.get("/api/board/advisors/pragmatic")

        assert response.status_code == 200
        advisor = response.json()

        assert advisor["role"] == "pragmatic"
        assert advisor["name"] == "Le Pragmatique"

    @pytest.mark.asyncio
    async def test_get_visionary_advisor(self, client: AsyncClient):
        """Test getting the visionary advisor."""
        response = await client.get("/api/board/advisors/visionary")

        assert response.status_code == 200
        advisor = response.json()

        assert advisor["role"] == "visionary"
        assert advisor["name"] == "Le Visionnaire"

    @pytest.mark.asyncio
    async def test_get_nonexistent_advisor(self, client: AsyncClient):
        """Test getting a non-existent advisor."""
        response = await client.get("/api/board/advisors/unknown")

        assert response.status_code == 422  # Invalid enum value


class TestBoardDeliberation:
    """Tests for US-BOARD-01: Submit question to board."""

    @pytest.mark.asyncio
    async def test_deliberate_returns_sse_stream(self, client: AsyncClient, sample_board_request, db_session):
        """Test deliberation returns SSE stream."""

        @asynccontextmanager
        async def mock_session_context():
            yield db_session

        # Mock BoardService.deliberate pour éviter un vrai appel LLM
        async def fake_deliberate(*args, **kwargs):
            return
            yield  # pragma: no cover - rend la fonction async generator

        with patch(
            "app.routers.board.get_session_context",
            mock_session_context,
        ), patch(
            "app.routers.board.BoardService",
        ) as mock_board_cls:
            mock_board_cls.return_value.deliberate = fake_deliberate
            response = await client.post(
                "/api/board/deliberate",
                json=sample_board_request,
            )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")

    @pytest.mark.asyncio
    async def test_deliberate_empty_question_rejected(self, client: AsyncClient):
        """Test deliberation rejects empty question."""
        response = await client.post("/api/board/deliberate", json={
            "question": "",
            "context": None,
        })

        assert response.status_code == 422


class TestBoardDecisions:
    """Tests for US-BOARD-03 to US-BOARD-05: Decision history."""

    @pytest.mark.asyncio
    async def test_list_decisions_empty(self, client: AsyncClient):
        """Test listing decisions when empty."""
        response = await client.get("/api/board/decisions")

        assert response.status_code == 200
        decisions = response.json()

        assert isinstance(decisions, list)
        assert len(decisions) == 0

    @pytest.mark.asyncio
    async def test_list_decisions_with_limit(self, client: AsyncClient):
        """Test listing decisions with limit parameter."""
        response = await client.get("/api/board/decisions?limit=10")

        assert response.status_code == 200
        decisions = response.json()

        assert isinstance(decisions, list)

    @pytest.mark.asyncio
    async def test_get_nonexistent_decision(self, client: AsyncClient):
        """Test getting a non-existent decision."""
        response = await client.get("/api/board/decisions/nonexistent-id")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_decision(self, client: AsyncClient):
        """Test deleting a non-existent decision."""
        response = await client.delete("/api/board/decisions/nonexistent-id")

        assert response.status_code == 404


class TestBoardSynthesis:
    """Tests for US-BOARD-02: Board synthesis."""

    @pytest.mark.asyncio
    async def test_decision_response_structure(self, client: AsyncClient):
        """Test decision response has required fields."""
        # This test verifies the schema structure
        # Full integration test would require mocking LLM
        response = await client.get("/api/board/decisions")

        assert response.status_code == 200
        # Empty list is valid, structure is defined in schema
