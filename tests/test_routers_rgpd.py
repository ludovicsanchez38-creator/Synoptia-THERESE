"""
THERESE v2 - RGPD Router Tests

Tests pour la conformite RGPD (Phase 6) :
- Export des donnees contact (portabilite)
- Anonymisation (droit a l'oubli)
- Renouvellement du consentement
- Statistiques RGPD
- Mise a jour des champs RGPD
"""

import pytest
from datetime import UTC, datetime, timedelta
from httpx import AsyncClient


# ============================================================
# Helpers
# ============================================================


async def _create_contact(
    client: AsyncClient,
    first_name: str = "Jean",
    last_name: str = "Dupont",
    **kwargs,
) -> str:
    """Cree un contact de test et retourne son ID."""
    data = {
        "first_name": first_name,
        "last_name": last_name,
        "company": "Synoptia",
        "email": f"{first_name.lower()}@synoptia.fr",
        "phone": "+33612345678",
    }
    data.update(kwargs)

    response = await client.post("/api/memory/contacts", json=data)
    assert response.status_code == 200, f"Echec creation contact: {response.text}"
    return response.json()["id"]


# ============================================================
# Export Tests
# ============================================================


class TestRGPDExport:
    """Tests pour l'export des donnees d'un contact (portabilite RGPD)."""

    @pytest.mark.asyncio
    async def test_export_contact_data(self, client: AsyncClient):
        """GET /api/rgpd/export/{contact_id} retourne les donnees du contact."""
        contact_id = await _create_contact(client)

        response = await client.get(f"/api/rgpd/export/{contact_id}")

        assert response.status_code == 200
        data = response.json()

        assert "contact" in data
        assert "activities" in data
        assert "projects" in data
        assert "tasks" in data
        assert "exported_at" in data

        # Verifier les donnees du contact
        assert data["contact"]["id"] == contact_id
        assert data["contact"]["first_name"] == "Jean"
        assert data["contact"]["last_name"] == "Dupont"

    @pytest.mark.asyncio
    async def test_export_contact_not_found(self, client: AsyncClient):
        """GET /api/rgpd/export/{contact_id} retourne 404 si le contact n'existe pas."""
        response = await client.get("/api/rgpd/export/contact-inexistant-12345")

        assert response.status_code == 404


# ============================================================
# Anonymization Tests
# ============================================================


