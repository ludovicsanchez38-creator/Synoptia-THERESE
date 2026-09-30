"""Le plan du lot C doit dire ce que la seconde passe a tranché, et ce
que l'article 242 nonies A, I, 7° ne justifie pas."""

from pathlib import Path

PLAN = Path("docs/plans/2026-09-29-lot-c-factures.md").read_text(encoding="utf-8")


def test_le_7_ne_justifie_pas_deux_series_et_on_s_arrete():
    assert "n'établit pas" in PLAN
    assert "FACT-" in PLAN and "AV-" in PLAN
    assert "conserv" in PLAN
    assert "décision humaine" in PLAN


def test_le_plan_decrit_lemission_la_date_et_l_avoir():
    texte = PLAN.casefold()
    assert "date du jour" in texte
    assert "avoir inverse" in texte
    assert "facture déjà émise" in texte
    assert "dernier" in texte
