"""B-1190 : sans périmètre, la déduplication de create_contact et create_project ferme aussi (reste de B-1110).

Attendu (B-1110, memory_tools.py:898-904, tests/test_b1110_…) : sans périmètre
(conversation absente ou introuvable, `_perimetre_de_conversation` rend
(None, None)), l'outil ferme : carnet général seul. Le docstring de
`_find_existing_contact` (memory_tools.py:387-389) et de `_cloison_projets`
(:268-272) dit la fuite fermée : « renvoyait le nom ET l'identifiant d'un
homonyme du projet A ». Règle contraire, plus ancienne : `_cloison_contacts`
:403-405 « scope is None : pas de cloison, comportement d'avant la 0.43 ».

Chemin atteignable : create_contact et create_project exigent une carte
(requires_confirmation vrai) ; la carte garde son conversation_id
(register_pending) et /confirm-tool relit le périmètre. Conversation supprimée
entre la carte et le clic « Confirmer » : (None, None).
"""

import json

import pytest


async def _dossier_avec_homonymes(client):
    projet_a = (await client.post("/api/memory/projects", json={"name": "Client A"})).json()["id"]
    projet_b = (await client.post("/api/memory/projects", json={"name": "Client B"})).json()["id"]
    contact = await client.post(
        "/api/memory/contacts",
        json={"first_name": "Jean", "last_name": "Dupont", "scope": "project", "scope_id": projet_a},
    )
    assert contact.status_code in (200, 201), contact.text
    for projet in (projet_a, projet_b):
        r = await client.post(
            "/api/memory/projects",
            json={"name": "Chantier confidentiel", "scope": "project", "scope_id": projet},
        )
        assert r.status_code in (200, 201), r.text
    return projet_a, contact.json()["id"]


async def _conversation_supprimee(client):
    conv = (await client.post("/api/chat/conversations", json={"title": "x"})).json()["id"]
    assert (await client.delete(f"/api/chat/conversations/{conv}")).status_code in (200, 204)
    return conv


@pytest.mark.asyncio
async def test_create_contact_confirme_apres_suppression_ne_revele_pas_l_homonyme(client):
    from app.services.tool_confirmations import register_pending, requires_confirmation

    assert requires_confirmation("create_contact")
    _, id_homonyme = await _dossier_avec_homonymes(client)
    conv = await _conversation_supprimee(client)
    carte = register_pending("create_contact", {"first_name": "Jean", "last_name": "Dupont"}, conversation_id=conv)
    reponse = await client.post("/api/chat/confirm-tool", json={"confirmation_id": carte, "approved": True})
    assert reponse.status_code == 200, reponse.text
    resultat = reponse.json()["result"]
    assert id_homonyme not in resultat and "already_existed" not in resultat, (
        f"conversation supprimée ({conv}) : create_contact rend {resultat}"
    )


@pytest.mark.asyncio
async def test_create_project_confirme_apres_suppression_ne_revele_pas_les_homonymes(client):
    from app.services.tool_confirmations import register_pending

    await _dossier_avec_homonymes(client)
    conv = await _conversation_supprimee(client)
    carte = register_pending("create_project", {"name": "Chantier confidentiel"}, conversation_id=conv)
    reponse = await client.post("/api/chat/confirm-tool", json={"confirmation_id": carte, "approved": True})
    resultat = reponse.json()["result"]
    assert "Plusieurs projets" not in resultat, f"create_project rend {resultat}"


@pytest.mark.asyncio
async def test_temoin_conversation_libre_ferme(client):
    """Témoin : une conversation qui existe (portée « global ») ne voit pas l'homonyme."""
    from app.services.tool_confirmations import register_pending

    _, id_homonyme = await _dossier_avec_homonymes(client)
    conv = (await client.post("/api/chat/conversations", json={"title": "x"})).json()["id"]
    carte = register_pending("create_contact", {"first_name": "Jean", "last_name": "Dupont"}, conversation_id=conv)
    reponse = await client.post("/api/chat/confirm-tool", json={"confirmation_id": carte, "approved": True})
    resultat = reponse.json()["result"]
    assert id_homonyme not in resultat, resultat
    assert json.loads(resultat).get("already_existed") is not True, resultat
