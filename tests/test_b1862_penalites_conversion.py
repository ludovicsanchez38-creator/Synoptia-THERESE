"""Une conversion et une facture directe appliquent la même règle par défaut."""

from unittest.mock import AsyncMock

import pytest
from app.routers import invoices
from app.services.user_profile import UserProfile
from pypdf import PdfReader


@pytest.mark.asyncio
async def test_conversion_utilise_la_meme_penalite_par_defaut_que_la_facture_directe(
    client, monkeypatch, tmp_path
):
    profil = UserProfile(name="Camille", address="Paris", siret="12345678900010", legal_form="EI")
    monkeypatch.setattr(invoices, "get_cached_profile", lambda: profil)
    monkeypatch.setattr(invoices, "_get_invoice_output_dir", AsyncMock(return_value=str(tmp_path)))
    contact = (await client.post("/api/memory/contacts", json={
        "first_name": "Alice", "address": "Lyon",
    })).json()
    donnees = {
        "contact_id": contact["id"],
        "lines": [{"description": "Prestation", "quantity": 1, "unit_price_ht": 10}],
    }
    directe = (await client.post("/api/invoices/", json=donnees)).json()
    devis = (await client.post("/api/invoices/", json={**donnees, "document_type": "devis"})).json()
    conversion = await client.post(f"/api/invoices/{devis['id']}/convert-to-invoice", json={})
    assert conversion.status_code == 200, conversion.text
    convertie = conversion.json()
    textes = []
    for piece in (directe, convertie):
        reponse = await client.get(f"/api/invoices/{piece['id']}/pdf")
        assert reponse.status_code == 200, reponse.text
        textes.append("\n".join(page.extract_text() for page in PdfReader(reponse.json()["pdf_path"]).pages))
    assert all("taux de refinancement" in texte and "majoré de 10 points" in texte for texte in textes)
    assert convertie["late_penalty_rate"] is None


@pytest.mark.asyncio
async def test_pdf_sans_mentions_conserve_le_taux_particulier_enregistre(client, monkeypatch, tmp_path):
    from app.models import database as db
    from app.models.entities import Invoice

    profil = UserProfile(name="Camille", address="Paris", siret="12345678900010", legal_form="EI")
    monkeypatch.setattr(invoices, "get_cached_profile", lambda: profil)
    monkeypatch.setattr(invoices, "_get_invoice_output_dir", AsyncMock(return_value=str(tmp_path)))
    contact = (await client.post("/api/memory/contacts", json={"first_name": "Alice", "address": "Lyon"})).json()
    piece = (await client.post("/api/invoices/", json={
        "contact_id": contact["id"],
        "lines": [{"description": "Prestation", "quantity": 1, "unit_price_ht": 10}],
    })).json()
    async with db.AsyncSessionLocal() as session:
        facture = await session.get(Invoice, piece["id"])
        facture.late_penalty_rate = 11.62
        facture.legal_mentions = None
        await session.commit()
    reponse = await client.get(f"/api/invoices/{piece['id']}/pdf")
    assert reponse.status_code == 200, reponse.text
    texte = "\n".join(page.extract_text() for page in PdfReader(reponse.json()["pdf_path"]).pages)
    assert "11,62 %" in texte
    assert "taux de refinancement" not in texte
