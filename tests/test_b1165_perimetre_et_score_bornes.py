"""B-1165 (cycle 13, lecteur D) : périmètre et score bornés à l'entrée.

Le périmètre d'une fiche (`scope`) était un texte libre : « Global » était
enregistré tel quel, et aucune règle de cloisonnement (qui compare à
« global », « project », « conversation ») ne le reconnaissait. Le score
acceptait -50 ou un milliard, hors de l'échelle 0-100 de l'écran.
"""

import pytest
from app.models.schemas import ContactCreate, ContactUpdate, ProjectCreate, ProjectUpdate
from pydantic import ValidationError


@pytest.mark.parametrize("schema", [ContactUpdate, ProjectUpdate])
def test_le_perimetre_est_normalise(schema):
    assert schema(scope=" Global ").scope == "global"
    assert schema(scope="PROJECT").scope == "project"


@pytest.mark.parametrize("schema", [ContactUpdate, ProjectUpdate])
def test_un_perimetre_inconnu_est_refuse(schema):
    with pytest.raises(ValidationError):
        schema(scope="partout")


def test_la_creation_normalise_aussi():
    assert ContactCreate(first_name="Léa", scope="Conversation").scope == "conversation"
    assert ProjectCreate(name="Grange", scope="Global").scope == "global"
    with pytest.raises(ValidationError):
        ProjectCreate(name="Grange", scope="partout")


@pytest.mark.parametrize("score", [-50, 101, 10**9])
def test_un_score_hors_echelle_est_refuse(score):
    with pytest.raises(ValidationError):
        ContactUpdate(score=score)


@pytest.mark.asyncio
async def test_le_patch_enregistre_le_perimetre_normalise(client):
    creation = await client.post("/api/memory/contacts", json={"first_name": "Client", "last_name": "Scope"})
    contact_id = creation.json()["id"]
    resp = await client.patch(f"/api/memory/contacts/{contact_id}", json={"scope": "Global", "score": 75})
    assert resp.status_code == 200, resp.text
    fiche = (await client.get(f"/api/memory/contacts/{contact_id}")).json()
    assert (fiche.get("scope", "global"), fiche["score"]) == ("global", 75)
