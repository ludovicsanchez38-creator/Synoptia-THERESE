"""B-1596 (régression de B-1483) : l'import remettait en « global » une
conversation réglée sur « Tous les projets » (memory_scope « all », sans
projet). Seule une politique « project » sans projet se rabat sur global.
"""

import pytest
from sqlmodel import select


@pytest.mark.asyncio
async def test_tous_les_projets_survit_a_l_import(client):
    from app.models import database as db_module
    from app.models.entities import Conversation

    resp = await client.post(
        "/api/data/import/conversations",
        json={"conversations": [{
            "id": "conv-b1596-tous", "title": "Point général",
            "project_id": None, "memory_scope": "all", "messages": [],
        }]},
    )
    assert resp.status_code == 200, resp.text
    async with db_module.AsyncSessionLocal() as session:
        conversation = (await session.execute(
            select(Conversation).where(Conversation.id == "conv-b1596-tous")
        )).scalar_one()
    assert conversation.memory_scope == "all"
