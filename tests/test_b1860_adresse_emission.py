"""L'adresse du destinataire doit être présente avant la première émission."""

import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize("document_type", ["facture", "avoir"])
@pytest.mark.parametrize("transition", ["sent", "paid", "overdue", "mark-paid"])
async def test_refuse_emission_sans_adresse_sans_numero(client, document_type, transition):
    contact = (await client.post("/api/memory/contacts", json={"first_name": "Alice"})).json()
    origine_id = None
    if document_type == "avoir":
        origine = await client.post("/api/invoices/", json={
            "contact_id": contact["id"], "client_address": "1 rue du Client, Lyon",
            "lines": [{"description": "Origine", "quantity": 1, "unit_price_ht": 10}],
        })
        origine_id = origine.json()["id"]
        assert (await client.put(f"/api/invoices/{origine_id}", json={"status": "sent"})).status_code == 200
    cree = await client.post("/api/invoices/", json={
        "contact_id": contact["id"], "document_type": document_type,
        "converted_from_id": origine_id,
        "lines": [{"description": "Prestation", "quantity": 1, "unit_price_ht": 10}],
    })
    assert cree.status_code == 200
    piece = cree.json()
    chemin = f"/api/invoices/{piece['id']}"
    if transition == "mark-paid":
        refus = await client.patch(f"{chemin}/mark-paid", json={})
    else:
        refus = await client.put(chemin, json={"status": transition})
    assert refus.status_code == 409, refus.text
    assert "adresse" in refus.text.lower()
    apres = (await client.get(chemin)).json()
    assert apres["status"] == "draft"
    assert apres["invoice_number"] == piece["invoice_number"]

    if transition == "mark-paid":
        assert (await client.put(chemin, json={"client_address": "1 rue du Client"})).status_code == 200
        accord = await client.patch(f"{chemin}/mark-paid", json={})
    else:
        accord = await client.put(chemin, json={
            "status": transition, "client_address": "1 rue du Client",
        })
    assert accord.status_code == 200, accord.text
