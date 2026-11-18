"""Les montants issus des tarifs en dollars annoncent leur unité aux clients API."""

import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["limits", "usage/daily", "usage/monthly"])
async def test_les_reponses_de_budget_precisent_la_devise(client, route):
    reponse = await client.get(f"/api/escalation/{route}")
    assert reponse.status_code == 200, reponse.text
    donnees = reponse.json()
    assert donnees["currency"] == "USD"
    if route == "limits":
        assert donnees["monthly_budget_usd"] == donnees["monthly_budget_eur"]
    elif route == "usage/monthly":
        assert donnees["budget_usd"] == donnees["budget_eur"]
        assert donnees["cost_usd"] == donnees["cost_eur"]
    else:
        assert donnees["cost_usd"] == donnees["cost_eur"]
