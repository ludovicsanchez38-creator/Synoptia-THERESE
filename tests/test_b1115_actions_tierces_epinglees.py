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

import pytest

RELEASE = Path(".github/workflows/release.yml")
# B-1183 : la release appelle ci.yml (gate de release, `contents: write`) ;
# ses actions tierces s'exécutent donc aussi dans le périmètre de la release.
WORKFLOWS = [RELEASE, Path(".github/workflows/ci.yml")]
EMPREINTE = re.compile(r"@[0-9a-f]{40}(\s|$)")


def _usages(workflow: Path) -> list[tuple[int, str]]:
    return [
        (numero, ligne.split("uses:", 1)[1].strip())
        for numero, ligne in enumerate(workflow.read_text(encoding="utf-8").splitlines(), 1)
        if "uses:" in ligne and not ligne.strip().startswith("#")
    ]


def test_la_release_appelle_bien_ci_yml():
    assert "uses: ./.github/workflows/ci.yml" in RELEASE.read_text(encoding="utf-8")


@pytest.mark.parametrize("workflow", WORKFLOWS, ids=lambda w: w.name)
def test_chaque_action_tierce_est_epinglee_par_empreinte(workflow: Path):
    tierces = [(n, u) for n, u in _usages(workflow) if not u.startswith(("./", "actions/"))]
    assert tierces, "aucune action tierce trouvée : le test ne lit plus le bon fichier"
    mobiles = [f"ligne {n} : {u}" for n, u in tierces if not EMPREINTE.search(u)]
    assert not mobiles, f"{workflow.name}, actions tierces par étiquette mobile : " + "; ".join(mobiles)


@pytest.mark.parametrize("workflow", WORKFLOWS, ids=lambda w: w.name)
def test_rust_toolchain_nomme_sa_chaine(workflow: Path):
    texte = workflow.read_text(encoding="utf-8")
    bloc = texte[texte.index("dtolnay/rust-toolchain"):]
    bloc = bloc[: bloc.index("\n      - ")]
    assert "toolchain: stable" in bloc, bloc


def _appeles_par_la_release() -> list[str]:
    return re.findall(r"uses: \./(\.github/workflows/[\w.-]+\.yml)", RELEASE.read_text(encoding="utf-8"))


def test_la_release_appelle_des_workflows_connus():
    assert set(_appeles_par_la_release()) >= {".github/workflows/ci.yml", ".github/workflows/tests-e2e.yml"}


@pytest.mark.parametrize("chemin", [".github/workflows/ci.yml", ".github/workflows/tests-e2e.yml"])
def test_un_workflow_appele_par_la_release_ne_garde_que_la_lecture(chemin: str):
    """B-1183, puis B-1210 pour tests-e2e.yml : appelé par la release, un
    workflow héritait de `contents: write` (journal du run 36034697390) alors
    qu'aucun de ses travaux n'écrit dans le dépôt. Le jeton est ramené à la
    lecture."""
    texte = Path(chemin).read_text(encoding="utf-8")
    entete = texte[: texte.index("\njobs:")]
    assert "\npermissions:\n  contents: read" in entete, entete
