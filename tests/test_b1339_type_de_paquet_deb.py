"""B-1339 : le .deb officiel doit se reconnaître comme paquet Debian.

Audit bêta du 27/10/2026 (A2) : sur la 0.81.0 installée, le bandeau « télécharge
la nouvelle version » s'affichait à chaque lancement et la mise à jour automatique
ne partait jamais : le binaire garde `__TAURI_BUNDLE_TYPE_VAR_UNK`.

Cause établie par la CI de la 0.81.1 : le bundler du CLI 2.9.6 cherche dans la
table des symboles un nom `__TAURI_BUNDLE_TYPE` que tauri-utils ne déclare pas
`no_mangle` ; garder les symboles (strip = "debuginfo") ne suffit donc pas.
Le bundler 2.10.4 (CLI 2.12) cherche directement le texte du marqueur.
Correctif reporté au lot qui monte le CLI ; la recette signale l'écart d'ici là.
"""
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]


def test_la_recette_du_deb_controle_le_marquage_du_binaire():
    recette = (RACINE / "scripts/recette-deb.sh").read_text(encoding="utf-8")

    assert 'grep -aq "__TAURI_BUNDLE_TYPE_VAR_DEB" "$APPLI"' in recette
