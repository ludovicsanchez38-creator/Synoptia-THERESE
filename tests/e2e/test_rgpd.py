"""
THERESE v2 - Tests E2E Conformite RGPD

Test des fonctionnalites RGPD : export contact, anonymisation,
consentement, statistiques, base legale.
Principalement des tests API (pas d'UI).
"""

from datetime import UTC, datetime, timedelta

import pytest

# ============================================================
# RGPD Export (Droit de portabilite - Art. 20)
# ============================================================


def test_rgpd_export_contact(api_client, seeded_contacts):
    """
    P0 - Export RGPD des donnees d'un contact.

    GET /api/rgpd/export/{contact_id} et verifie que l'export
    contient le contact, ses activites, projets et taches.
    """
    if not seeded_contacts:
        pytest.skip("Pas de contacts seeded")

    contact_id = seeded_contacts[0]["id"]

    resp = api_client.get(f"/api/rgpd/export/{contact_id}")
    assert resp.status_code == 200, f"Erreur export RGPD: {resp.status_code} - {resp.text}"

    data = resp.json()

    # Verifier la structure de la reponse
    assert "contact" in data
    assert "activities" in data
    assert "projects" in data
    assert "tasks" in data
    assert "exported_at" in data

    # Verifier les donnees du contact
    contact = data["contact"]
    assert contact["id"] == contact_id
    assert "first_name" in contact
    assert "email" in contact
    assert "stage" in contact

    # Les activites, projets et taches doivent etre des listes
    assert isinstance(data["activities"], list)
    assert isinstance(data["projects"], list)
    assert isinstance(data["tasks"], list)


# ============================================================
# RGPD Anonymisation (Droit a l'oubli - Art. 17)
# ============================================================


def test_rgpd_anonymize_contact(api_client, seeded_contacts):
    """
    P0 - Anonymisation d'un contact (droit a l'oubli).

    POST /api/rgpd/anonymize/{contact_id} et verifie que les
    donnees personnelles sont remplacees par [ANONYMISE].
    """
    if not seeded_contacts or len(seeded_contacts) < 5:
        pytest.skip("Pas assez de contacts seeded")

    # Utiliser le dernier contact pour ne pas casser les autres tests
    contact = seeded_contacts[-1]
    contact_id = contact["id"]

    # Anonymiser le contact
    resp = api_client.post(
        f"/api/rgpd/anonymize/{contact_id}",
        json={"reason": "Test E2E - demande de suppression"},
    )
    assert resp.status_code == 200, f"Erreur anonymisation: {resp.status_code} - {resp.text}"

    data = resp.json()
    assert data["success"] is True
    assert data["contact_id"] == contact_id
    assert "anonymis" in data["message"].lower()

    # Verifier que le contact est bien anonymise via export RGPD
    resp_export = api_client.get(f"/api/rgpd/export/{contact_id}")
    assert resp_export.status_code == 200

    export_data = resp_export.json()
    anonymized_contact = export_data["contact"]

    # Les donnees personnelles doivent etre effacees
    assert anonymized_contact["first_name"] == "[ANONYMISE]"
    assert anonymized_contact["email"] is None
    assert anonymized_contact["phone"] is None
    assert anonymized_contact["company"] == "[ANONYMISE]"
    assert anonymized_contact["stage"] == "archive"


# ============================================================
# RGPD Consentement
# ============================================================


