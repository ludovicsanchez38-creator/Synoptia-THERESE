"""Mesure la taille et le contraste du pied sur un véritable PDF généré."""

from app.services.invoice_pdf import InvoicePDFGenerator
from app.services.pdf_theme import SYNOPTIA_THEME
from pypdf import PdfReader

from tests.test_invoice_pdf_francais import donnees_facture


def _luminance(rgb):
    composantes = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
    return sum(valeur * poids for valeur, poids in zip(composantes, (0.2126, 0.7152, 0.0722), strict=True))


def test_pied_du_pdf_a_un_contraste_et_un_corps_lisibles(tmp_path):
    chemin = InvoicePDFGenerator(output_dir=str(tmp_path)).generate_invoice_pdf(
        donnees_facture(),
        {"name": "Alice", "address": "Lyon"},
        {"name": "Camille", "company": "Atelier", "address": "Paris", "siret": "12345678900010"},
    )
    page = PdfReader(chemin).pages[0]
    couleur = (0.0, 0.0, 0.0)
    pile = []
    pied = []

    def operande(op, args, _cm, _tm):
        nonlocal couleur
        if op == b"q":
            pile.append(couleur)
        elif op == b"Q":
            couleur = pile.pop()
        elif op == b"rg":
            couleur = tuple(float(valeur) for valeur in args)
        elif op == b"g":
            couleur = (float(args[0]),) * 3

    def texte(contenu, _cm, _tm, _police, taille):
        if "Document généré par THÉRÈSE" in contenu:
            pied.append((couleur, taille))

    page.extract_text(visitor_operand_before=operande, visitor_text=texte)
    assert pied, "Le texte du pied doit être présent dans le PDF."
    rgb, taille = pied[0]
    contraste_sur_blanc = 1.05 / (_luminance(rgb) + 0.05)
    assert contraste_sur_blanc >= 4.5, f"Contraste du pied : {contraste_sur_blanc:.2f}:1"
    assert taille >= SYNOPTIA_THEME.get_styles()["small"].fontSize
