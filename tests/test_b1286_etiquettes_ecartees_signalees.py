"""B-1286 : à l'import de fichier CRM, une mise à jour dont toutes les
étiquettes sont écartées (B-1272) effaçait en silence celles de la fiche ; et
aucune des deux portes ne disait ce qu'elle écartait. Revue du diff, passe 6
(cas H)."""

import json

import pytest
from app.models.entities import Contact
from app.services.crm_import import CRMImportService
from sqlmodel import select


@pytest.mark.asyncio
async def test_des_etiquettes_toutes_ecartees_ne_remplacent_rien(db_session):
    db_session.add(Contact(id="c-h", first_name="Marie", last_name="Exemple", tags=json.dumps(["vip", "client"])))
    await db_session.commit()
    contenu = json.dumps([{"id": "c-h", "first_name": "Marie", "last_name": "Exemple", "tags": [1, 2]}]).encode()
    res = await CRMImportService(db_session).import_contacts(contenu, filename="c.json")
    await db_session.commit()
    db_session.expire_all()
    fiche = (await db_session.execute(select(Contact).where(Contact.id == "c-h"))).scalar_one()
    assert json.loads(fiche.tags) == ["vip", "client"], fiche.tags
    assert any(e.column == "tags" for e in res.errors), [e.message for e in res.errors]


@pytest.mark.asyncio
async def test_une_cellule_vide_efface_toujours(db_session):
    """Un champ présent dans l'export fait foi, y compris vide."""
    db_session.add(Contact(id="c-v", first_name="Jean", last_name="Exemple", tags=json.dumps(["vip"])))
    await db_session.commit()
    contenu = json.dumps([{"id": "c-v", "first_name": "Jean", "last_name": "Exemple", "tags": ""}]).encode()
    res = await CRMImportService(db_session).import_contacts(contenu, filename="c.json")
    await db_session.commit()
    db_session.expire_all()
    fiche = (await db_session.execute(select(Contact).where(Contact.id == "c-v"))).scalar_one()
    assert fiche.tags is None, fiche.tags
    assert not res.errors, [e.message for e in res.errors]


@pytest.mark.asyncio
async def test_l_import_json_dit_ce_qu_il_ecarte(client):
    resp = await client.post(
        "/api/data/import/contacts",
        json={"contacts": [{"id": "c-j", "first_name": "Léa", "tags": ["vip", 3, None]}]},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json().get("etiquettes_ecartees") == 2, resp.json()
