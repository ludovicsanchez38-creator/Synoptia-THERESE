"""B-1338 : les mentions de pénalités d'une facture respectent L441-10.

Audit bêta du 27/10/2026 (A4) : une facture créée directement (écran Factures
ou chat) n'a pas de `legal_mentions` ; le PDF imprimait alors « application
d'intérêts de retard au taux légal », soit un taux sous le plancher légal
(trois fois le taux d'intérêt légal), et n'indiquait aucune condition
d'escompte, deux mentions obligatoires (art. L441-9 du Code de commerce).
La conversion d'un devis, elle, annonçait « 11,62 % (3 fois le taux
d'intérêt légal en vigueur) », parenthèse fausse.

La formule retenue ne vieillit pas : le taux supplétif de L441-10 (taux de
refinancement de la BCE majoré de 10 points), sans chiffre écrit en dur.
"""
import re
from pathlib import Path

from app.routers.invoices import generate_legal_mentions
from app.services.invoice_pdf import InvoicePDFGenerator
from pypdf import PdfReader

from tests.test_invoice_pdf_francais import donnees_facture

PROFIL = {
    "name": "Ludovic Sanchez",
    "company": "Synoptïa",
    "address": "Manosque",
    "siret": "99160678100011",
    "code_ape": "6202A",
    "tva_intra": "FR08991606781",
}
CLIENT = {"name": "Élodie Martin", "company": "Atelier Élan", "email": "", "phone": "", "address": "Manosque"}


def _texte_pdf(tmp_path: Path, **surcharges) -> str:
    donnees = {**donnees_facture(), **surcharges}
    chemin = InvoicePDFGenerator(output_dir=str(tmp_path)).generate_invoice_pdf(
        invoice_data=donnees, contact_data=CLIENT, user_profile=PROFIL,
    )
    texte = " ".join(page.extract_text() or "" for page in PdfReader(chemin).pages)
    return re.sub(r"\s+", " ", texte)


def test_facture_directe_annonce_le_taux_legal_de_l441_10(tmp_path):
    texte = _texte_pdf(tmp_path)

    assert "majoré de 10 points" in texte
    assert "L441-10" in texte
    assert "au taux légal" not in texte


def test_facture_directe_porte_la_mention_d_escompte(tmp_path):
    texte = _texte_pdf(tmp_path)

    assert "Escompte pour paiement anticipé : néant" in texte
    assert "Indemnité forfaitaire pour frais de recouvrement : 40" in texte


def test_devis_converti_ne_pretend_plus_que_le_taux_vaut_trois_fois_le_legal():
    texte = generate_legal_mentions(late_penalty_rate=11.62, due_date_str="30/11/2026")

    assert "11,62 %" in texte
    assert "3 fois le taux d'intérêt légal en vigueur" not in texte
    assert "Escompte pour paiement anticipé : néant" in texte
