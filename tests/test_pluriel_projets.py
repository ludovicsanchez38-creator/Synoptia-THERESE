"""Finding 7 (revue 30/08) : deux projets du même nom, le chat fusionnait.

`_find_existing_project` prenait `.first()` parmi les globaux : « existe déjà,
je le réutilise » pouvait renvoyer l'id de l'autre client.
"""

from __future__ import annotations

import json

import pytest
from app.models.entities import Project
from app.services.memory_tools import execute_create_project


@pytest.mark.asyncio
async def test_deux_projets_meme_nom_refuse_la_fusion(db_session):
    db_session.add_all([
        Project(id="p-a", name="Chantier", description="client A", scope="global"),
        Project(id="p-b", name="Chantier", description="client B", scope="global"),
    ])
    await db_session.commit()

    resultat = json.loads(
        await execute_create_project({"name": "Chantier"}, db_session)
    )
    assert "error" in resultat
    assert resultat.get("already_existed") is not True
    assert "p-a" not in json.dumps(resultat)
    assert "p-b" not in json.dumps(resultat)
    assert "plusieurs" in resultat["error"].lower()
