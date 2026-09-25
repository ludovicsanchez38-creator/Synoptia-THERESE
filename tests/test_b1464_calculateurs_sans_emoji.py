"""B-1464 (recette P-146, lot 4, O-4) : les phrases des calculateurs
mêlaient des émojis (🚀, ✅, 📊…) et des décimaux à point (« 30.0% »,
« +129900.0% ») à des montants au format français. Les interprétations
parlent français : virgule décimale, espace insécable avant « % », aucun
émoji."""

import re

import pytest
from app.services.calculators import CalculatorService

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿️]")
DECIMAL_A_POINT = re.compile(r"\d\.\d")


def _interpretations() -> list[str]:
    service = CalculatorService()
    return [
        service.calculate_roi(investment=10000, gain=8000).interpretation,
        service.calculate_roi(investment=1000, gain=3000).interpretation,
        service.calculate_roi(investment=1000, gain=500).interpretation,
        service.calculate_ice(impact=8, confidence=7, ease=6).interpretation,
        service.calculate_rice(reach=1000, impact=2, confidence=80, effort=3).interpretation,
        service.calculate_npv(initial_investment=10000, cash_flows=[4000, 4000, 4000], discount_rate=5).interpretation,
        service.calculate_break_even(fixed_costs=18510, variable_cost_per_unit=40, price_per_unit=70).interpretation,
    ]


@pytest.mark.parametrize("texte", _interpretations())
def test_une_interpretation_n_a_ni_emoji_ni_decimal_a_point(texte):
    assert not EMOJI.search(texte), texte
    assert not DECIMAL_A_POINT.search(texte), texte


def test_un_pourcentage_s_ecrit_a_la_francaise():
    texte = CalculatorService().calculate_roi(investment=1000, gain=1300).interpretation
    assert "30,0 %" in texte, texte
