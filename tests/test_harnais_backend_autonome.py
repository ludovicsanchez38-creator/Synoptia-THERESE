"""
Chaque fichier de `src/backend/tests/` tient lancé seul.

**B-249 / B-258.** `pyproject.toml` collecte deux racines
(`testpaths = ["tests", "src/backend/tests"]`), mais seule la première portait
un `conftest.py` complet. Lancé seul, un fichier de `src/backend/tests/`
mourait donc à la collecte (`ModuleNotFoundError: No module named 'app'`,
faute de `src/backend` sur `sys.path`) et, une fois `PYTHONPATH` posé à la
main, rendait 503 `AUTH_NOT_READY` sur toute route HTTP : le middleware d'auth
est fail-closed et rien ne le coupait, là où `tests/conftest.py` pose
`app.state.auth_disabled = True` au niveau module.

C'est aussi toute l'explication de B-258 : `test_cancel_generation_endpoint`
était rouge en sélection ciblée et vert en suite complète, non par un effet
d'ordonnancement mais parce qu'un `conftest` de l'autre racine devait être
CHARGÉ pour que la route réponde. Réparer le harnais ferme les deux fiches ;
un test propre à ce seul nodeid figerait un symptôme dont la cause est
ailleurs.

Le sous-processus est lancé avec un environnement volontairement pauvre :
`PYTHONPATH` retiré (sinon on ne prouve pas le `sys.path` du conftest) et les
réglages `THERESE_*` hérités de la suite retirés eux aussi (sinon on ne prouve
pas que le harnais se suffit). Seul `THERESE_DATA_DIR` est imposé, sur un
dossier jetable : un test qui vérifie l'isolation n'a pas le droit de risquer
`~/.therese` si la réparation venait à régresser.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_BACKEND = RACINE / "src" / "backend" / "tests"

FICHIERS = sorted(chemin.name for chemin in DOSSIER_BACKEND.glob("test_*.py"))

# Réglages que la suite complète pose pour tout le monde et dont le harnais
# autonome doit se passer.
REGLAGES_HERITES = (
    "PYTHONPATH",
    "THERESE_ENV",
    "THERESE_DB_KEY",
    "THERESE_SKIP_SERVICES",
    "THERESE_SONDE_CATALOGUE",
    "THERESE_BACKUP_KDF_ITERATIONS",
    "THERESE_DB_PATH",
)


def test_le_dossier_backend_a_bien_ses_fichiers_de_test():
    """Garde-fou : sans ça, un glob vide rendrait la paramétrisation vide et
    le contrôle ci-dessous passerait au vert sans rien vérifier."""
    assert len(FICHIERS) >= 11, FICHIERS


@pytest.mark.parametrize("fichier", FICHIERS)
def test_chaque_fichier_de_src_backend_tests_tient_seul(fichier, tmp_path):
    environnement = {
        cle: valeur
        for cle, valeur in os.environ.items()
        if cle not in REGLAGES_HERITES
    }
    environnement["THERESE_DATA_DIR"] = str(tmp_path)
    environnement["TRANSFORMERS_OFFLINE"] = "1"
    environnement.setdefault("OLLAMA_BASE_URL", "http://127.0.0.1:9")

    execution = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            f"src/backend/tests/{fichier}",
            "-p",
            "no:cacheprovider",
            "-q",
            "--no-header",
        ],
        cwd=str(RACINE),
        env=environnement,
        capture_output=True,
        text=True,
        timeout=300,
    )

    assert execution.returncode == 0, (
        f"src/backend/tests/{fichier} ne tient pas lancé seul "
        f"(code {execution.returncode}) :\n"
        f"{execution.stdout[-2500:]}\n{execution.stderr[-1500:]}"
    )
