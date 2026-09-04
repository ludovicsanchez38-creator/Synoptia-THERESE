"""B-306 : le workflow Windows ne rejoue plus le backend dans un enfant imbriqué.

La suite principale atteignait 99 %, puis le test du harnais relançait toute la
seconde racine dans un sous-processus. Le workflow exécute désormais cette
racine directement, puis la suite principale sans le seul cas runtime devenu
redondant. Les collectes fichier par fichier restent actives.
"""

from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent
WORKFLOW = RACINE / ".github" / "workflows" / "tests-windows.yml"


def _commandes_pytest() -> list[str]:
    contenu = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    etapes = contenu["jobs"]["backend-tests-windows"]["steps"]
    return [etape["run"] for etape in etapes if "pytest" in etape.get("name", "").lower()]


def test_le_backend_autonome_est_execute_directement_une_seule_fois():
    commandes = _commandes_pytest()

    assert len(commandes) == 2
    assert "pytest src/backend/tests/" in commandes[0]
    assert "pytest tests/" in commandes[1]
    assert "tests/ src/backend/tests/" not in commandes[1]


def test_la_suite_principale_ecarte_seulement_la_reexecution_runtime():
    commande_principale = _commandes_pytest()[1]

    assert '-k "not test_le_dossier_src_backend_tests_tient_seul"' in commande_principale
    assert "--ignore=tests/e2e" in commande_principale


def test_les_deux_rapports_junit_sont_publies():
    contenu = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    etapes = contenu["jobs"]["backend-tests-windows"]["steps"]
    publication = next(
        etape for etape in etapes if etape.get("uses") == "actions/upload-artifact@v4"
    )

    assert publication["with"]["path"] == "junit-windows*.xml"
