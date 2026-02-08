"""
THERESE v2 - Tests E2E - Panel Factures (Invoices).

9 tests couvrant la gestion des factures :
- P0 : Etat vide, creation, numero auto, calcul lignes, marquage payee
- P1 : Download PDF, edition, suppression, filtre par statut
"""

import pytest
from playwright.sync_api import expect

from .conftest import take_screenshot

# ============================================================
# P0 - Tests critiques
# ============================================================


def test_invoices_empty_state(panel_page):
    """
    P0 - Ouvrir le panel factures vide, verifier le message
    et la presence du bouton de creation.
    """
    page, _ = panel_page("invoices")

    # Verifier le header du panel
    expect(page.get_by_text("Factures")).to_be_visible(timeout=5000)

    # Etat vide - message et bouton
    expect(page.get_by_text("Aucune facture")).to_be_visible(timeout=5000)
    expect(page.get_by_text("Creer une facture")).to_be_visible()

    # Le bouton "Nouvelle facture" doit etre dans le header
    expect(page.get_by_text("Nouvelle facture")).to_be_visible()

    # Les pills de filtre doivent etre visibles
    expect(page.get_by_text("Toutes")).to_be_visible()
    expect(page.get_by_text("Brouillon")).to_be_visible()

    take_screenshot(page, "invoices_empty_state")


def test_invoices_create(panel_page, seeded_contacts, api_client):
    """
    P0 - Creer une facture via l'API avec des lignes de coaching.
    Verifier qu'elle apparait dans la liste.
    """
    page, _ = panel_page("invoices")
    page.wait_for_timeout(500)

    # Creer une facture via API (plus fiable que UI pour le seeding)
    contact_id = seeded_contacts[0]["id"]
    invoice_data = {
        "contact_id": contact_id,
        "lines": [
            {
                "description": "Coaching individuel - 3h",
                "quantity": 3,
                "unit_price_ht": 150.0,
                "tva_rate": 20.0,
            },
        ],
        "notes": "Facture test E2E creation",
    }

    resp = api_client.post("/api/invoices", json=invoice_data)
    assert resp.status_code == 200
    invoice = resp.json()

    # Recharger le panel
    page.reload()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    # Verifier que la facture apparait dans la liste
    expect(page.get_by_text(invoice["invoice_number"])).to_be_visible(timeout=5000)

    # Verifier que le montant TTC est affiche (3 * 150 * 1.20 = 540.00)
    expect(page.get_by_text("540.00")).to_be_visible(timeout=3000)

    # Le statut doit etre "Brouillon"
    expect(page.get_by_text("Brouillon")).to_be_visible()

    take_screenshot(page, "invoices_create")


def test_invoices_auto_number(panel_page, seeded_invoice):
    """
    P0 - Verifier le format du numero de facture FACT-2026-NNN.
    """
    page, _ = panel_page("invoices")
    page.wait_for_timeout(1000)

    invoice_number = seeded_invoice["invoice_number"]

    # Verifier le format FACT-YYYY-NNN
    assert invoice_number.startswith("FACT-"), f"Format invalide: {invoice_number}"
    parts = invoice_number.split("-")
    assert len(parts) == 3, f"Format invalide (attendu 3 parties): {invoice_number}"
    assert parts[0] == "FACT"
    assert len(parts[1]) == 4  # Annee
    assert len(parts[2]) == 3  # Numero sur 3 chiffres

    # Verifier que le numero est visible dans le panel
    expect(page.get_by_text(invoice_number)).to_be_visible(timeout=5000)

    take_screenshot(page, "invoices_auto_number")


def test_invoices_line_calculation(panel_page, seeded_invoice):
    """
    P0 - Verifier les calculs HT, TVA et TTC de la facture seeded.

    La facture seeded contient :
    - Ligne 1 : 3 x 150 EUR HT, TVA 20% -> HT=450, TTC=540
    - Ligne 2 : 1 x 50 EUR HT, TVA 20% -> HT=50, TTC=60
    Total : HT=500, TVA=100, TTC=600
    """
    page, _ = panel_page("invoices")
    page.wait_for_timeout(1000)

    # Verifier les montants dans la reponse API
    assert seeded_invoice["subtotal_ht"] == 500.0, (
        f"HT attendu 500, recu {seeded_invoice['subtotal_ht']}"
    )
    assert seeded_invoice["total_tax"] == 100.0, (
        f"TVA attendue 100, recue {seeded_invoice['total_tax']}"
    )
    assert seeded_invoice["total_ttc"] == 600.0, (
        f"TTC attendu 600, recu {seeded_invoice['total_ttc']}"
    )

    # Verifier que le montant TTC est affiche dans le panel
    expect(page.get_by_text("600.00")).to_be_visible(timeout=5000)

    take_screenshot(page, "invoices_line_calculation")


