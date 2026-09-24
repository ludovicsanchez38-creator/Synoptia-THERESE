"""P-099 (acceptée par Ludo le 24/09/2026) : recette automatique du paquet
Linux .deb comme porte du workflow de release.

B-948 (DOCX en échec sur .deb depuis la 0.4.6) ne se voyait qu'en ouvrant le
paquet publié. `scripts/recette-deb.sh` extrait le .deb produit, le rend non
inscriptible comme /usr/lib, vérifie les dossiers témoins, démarre le moteur
et génère un DOCX avec pied de page. Calibré le 24/09/2026 sur DQ SYN : le
paquet publié 0.74.1 passe (0 échec), le 0.74.0 échoue (5 échecs, la
FileNotFoundError de B-948).
"""

from __future__ import annotations

from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "scripts" / "recette-deb.sh"
RELEASE = RACINE / ".github" / "workflows" / "release.yml"


def test_le_script_de_recette_controle_les_temoins_de_b948_et_le_pied_de_page():
    texte = SCRIPT.read_text(encoding="utf-8")
    for requis in ("docx/parts", "pptx/oxml", "pptx/shapes"):
        assert requis in texte, requis
    assert "dpkg-deb -x" in texte and "chmod -R a-w" in texte
    assert "format=docx" in texte and "word/footer" in texte
    # Sous pipefail, un tube vers grep -q échoue à tort (calibration du 24/09).
    assert "| grep -q" not in texte


def test_la_release_linux_joue_la_recette_apres_la_construction():
    texte = RELEASE.read_text(encoding="utf-8")
    assert "scripts/recette-deb.sh" in texte, "la release ne joue pas la recette du .deb"
    construction = texte.index("name: Build THÉRÈSE (Tauri)")
    recette = texte.index("scripts/recette-deb.sh")
    assert recette > construction, "la recette doit suivre la construction du paquet"
    etape = texte[texte.rfind("- name:", 0, recette):recette]
    assert "runner.os == 'Linux'" in etape, etape
