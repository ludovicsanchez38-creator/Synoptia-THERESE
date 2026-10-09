"""Gemini 3.8 Flash passe à 1,50 / 7,50 le 1er janvier 2027.

La grille officielle date ce couple. TOKEN_PRICES garde 0,75 / 3,75,
le tarif d'avant. Le calcul, budget compris, lit le jour.
"""

from __future__ import annotations

from datetime import date, datetime

import pytest
from app.services.token_tracker import TOKEN_PRICES, TokenLimits, TokenTracker


def _figer_le_jour(monkeypatch: pytest.MonkeyPatch, jour: date) -> None:
    class _Horloge(datetime):
        @classmethod
        def now(cls, tz=None):  # noqa: ANN001
            return datetime(jour.year, jour.month, jour.day, tzinfo=tz)

    monkeypatch.setattr("app.services.token_tracker.datetime", _Horloge)


def _traceur() -> TokenTracker:
    traceur = object.__new__(TokenTracker)
    traceur._initialized = False
    traceur.__init__()
    return traceur


class TestBasculeGemini38:
    def test_le_31_decembre_2026_reste_au_couple_court(self, monkeypatch):
        _figer_le_jour(monkeypatch, date(2026, 12, 31))
        cout = _traceur().estimate_cost("gemini-3.8-flash", 1_000_000, 1_000_000)
        assert cout == pytest.approx(0.75 + 3.75)

    def test_le_1er_janvier_2027_passe_a_150_et_750(self, monkeypatch):
        _figer_le_jour(monkeypatch, date(2027, 1, 1))
        cout = _traceur().estimate_cost("gemini-3.8-flash", 1_000_000, 1_000_000)
        assert cout == pytest.approx(1.50 + 7.50)

    def test_le_budget_refuse_le_nouveau_couple_des_le_1er_janvier(self, monkeypatch):
        """Un million de jetons d'entrée : 0,75 tient sous 1 USD, 1,50 non."""
        traceur = _traceur()
        traceur.set_limits(TokenLimits(
            max_input_tokens=10_000_000,
            max_output_tokens=10_000_000,
            daily_input_limit=100_000_000,
            daily_output_limit=100_000_000,
            monthly_budget_eur=1.0,
            warn_at_percentage=100,
        ))
        traceur._month_cost = 0.0
        _figer_le_jour(monkeypatch, date(2026, 12, 31))
        assert traceur.check_limits(
            1_000_000, 0, model="gemini-3.8-flash",
        )["allowed"] is True
        _figer_le_jour(monkeypatch, date(2027, 1, 1))
        verdict = traceur.check_limits(1_000_000, 0, model="gemini-3.8-flash")
        assert verdict["allowed"] is False
        assert any("Budget mensuel" in erreur for erreur in verdict["errors"])

    def test_la_bascule_est_datee_et_cite_la_grille(self):
        from app.services import token_tracker as module

        bascules = getattr(module, "BASCULES_TARIF", None)
        assert bascules is not None
        bascule = bascules["gemini-3.8-flash"]
        assert bascule.debut == date(2027, 1, 1)
        assert bascule.entree == 1.50
        assert bascule.sortie == 7.50
        assert "ai.google.dev/gemini-api/docs/pricing" in bascule.source
        assert TOKEN_PRICES["gemini-3.8-flash"] == {"input": 0.75, "output": 3.75}


class TestBasculeGemini37:
    """La grille officielle date le même couple pour Gemini 3.7 Flash.

    0,75 / 3,75 jusqu'au 31 décembre 2026, 1,50 / 7,50 dès le 1er janvier 2027.
    Source : https://ai.google.dev/gemini-api/docs/pricing
    """

    def test_le_31_decembre_2026_reste_au_couple_court(self, monkeypatch):
        _figer_le_jour(monkeypatch, date(2026, 12, 31))
        cout = _traceur().estimate_cost("gemini-3.7-flash", 1_000_000, 1_000_000)
        assert cout == pytest.approx(0.75 + 3.75)

    def test_le_1er_janvier_2027_passe_a_150_et_750(self, monkeypatch):
        _figer_le_jour(monkeypatch, date(2027, 1, 1))
        cout = _traceur().estimate_cost("gemini-3.7-flash", 1_000_000, 1_000_000)
        assert cout == pytest.approx(1.50 + 7.50)
