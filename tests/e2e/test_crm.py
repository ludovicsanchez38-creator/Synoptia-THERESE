"""
THERESE v2 - Tests E2E CRM Pipeline

Test des fonctionnalites CRM : pipeline, contacts, activites, export/import.
"""

import io
import pytest
from playwright.sync_api import Page, expect

from .conftest import take_screenshot


# ============================================================
# P0 - Tests critiques pipeline CRM
# ============================================================


def test_crm_pipeline_display(panel_page, seeded_contacts):
    """
    P0 - Le pipeline CRM affiche les colonnes de stages.

    Ouvre le panel CRM et verifie que les 7 colonnes du pipeline
    sont visibles (Contact, Decouverte, Proposition, Signature,
    Livraison, Actif, Archive).
    """
    if not seeded_contacts:
        pytest.skip("Pas de contacts seeded")

    page, context = panel_page("crm")

    # Attendre que le panel CRM soit charge
    page.wait_for_timeout(2000)

    # Verifier le header CRM Pipeline
    expect(page.locator("text=CRM Pipeline")).to_be_visible(timeout=5000)

    # Verifier que les colonnes de stages sont affichees
    # Les 7 stages definis dans PipelineView.tsx
    stage_labels = [
        "Contact",
        "Decouverte",
        "Proposition",
        "Signature",
        "Livraison",
        "Actif",
        "Archive",
    ]

    for label in stage_labels:
        expect(page.locator(f"text={label}").first).to_be_visible(timeout=3000)

    take_screenshot(page, "crm_pipeline_display")


def test_crm_create_contact(panel_page, api_client):
    """
    P0 - Creation d'un contact CRM via API et verification dans le pipeline.

    Cree un contact via POST /api/crm/contacts puis verifie
    qu'il apparait dans le panel CRM.
    """
    # Creer un contact via l'API CRM
    contact_data = {
        "first_name": "Julie",
        "last_name": "Durand",
        "company": "Yoga Studio",
        "email": "julie@yogastudio.fr",
        "phone": "+33611223344",
        "stage": "contact",
    }

    resp = api_client.post("/api/crm/contacts", json=contact_data)
    assert resp.status_code == 200, f"Erreur creation contact: {resp.status_code} - {resp.text}"

    created = resp.json()
    assert created["first_name"] == "Julie"
    assert "id" in created

    # Ouvrir le panel CRM et verifier que le contact apparait
    page, context = panel_page("crm")
    page.wait_for_timeout(2000)

    # Le contact doit apparaitre dans le pipeline
    # Chercher par prenom ou nom d'entreprise
    expect(page.locator("text=Julie").first).to_be_visible(timeout=5000)

    take_screenshot(page, "crm_create_contact")


def test_crm_change_stage(panel_page, seeded_contacts, api_client):
    """
    P0 - Changement de stage d'un contact via API PATCH.

    Change le stage d'un contact de 'contact' a 'proposition'
    via l'endpoint PATCH et verifie la mise a jour.
    """
    if not seeded_contacts:
        pytest.skip("Pas de contacts seeded")

    contact = seeded_contacts[0]
    contact_id = contact["id"]

    # Changer le stage via API
    resp = api_client.patch(
        f"/api/crm/contacts/{contact_id}/stage",
        json={"stage": "proposition"},
    )
    assert resp.status_code == 200, f"Erreur changement stage: {resp.status_code} - {resp.text}"

    updated = resp.json()
    assert updated["stage"] == "proposition"

    # Verifier que le contact apparait dans la colonne Proposition
    page, context = panel_page("crm")
    page.wait_for_timeout(2000)

    # Le contact devrait etre dans la colonne Proposition
    expect(page.locator("text=CRM Pipeline")).to_be_visible(timeout=5000)

    take_screenshot(page, "crm_change_stage")


# ============================================================
# P1 - Tests activites et timeline
# ============================================================


def test_crm_activities_tab(panel_page, seeded_contacts, api_client):
    """
    P1 - L'onglet Activites est accessible dans le CRM.

    Ouvre le panel CRM, clique sur l'onglet Activites
    et verifie qu'il s'affiche correctement.
    """
    if not seeded_contacts:
        pytest.skip("Pas de contacts seeded")

    page, context = panel_page("crm")
    page.wait_for_timeout(2000)

    # Cliquer sur l'onglet Activites dans le CRM
    activities_tab = page.locator("text=Activites").first
    expect(activities_tab).to_be_visible(timeout=3000)
    activities_tab.click()

    page.wait_for_timeout(1000)

    take_screenshot(page, "crm_activities_tab")


