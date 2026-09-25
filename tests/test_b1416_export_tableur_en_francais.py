"""B-1416 (recette P-146) : l'export tableur des contacts écrivait « Prenom »,
« Telephone », « Stage » et des étapes en identifiants anglais
(« discovery »). Une utilisatrice lit « Prénom », « Téléphone », « Étape »
et « Découverte », les libellés de l'écran. L'aller-retour tient : l'import
compare les en-têtes sans accents (B-1418) et reconnaît le libellé d'étape.
"""

import csv
import io

import pytest
from httpx import AsyncClient


async def _exporter(client: AsyncClient) -> list[dict[str, str]]:
    reponse = await client.post("/api/crm/export/contacts?format=csv")
    assert reponse.status_code == 200, reponse.text
    texte = reponse.content.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(texte)))


@pytest.mark.asyncio
async def test_l_export_parle_francais_et_l_import_le_relit(client: AsyncClient):
    cree = await client.post(
        "/api/memory/contacts",
        json={"first_name": "Nadia", "last_name": "Roux", "phone": "06 11 22 33 44", "stage": "discovery"},
    )
    assert cree.status_code in (200, 201), cree.text

    lignes = await _exporter(client)
    nadia = next(ligne for ligne in lignes if ligne.get("Nom") == "Roux")
    assert {"Prénom", "Téléphone", "Étape"} <= set(nadia), sorted(nadia)
    assert nadia["Étape"] == "Découverte"

    # Aller-retour : la même ligne, réimportée sans identifiant, garde son étape.
    nadia = {**nadia, "ID": "", "Nom": "Roux-bis"}
    tampon = io.StringIO()
    graveur = csv.DictWriter(tampon, fieldnames=list(nadia))
    graveur.writeheader()
    graveur.writerow(nadia)
    importe = await client.post(
        "/api/crm/import/contacts",
        files={"file": ("contacts.csv", tampon.getvalue().encode("utf-8"), "text/csv")},
    )
    assert importe.status_code == 200, importe.text
    assert importe.json()["created"] == 1, importe.json()
    relue = next(ligne for ligne in await _exporter(client) if ligne.get("Nom") == "Roux-bis")
    assert relue["Étape"] == "Découverte"
    assert relue["Téléphone"] == "06 11 22 33 44"


def test_chaque_etape_du_pipeline_a_son_libelle_et_se_relit():
    from app.services.crm_utils import ETAPES_PIPELINE, LIBELLES_ETAPES, etape_depuis_cellule

    assert set(LIBELLES_ETAPES) == ETAPES_PIPELINE
    for identifiant, libelle in LIBELLES_ETAPES.items():
        assert etape_depuis_cellule(libelle) == identifiant
        assert etape_depuis_cellule(libelle.upper()) == identifiant
        assert etape_depuis_cellule(identifiant) == identifiant
    assert etape_depuis_cellule("decouverte") == "discovery"
    assert etape_depuis_cellule("inconnue") is None
