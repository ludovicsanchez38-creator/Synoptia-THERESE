"""B-128 : le cliquet mypy de la CI tolerait silencieusement des erreurs neuves.

L'etape `mypy - BLOQUANT au-dela de la baseline` (`.github/workflows/ci.yml`)
comparait le compte reel a `MYPY_BASELINE` avec `-gt` : tant que la constante
etait posee AU-DESSUS du compte reel, l'ecart devenait du mou, et le cliquet
laissait passer autant de nouvelles erreurs qu'il y avait d'ecart, sans un mot.
Le commentaire de l'etape raconte deja ce mecanisme d'usure : recalage de 999 a
1004 le 24/08 apres l'avoir laisse rouge plusieurs chantiers.

Le test n'appelle JAMAIS mypy (dix minutes en CI) : il extrait le vrai `run:`
du workflow, le lance avec un faux `uv` en tete de PATH qui rend K erreurs
mises en forme, et verifie les TROIS issues autour de la baseline. K < baseline
doit echouer aussi - sinon le mou peut se reconstituer a la prochaine
amelioration non repercutee.
"""

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

RACINE = Path(__file__).resolve().parent.parent
WORKFLOW = RACINE / ".github" / "workflows" / "ci.yml"


def _etape_mypy() -> dict:
    contenu = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    etapes = contenu["jobs"]["mypy"]["steps"]
    for etape in etapes:
        if "mypy" in etape.get("name", "") and "run" in etape:
            return etape
    raise AssertionError("etape mypy introuvable dans ci.yml")


def _lancer(tmp_path: Path, nombre_d_erreurs: int, baseline: str) -> subprocess.CompletedProcess:
    """Rejoue le `run:` du workflow avec un faux `uv` qui rend K erreurs."""
    faux_bin = tmp_path / "bin"
    faux_bin.mkdir(exist_ok=True)
    faux_uv = faux_bin / "uv"
    lignes = "\n".join(
        f"src/backend/app/faux{i}.py:1: error: Faux defaut de typage  [no-untyped-def]"
        for i in range(nombre_d_erreurs)
    )
    faux_uv.write_text(
        "#!/bin/sh\n"
        f"cat <<'FIN'\n{lignes}\nFIN\n"
        # mypy sort en 1 des qu'il trouve une erreur : le `|| true` du
        # workflow doit continuer a absorber ce code de sortie.
        "exit 1\n",
        encoding="utf-8",
    )
    faux_uv.chmod(0o755)

    script = tmp_path / "etape.sh"
    script.write_text(_etape_mypy()["run"], encoding="utf-8")

    return subprocess.run(
        ["bash", str(script)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env={
            "PATH": f"{faux_bin}:/usr/bin:/bin",
            "MYPY_BASELINE": baseline,
        },
    )


class TestCliquetMypy:
    def test_au_dessus_de_la_baseline_echoue(self, tmp_path):
        resultat = _lancer(tmp_path, 6, "5")
        assert resultat.returncode == 1, resultat.stdout
        assert "baseline" in resultat.stdout

    def test_egal_a_la_baseline_passe(self, tmp_path):
        resultat = _lancer(tmp_path, 5, "5")
        assert resultat.returncode == 0, resultat.stdout + resultat.stderr

    def test_sous_la_baseline_echoue_et_donne_le_chiffre(self, tmp_path):
        """C'est LE defaut B-128 : sous `-gt`, un compte inferieur passait au
        vert et l'ecart devenait du mou tolere en silence."""
        resultat = _lancer(tmp_path, 4, "5")
        assert resultat.returncode == 1, resultat.stdout
        # Le message doit dire quoi ecrire, sinon personne ne recale.
        assert "MYPY_BASELINE" in resultat.stdout
        assert "4" in resultat.stdout

    def test_sortie_vide_reste_rouge(self, tmp_path):
        """Garde anti-fail-open deja en place : ne pas la perdre au passage."""
        resultat = _lancer(tmp_path, 0, "5")
        assert resultat.returncode == 1, resultat.stdout

    def test_la_baseline_est_celle_mesuree_sur_le_runner(self):
        """Le compte est mesure sur ubuntu-latest, pas sur un poste de dev :
        run CI 33664976637 (commit 1b3a40fc) affiche « mypy : 1001 erreurs »
        la ou la mesure fraiche locale macOS en donne 1002."""
        assert _etape_mypy()["env"]["MYPY_BASELINE"] == "1001"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash requis")
def test_le_workflow_ne_compare_plus_avec_le_seul_gt():
    """Garde de lecture : la comparaison stricte doit rester a DEUX branches."""
    run = _etape_mypy()["run"]
    assert '-lt "$MYPY_BASELINE"' in run
    assert '-gt "$MYPY_BASELINE"' in run
