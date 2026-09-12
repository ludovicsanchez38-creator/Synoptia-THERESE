"""B-306 : le gate Linux ne rejoue plus le backend dans un enfant imbriqué."""

from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent
WORKFLOW = RACINE / ".github" / "workflows" / "ci.yml"


def _jobs() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]


def _commande(job: dict, nom_etape: str) -> str:
    return next(etape["run"] for etape in job["steps"] if etape.get("name") == nom_etape)


def test_le_backend_autonome_linux_est_execute_directement_en_parallele():
    jobs = _jobs()
    autonome = jobs["backend-autonomous"]
    commande = _commande(autonome, "Tests backend autonomes (pytest)")

    assert "pytest src/backend/tests/" in commande
    assert "needs" not in autonome
    assert autonome["timeout-minutes"] == 15


def test_la_suite_principale_linux_ecarte_seulement_la_reexecution_runtime():
    jobs = _jobs()
    principale = jobs["backend-tests"]
    commande = _commande(principale, "Tests unitaires (pytest)")

    assert "pytest tests/" in commande
    assert "tests/ src/backend/tests/" not in commande
    assert '-k "not test_le_dossier_src_backend_tests_tient_seul"' in commande
    assert "--ignore=tests/e2e" in commande


def test_le_backend_autonome_linux_garde_ses_bornes_et_son_rapport():
    autonome = _jobs()["backend-autonomous"]
    etape = next(
        etape
        for etape in autonome["steps"]
        if etape.get("name") == "Tests backend autonomes (pytest)"
    )
    publication = next(
        etape
        for etape in autonome["steps"]
        if etape.get("uses") == "actions/upload-artifact@v4"
    )

    assert etape["timeout-minutes"] == 12
    assert etape["timeout-minutes"] < autonome["timeout-minutes"]
    assert "--timeout=60" in etape["run"]
    assert publication["with"]["path"] == "pytest-backend-autonomous.xml"