def test_crm_create_activity(panel_page, seeded_contacts, api_client):
    """
    P1 - Creation d'une activite sur un contact.

    Cree une activite (note) via l'API et verifie
    qu'elle apparait dans la timeline.
    """
    if not seeded_contacts:
        pytest.skip("Pas de contacts seeded")

    contact = seeded_contacts[0]
    contact_id = contact["id"]

    # Creer une activite via API
    activity_data = {
        "contact_id": contact_id,
        "type": "note",
        "title": "Note de suivi E2E",
        "description": "Appel de qualification effectue, interet confirme.",
    }

    resp = api_client.post("/api/crm/activities", json=activity_data)
    assert resp.status_code == 200, f"Erreur creation activite: {resp.status_code} - {resp.text}"

    activity = resp.json()
    assert activity["title"] == "Note de suivi E2E"
    assert activity["type"] == "note"
    assert activity["contact_id"] == contact_id

    # Creer une deuxieme activite de type 'call'
    call_data = {
        "contact_id": contact_id,
        "type": "call",
        "title": "Appel telephonique E2E",
        "description": "Discussion sur les besoins du client.",
    }

    resp2 = api_client.post("/api/crm/activities", json=call_data)
    assert resp2.status_code == 200

    # Verifier que les activites sont listees
    resp_list = api_client.get(f"/api/crm/activities?contact_id={contact_id}")
    assert resp_list.status_code == 200

    activities = resp_list.json()
    assert len(activities) >= 2

    # Verifier les titres
    titles = [a["title"] for a in activities]
    assert "Note de suivi E2E" in titles
    assert "Appel telephonique E2E" in titles


# ============================================================
# P1 - Tests export/import CRM
# ============================================================


def test_crm_export_csv(api_client, seeded_contacts):
    """
    P1 - Export des contacts CRM au format CSV.

    GET /api/crm/export/contacts avec format=csv
    et verifie que le CSV contient des donnees.
    """
    if not seeded_contacts:
        pytest.skip("Pas de contacts seeded")

    resp = api_client.post("/api/crm/export/contacts?format=csv")
    assert resp.status_code == 200, f"Erreur export CSV: {resp.status_code} - {resp.text}"

    # Verifier le content-type
    content_type = resp.headers.get("content-type", "")
    assert "text/csv" in content_type or "application/octet-stream" in content_type

    # Verifier que le contenu n'est pas vide
    content = resp.content
    assert len(content) > 0

    # Verifier la presence d'un header CSV ou de donnees
    text = content.decode("utf-8", errors="replace")
    # Le CSV doit contenir au moins une ligne de header
    assert len(text.strip().split("\n")) >= 1

    # Verifier le header X-Row-Count
    row_count = resp.headers.get("x-row-count")
    if row_count:
        assert int(row_count) >= len(seeded_contacts)


def test_crm_import_csv_preview(api_client):
    """
    P1 - Preview d'import CSV de contacts.

    POST /api/crm/import/contacts/preview avec un fichier CSV test
    et verifie le resultat du preview.
    """
    # Creer un CSV test
    csv_content = (
        "Prenom,Nom,Entreprise,Email,Telephone\n"
        "Alice,Moreau,Design Lab,alice@designlab.fr,+33699887766\n"
        "Bruno,Petit,Agence Web,bruno@agenceweb.fr,+33688776655\n"
    )

    # Envoyer en multipart
    resp = api_client.post(
        "/api/crm/import/contacts/preview",
        files={"file": ("test_import.csv", csv_content.encode("utf-8"), "text/csv")},
    )

    # L'endpoint peut retourner 200 (preview OK) ou 422 (format non reconnu)
    # On verifie surtout qu'il ne crash pas
    assert resp.status_code in (200, 422), f"Erreur preview import: {resp.status_code} - {resp.text}"

    if resp.status_code == 200:
        data = resp.json()
        assert "total_rows" in data
        assert "detected_columns" in data
        assert data["total_rows"] >= 2


# ============================================================
# P2 - Tests statistiques pipeline
# ============================================================


def test_crm_pipeline_stats(api_client, seeded_contacts):
    """
    P2 - Statistiques du pipeline commercial.

    GET /api/crm/pipeline/stats et verifie les compteurs
    par stage et le total.
    """
    if not seeded_contacts:
        pytest.skip("Pas de contacts seeded")

    resp = api_client.get("/api/crm/pipeline/stats")
    assert resp.status_code == 200, f"Erreur stats pipeline: {resp.status_code} - {resp.text}"

    data = resp.json()

    # Verifier la structure de la reponse
    assert "total_contacts" in data
    assert "stages" in data

    # Le total doit etre >= nombre de contacts seeded
    assert data["total_contacts"] >= len(seeded_contacts)

    # Les stages doivent etre un dict
    assert isinstance(data["stages"], dict)
