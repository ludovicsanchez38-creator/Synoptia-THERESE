"""Le bilan du lot distingue son candidat retiré du test conservé dans l'arbre."""

from pathlib import Path


def test_bilan_distingue_retrait_b2029_et_test_integre():
    racine = Path(__file__).resolve().parents[1]
    assert (racine / "tests/test_b2029_couverture.py").is_file()
    bilan = (racine / "docs/qualite/c20-diff-4.md").read_text(encoding="utf-8")
    collecte_niee = "le fichier retiré n'y est donc plus collecté" in bilan
    assert not collecte_niee, "Le bilan nie la collecte du test B-2029 pourtant présent."

    etat_courant = bilan.split("\n## ", 1)[0]
    assert "retirés du lot, reportés" in etat_courant
    assert "tests/test_b2029_couverture.py" in etat_courant
    assert "conservé par l'intégration" in etat_courant
    assert "reste collecté" in etat_courant
