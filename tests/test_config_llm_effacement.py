"""B-607 (persona Jean, c4) : « Configurer plus tard » doit pouvoir défaire un
fournisseur enregistré un écran plus tôt. DELETE /api/config/llm efface les
trois préférences du service d'IA."""

from __future__ import annotations

import pytest
from sqlalchemy import select


@pytest.mark.asyncio
async def test_effacer_la_configuration_ia_retire_les_preferences(client, db_session):
    from app.models.entities import Preference

    pose = await client.post("/api/config/llm", json={"provider": "ollama", "model": "gemma4-tia:latest"})
    assert pose.status_code == 200, pose.text
    cles = {p.key for p in (await db_session.execute(select(Preference).where(Preference.key.like("llm_%")))).scalars().all()}
    assert "llm_provider" in cles

    effacement = await client.delete("/api/config/llm")
    assert effacement.status_code == 200, effacement.text

    db_session.expire_all()
    restantes = {p.key for p in (await db_session.execute(select(Preference).where(Preference.key.in_(["llm_provider", "llm_model", "llm_effort"])))).scalars().all()}
    assert restantes == set(), restantes
