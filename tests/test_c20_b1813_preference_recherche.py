"""La préférence de recherche et le garde effectif restent cohérents."""

import pytest
from app.services.web_search import recherche_web_autorisee


@pytest.mark.asyncio
async def test_preference_generique_ne_laisse_pas_la_recherche_autorisee(client):
    active = await client.post("/api/config/web-search", params={"enabled": "true"})
    assert active.status_code == 200
    assert recherche_web_autorisee() is True

    modification = await client.put(
        "/api/config/preferences/web_search_enabled", json={"value": False}
    )
    if modification.status_code == 200:
        assert recherche_web_autorisee() is False
    else:
        assert 400 <= modification.status_code < 500
        assert recherche_web_autorisee() is True
        etat = await client.get("/api/config/web-search")
        assert etat.status_code == 200
        assert etat.json()["enabled"] is True


@pytest.mark.asyncio
async def test_preference_generique_ne_contourne_pas_le_reglage_de_recherche(client):
    await client.post("/api/config/web-search", params={"enabled": "false"})
    creation = await client.post(
        "/api/config/preferences", json={"key": "web_search_enabled", "value": True}
    )
    suppression = await client.delete("/api/config/preferences/web_search_enabled")

    assert 400 <= creation.status_code < 500
    assert 400 <= suppression.status_code < 500
    assert recherche_web_autorisee() is False
    assert (await client.get("/api/config/web-search")).json()["enabled"] is False
