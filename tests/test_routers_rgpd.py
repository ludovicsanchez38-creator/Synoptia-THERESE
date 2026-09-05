"""
THERESE v2 - RGPD Router Tests

Tests pour la conformite RGPD (Phase 6) :
- Export des donnees contact (portabilite)
- Anonymisation (droit a l'oubli)
- Renouvellement du consentement
- Statistiques RGPD
- Mise a jour des champs RGPD
"""

from datetime import UTC, datetime

import pytest
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
    async def test_anonymize_contact_purge_ses_prestations(self, client: AsyncClient):
        """Art. 17 : une prestation ne doit pas rester liée à [ANONYMISÉ]."""
        contact_id = await _create_contact(client, "ClientAvecPrestation")
        prestation = await client.post(
            "/api/prestations",
            json={
                "contact_id": contact_id,
                "intitule": "Accompagnement sensible",
                "montant_ht": 5000.0,
                "phase": "en_cours",
                "financeur": "OPCO",
            },
        )
        assert prestation.status_code == 201, prestation.text

        response = await client.post(
            f"/api/rgpd/anonymize/{contact_id}",
            json={"reason": "demande du client"},
        )

        assert response.status_code == 200
        prestations = await client.get(f"/api/prestations?contact_id={contact_id}")
        assert prestations.status_code == 200
        assert prestations.json() == []

    @pytest.mark.asyncio
    async def test_anonymize_supprime_le_dossier_par_le_chemin_canonique(
        self, client: AsyncClient
    ):
        """B-140 : l'anonymisation détruisait le dossier par un chemin à elle.

        rgpd.py faisait `session.delete(project)` après avoir vidé tâches et
        livrables, là où la suppression de dossier passe par
        `_nettoyer_et_supprimer_projet` : purge Qdrant du périmètre, des
        fichiers indexés, détachement des conversations, documents et
        événements. Résultat : la ligne partait, ses fragments restaient
        interrogeables et ses fichiers pointaient un dossier disparu.
        """
        from app.services.qdrant import get_qdrant_service

        contact_id = await _create_contact(client, "ClientAvecDossier")
        projet = await client.post(
            "/api/memory/projects",
            json={"name": "Projet Robustesse", "contact_id": contact_id},
        )
        assert projet.status_code in (200, 201), projet.text
        project_id = projet.json()["id"]

        qdrant = get_qdrant_service()
        qdrant.async_delete_by_scope.reset_mock()
        qdrant.async_delete_by_entity.reset_mock()

        response = await client.post(
            f"/api/rgpd/anonymize/{contact_id}",
            json={"reason": "demande du client"},
        )
        assert response.status_code == 200, response.text

        perimetres = [c.args for c in qdrant.async_delete_by_scope.call_args_list]
        assert ("project", project_id) in perimetres, perimetres
        entites = [c.args[0] for c in qdrant.async_delete_by_entity.call_args_list]
        assert project_id in entites, entites

    @pytest.mark.asyncio
    async def test_anonymize_annonce_les_dossiers_detruits(self, client: AsyncClient):
        """B-140 / RB-011 : la destruction du dossier est irréversible et
        n'était annoncée nulle part - ni dans la réponse, ni dans le libellé
        de l'action."""
        contact_id = await _create_contact(client, "ClientQuiPerdSonDossier")
        projet = await client.post(
            "/api/memory/projects",
            json={"name": "Dossier Rousset", "contact_id": contact_id},
        )
        assert projet.status_code in (200, 201), projet.text

        response = await client.post(
            f"/api/rgpd/anonymize/{contact_id}",
            json={"reason": "demande du client"},
        )

        assert response.status_code == 200
        message = response.json()["message"]
        assert "dossier" in message.lower(), message
        assert "1" in message, message

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


class TestB445LesOctetsDUnDossierPartentAvecLAnonymisation:
    """B-445 (05/09/2026) : la réponse annonçait « fichiers rattachés »
    supprimés alors que le dépôt disque du dossier restait en place.

    rgpd.py empruntait _nettoyer_et_supprimer_projet (B-140) mais jamais
    _purger_le_depot_du_dossier, que seule la route DELETE /projects appelle
    après son commit. A/B prouvé sur le jetable : anonymisation -> dossier
    disque intact ; suppression de dossier -> dossier disque purgé.
    """

    @pytest.mark.asyncio
    async def test_le_depot_disque_du_dossier_est_purge(self, client: AsyncClient):
        from pathlib import Path

        from app.config import settings

        contact_id = await _create_contact(client, "ClientAvecFichiers")
        projet = await client.post(
            "/api/memory/projects",
            json={"name": "Projet avec fichiers", "contact_id": contact_id},
        )
        assert projet.status_code in (200, 201), projet.text
        project_id = projet.json()["id"]

        depot = Path(settings.data_dir) / "projects" / project_id / "files"
        depot.mkdir(parents=True, exist_ok=True)
        (depot / "confidentiel.txt").write_text("octets du client")
        assert depot.exists()

        reponse = await client.post(
            f"/api/rgpd/anonymize/{contact_id}", json={"reason": "demande du client"}
        )
        assert reponse.status_code == 200, reponse.text

        assert not (Path(settings.data_dir) / "projects" / project_id).exists(), (
            "les octets du dossier survivent à l'effacement annoncé"
        )
