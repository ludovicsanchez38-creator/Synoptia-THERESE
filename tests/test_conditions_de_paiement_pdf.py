"""B-339 (05/09/2026) : le PDF imprimait « net à 30 jours » quelle que soit
l'échéance négociée.

Une facture convertie depuis un devis « 90 jours » portait une échéance au
04/12/2026 dans son en-tête et « Paiement à réception de facture, net à 30
jours » dans son bloc conditions, sur la même page. Le texte était en dur
dans `_build_conditions_block`, et le routeur ne transmettait même pas
`payment_terms`, `payment_method` ni `legal_mentions` au générateur.
"""

from __future__ import annotations

from pathlib import Path

from app.services.invoice_pdf import InvoicePDFGenerator
from pypdf import PdfReader


def _texte_du_pdf(tmp_path: Path, **surcharges) -> str:
    donnees = {
        "invoice_number": "FACT-2026-021",
        "document_type": "facture",
        "tva_applicable": True,
        "issue_date": "2026-09-05T00:00:00",
        "due_date": "2026-12-04T00:00:00",
        "status": "sent",
        "subtotal_ht": 100.0,
        "total_tax": 20.0,
        "total_ttc": 120.0,
        "notes": "",
        "lines": [
            {
                "description": "Conseil",
                "quantity": 1.0,
                "unit_price_ht": 100.0,
                "tva_rate": 20.0,
                "total_ht": 100.0,
                "total_ttc": 120.0,
            }
        ],
    }
    donnees.update(surcharges)
    chemin = InvoicePDFGenerator(output_dir=str(tmp_path)).generate_invoice_pdf(
        invoice_data=donnees,
        contact_data={"name": "Paul Durand", "company": "", "email": "", "phone": "", "address": "Manosque"},
        user_profile={"name": "Marie Exemple", "company": "Atelier Exemple", "address": "Manosque",
                      "siret": "12345678900011"},
    )
    return " ".join((page.extract_text() or "").replace("\n", " ") for page in PdfReader(chemin).pages)


def test_les_conditions_negociees_remplacent_le_texte_en_dur(tmp_path: Path):
    texte = _texte_du_pdf(
        tmp_path,
        payment_terms="90 jours",
        payment_method="Virement bancaire",
    )
    assert "90 jours" in texte, "l'échéance négociée n'est pas imprimée"
    assert "Virement bancaire" in texte, "le mode de règlement n'est pas imprimé"
    assert "net à 30 jours" not in texte, (
        "le PDF contredit son propre en-tête : échéance au 04/12 et « net à 30 jours »"
    )


def test_sans_conditions_negociees_le_defaut_reste_30_jours(tmp_path: Path):
    texte = _texte_du_pdf(tmp_path)
    assert "30 jours" in texte


def test_les_chevrons_des_conditions_sont_imprimes_et_ne_cassent_pas_le_pdf(tmp_path: Path):
    """Revue COCO 0.67 : payment_terms et payment_method sont des textes libres
    interpolés dans un Paragraph ReportLab. « 30 jours <fin de mois> » perdait
    la précision en silence, « 30 jours <b> » levait une erreur de parsing."""
    texte = _texte_du_pdf(
        tmp_path,
        payment_terms="30 jours <fin de mois>",
        payment_method="Virement <b>",
    )
    assert "fin de mois" in texte, "la précision entre chevrons a disparu du PDF"
    assert "Virement" in texte
