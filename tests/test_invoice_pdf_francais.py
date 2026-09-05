"""B-324 : le PDF final doit parler français, accents compris."""

from pathlib import Path

from app.services.invoice_pdf import InvoicePDFGenerator, libelle_statut_pdf
from pypdf import PdfReader


def donnees_facture(statut: str = "sent") -> dict:
    return {
        "invoice_number": "FACT-2026-324",
        "document_type": "facture",
        "tva_applicable": True,
        "issue_date": "2026-08-01T00:00:00",
        "due_date": "2026-08-31T00:00:00",
        "status": statut,
        "subtotal_ht": 100.0,
        "total_tax": 20.0,
        "total_ttc": 120.0,
        "notes": "Prestation réalisée à Manosque.",
        "lines": [{
            "description": "Conseil stratégique",
            "quantity": 1,
            "unit_price_ht": 100.0,
            "tva_rate": 20.0,
            "total_ht": 100.0,
            "total_ttc": 120.0,
        }],
    }


def test_les_statuts_sont_traduits_et_accordes():
    assert libelle_statut_pdf("sent", "facture") == "Envoyée"
    assert libelle_statut_pdf("overdue", "facture") == "En retard"
    assert libelle_statut_pdf("sent", "devis") == "Envoyé"
    assert libelle_statut_pdf("accepted", "devis") == "Accepté"
    assert libelle_statut_pdf("custom_status", "facture") == "Custom status"


def test_le_texte_extrait_du_pdf_conserve_accents_et_statut_francais(tmp_path: Path):
    generateur = InvoicePDFGenerator(output_dir=str(tmp_path))
    chemin = generateur.generate_invoice_pdf(
        invoice_data=donnees_facture(),
        contact_data={
            "name": "Élodie Martin",
            "company": "Atelier Élan",
            "email": "elodie@example.test",
            "phone": "",
            "address": "Manosque",
        },
        user_profile={
            "name": "Ludovic Sanchez",
            "company": "Synoptïa",
            "address": "Manosque",
            "siret": "99160678100011",
            "code_ape": "6202A",
            "tva_intra": "FR08991606781",
        },
    )

    texte = "\n".join(page.extract_text() or "" for page in PdfReader(chemin).pages)

    for attendu in (
        "FACTURE",
        "ÉMETTEUR",
        "Date d’émission",
        "Date d’échéance",
        "Envoyée",
        "DÉTAIL DES PRESTATIONS",
        "intérêts de retard",
        "taux légal",
        "Indemnité forfaitaire",
        "Mentions légales",
        "Document généré par THÉRÈSE",
    ):
        assert attendu in texte
    assert "SENT" not in texte


class TestB507LesChevronsDUnTexteLibreNeSontPasDesBalises:
    """B-507 (05/09/2026) : aucun échappement XML avant Paragraph. « Réf
    <ABC-12> » disparaissait du PDF sans erreur (pris pour une balise), et
    « Société <A> Conseil » faisait tomber la génération (ValueError du
    paraparser, recopiée en 500).
    """

    def _pdf(self, tmp_path: Path, **surcharges) -> str:
        donnees = donnees_facture()
        donnees["lines"][0]["description"] = "Prestation Réf <ABC-12> à <urgent>"
        contact = {
            "name": "Société <A> Conseil",
            "company": "Dupont <SARL> & Fils",
            "email": "",
            "phone": "",
            "address": "1 rue a<b",
        }
        contact.update(surcharges)
        chemin = InvoicePDFGenerator(output_dir=str(tmp_path)).generate_invoice_pdf(
            invoice_data=donnees,
            contact_data=contact,
            user_profile={"name": "Marie <Exemple>", "company": "Atelier", "address": "Manosque",
                          "siret": "12345678900011"},
        )
        return " ".join((p.extract_text() or "").replace("\n", " ") for p in PdfReader(chemin).pages)

    def test_un_chevron_ne_fait_plus_tomber_la_generation(self, tmp_path: Path):
        texte = self._pdf(tmp_path)
        assert "Société <A> Conseil" in texte

    def test_un_chevron_n_efface_plus_de_texte(self, tmp_path: Path):
        texte = self._pdf(tmp_path)
        assert "<ABC-12>" in texte, "la référence entre chevrons a disparu du PDF"
        assert "<urgent>" in texte
        assert "Dupont <SARL> & Fils" in texte
