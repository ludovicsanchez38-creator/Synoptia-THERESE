"""Tests du module execution_truth (Chantier A - vérité d'exécution).

Deux helpers purs et testables :
- enforce_create_cap : plafonne le nombre de créations d'entités par tour (anti rafale).
- summarize_executions : résumé DÉTERMINISTE de ce qui a réellement été créé/réutilisé/échoué.
"""

import json
from types import SimpleNamespace

from app.services.execution_truth import enforce_create_cap, summarize_executions


def tc(name: str):
    return SimpleNamespace(name=name, id=name, arguments={})


class TestEnforceCreateCap:
    def test_under_cap_all_allowed(self):
        calls = [tc("create_contact"), tc("create_project")]
        allowed, blocked = enforce_create_cap(calls, max_creates=10)
        assert len(allowed) == 2
        assert blocked == []

    def test_over_cap_excess_blocked(self):
        calls = [tc("create_project") for _ in range(15)]
        allowed, blocked = enforce_create_cap(calls, max_creates=10)
        assert len(allowed) == 10
        assert len(blocked) == 5

    def test_non_create_tools_never_blocked(self):
        # 12 créations + 2 outils non-créateurs : seuls les créations en excès sont bloquées
        calls = [tc("create_contact") for _ in range(12)] + [tc("web_search"), tc("read_calendar")]
        allowed, blocked = enforce_create_cap(calls, max_creates=10)
        assert sum(1 for c in allowed if c.name in ("create_contact", "create_project")) == 10
        assert all(c.name == "create_contact" for c in blocked)
        assert {c.name for c in allowed} >= {"web_search", "read_calendar"}


class TestSummarizeExecutions:
    def _ok_contact(self, reused=False):
        return ("create_contact", json.dumps({"success": True, "contact_id": "c1", "already_existed": reused}), False)

    def _ok_project(self, reused=False):
        return ("create_project", json.dumps({"success": True, "project_id": "p1", "already_existed": reused}), False)

    def _failed_contact(self):
        return ("create_contact", json.dumps({"error": "boom"}), False)

    def test_no_create_returns_none(self):
        results = [("web_search", "des résultats", False)]
        assert summarize_executions(results) is None

    def test_counts_created(self):
        results = [self._ok_contact(), self._ok_contact(), self._ok_project()]
        s = summarize_executions(results)
        assert "2 contact" in s and "1 projet" in s
        assert "créé" in s

    def test_counts_reused_and_failures(self):
        results = [self._ok_contact(reused=True), self._failed_contact()]
        s = summarize_executions(results)
        assert "déjà existant" in s
        assert "échec" in s

    def test_error_flag_counts_as_failure(self):
        results = [("create_project", "Error: db down", True)]
        s = summarize_executions(results)
        assert "échec" in s
