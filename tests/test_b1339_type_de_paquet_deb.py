"""B-1339 : le .deb officiel doit se reconnaître comme paquet Debian.

Audit bêta du 27/10/2026 (A2) : sur la 0.81.0 installée, le bandeau « télécharge
la nouvelle version » s'affichait à chaque lancement alors que l'application
était à jour, et la mise à jour automatique ne partait jamais. `strip = true`
retirait la table des symboles ; le bundler Tauri n'y trouvait plus le symbole
`__TAURI_BUNDLE_TYPE` à marquer, le binaire gardait `__TAURI_BUNDLE_TYPE_VAR_UNK`
(constaté par `strings /usr/bin/therese`) et `getBundleType()` ne renvoyait pas
`deb`.

La preuve de bout en bout vit dans la recette du paquet produit par la CI
(`scripts/recette-deb.sh`), jouée contre le .deb 0.81.0 : rouge. Ces gardes
empêchent de retirer l'une ou l'autre moitié du correctif.
"""
import tomllib
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]


def test_le_profil_release_garde_la_table_des_symboles():
    cargo = tomllib.loads((RACINE / "src/frontend/src-tauri/Cargo.toml").read_text(encoding="utf-8"))
    strip = cargo["profile"]["release"].get("strip", False)

    assert strip not in (True, "symbols"), (
        "strip complet : le bundler ne peut plus marquer le type de paquet (B-1339)"
    )


def test_la_recette_du_deb_controle_le_marquage_du_binaire():
    recette = (RACINE / "scripts/recette-deb.sh").read_text(encoding="utf-8")

    assert "__TAURI_BUNDLE_TYPE_VAR_DEB" in recette
    assert 'grep -aq "__TAURI_BUNDLE_TYPE_VAR_DEB" "$APPLI"' in recette
