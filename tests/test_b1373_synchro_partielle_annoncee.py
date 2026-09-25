"""B-1373 (persona Hugo, cycle 13) : « Travaux » annonçait « Terminé » pour une
synchronisation qui n'avait rien indexé.

Le plan finissait `applique_partiel` (des fichiers écartés, des conflits), mais
le traitement était clos `done` sans un mot : seul un échec réessayable
produisait un message. Une synchronisation partielle le dit désormais dans la
ligne de « Travaux ».
"""

from pathlib import Path

import pytest

from tests.test_project_sync_service import _creer_projet, qdrant_factice, racine  # noqa: F401


async def _ligne_de_synchro(plan_id: str) -> dict:
    from app.services import traitements

    lignes = [t for t in await traitements.lister(limit=50) if t.get("entity_id") == plan_id]
    assert len(lignes) == 1, lignes
    return lignes[0]


@pytest.mark.asyncio
async def test_une_synchro_partielle_le_dit_dans_travaux(client, racine, qdrant_factice):  # noqa: F811
    from app.services import project_sync_service as svc

    projet = await _creer_projet(client)
    await svc.definir_racine(projet, str(racine))
    plan = await svc.preparer_plan(projet)
    (racine / "un.txt").write_text("modifié après le plan", encoding="utf-8")
    await svc.appliquer_plan(projet, plan.id)

    ligne = await _ligne_de_synchro(plan.id)
    assert ligne["state"] == "done"
    assert ligne["error"], "une synchronisation partielle ne se clôt pas en silence"
    assert "partielle" in ligne["error"] and "1 fichier" in ligne["error"]


@pytest.mark.asyncio
async def test_une_synchro_complete_reste_sans_message(client, racine, qdrant_factice):  # noqa: F811
    from app.services import project_sync_service as svc

    projet = await _creer_projet(client)
    await svc.definir_racine(projet, str(racine))
    plan = await svc.preparer_plan(projet)
    await svc.appliquer_plan(projet, plan.id)

    ligne = await _ligne_de_synchro(plan.id)
    assert ligne["state"] == "done"
    assert not ligne["error"]
    assert Path(racine).exists()
