"""B-1115 (cycle 12, réparé au cycle 13) : les actions tierces de la release
sont épinglées par empreinte.

Le travail de build de `release.yml` reçoit la clé privée de l'updater
(TAURI_SIGNING_PRIVATE_KEY). Il utilisait des actions tierces par étiquette
mobile (`tauri-action@v0`, `rust-cache@v2`…) : quiconque déplace l'étiquette
exécute son code avec la clé. Chaque action hors `actions/` (GitHub) et hors
workflow local est épinglée par une empreinte de commit, l'étiquette en
commentaire. `rust-toolchain` épinglé par empreinte perd la chaîne déduite du
nom de branche : l'entrée `toolchain` est obligatoire.
"""

import re
from pathlib import Path

RELEASE = Path(".github/workflows/release.yml")
EMPREINTE = re.compile(r"@[0-9a-f]{40}(\s|$)")


def _usages() -> list[tuple[int, str]]:
    return [
        (numero, ligne.split("uses:", 1)[1].strip())
        for numero, ligne in enumerate(RELEASE.read_text(encoding="utf-8").splitlines(), 1)
        if "uses:" in ligne and not ligne.strip().startswith("#")
    ]


def test_chaque_action_tierce_est_epinglee_par_empreinte():
    tierces = [(n, u) for n, u in _usages() if not u.startswith(("./", "actions/"))]
    assert tierces, "aucune action tierce trouvée : le test ne lit plus le bon fichier"
    mobiles = [f"ligne {n} : {u}" for n, u in tierces if not EMPREINTE.search(u)]
    assert not mobiles, "actions tierces par étiquette mobile : " + "; ".join(mobiles)


def test_rust_toolchain_nomme_sa_chaine():
    texte = RELEASE.read_text(encoding="utf-8")
    bloc = texte[texte.index("dtolnay/rust-toolchain"):]
    bloc = bloc[: bloc.index("\n      - ")]
    assert "toolchain: stable" in bloc, bloc
