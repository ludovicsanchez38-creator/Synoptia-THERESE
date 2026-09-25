"""P-136 (acceptée le 25/09) : le formulaire avertit quand une facture avec
TVA partirait sans le numéro de TVA de l'émetteur. Règle relevée le
26/09/2026 sur service-public.fr (F31808, vérifié le 11 août 2026) : le
« numéro individuel d'identification à la TVA du vendeur » figure sur la
facture, sauf pour un montant total HT inférieur ou égal à 150 €. Le moteur
dit si le profil le porte ; l'avertissement est non bloquant."""

import pytest
from httpx import AsyncClient

PROFIL = {"name": "Hélène Ménard", "company": "Atelier Ménard", "address": "Manosque", "siret": "99988877900009"}


@pytest.mark.asyncio
async def test_le_statut_du_profil_dit_si_le_numero_de_tva_est_renseigne(client: AsyncClient):
    assert (await client.post("/api/config/profile", json=PROFIL)).status_code == 200
    sans = (await client.get("/api/invoices/billing/profile-status")).json()
    assert sans["tva_intra_renseigne"] is False

    assert (await client.post("/api/config/profile", json={**PROFIL, "tva_intra": "FR 00 999888779"})).status_code == 200
    avec = (await client.get("/api/invoices/billing/profile-status")).json()
    assert avec["tva_intra_renseigne"] is True
