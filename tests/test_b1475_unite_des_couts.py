"""B-1475 (recette P-146, lot 5, KO-7) : l'unité des coûts.

L'écran et le journal disent « $ » et « USD » ; l'API de consommation
renvoyait `cost_eur` et `budget_eur` sans dire l'unité, pour des montants
calculés sur la grille en dollars de GET /prices. Le renommage des champs
(API et base) reste une dette inscrite ; la réponse dit désormais son unité,
comme GET /prices et POST /estimate-cost.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["/api/escalation/usage/stats", "/api/escalation/status"])
async def test_la_consommation_dit_son_unite(client: AsyncClient, route: str):
    reponse = await client.get(route)
    assert reponse.status_code == 200
    assert reponse.json().get("currency") == "USD"
