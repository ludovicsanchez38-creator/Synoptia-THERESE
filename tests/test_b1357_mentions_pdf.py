"""B-1357 (persona Claire, cycle 13) : les mentions des PDF de devis et de
facture doivent être vraies et écrites en français correct.

Observé sur le devis DEV-2026-001 et la facture FACT-2026-001, toutes deux à
TVA 0 % :

- « Mentions légales : TVA incluse selon les taux en vigueur », alors
  qu'aucune ligne ne porte de TVA ;
- des conditions sans accents (« Date d'echeance », « penalite… appliquee »,
  « indemnite… exigee », « anticipe : neant ») et un taux au point décimal
  (« 11.62% ») ;
- « Paiement à réception de facture, net à 30 jours », qui se contredit
  (à réception, ou à trente jours ?).
"""

from app.routers.invoices import generate_legal_mentions
from app.services.invoice_pdf import InvoicePDFGenerator
from pypdf import PdfReader


def _rendre_pdf(tmp_path, *, document_type="facture", taux=0.0, legal_mentions=""):
    gen = InvoicePDFGenerator(output_dir=str(tmp_path))
    tva = round(100.0 * taux / 100, 2)
    invoice_data = {
        "invoice_number": f"{document_type.upper()}-B1357-{int(taux)}",
        "document_type": document_type,
        "tva_applicable": True,
        "validite_jours": 30,
        "issue_date": "2026-09-25T00:00:00",
        "due_date": "2026-10-25T00:00:00",
        "status": "draft",
        "subtotal_ht": 100.0,
        "total_tax": tva,
        "total_ttc": 100.0 + tva,
        "notes": "",
        "legal_mentions": legal_mentions,
        "lines": [{
            "description": "Séance de coaching",
            "quantity": 1,
            "unit_price_ht": 100.0,
            "tva_rate": taux,
            "total_ht": 100.0,
            "total_ttc": 100.0 + tva,
        }],
    }
    contact = {"name": "Hélène Ménard", "company": "", "email": "", "phone": "", "address": ""}
    profil = {
        "name": "Claire Exemple", "company": "Claire Exemple Coaching",
        "address": "Lyon", "siren": "", "siret": "99988877900009",
        "code_ape": "", "tva_intra": "",
    }
    chemin = gen.generate_invoice_pdf(
        invoice_data=invoice_data, contact_data=contact, user_profile=profil,
    )
    texte = "".join(page.extract_text() for page in PdfReader(chemin).pages)
    return " ".join(texte.split())


def test_les_mentions_de_la_facture_sont_accentuees():
    texte = generate_legal_mentions(due_date_str="25/10/2026", currency="EUR")
    for attendu in (
        "Date d'échéance",
        "pénalité",
        "appliquée",
        "indemnité",
        "exigée",
        "anticipé : néant",
    ):
        assert attendu in texte, f"« {attendu} » manque dans : {texte}"


def test_le_taux_de_penalite_s_ecrit_a_la_francaise():
    texte = generate_legal_mentions(due_date_str="25/10/2026", currency="EUR")
    assert "11,62 %" in texte
    assert "11.62" not in texte


def test_la_mention_hors_euro_est_accentuee():
    texte = generate_legal_mentions(due_date_str="25/10/2026", currency="CAD")
    assert "pénalités pourront être appliquées" in texte


def test_un_pdf_sans_tva_ne_dit_pas_tva_incluse(tmp_path):
    texte = _rendre_pdf(tmp_path, taux=0.0)
    assert "TVA incluse" not in texte


def test_un_pdf_avec_tva_garde_sa_mention(tmp_path):
    texte = _rendre_pdf(tmp_path, taux=20.0)
    assert "TVA incluse" in texte


def test_le_reglement_par_defaut_ne_se_contredit_pas(tmp_path):
    for type_de_piece in ("devis", "facture"):
        texte = _rendre_pdf(tmp_path, document_type=type_de_piece, taux=20.0)
        assert "réception de facture, net à 30 jours" not in texte, type_de_piece
        assert "30 jours" in texte, type_de_piece
