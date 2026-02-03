"""
Tests E2E - Calculateurs financiers (via API).

Tests des 5 calculateurs : ROI, ICE, RICE, NPV, Break-even.
Utilise le fixture api_client (httpx) sans navigateur.
"""

import pytest


def test_calculator_roi(api_client):
    """
    POST /api/calc/roi avec investment=10000, gain=15000
    doit retourner roi_percent=50 et profit=5000.
    """
    payload = {
        "investment": 10000,
        "gain": 15000,
    }

    resp = api_client.post("/api/calc/roi", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert data["investment"] == 10000
    assert data["gain"] == 15000
    assert data["roi_percent"] == 50.0
    assert data["profit"] == 5000.0
    assert "interpretation" in data
    assert len(data["interpretation"]) > 0


def test_calculator_ice(api_client):
    """
    POST /api/calc/ice avec impact=8, confidence=7, ease=6
    doit retourner score=336 (8 x 7 x 6).
    """
    payload = {
        "impact": 8,
        "confidence": 7,
        "ease": 6,
    }

    resp = api_client.post("/api/calc/ice", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert data["impact"] == 8
    assert data["confidence"] == 7
    assert data["ease"] == 6
    assert data["score"] == 336.0
    assert "interpretation" in data
    assert len(data["interpretation"]) > 0


def test_calculator_rice(api_client):
    """
    POST /api/calc/rice avec reach=1000, impact=2, confidence=80, effort=2
    doit retourner score=800 ((1000 x 2 x 80) / 2 = 80000 ... check formula).

    Formule RICE : (Reach x Impact x Confidence%) / Effort
    = (1000 x 2 x 80) / 2 = 80000
    Note: confidence est en % (80 = 80%), certaines implementations
    divisent par 100, ce qui donnerait 800. On verifie la coherence.
    """
    payload = {
        "reach": 1000,
        "impact": 2,
        "confidence": 80,
        "effort": 2,
    }

    resp = api_client.post("/api/calc/rice", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert data["reach"] == 1000
    assert data["impact"] == 2
    assert data["confidence"] == 80
    assert data["effort"] == 2

    # La formule RICE standard : (Reach x Impact x Confidence%) / Effort
    # Avec confidence en % : (1000 x 2 x 0.80) / 2 = 800
    # Ou sans conversion : (1000 x 2 x 80) / 2 = 80000
    # Le backend documente score=800 dans l'exemple, donc confidence/100
    assert data["score"] == pytest.approx(800.0, rel=0.01)

    assert "interpretation" in data
    assert len(data["interpretation"]) > 0


def test_calculator_npv(api_client):
    """
    POST /api/calc/npv avec initial_investment=100000,
    cash_flows=[30000, 40000, 50000, 60000], discount_rate=0.10.

    NPV = -100000 + 30000/1.1 + 40000/1.21 + 50000/1.331 + 60000/1.4641
         = -100000 + 27272.73 + 33057.85 + 37565.74 + 40980.81
         ~ 38877.13 (approximation)
    """
    payload = {
        "initial_investment": 100000,
        "cash_flows": [30000, 40000, 50000, 60000],
        "discount_rate": 0.10,
    }

    resp = api_client.post("/api/calc/npv", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert data["initial_investment"] == 100000
    assert data["cash_flows"] == [30000, 40000, 50000, 60000]
    assert data["discount_rate"] == 0.10

    # NPV doit etre positive (projet rentable)
    assert data["npv"] > 0

    # Verification approximative du calcul
    # NPV ~ 38877 (selon le calcul manuel)
    assert data["npv"] == pytest.approx(38877.13, rel=0.02)

    assert "interpretation" in data
    assert len(data["interpretation"]) > 0


def test_calculator_breakeven(api_client):
    """
    POST /api/calc/break-even avec fixed_costs=50000,
    variable_cost_per_unit=20, price_per_unit=50.

    Break-even = 50000 / (50 - 20) = 50000 / 30 ~ 1666.67 unites
    Break-even revenue = 1666.67 x 50 ~ 83333.33 euros
    """
    payload = {
        "fixed_costs": 50000,
        "variable_cost_per_unit": 20,
        "price_per_unit": 50,
    }

    resp = api_client.post("/api/calc/break-even", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert data["fixed_costs"] == 50000
    assert data["variable_cost_per_unit"] == 20
    assert data["price_per_unit"] == 50

    # Break-even units = 50000 / (50 - 20) = 1666.67
    assert data["break_even_units"] == pytest.approx(1666.67, rel=0.01)

    # Break-even revenue = break_even_units x price_per_unit
    assert data["break_even_revenue"] == pytest.approx(83333.33, rel=0.01)

    assert "interpretation" in data
    assert len(data["interpretation"]) > 0
