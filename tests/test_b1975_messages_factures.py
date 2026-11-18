"""Les réponses de facturation destinées à l'utilisateur sont en français."""

from unittest.mock import AsyncMock

import pytest
from app.routers import invoices


@pytest.mark.asyncio
@pytest.mark.parametrize("cas", ["absente", "sans_email", "suppression"])
async def test_messages_visibles_de_facturation_sont_en_francais(client, monkeypatch, tmp_path, cas):
    monkeypatch.setattr(invoices, "_get_invoice_output_dir", AsyncMock(return_value=str(tmp_path)))
    if cas == "absente":
        reponse = await client.get("/api/invoices/inexistante")
        assert reponse.status_code == 404
        assert "Pièce introuvable." in reponse.text
        return
    contact = (await client.post("/api/memory/contacts", json={"first_name": "Alice"})).json()
    piece = (await client.post("/api/invoices/", json={
        "contact_id": contact["id"],
        "lines": [{"description": "Prestation", "quantity": 1, "unit_price_ht": 10}],
    })).json()
    if cas == "sans_email":
        reponse = await client.post(f"/api/invoices/{piece['id']}/send")
        assert reponse.status_code == 400
        assert "adresse e-mail" in reponse.text
    else:
        reponse = await client.delete(f"/api/invoices/{piece['id']}")
        assert reponse.status_code == 200
        assert reponse.json()["message"] == "Pièce supprimée."
