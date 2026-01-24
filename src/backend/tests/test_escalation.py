"""
THERESE v2 - Escalation Tests

Tests for US-ESC-01 to US-ESC-05.
"""

import pytest
from httpx import AsyncClient


class TestCostEstimation:
    """Tests for US-ESC-02: Cost estimation."""

    @pytest.mark.asyncio
    async def test_estimate_cost(self, async_client: AsyncClient):
        """Test cost estimation for a request."""
        response = await async_client.post(
            "/api/escalation/estimate-cost",
            json={
                "model": "claude-sonnet-4-5-20250929",
                "input_tokens": 1000,
                "output_tokens": 500,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert "estimated_cost_eur" in data
        assert data["estimated_cost_eur"] > 0
        assert data["input_tokens"] == 1000
        assert data["output_tokens"] == 500

    @pytest.mark.asyncio
    async def test_get_token_prices(self, async_client: AsyncClient):
        """Test getting token prices."""
        response = await async_client.get("/api/escalation/prices")
        assert response.status_code == 200

        data = response.json()
        assert "prices" in data
        assert "currency" in data
        assert data["currency"] == "EUR"

        # Check some models have pricing
        prices = data["prices"]
        assert "claude-sonnet-4-5-20250929" in prices
        assert "gpt-4o" in prices


class TestTokenLimits:
    """Tests for US-ESC-03: Token limits."""

    @pytest.mark.asyncio
    async def test_get_limits_defaults(self, async_client: AsyncClient):
        """Test getting default token limits."""
        response = await async_client.get("/api/escalation/limits")
        assert response.status_code == 200

        data = response.json()
        assert "max_input_tokens" in data
        assert "max_output_tokens" in data
        assert "daily_input_limit" in data
        assert "monthly_budget_eur" in data

    @pytest.mark.asyncio
    async def test_set_limits(self, async_client: AsyncClient):
        """Test setting token limits."""
        response = await async_client.post(
            "/api/escalation/limits",
            json={
                "max_input_tokens": 10000,
                "max_output_tokens": 5000,
                "daily_input_limit": 600000,
                "daily_output_limit": 150000,
                "monthly_budget_eur": 100.0,
                "warn_at_percentage": 75,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["max_input_tokens"] == 10000
        assert data["monthly_budget_eur"] == 100.0

    @pytest.mark.asyncio
    async def test_check_limits_allowed(self, async_client: AsyncClient):
        """Test checking limits - allowed request."""
        response = await async_client.post(
            "/api/escalation/check-limits",
            params={"input_tokens": 1000},
        )
        assert response.status_code == 200

        data = response.json()
        assert "allowed" in data
        assert "warnings" in data
        assert "errors" in data

    @pytest.mark.asyncio
    async def test_check_limits_exceeded(self, async_client: AsyncClient):
        """Test checking limits - exceeded request."""
        # Set low limits
        await async_client.post(
            "/api/escalation/limits",
            json={
                "max_input_tokens": 100,
                "max_output_tokens": 100,
                "daily_input_limit": 500000,
                "daily_output_limit": 100000,
                "monthly_budget_eur": 50.0,
                "warn_at_percentage": 80,
            },
        )

        # Check with tokens exceeding limit
        response = await async_client.post(
            "/api/escalation/check-limits",
            params={"input_tokens": 1000},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["allowed"] is False
        assert len(data["errors"]) > 0


class TestUsageHistory:
    """Tests for US-ESC-04: Usage history."""

    @pytest.mark.asyncio
    async def test_get_daily_usage(self, async_client: AsyncClient):
        """Test getting daily usage."""
        response = await async_client.get("/api/escalation/usage/daily")
        assert response.status_code == 200

        data = response.json()
        assert "date" in data
        assert "input_tokens" in data
        assert "output_tokens" in data
        assert "cost_eur" in data

    @pytest.mark.asyncio
    async def test_get_monthly_usage(self, async_client: AsyncClient):
        """Test getting monthly usage."""
        response = await async_client.get("/api/escalation/usage/monthly")
        assert response.status_code == 200

        data = response.json()
        assert "month" in data
        assert "input_tokens" in data
        assert "cost_eur" in data
        assert "budget_eur" in data

    @pytest.mark.asyncio
    async def test_get_usage_history(self, async_client: AsyncClient):
        """Test getting usage history."""
        response = await async_client.get("/api/escalation/usage/history?limit=10")
        assert response.status_code == 200

        data = response.json()
        assert "history" in data
        assert "count" in data

    @pytest.mark.asyncio
    async def test_get_usage_stats(self, async_client: AsyncClient):
        """Test getting usage statistics."""
        response = await async_client.get("/api/escalation/usage/stats")
        assert response.status_code == 200

        data = response.json()
        assert "daily" in data
        assert "monthly" in data
        assert "limits" in data


class TestUncertaintyDetection:
    """Tests for US-ESC-01: Uncertainty detection."""

    @pytest.mark.asyncio
    async def test_check_uncertainty_confident(self, async_client: AsyncClient):
        """Test checking a confident response."""
        response = await async_client.post(
            "/api/escalation/check-uncertainty",
            json={
                "response": "Le resultat est 42. La formule utilisee est E=mc^2."
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["is_uncertain"] is False
        assert data["confidence_level"] == "high"
        assert data["confidence_score"] >= 80

    @pytest.mark.asyncio
    async def test_check_uncertainty_uncertain(self, async_client: AsyncClient):
        """Test checking an uncertain response."""
        response = await async_client.post(
            "/api/escalation/check-uncertainty",
            json={
                "response": "Je ne suis pas certain, mais je pense que c'est peut-etre 42. Il est possible que ce soit autre chose."
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["is_uncertain"] is True
        assert data["confidence_level"] in ["low", "medium"]
        assert len(data["uncertainty_phrases"]) > 0


class TestContextTruncation:
    """Tests for US-ESC-05: Context truncation info."""

    @pytest.mark.asyncio
    async def test_get_context_info(self, async_client: AsyncClient):
        """Test getting context window information."""
        response = await async_client.get("/api/escalation/context-info")
        assert response.status_code == 200

        data = response.json()
        assert "context_limits" in data
        assert "truncation_policy" in data
        assert "recommendation" in data

        # Check some models have context limits
        limits = data["context_limits"]
        assert "claude-sonnet-4-5-20250929" in limits
        assert limits["claude-sonnet-4-5-20250929"] == 200000


class TestEscalationStatus:
    """Tests for combined escalation status."""

    @pytest.mark.asyncio
    async def test_get_escalation_status(self, async_client: AsyncClient):
        """Test getting combined escalation status."""
        response = await async_client.get("/api/escalation/status")
        assert response.status_code == 200

        data = response.json()
        assert "daily_usage" in data
        assert "monthly_usage" in data
        assert "limits" in data


class TestTokenTrackerUnit:
    """Unit tests for token tracker."""

    def test_estimate_cost(self):
        """Test cost estimation calculation."""
        from app.services.token_tracker import get_token_tracker

        tracker = get_token_tracker()

        # Claude Sonnet: $3/1M input, $15/1M output
        cost = tracker.estimate_cost(
            "claude-sonnet-4-5-20250929",
            input_tokens=1000000,
            output_tokens=100000,
        )
        expected = 3.00 + 1.50  # $3 input + $1.50 output
        assert abs(cost - expected) < 0.01

    def test_record_usage(self):
        """Test recording usage."""
        from app.services.token_tracker import get_token_tracker

        tracker = get_token_tracker()
        initial_count = len(tracker._usage_history)

        record = tracker.record_usage(
            conversation_id="test-conv",
            model="gpt-4o",
            provider="openai",
            input_tokens=1000,
            output_tokens=500,
        )

        assert record.input_tokens == 1000
        assert record.output_tokens == 500
        assert record.cost_eur > 0
        assert len(tracker._usage_history) == initial_count + 1

    def test_detect_uncertainty(self):
        """Test uncertainty detection."""
        from app.services.token_tracker import detect_uncertainty

        # Confident response
        confident = detect_uncertainty("Le resultat est exactement 42.")
        assert confident["is_uncertain"] is False

        # Uncertain response
        uncertain = detect_uncertainty(
            "Je ne suis pas certain, mais je pense que c'est peut-etre correct."
        )
        assert uncertain["is_uncertain"] is True
        assert len(uncertain["uncertainty_phrases"]) >= 2
