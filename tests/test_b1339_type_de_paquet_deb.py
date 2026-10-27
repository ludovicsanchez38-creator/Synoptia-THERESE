"""B-1339 : le .deb officiel doit se reconnaître comme paquet Debian.

Audit bêta du 27/10/2026 (A2) : sur la 0.81.0 installée, le bandeau « télécharge
la nouvelle version » s'affichait à chaque lancement et la mise à jour automatique
ne partait jamais : le binaire garde `__TAURI_BUNDLE_TYPE_VAR_UNK`.

Cause établie par la CI de la 0.81.1 : le bundler du CLI 2.9.6 cherchait dans la
table des symboles un nom `__TAURI_BUNDLE_TYPE` que tauri-utils ne déclare pas
`no_mangle` (« variable not found in binary »). Depuis le CLI 2.10 (bundler 2.8),
le bundler remplace le texte du marqueur dans les octets du binaire.
"""
import json
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
FRONT = RACINE / "src/frontend"


def _version(texte: str) -> tuple[int, ...]:
    return tuple(int(x) for x in texte.split("-")[0].split("."))


def test_le_cli_verrouille_sait_marquer_le_paquet():
    verrou = json.loads((FRONT / "package-lock.json").read_text(encoding="utf-8"))
    version = verrou["packages"]["node_modules/@tauri-apps/cli"]["version"]

    assert _version(version) >= (2, 10, 0), (
        f"@tauri-apps/cli {version} : son bundler ne marque pas le binaire (B-1339)"
    )


def test_le_cli_est_epingle_sans_derive():
    paquet = json.loads((FRONT / "package.json").read_text(encoding="utf-8"))
    declare = paquet["devDependencies"]["@tauri-apps/cli"]

    assert declare[0].isdigit(), f"« {declare} » : une montée du CLI doit être un choix, pas une dérive"


def test_la_recette_du_deb_refuse_un_binaire_non_marque():
    recette = (RACINE / "scripts/recette-deb.sh").read_text(encoding="utf-8")
    bloc = recette.split("B-1339", 1)[1]

    assert 'grep -aq "__TAURI_BUNDLE_TYPE_VAR_DEB" "$APPLI"' in recette
    assert 'ko "binaire non marqué comme paquet Debian' in bloc, "le contrôle doit être bloquant"
    assert "AVERTISSEMENT" not in bloc
