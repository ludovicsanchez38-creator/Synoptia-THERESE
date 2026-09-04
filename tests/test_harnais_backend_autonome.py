"""
`src/backend/tests/` tient lancé seul, sans le conftest de l'autre racine.

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

**B-306, la forme de ce harnais.** La première version lançait un
sous-processus pytest COMPLET par fichier, soit onze exécutions payant chacune
la collecte et le chargement des modules lourds : 2,2 à 5,2 s par cas en local,
et onze cas SANS marque de délai, donc soumis au `--timeout=30` de la CI. Deux
runs sur douze sont morts là-dessus (33707222584 et 33730115398, le 03/09) :
`+++ Timeout +++` en série à partir de 26 % de la suite, puis `timeout 480` qui
tue pytest à 83 % sans qu'aucun junit ne soit écrit.

Ce que les journaux disent au juste, car ce n'est pas « le runner est lent » :
sur 33707222584, les cas qui PASSENT tiennent 4 à 5,3 s, soit la vitesse
locale, pendant que cinq autres meurent pile au mur des 30 s ; sur
33730115398, les huit qui passent tiennent 7 à 14 s et trois meurent au mur.
Une lenteur uniforme ne produit pas ce partage-là. Les piles dumpées ne
tranchent pas davantage : pytest-timeout n'imprime jamais le thread courant, de
sorte qu'on ne voit que deux threads `aiosqlite` OISIFS du processus PARENT
(`future, function = tx.get()`), hérités de tests antérieurs et étrangers au
harnais. Ce qui retenait ces sous-processus n'est donc pas identifié, et ne
peut pas l'être depuis un poste local.

La forme retenue vaut dans les deux hypothèses : contre la lenteur, le travail
lourd n'est plus payé onze fois ; contre un blocage, il n'est plus exposé
qu'UNE fois, sous une borne explicite de 180 s au lieu de onze fenêtres de
30 s. Elle ne prétend pas dire lequel des deux c'était.

L'intention de B-249 est gardée, la dépense est redistribuée :

- **l'exécution** tient en UN sous-processus pour tout le dossier. C'est lui
  qui prouve la partie RUNTIME de l'autonomie (auth coupée, `init_db`, mock
  Qdrant) ; mesuré rouge sur 73 tests des sept mêmes fichiers quand on retire
  `app.state.auth_disabled`, exactement ceux que B-249 avait relevés. Il porte
  `@pytest.mark.timeout(180)` pour ne pas dépendre du délai global de 30 s, qui
  n'a jamais été taillé pour un cas qui rejoue un dossier entier ;
- **la propriété « chaque fichier tient seul »** se vérifie par une COLLECTE
  seule, ~2,1 s par fichier. C'est la partie IMPORT de l'autonomie : sans le
  `sys.path` du conftest, la collecte meurt en code 4 sur les onze. Ces cas
  restent délibérément SANS marque de délai, donc sous le budget de 30 s de la
  CI : c'est là que se lirait une régression de coût.

Aucun des deux ne remplace l'autre : la collecte seule ne réveille aucune
route, et le dossier lancé d'un bloc ne dirait pas quel fichier ne s'importe
pas tout seul.

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

# B-306 : bornes du sous-processus, tenues SOUS la marque de délai du cas pour
# que ce soit `subprocess.run` qui tue l'enfant et rende un message lisible,
# plutôt que pytest-timeout qui laisserait un pytest orphelin. Le dossier tient
# sous 170 s sur Linux/macOS ; le runner Windows observé le 04/09/2026 demande
# davantage, sans qu'aucun test individuel puisse dépasser ses propres 60 s.
DELAI_EXECUTION_SECONDES = 300 if sys.platform == "win32" else 170
# La collecte tourne en ~2,1 s ; ce délai n'est qu'un filet pour le lancement
# en local, où aucun `--timeout` global ne s'applique.
DELAI_COLLECTE_SECONDES = 90


def _environnement_pauvre(dossier_donnees: Path) -> dict[str, str]:
    environnement = {
        cle: valeur for cle, valeur in os.environ.items() if cle not in REGLAGES_HERITES
    }
    environnement["THERESE_DATA_DIR"] = str(dossier_donnees)
    environnement["TRANSFORMERS_OFFLINE"] = "1"
    environnement.setdefault("OLLAMA_BASE_URL", "http://127.0.0.1:9")
    return environnement


def _lancer_pytest(
    arguments: list[str], dossier_donnees: Path, delai: int
) -> subprocess.CompletedProcess[str]:
    commande = [sys.executable, "-m", "pytest", *arguments, "-p", "no:cacheprovider", "-q"]
    try:
        return subprocess.run(
            commande,
            cwd=str(RACINE),
            env=_environnement_pauvre(dossier_donnees),
            capture_output=True,
            text=True,
            timeout=delai,
        )
    except subprocess.TimeoutExpired as expiration:
        sortie = expiration.stdout or ""
        if isinstance(sortie, bytes):
            sortie = sortie.decode(errors="replace")
        pytest.fail(
            f"{' '.join(arguments)} n'a pas rendu la main en {delai} s "
            f"(B-306 : le harnais doit rester borné) :\n"
            f"{sortie[-2000:]}"
        )


def test_le_dossier_backend_a_bien_ses_fichiers_de_test():
    """Garde-fou : sans ça, un glob vide rendrait la paramétrisation vide et
    le contrôle ci-dessous passerait au vert sans rien vérifier."""
    assert len(FICHIERS) >= 11, FICHIERS


@pytest.mark.timeout(DELAI_EXECUTION_SECONDES + 10)
def test_le_dossier_src_backend_tests_tient_seul(tmp_path):
    """Volet RUNTIME de B-249, en UN seul sous-processus (B-306).

    C'est ce cas qui tombe si `app.state.auth_disabled`, la fixture `init_db`
    ou le mock Qdrant du conftest de `src/backend/tests` disparaissent.
    """
    execution = _lancer_pytest(
        ["src/backend/tests", "--no-header"], tmp_path, DELAI_EXECUTION_SECONDES
    )

    assert execution.returncode == 0, (
        f"src/backend/tests ne tient pas lancé seul (code {execution.returncode}) :\n"
        f"{execution.stdout[-4000:]}\n{execution.stderr[-2000:]}"
    )


@pytest.mark.parametrize("fichier", FICHIERS)
def test_chaque_fichier_de_src_backend_tests_se_collecte_seul(fichier, tmp_path):
    """Volet IMPORT de B-249, par collecte seule (B-306).

    Pas de marque de délai à dessein : ces cas doivent tenir dans le budget de
    30 s de la CI, sans quoi le harnais recommencerait à la tuer.
    """
    execution = _lancer_pytest(
        [f"src/backend/tests/{fichier}", "--collect-only", "--no-header"],
        tmp_path,
        DELAI_COLLECTE_SECONDES,
    )

    assert execution.returncode == 0, (
        f"src/backend/tests/{fichier} ne se collecte pas lancé seul "
        f"(code {execution.returncode}) :\n"
        f"{execution.stdout[-2500:]}\n{execution.stderr[-1500:]}"
    )
    # Une collecte vide rendrait le code 5, mais on le dit explicitement : ce
    # test n'a de valeur que s'il a bien vu les cas DE CE fichier.
    assert f"src/backend/tests/{fichier}::" in execution.stdout, (
        f"aucun cas collecté pour src/backend/tests/{fichier} :\n{execution.stdout[-2000:]}"
    )
