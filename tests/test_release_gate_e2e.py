"""B-158 (cycle 4) : le workflow des parcours de bout en bout ne conditionnait
pas la release et n'était appelé par personne : un échec des contrats d'API
n'empêchait rien. Il est appelable et la construction en dépend."""

from __future__ import annotations

from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parents[1]


def _workflow(nom: str) -> dict:
    return yaml.safe_load((RACINE / ".github" / "workflows" / nom).read_text(encoding="utf-8"))


def test_les_parcours_e2e_sont_appelables():
    declencheurs = _workflow("tests-e2e.yml")[True] if True in _workflow("tests-e2e.yml") else _workflow("tests-e2e.yml")["on"]
    assert "workflow_call" in declencheurs


def test_la_construction_de_release_attend_les_parcours_e2e():
    jobs = _workflow("release.yml")["jobs"]
    assert jobs["e2e"]["uses"].endswith("tests-e2e.yml")
    assert "e2e" in jobs["build"]["needs"]