def test_rgpd_renew_consent(api_client, seeded_contacts):
    """
    P1 - Renouvellement du consentement RGPD d'un contact.

    POST /api/rgpd/renew-consent/{contact_id} et verifie
    que les dates de collecte et expiration sont mises a jour.
    """
    if not seeded_contacts:
        pytest.skip("Pas de contacts seeded")

    contact_id = seeded_contacts[0]["id"]

    resp = api_client.post(f"/api/rgpd/renew-consent/{contact_id}")
    assert resp.status_code == 200, f"Erreur renouvellement: {resp.status_code} - {resp.text}"

    data = resp.json()
    assert data["success"] is True
    assert "new_expiration" in data

    # Verifier que la nouvelle expiration est dans environ 3 ans
    new_expiration = datetime.fromisoformat(
        data["new_expiration"].replace("Z", "+00:00").replace("+00:00", "")
    )
    now = datetime.now(UTC)
    expected_min = now + timedelta(days=3 * 365 - 5)  # marge de 5 jours
    expected_max = now + timedelta(days=3 * 365 + 5)

    assert expected_min <= new_expiration <= expected_max, (
        f"Expiration hors plage attendue: {new_expiration}"
    )

    # Verifier via export RGPD que le consentement est bien a jour
    resp_export = api_client.get(f"/api/rgpd/export/{contact_id}")
    assert resp_export.status_code == 200

    export_data = resp_export.json()
    contact_data = export_data["contact"]
    assert contact_data["rgpd_base_legale"] == "consentement"
    assert contact_data["rgpd_consentement"] is True


# ============================================================
# RGPD Statistiques
# ============================================================


def test_rgpd_stats(api_client, seeded_contacts):
    """
    P1 - Statistiques RGPD globales.

    GET /api/rgpd/stats et verifie les compteurs
    (total, par base legale, sans info, expires, consentement).
    """
    if not seeded_contacts:
        pytest.skip("Pas de contacts seeded")

    resp = api_client.get("/api/rgpd/stats")
    assert resp.status_code == 200, f"Erreur stats RGPD: {resp.status_code} - {resp.text}"

    data = resp.json()

    # Verifier la structure de la reponse
    assert "total_contacts" in data
    assert "par_base_legale" in data
    assert "sans_info_rgpd" in data
    assert "expires_ou_bientot" in data
    assert "avec_consentement" in data

    # Le total doit etre >= nombre de contacts seeded
    assert data["total_contacts"] >= len(seeded_contacts)

    # Verifier la repartition par base legale
    par_base = data["par_base_legale"]
    assert isinstance(par_base, dict)

    # Les cles attendues
    expected_bases = [
        "consentement",
        "contrat",
        "interet_legitime",
        "obligation_legale",
        "non_defini",
    ]
    for base in expected_bases:
        assert base in par_base, f"Base legale manquante: {base}"
        assert isinstance(par_base[base], int)

    # Les compteurs doivent etre des entiers >= 0
    assert data["sans_info_rgpd"] >= 0
    assert data["expires_ou_bientot"] >= 0
    assert data["avec_consentement"] >= 0


# ============================================================
# RGPD Mise a jour base legale
# ============================================================


def test_rgpd_update_legal_basis(api_client, seeded_contacts):
    """
    P1 - Mise a jour de la base legale RGPD d'un contact.

    PATCH /api/rgpd/{contact_id} avec base_legale="consentement"
    et verifie la mise a jour.
    """
    if not seeded_contacts:
        pytest.skip("Pas de contacts seeded")

    contact_id = seeded_contacts[1]["id"]

    # Mettre a jour la base legale
    resp = api_client.patch(
        f"/api/rgpd/{contact_id}",
        json={
            "rgpd_base_legale": "consentement",
            "rgpd_consentement": True,
        },
    )
    assert resp.status_code == 200, f"Erreur update RGPD: {resp.status_code} - {resp.text}"

    data = resp.json()
    assert data["success"] is True

    # Verifier via export que la base legale est bien mise a jour
    resp_export = api_client.get(f"/api/rgpd/export/{contact_id}")
    assert resp_export.status_code == 200

    export_data = resp_export.json()
    contact_data = export_data["contact"]
    assert contact_data["rgpd_base_legale"] == "consentement"
    assert contact_data["rgpd_consentement"] is True

    # Verifier que les dates ont ete auto-remplies
    assert contact_data["rgpd_date_collecte"] is not None
    assert contact_data["rgpd_date_expiration"] is not None
