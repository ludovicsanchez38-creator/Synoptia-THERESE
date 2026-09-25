"""B-1300 : la synchro tableur des contacts lisait les étiquettes par
parse_tags_json (découpage brut, espaces gardés, tableau JSON coupé en deux)
au lieu de la règle unique etiquettes_lues des deux autres portes (B-1264,
B-1272, B-1275, B-1287). Lecteur X, passe 5."""

import json

import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("cellule", "attendu"),
    [("vip, client", ["vip", "client"]), ('["Paris, France", "vip"]', ["Paris, France", "vip"])],
)
async def test_la_synchro_suit_la_regle_unique(db_session, cellule, attendu):
    from app.services.crm_utils import upsert_contact

    contact, _ = await upsert_contact(db_session, {"ID": "crm-tags", "Nom": "Jeanne Martin", "Tags": cellule})
    assert json.loads(contact.tags) == attendu, contact.tags
