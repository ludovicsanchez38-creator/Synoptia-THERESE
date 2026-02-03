"""
THERESE v2 - Calculator Router Tests

Tests for US-CALC-01 to US-CALC-05.
"""

import pytest
from httpx import AsyncClient


class TestROICalculator:
    """Tests for US-CALC-01: ROI calculation."""

    @pytest.mark.asyncio
    async def test_roi_positive_return(self, client: AsyncClient, sample_roi_request):
        """Test ROI with positive return."""
        response = await client.post("/api/calc/roi", json=sample_roi_request)

        assert response.status_code == 200
        data = response.json()

        assert data["investment"] == 10000
        assert data["gain"] == 15000
        assert data["roi_percent"] == 50.0
        assert data["profit"] == 5000
        assert "interpretation" in data

    @pytest.mark.asyncio
    async def test_roi_negative_return(self, client: AsyncClient):
        """Test ROI with loss."""
        response = await client.post("/api/calc/roi", json={
            "investment": 10000,
            "gain": 8000,
        })

        assert response.status_code == 200
        data = response.json()

        assert data["roi_percent"] == -20.0
        assert data["profit"] == -2000

    @pytest.mark.asyncio
    async def test_roi_zero_investment_rejected(self, client: AsyncClient):
        """Test ROI rejects zero investment."""
        response = await client.post("/api/calc/roi", json={
            "investment": 0,
            "gain": 1000,
        })

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_roi_break_even(self, client: AsyncClient):
        """Test ROI at break-even (0%)."""
        response = await client.post("/api/calc/roi", json={
            "investment": 10000,
            "gain": 10000,
        })

        assert response.status_code == 200
        data = response.json()
        assert data["roi_percent"] == 0.0


class TestICECalculator:
    """Tests for US-CALC-02: ICE scoring."""

    @pytest.mark.asyncio
    async def test_ice_high_score(self, client: AsyncClient, sample_ice_request):
        """Test ICE with high scores."""
        response = await client.post("/api/calc/ice", json=sample_ice_request)

        assert response.status_code == 200
        data = response.json()

        assert data["impact"] == 8
        assert data["confidence"] == 7
        assert data["ease"] == 6
        assert data["score"] == 336  # 8 * 7 * 6
        assert "interpretation" in data

    @pytest.mark.asyncio
    async def test_ice_minimum_score(self, client: AsyncClient):
        """Test ICE with minimum scores (1,1,1)."""
        response = await client.post("/api/calc/ice", json={
            "impact": 1,
            "confidence": 1,
            "ease": 1,
        })

        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 1

    @pytest.mark.asyncio
    async def test_ice_maximum_score(self, client: AsyncClient):
        """Test ICE with maximum scores (10,10,10)."""
        response = await client.post("/api/calc/ice", json={
            "impact": 10,
            "confidence": 10,
            "ease": 10,
        })

        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 1000

    @pytest.mark.asyncio
    async def test_ice_out_of_range_rejected(self, client: AsyncClient):
        """Test ICE rejects values outside 1-10."""
        response = await client.post("/api/calc/ice", json={
            "impact": 11,
            "confidence": 5,
            "ease": 5,
        })

        assert response.status_code == 422


class TestRICECalculator:
    """Tests for US-CALC-03: RICE scoring."""

    @pytest.mark.asyncio
    async def test_rice_standard_calculation(self, client: AsyncClient, sample_rice_request):
        """Test RICE calculation with standard values."""
        response = await client.post("/api/calc/rice", json=sample_rice_request)

        assert response.status_code == 200
        data = response.json()

        # (1000 * 2 * 0.80) / 2 = 800  (confidence is divided by 100)
        assert data["score"] == 800
        assert "interpretation" in data

    @pytest.mark.asyncio
    async def test_rice_low_effort(self, client: AsyncClient):
        """Test RICE with minimal effort."""
        response = await client.post("/api/calc/rice", json={
            "reach": 500,
            "impact": 1,
            "confidence": 50,
            "effort": 0.5,
        })

        assert response.status_code == 200
        data = response.json()
        # (500 * 1 * 0.50) / 0.5 = 500  (confidence is divided by 100)
        assert data["score"] == 500

    @pytest.mark.asyncio
    async def test_rice_zero_effort_rejected(self, client: AsyncClient):
        """Test RICE rejects zero effort."""
        response = await client.post("/api/calc/rice", json={
            "reach": 1000,
            "impact": 2,
            "confidence": 80,
            "effort": 0,
        })

        assert response.status_code == 422


