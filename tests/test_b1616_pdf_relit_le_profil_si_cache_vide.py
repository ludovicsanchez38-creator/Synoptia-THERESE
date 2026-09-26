"""B-1616 (suite de B-1540) : quand le cache du profil est vide (démarrage ou
restauration avec un profil chiffré, relu sans trousseau), la génération du
PDF refusait « Profil émetteur incomplet » alors que le profil est complet.
Elle relit désormais le profil en base, comme le statut de facturation.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_le_pdf_relit_le_profil_quand_le_cache_est_vide(client: AsyncClient):
    from app.services.user_profile import set_cached_profile

    profil = await client.post("/api/config/profile", json={
        "name": "Claire Exemple", "company": "Claire Exemple Coaching", "address": "Lyon",
        "siret": "99988877900009",
    })
    assert profil.status_code == 200, profil.text
    contact = await client.post("/api/memory/contacts", json={"first_name": "Hélène", "last_name": "Ménard"})
    facture = await client.post("/api/invoices/", json={
        "contact_id": contact.json()["id"], "document_type": "facture",
        "lines": [{"description": "Séance", "quantity": 1, "unit_price_ht": 100.0, "tva_rate": 20.0}],
    })
    set_cached_profile(None)  # démarrage ou restauration : profil chiffré non relu

    reponse = await client.get(f"/api/invoices/{facture.json()['id']}/pdf")

    assert reponse.status_code == 200, reponse.text
