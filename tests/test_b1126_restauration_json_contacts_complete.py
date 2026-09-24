"""B-1126 (cycle 12, réparé au cycle 13) : la restauration JSON des contacts
rend tout ce que l'export a écrit.

`/api/data/import/contacts` ne relisait que l'identité, le téléphone, les
notes et les étiquettes : périmètre, étape, score, source, adresse postale,
dates et surtout champs RGPD étaient perdus. Un contact exclu de la purge
redevenait purgeable, un contact cloisonné à un projet redevenait global.
"""

import pytest
from app.models.entities import Contact

EXPORT = {
    "id": "restau-b1126",
    "first_name": "Léa",
    "last_name": "Martin",
    "company": "Brasserie Lumière",
    "email": "lea@exemple.fr",
    "phone": "+33 6 12 34 56 78",
    "address": "3 rue des Lilas, Manosque",
    "notes": "Rappeler en octobre",
    "tags": ["client", "bière"],
    "extra_data": {"siret": "12345678900011"},
    "stage": "signature",
    "score": 82,
    "source": "salon",
    "last_interaction": "2026-09-01T10:00:00",
    "next_follow_up": "2026-10-01T00:00:00",
    "rgpd_base_legale": "contrat",
    "rgpd_date_collecte": "2025-01-15T00:00:00",
    "rgpd_date_expiration": "2028-01-15T00:00:00",
    "rgpd_consentement": True,
    "purge_excluded": True,
    "scope": "project",
    "scope_id": "projet-grange",
    "created_at": "2025-01-15T09:30:00",
    "updated_at": "2026-09-01T10:00:00",
}


@pytest.mark.asyncio
async def test_la_restauration_rend_tous_les_champs_exportes(client, db_session):
    resp = await client.post("/api/data/import/contacts", json={"contacts": [EXPORT]})
    assert resp.status_code == 200, resp.text
    assert resp.json()["imported"] == 1

    fiche = await db_session.get(Contact, "restau-b1126")
    assert fiche.purge_excluded is True
    assert fiche.rgpd_consentement is True
    assert (fiche.scope, fiche.scope_id) == ("project", "projet-grange")
    assert (fiche.stage, fiche.score, fiche.source) == ("signature", 82, "salon")
    assert fiche.address == "3 rue des Lilas, Manosque"
    assert fiche.rgpd_base_legale == "contrat"
    assert fiche.rgpd_date_expiration.strftime("%Y-%m-%d") == "2028-01-15"
    assert fiche.created_at.strftime("%Y-%m-%d %H:%M") == "2025-01-15 09:30"
    assert "12345678900011" in (fiche.extra_data or "")


@pytest.mark.asyncio
async def test_une_valeur_hors_regle_prend_le_defaut_sans_faire_echouer(client, db_session):
    abime = EXPORT | {"id": "restau-b1126-abime", "scope": "partout", "score": 10**9, "stage": "", "created_at": "jamais", "purge_excluded": "peut-être"}
    resp = await client.post("/api/data/import/contacts", json={"contacts": [abime]})
    assert resp.status_code == 200, resp.text
    fiche = await db_session.get(Contact, "restau-b1126-abime")
    assert (fiche.scope, fiche.stage, fiche.purge_excluded) == ("global", "contact", False)
    assert 0 <= fiche.score <= 100
    assert fiche.created_at is not None