class TestNPVCalculator:
    """Tests for US-CALC-04: NPV calculation."""

    @pytest.mark.asyncio
    async def test_npv_positive_project(self, client: AsyncClient, sample_npv_request):
        """Test NPV with positive outcome."""
        response = await client.post("/api/calc/npv", json=sample_npv_request)

        assert response.status_code == 200
        data = response.json()

        assert data["initial_investment"] == 100000
        assert len(data["cash_flows"]) == 4
        assert data["discount_rate"] == 0.10
        # NPV should be positive for this example
        assert data["npv"] > 0
        assert "interpretation" in data

    @pytest.mark.asyncio
    async def test_npv_negative_project(self, client: AsyncClient):
        """Test NPV with negative outcome."""
        response = await client.post("/api/calc/npv", json={
            "initial_investment": 100000,
            "cash_flows": [10000, 10000, 10000],
            "discount_rate": 0.10,
        })

        assert response.status_code == 200
        data = response.json()
        # NPV should be negative (low cash flows)
        assert data["npv"] < 0

    @pytest.mark.asyncio
    async def test_npv_empty_cashflows_rejected(self, client: AsyncClient):
        """Test NPV rejects empty cash flows."""
        response = await client.post("/api/calc/npv", json={
            "initial_investment": 100000,
            "cash_flows": [],
            "discount_rate": 0.10,
        })

        assert response.status_code == 422


class TestBreakEvenCalculator:
    """Tests for US-CALC-05: Break-even calculation."""

    @pytest.mark.asyncio
    async def test_breakeven_standard(self, client: AsyncClient, sample_breakeven_request):
        """Test break-even with standard values."""
        response = await client.post("/api/calc/break-even", json=sample_breakeven_request)

        assert response.status_code == 200
        data = response.json()

        # Break-even = 50000 / (50 - 20) = 1666.67
        assert data["break_even_units"] == pytest.approx(1666.67, rel=0.01)
        assert data["break_even_revenue"] == pytest.approx(83333.33, rel=0.01)
        assert "interpretation" in data

    @pytest.mark.asyncio
    async def test_breakeven_no_fixed_costs(self, client: AsyncClient):
        """Test break-even with zero fixed costs."""
        response = await client.post("/api/calc/break-even", json={
            "fixed_costs": 0,
            "variable_cost_per_unit": 20,
            "price_per_unit": 50,
        })

        assert response.status_code == 200
        data = response.json()
        assert data["break_even_units"] == 0

    @pytest.mark.asyncio
    async def test_breakeven_margin_too_low_rejected(self, client: AsyncClient):
        """Test break-even with price <= variable cost."""
        response = await client.post("/api/calc/break-even", json={
            "fixed_costs": 50000,
            "variable_cost_per_unit": 50,
            "price_per_unit": 50,
        })

        # Should fail - division by zero margin
        assert response.status_code in [400, 422]


class TestCalculatorsHelp:
    """Test calculator help endpoint."""

    @pytest.mark.asyncio
    async def test_help_lists_all_calculators(self, client: AsyncClient):
        """Test help endpoint lists all 5 calculators."""
        response = await client.get("/api/calc/help")

        assert response.status_code == 200
        data = response.json()

        assert "calculators" in data
        calculators = data["calculators"]
        assert len(calculators) == 5

        names = [c["name"] for c in calculators]
        assert "ROI" in names
        assert "ICE" in names
        assert "RICE" in names
        assert "NPV" in names
        assert "Break-even" in names
