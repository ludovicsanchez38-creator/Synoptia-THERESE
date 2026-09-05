"""B-570 (05/09/2026) : le PDF écrivait « 1490,00 » là où l'écran dit
« 1 490,00 », et « N. FACT-2026-002 » au lieu de « N° FACT-2026-002 »."""

from pathlib import Path

from app.services.invoice_pdf import _montant_fr

SOURCE = Path(__file__).resolve().parents[1] / "src" / "backend" / "app" / "services" / "invoice_pdf.py"


def test_les_milliers_sont_groupes_a_la_francaise():
    assert _montant_fr(1490.0) == "1 490,00"
    assert _montant_fr(1234567.891) == "1 234 567,89"
    assert _montant_fr(22.0) == "22,00"
    assert _montant_fr(-1490.5) == "-1 490,50"


def test_le_numero_de_document_porte_le_symbole_numero():
    source = SOURCE.read_text(encoding="utf-8")
    assert 'f"N. {' not in source
    assert 'f"N° {' in source
