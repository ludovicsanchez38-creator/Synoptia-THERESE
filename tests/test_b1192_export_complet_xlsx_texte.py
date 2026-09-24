"""B-1192 : l'export complet XLSX (POST /api/crm/export/all, format par défaut)
remplit ses onglets par `_populate_xlsx_sheet`, qui n'a pas la garde de B-449 :
une société « =HYPERLINK(...) » ressort en formule ACTIVE.

Attendu : B-449 (high, fixed) et crm_export.py:254-257 dans export_to_xlsx :
« openpyxl range une chaîne "=..." en formule (type 'f') ; elle doit rester du
texte dans le classeur ». _neutraliser_formule (crm_export.py:123-132) :
« L'export est le dernier rempart ».
"""

from __future__ import annotations

import io

import pytest
from openpyxl import load_workbook

SOCIETE = '=HYPERLINK("http://exemple.invalid/piege";"Ouvrir")'


async def _contact_piege(client) -> str:
    """Création servie (POST /api/memory/contacts) ; on vérifie que la valeur
    est stockée telle quelle, sinon on la pose comme l'outil create_contact du
    chat (memory_tools.py:537-550, sans neutralisation)."""
    resp = await client.post(
        "/api/memory/contacts",
        json={"first_name": "Alice", "last_name": "Martin", "company": SOCIETE},
    )
    assert resp.status_code == 200, resp.text
    stocke = resp.json()["company"]
    assert stocke == SOCIETE, f"valeur stockée par la route : {stocke!r}"
    return resp.json()["id"]


def _cellule_societe(contenu: bytes, onglet: str):
    classeur = load_workbook(io.BytesIO(contenu))
    feuille = classeur[onglet]
    entetes = [c.value for c in feuille[1]]
    colonne = entetes.index("Entreprise") + 1
    return feuille.cell(row=2, column=colonne)


@pytest.mark.asyncio
async def test_l_export_complet_xlsx_ne_rend_pas_une_formule_active(client):
    await _contact_piege(client)

    resp = await client.post("/api/crm/export/all?format=xlsx")
    assert resp.status_code == 200, resp.text
    cellule = _cellule_societe(resp.content, "Contacts")

    assert cellule.data_type != "f", (
        f"onglet Contacts, colonne Entreprise : data_type={cellule.data_type!r}, "
        f"valeur={cellule.value!r}"
    )


@pytest.mark.asyncio
async def test_temoin_l_export_des_contacts_seuls_garde_le_texte(client):
    await _contact_piege(client)

    resp = await client.post("/api/crm/export/contacts?format=xlsx")
    assert resp.status_code == 200, resp.text
    classeur = load_workbook(io.BytesIO(resp.content))
    feuille = classeur.active
    entetes = [c.value for c in feuille[1]]
    cellule = feuille.cell(row=2, column=entetes.index("Entreprise") + 1)

    assert cellule.data_type == "s", (cellule.data_type, cellule.value)
