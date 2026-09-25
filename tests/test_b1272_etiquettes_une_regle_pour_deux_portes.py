"""B-1272, B-1275 : une règle unique pour les étiquettes importées.

- B-1272 : l'import de fichier CRM stockait tel quel une liste d'étiquettes
  non textuelles ([1, 2]) ; la fiche relue ne passait plus le schéma de
  réponse et la liste des contacts tombait en 500 (B-1264 ne fermait que
  l'import JSON des sauvegardes).
- B-1275 : l'import JSON des sauvegardes jetait sans trace des étiquettes en
  texte (« vip,client »), que l'export garde à dessein et que l'import CRM
  découpe sur les virgules.
Revue du diff, passe 5 (cas G)."""

import json

import pytest
from app.models.entities import Contact
from app.services.crm_import import CRMImportService
from sqlmodel import select


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("etiquettes", "attendu"),
    [([1, 2], None), (["vip", 3, " btp "], ["vip", "btp"]), ("vip, client", ["vip", "client"])],
)
async def test_import_crm_des_etiquettes(db_session, etiquettes, attendu):
    contenu = json.dumps([{"first_name": "Crm", "last_name": "Exemple", "tags": etiquettes}]).encode()
    res = await CRMImportService(db_session).import_contacts(contenu, filename="c.json")
    await db_session.commit()
    db_session.expire_all()
    fiche = (await db_session.execute(select(Contact))).scalar_one()
    lues = json.loads(fiche.tags) if fiche.tags else None
    assert lues == attendu, (fiche.tags, [e.message for e in res.errors])


@pytest.mark.asyncio
async def test_import_json_des_etiquettes_en_texte(client):
    resp = await client.post(
        "/api/data/import/contacts",
        json={"contacts": [{"id": "c-legacy", "first_name": "Legacy", "tags": "vip,client"}]},
    )
    assert resp.status_code == 200, resp.text
    fiche = next(c for c in (await client.get("/api/memory/contacts")).json() if c["id"] == "c-legacy")
    assert fiche["tags"] == ["vip", "client"], fiche
