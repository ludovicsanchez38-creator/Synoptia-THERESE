"""B-1167 : les compteurs et plafonds suivent le jour et le mois de Paris."""

import json
from datetime import UTC, datetime

import pytest
from app.services import token_tracker as module
from app.services.civil_time import PARIS


@pytest.fixture
def suivi(monkeypatch, tmp_path):
    horloge = [datetime(2026, 10, 23, 23, 30, tzinfo=PARIS)]

    class Horloge(datetime):
        @classmethod
        def now(cls, tz=None):
            return horloge[0].astimezone(tz) if tz else horloge[0].replace(tzinfo=None)

    monkeypatch.setattr(module, "datetime", Horloge)
    monkeypatch.setattr(module.TokenTracker, "_instance", None)
    fichier = tmp_path / "usage.json"
    monkeypatch.setattr(module.TokenTracker, "_fichier_usage", staticmethod(lambda: fichier))
    return horloge, fichier


def creer_suivi():
    tracker = module.TokenTracker()
    tracker.set_limits(module.TokenLimits())
    return tracker


def consommer(tracker, entree=1000, sortie=500):
    return tracker.record_usage("locale", "mistral-small-2603", "simulé", entree, sortie)


def verifier_bascule(suivi, avant, apres, *, mensuel=False):
    horloge, fichier = suivi
    horloge[0] = datetime.fromisoformat(avant).replace(tzinfo=PARIS)
    tracker = creer_suivi()
    usage = consommer(tracker)
    tracker.set_limits(module.TokenLimits(
        daily_input_limit=100_000 if mensuel else 1000,
        monthly_budget_eur=usage.cost_eur if mensuel else 100,
    ))
    assert tracker.check_limits(1)["allowed"] is False
    horloge[0] = datetime.fromisoformat(apres).replace(tzinfo=PARIS)
    verdict = tracker.check_limits(1)
    assert verdict["allowed"] is True, verdict
    jour = tracker.get_daily_usage()
    assert jour["date"] == apres[:10]
    assert jour["total_tokens"] == 0
    mois = tracker.get_monthly_usage()
    assert mois["month"] == apres[:7]
    assert mois["input_tokens"] == (0 if mensuel else 1000)
    record = consommer(tracker, 20, 10)
    assert record.timestamp == horloge[0].astimezone(UTC)
    charge = json.loads(fichier.read_text())
    assert charge["today_date"] == apres[:10]
    assert charge["current_month"] == apres[:7]
    assert charge["today_input"] == 20
    # Redémarrage réel du singleton : les nouveaux compteurs sont persistés.
    module.TokenTracker._instance = None
    relu = creer_suivi()
    assert relu.get_daily_usage()["total_tokens"] == 30
    assert relu.get_monthly_usage()["input_tokens"] == (20 if mensuel else 1020)


@pytest.mark.parametrize("avant,apres,mensuel", [
    ("2026-10-23T23:30", "2026-10-24T00:30", False),
    ("2026-10-31T23:30", "2026-11-01T00:30", True),
])
def test_minuit_paris_debloque_les_plafonds(suivi, avant, apres, mensuel):
    verifier_bascule(suivi, avant, apres, mensuel=mensuel)


def test_demarrage_a_minuit_charge_le_jour_et_le_mois_de_paris(suivi):
    horloge, fichier = suivi
    horloge[0] = datetime(2026, 11, 1, 0, 30, tzinfo=PARIS)
    fichier.write_text(json.dumps({
        "today_date": "2026-11-01", "today_input": 321, "today_output": 123,
        "current_month": "2026-11", "month_input": 321, "month_output": 123,
    }))
    tracker = creer_suivi()
    assert tracker.get_daily_usage()["total_tokens"] == 444
    assert tracker.get_monthly_usage()["total_tokens"] == 444


@pytest.mark.parametrize("avant,apres,mensuel", [
    ("2026-01-14T23:59", "2026-01-15T00:00", False),
    ("2026-08-14T23:59", "2026-08-15T00:00", False),
    ("2026-03-28T23:59", "2026-03-29T00:01", False),
    ("2026-03-29T23:59", "2026-03-30T00:01", False),
    ("2026-10-24T23:59", "2026-10-25T00:01", False),
    ("2026-10-25T23:59", "2026-10-26T00:01", False),
    ("2026-12-31T23:59", "2027-01-01T00:01", True),
])
def test_sept_rejeux_bascule_apres_astra(suivi, avant, apres, mensuel):
    verifier_bascule(suivi, avant, apres, mensuel=mensuel)


@pytest.mark.parametrize("avant,apres", [
    ("2026-01-15T00:30+01:00", "2026-01-15T01:30+01:00"),
    ("2026-08-15T00:30+02:00", "2026-08-15T02:30+02:00"),
    ("2026-10-25T02:30+02:00", "2026-10-25T02:30+01:00"),
])
def test_trois_rejeux_sans_double_remise_a_zero(suivi, avant, apres):
    horloge, _ = suivi
    horloge[0] = datetime.fromisoformat(avant)
    tracker = creer_suivi()
    consommer(tracker)
    tracker.set_limits(module.TokenLimits(daily_input_limit=1000))
    horloge[0] = datetime.fromisoformat(apres)
    assert tracker.check_limits(1)["allowed"] is False
    assert tracker.get_daily_usage()["total_tokens"] == 1500
    module.TokenTracker._instance = None
    assert creer_suivi().get_daily_usage()["total_tokens"] == 1500