class TestRGPDAnonymize:
    """Tests pour l'anonymisation des contacts (droit a l'oubli)."""

    @pytest.mark.asyncio
    async def test_anonymize_contact(self, client: AsyncClient):
        """POST /api/rgpd/anonymize/{contact_id} anonymise un contact."""
        contact_id = await _create_contact(client, "Pierre", "Durand")

        response = await client.post(
            f"/api/rgpd/anonymize/{contact_id}",
            json={"reason": "Demande du client"},
        )

        assert response.status_code == 200
        result = response.json()

        assert result["success"] is True
        assert result["contact_id"] == contact_id
        assert "anonymis" in result["message"].lower()

        # Verifier que le contact est anonymise (via export RGPD)
        export_response = await client.get(f"/api/rgpd/export/{contact_id}")
        assert export_response.status_code == 200
        export_data = export_response.json()

        assert export_data["contact"]["first_name"] == "[ANONYMISE]" or export_data["contact"]["first_name"] == "[ANONYMISÉ]"
        assert export_data["contact"]["email"] is None
        assert export_data["contact"]["phone"] is None

    @pytest.mark.asyncio
    async def test_anonymize_contact_not_found(self, client: AsyncClient):
        """POST /api/rgpd/anonymize/{contact_id} retourne 404 si le contact n'existe pas."""
        response = await client.post(
            "/api/rgpd/anonymize/contact-inexistant-12345",
            json={"reason": "Test"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_anonymize_contact_default_reason(self, client: AsyncClient):
        """POST /api/rgpd/anonymize/{contact_id} utilise la raison par defaut."""
        contact_id = await _create_contact(client, "Sophie")

        response = await client.post(
            f"/api/rgpd/anonymize/{contact_id}",
            json={},
        )

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True


# ============================================================
# Consent Renewal Tests
# ============================================================


class TestRGPDConsent:
    """Tests pour le renouvellement du consentement RGPD."""

    @pytest.mark.asyncio
    async def test_renew_consent(self, client: AsyncClient):
        """POST /api/rgpd/renew-consent/{contact_id} renouvelle le consentement."""
        contact_id = await _create_contact(client)

        response = await client.post(f"/api/rgpd/renew-consent/{contact_id}")

        assert response.status_code == 200
        result = response.json()

        assert result["success"] is True
        assert "new_expiration" in result

        # Verifier que l'expiration est dans environ 3 ans
        expiration = datetime.fromisoformat(result["new_expiration"])
        now = datetime.now(UTC)
        diff_days = (expiration - now).days
        # 3 ans = ~1095 jours (tolerance de 2 jours)
        assert 1090 <= diff_days <= 1100

    @pytest.mark.asyncio
    async def test_renew_consent_not_found(self, client: AsyncClient):
        """POST /api/rgpd/renew-consent/{contact_id} retourne 404 si contact inexistant."""
        response = await client.post("/api/rgpd/renew-consent/contact-inexistant-12345")

        assert response.status_code == 404


# ============================================================
# RGPD Update Tests
# ============================================================


class TestRGPDUpdate:
    """Tests pour la mise a jour des champs RGPD."""

    @pytest.mark.asyncio
    async def test_update_rgpd(self, client: AsyncClient):
        """PATCH /api/rgpd/{contact_id} met a jour la base legale et le consentement."""
        contact_id = await _create_contact(client)

        response = await client.patch(
            f"/api/rgpd/{contact_id}",
            json={
                "rgpd_base_legale": "contrat",
                "rgpd_consentement": True,
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_update_rgpd_invalid_base_legale(self, client: AsyncClient):
        """PATCH /api/rgpd/{contact_id} refuse une base legale invalide."""
        contact_id = await _create_contact(client)

        response = await client.patch(
            f"/api/rgpd/{contact_id}",
            json={
                "rgpd_base_legale": "base_invalide",
            },
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_legal_basis_required(self, client: AsyncClient):
        """Verifie que chaque base legale valide est acceptee."""
        valid_bases = ["consentement", "contrat", "interet_legitime", "obligation_legale"]

        for base in valid_bases:
            contact_id = await _create_contact(client, f"Contact{base}")

            response = await client.patch(
                f"/api/rgpd/{contact_id}",
                json={"rgpd_base_legale": base},
            )

            assert response.status_code == 200, f"Echec pour la base legale: {base}"


# ============================================================
# RGPD Stats Tests
# ============================================================


class TestRGPDStats:
    """Tests pour les statistiques RGPD."""

    @pytest.mark.asyncio
    async def test_rgpd_stats(self, client: AsyncClient):
        """GET /api/rgpd/stats retourne les statistiques RGPD globales."""
        response = await client.get("/api/rgpd/stats")

        assert response.status_code == 200
        stats = response.json()

        assert "total_contacts" in stats
        assert "par_base_legale" in stats
        assert "sans_info_rgpd" in stats
        assert "expires_ou_bientot" in stats
        assert "avec_consentement" in stats

        # Verifier la structure par_base_legale
        bases = stats["par_base_legale"]
        assert "consentement" in bases
        assert "contrat" in bases
        assert "interet_legitime" in bases
        assert "obligation_legale" in bases
        assert "non_defini" in bases

    @pytest.mark.asyncio
    async def test_rgpd_stats_without_consent(self, client: AsyncClient):
        """Verifie les compteurs avec des contacts sans consentement."""
        # Creer des contacts (pas de RGPD defini par defaut)
        await _create_contact(client, "AliceSansRGPD")
        await _create_contact(client, "BobSansRGPD")

        response = await client.get("/api/rgpd/stats")

        assert response.status_code == 200
        stats = response.json()

        assert stats["total_contacts"] >= 2
        assert stats["sans_info_rgpd"] >= 2
        # Pas de consentement defini
        assert stats["par_base_legale"]["non_defini"] >= 2

    @pytest.mark.asyncio
    async def test_rgpd_stats_with_consent(self, client: AsyncClient):
        """Verifie les compteurs apres renouvellement de consentement."""
        contact_id = await _create_contact(client, "MarieConsent")

        # Renouveler le consentement
        await client.post(f"/api/rgpd/renew-consent/{contact_id}")

        response = await client.get("/api/rgpd/stats")

        assert response.status_code == 200
        stats = response.json()

        assert stats["avec_consentement"] >= 1
        assert stats["par_base_legale"]["consentement"] >= 1
