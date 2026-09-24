"""B-1161 (cycle 13) : une ligne de facture qui déborde est refusée en 422.

B-559 avait interdit inf et nan en entrée, mais 1e200 × 1e200 est fini à
l'entrée et infini au produit : total_tax devenait nan, la colonne NOT NULL
refusait l'écriture, et la création rendait 500. Le total d'une ligne doit
rester fini et au plus 10¹² ; le taux de TVA est borné à 100 %, pour que ni la
ligne ni la somme des lignes ne débordent.
"""

import pytest
from app.models.schemas import InvoiceLineRequest
from pydantic import ValidationError


async def _contact(client) -> str:
    resp = await client.post("/api/memory/contacts", json={"first_name": "Client", "last_name": "Facture"})
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_une_ligne_qui_deborde_est_refusee_en_422_sans_rien_ecrire(client):
    contact_id = await _contact(client)
    resp = await client.post(
        "/api/invoices/",
        json={
            "contact_id": contact_id,
            "document_type": "facture",
            "lines": [{"description": "Débord", "quantity": 1e200, "unit_price_ht": 1e200, "tva_rate": 20.0}],
        },
    )
    assert resp.status_code == 422, resp.text
    assert (await client.get("/api/invoices/")).json() == []


@pytest.mark.parametrize(
    "ligne",
    [
        {"description": "x", "quantity": 1e200, "unit_price_ht": 1e200},
        {"description": "x", "quantity": 2, "unit_price_ht": 1e12},
        {"description": "x", "quantity": 1, "unit_price_ht": 10, "tva_rate": 101},
    ],
)
def test_une_ligne_hors_limite_est_refusee(ligne):
    with pytest.raises(ValidationError):
        InvoiceLineRequest(**ligne)


def test_une_grosse_ligne_legitime_passe():
    ligne = InvoiceLineRequest(description="Chantier", quantity=12.5, unit_price_ht=80_000_000, tva_rate=20)
    assert ligne.quantity * ligne.unit_price_ht == 1e9