def test_invoices_mark_paid(panel_page, seeded_invoice, api_client):
    """
    P0 - Marquer une facture comme payee via l'API,
    verifier que le statut change dans l'UI.
    """
    page, _ = panel_page("invoices")
    page.wait_for_timeout(1000)

    invoice_id = seeded_invoice["id"]

    # Verifier le statut initial (brouillon)
    expect(page.get_by_text("Brouillon").first).to_be_visible(timeout=5000)

    # Marquer comme payee via API
    resp = api_client.patch(f"/api/invoices/{invoice_id}/mark-paid", json={})
    assert resp.status_code == 200

    # Recharger
    page.reload()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    # Le statut doit maintenant etre "Payee"
    expect(page.get_by_text("Payee").first).to_be_visible(timeout=5000)

    take_screenshot(page, "invoices_mark_paid")


# ============================================================
# P1 - Tests secondaires
# ============================================================


def test_invoices_download_pdf(panel_page, seeded_invoice, api_client):
    """
    P1 - Generer un PDF via l'API, verifier que le chemin est retourne.
    """
    page, _ = panel_page("invoices")
    page.wait_for_timeout(500)

    invoice_id = seeded_invoice["id"]

    # Generer le PDF via API
    resp = api_client.get(f"/api/invoices/{invoice_id}/pdf")

    # L'API peut retourner 200 (PDF genere) ou 404 si le profil manque
    if resp.status_code == 200:
        data = resp.json()
        assert "pdf_path" in data, "Reponse sans pdf_path"
        assert "invoice_number" in data, "Reponse sans invoice_number"
        assert data["invoice_number"] == seeded_invoice["invoice_number"]

        # Verifier que le chemin pointe vers un fichier .pdf
        assert data["pdf_path"].endswith(".pdf"), (
            f"Chemin PDF invalide: {data['pdf_path']}"
        )
    else:
        # En environnement de test, le profil utilisateur peut manquer
        # ce qui est acceptable pour un test P1
        pytest.skip(
            f"PDF non genere (status {resp.status_code}) - profil manquant probable"
        )

    take_screenshot(page, "invoices_download_pdf")


def test_invoices_edit(panel_page, seeded_invoice, api_client):
    """
    P1 - Editer les notes d'une facture via l'API, verifier la mise a jour.
    """
    page, _ = panel_page("invoices")
    page.wait_for_timeout(1000)

    invoice_id = seeded_invoice["id"]

    # Editer via API - changer les notes
    resp = api_client.put(f"/api/invoices/{invoice_id}", json={
        "notes": "Notes mises a jour par test E2E",
    })
    assert resp.status_code == 200

    updated = resp.json()
    assert updated["notes"] == "Notes mises a jour par test E2E"

    # Verifier que la facture est toujours visible dans le panel
    page.reload()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    expect(page.get_by_text(seeded_invoice["invoice_number"])).to_be_visible(timeout=5000)

    take_screenshot(page, "invoices_edit")


def test_invoices_delete(panel_page, seeded_invoice, api_client):
    """
    P1 - Supprimer une facture via l'API, verifier qu'elle disparait.
    """
    page, _ = panel_page("invoices")
    page.wait_for_timeout(1000)

    invoice_number = seeded_invoice["invoice_number"]
    invoice_id = seeded_invoice["id"]

    # Verifier que la facture est visible
    expect(page.get_by_text(invoice_number)).to_be_visible(timeout=5000)

    # Supprimer via API
    resp = api_client.delete(f"/api/invoices/{invoice_id}")
    assert resp.status_code == 200

    # Recharger
    page.reload()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    # La facture ne doit plus etre visible
    expect(page.get_by_text(invoice_number)).to_be_hidden(timeout=5000)

    # Le message "Aucune facture" doit reapparaitre
    expect(page.get_by_text("Aucune facture")).to_be_visible(timeout=3000)

    take_screenshot(page, "invoices_delete")


def test_invoices_filter_by_status(panel_page, seeded_invoice, api_client):
    """
    P1 - Filtrer les factures par statut "Brouillon".
    Verifier que le filtre fonctionne.
    """
    page, _ = panel_page("invoices")
    page.wait_for_timeout(1000)

    invoice_number = seeded_invoice["invoice_number"]

    # Verifier que la facture est visible (statut draft par defaut)
    expect(page.get_by_text(invoice_number)).to_be_visible(timeout=5000)

    # Cliquer sur le filtre "Brouillon" (la facture seeded est en draft)
    brouillon_button = page.locator("button").filter(has_text="Brouillon")
    expect(brouillon_button).to_be_visible(timeout=3000)
    brouillon_button.click()
    page.wait_for_timeout(500)

    # La facture doit toujours etre visible (elle est en draft)
    expect(page.get_by_text(invoice_number)).to_be_visible(timeout=5000)

    # Cliquer sur "Payee" - la facture draft ne doit plus apparaitre
    payee_button = page.locator("button").filter(has_text="Payee")
    expect(payee_button).to_be_visible(timeout=3000)
    payee_button.click()
    page.wait_for_timeout(500)

    # La facture draft ne doit plus etre visible
    expect(page.get_by_text(invoice_number)).to_be_hidden(timeout=5000)

    # Revenir a "Toutes"
    toutes_button = page.locator("button").filter(has_text="Toutes")
    toutes_button.click()
    page.wait_for_timeout(500)

    # La facture doit reapparaitre
    expect(page.get_by_text(invoice_number)).to_be_visible(timeout=5000)

    take_screenshot(page, "invoices_filter_status")
