"""Le PDF ne prête pas la franchise à un émetteur au régime normal."""

from tests.test_p119_regime_tva import _texte_du_pdf


def test_sans_tva_le_regime_normal_ne_devient_pas_une_franchise(tmp_path):
    texte = _texte_du_pdf(tmp_path, regime="normal", taux=0, tva_applicable=False)
    assert "293 B" not in texte
    assert "Aucune TVA facturée" in texte
