"""B-1506 : une facture émise pouvait être supprimée ou repasser en brouillon.

La numérotation des factures repose sur une séquence chronologique et
continue (BOFiP, BOI-TVA-DECLA-30-20-20-10) : supprimer une facture émise
y laisse un trou, et la repasser en brouillon permet d'en réécrire le
contenu. On l'annule par un avoir. Le brouillon d'une facture, jamais
parti, et un devis, qui n'entre pas dans cette séquence, restent libres.
"""

import pytest
from httpx import AsyncClient


async def _piece(client: AsyncClient, type_: str, envoyee: bool) -> str:
    contact = await client.post("/api/memory/contacts", json={"first_name": "Hélène", "last_name": "Ménard"})
    piece = await client.post("/api/invoices/", json={
        "contact_id": contact.json()["id"], "document_type": type_,
        "lines": [{"description": "Table en chêne", "quantity": 1, "unit_price_ht": 900.0, "tva_rate": 20.0}],
    })
    assert piece.status_code in (200, 201), piece.text
    identifiant = piece.json()["id"]
    if envoyee:
        route = "devis-status" if type_ == "devis" else None
        reponse = (
            await client.patch(f"/api/invoices/{identifiant}/{route}", json={"status": "sent"})
            if route else await client.put(f"/api/invoices/{identifiant}", json={"status": "sent"})
        )
        assert reponse.status_code == 200, reponse.text
    return identifiant


@pytest.mark.asyncio
async def test_une_facture_emise_ne_se_supprime_pas(client: AsyncClient):
    identifiant = await _piece(client, "facture", envoyee=True)
    reponse = await client.delete(f"/api/invoices/{identifiant}")
    assert reponse.status_code == 409, reponse.text
    assert "avoir" in reponse.text
    assert (await client.get(f"/api/invoices/{identifiant}")).status_code == 200


@pytest.mark.asyncio
async def test_une_facture_emise_ne_repasse_pas_en_brouillon(client: AsyncClient):
    identifiant = await _piece(client, "facture", envoyee=True)
    reponse = await client.put(f"/api/invoices/{identifiant}", json={"status": "draft"})
    assert reponse.status_code == 409, reponse.text
    assert (await client.get(f"/api/invoices/{identifiant}")).json()["status"] == "sent"


@pytest.mark.asyncio
async def test_un_brouillon_de_facture_et_un_devis_envoye_restent_libres(client: AsyncClient):
    brouillon = await _piece(client, "facture", envoyee=False)
    assert (await client.delete(f"/api/invoices/{brouillon}")).status_code == 200

    devis = await _piece(client, "devis", envoyee=True)
    assert (await client.put(f"/api/invoices/{devis}", json={"status": "draft"})).status_code == 200
    assert (await client.delete(f"/api/invoices/{devis}")).status_code == 200
