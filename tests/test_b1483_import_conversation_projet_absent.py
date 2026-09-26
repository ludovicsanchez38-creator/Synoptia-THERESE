"""B-1483 : l'import de conversations recopiait project_id sans vérifier.

La route de rattachement refuse un projet inexistant (404, « rattacher à
un projet inexistant cloisonnerait sur du vide »). L'import recopiait
l'identifiant tel quel : une conversation importée depuis une archive
où le projet manquait se retrouvait cloisonnée sur un projet fantôme, sans
plus voir aucun document ni pouvoir être rattachée ailleurs à l'écran.
"""

import pytest
from sqlmodel import select


async def _conversation(conv_id: str):
    from app.models import database as db_module
    from app.models.entities import Conversation

    async with db_module.AsyncSessionLocal() as session:
        return (await session.execute(
            select(Conversation).where(Conversation.id == conv_id)
        )).scalar_one()


@pytest.mark.asyncio
async def test_un_projet_absent_n_est_pas_recopie(client):
    resp = await client.post(
        "/api/data/import/conversations",
        json={"conversations": [{
            "id": "conv-b1483-fantome", "title": "Chantier Roux",
            "project_id": "projet-qui-n-existe-pas",
            "memory_scope": "project",
            "messages": [{"role": "user", "content": "Où en est le devis ?"}],
        }]},
    )
    assert resp.status_code == 200, resp.text
    conversation = await _conversation("conv-b1483-fantome")
    assert conversation.project_id is None
    # Une politique « project » sans projet cloisonnerait sur du vide.
    assert conversation.memory_scope == "global"


@pytest.mark.asyncio
async def test_un_projet_present_reste_rattache(client):
    from app.models import database as db_module
    from app.models.entities import Project

    async with db_module.AsyncSessionLocal() as session:
        projet = Project(name="Cuisine Roux")
        session.add(projet)
        await session.commit()
        projet_id = projet.id

    resp = await client.post(
        "/api/data/import/conversations",
        json={"conversations": [{
            "id": "conv-b1483-present", "title": "Cuisine",
            "project_id": projet_id, "memory_scope": "project",
            "messages": [],
        }]},
    )
    assert resp.status_code == 200, resp.text
    conversation = await _conversation("conv-b1483-present")
    assert conversation.project_id == projet_id
    assert conversation.memory_scope == "project"
