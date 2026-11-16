"""Le statut de recherche reflète une clé illisible comme la carte générale."""

import pytest
from app.models.entities import Preference
from app.routers import config


@pytest.mark.asyncio
async def test_recherche_n_annonce_pas_brave_quand_la_cle_est_illisible(
    client, db_session, monkeypatch
):
    monkeypatch.delenv("BRAVE_API_KEY", raising=False)
    db_session.add(Preference(key="brave_api_key", value="donnee-chiffree-fictive"))
    await db_session.commit()
    monkeypatch.setattr(config, "is_value_encrypted", lambda _valeur: True)

    def dechiffrer_impossible(_valeur):
        raise ValueError("donnée fictive illisible")

    monkeypatch.setattr(config, "decrypt_value", dechiffrer_impossible)
    general = await client.get("/api/config/")
    recherche = await client.get("/api/config/web-search")
    assert general.status_code == recherche.status_code == 200
    assert general.json()["has_brave_key"] is False
    assert recherche.json()["has_brave_key"] is False
    assert "Brave" not in recherche.json()["providers"]["others"]
