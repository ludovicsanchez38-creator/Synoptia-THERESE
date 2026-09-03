"""B-298 : les montants rendus par les calculateurs sont écrits en français.

Le service rendait « 1,234.50€ » (virgule des milliers, point décimal, euro
collé) et ce texte est affiché tel quel dans la carte de résultat, juste sous
des montants que le frontend, lui, formate avec
`Intl.NumberFormat('fr-FR', {style:'currency', currency:'EUR'})`. La même carte
disait donc deux fois le même montant de deux façons.

Référence de forme : la sortie exacte de cet `Intl` (mesurée sous Node),
soit l'espace insécable étroite U+202F pour les milliers, la virgule décimale,
et l'espace insécable U+00A0 devant le symbole.

Les cinq sites de montant du service sont couverts : ROI négatif, NPV positive,
NPV négative, CA minimum et marge unitaire du seuil de rentabilité.
"""

import re

import pytest
from app.services.calculators import CalculatorService

MILLIERS = "\u202f"  # espace insécable étroite (U+202F)
AVANT_SYMBOLE = "\u00a0"  # espace insécable (U+00A0)

# Ce que rend Intl.NumberFormat('fr-FR', {style:'currency', currency:'EUR'})
# côté frontend, pour les mêmes valeurs.
REFERENCE_FRONTEND = {
    1234.5: f"1{MILLIERS}234,50{AVANT_SYMBOLE}€",
    -1234.5: f"-1{MILLIERS}234,50{AVANT_SYMBOLE}€",
    61700.0: f"61{MILLIERS}700,00{AVANT_SYMBOLE}€",
    30.0: f"30,00{AVANT_SYMBOLE}€",
    2000.0: f"2{MILLIERS}000,00{AVANT_SYMBOLE}€",
}

_MILLIERS_ANGLAIS = re.compile(r"\d,\d{3}")
_EURO_COLLE = re.compile(r"\d€")


def _sans_forme_anglaise(texte: str) -> list[str]:
    """Les fautes de forme restantes, nommées plutôt que comptées."""
    fautes = []
    if _MILLIERS_ANGLAIS.search(texte):
        fautes.append(f"séparateur de milliers anglais dans « {texte} »")
    if _EURO_COLLE.search(texte):
        fautes.append(f"euro collé au nombre dans « {texte} »")
    return fautes


@pytest.fixture
def service() -> CalculatorService:
    return CalculatorService()


class TestMontantsAuFormatFrancais:
    def test_montants_au_format_francais_roi_negatif(self, service):
        interpretation = service.calculate_roi(investment=10000, gain=8000).interpretation

        assert REFERENCE_FRONTEND[2000.0] in interpretation
        assert _sans_forme_anglaise(interpretation) == []

    def test_montants_au_format_francais_npv_positive(self, service):
        interpretation = service.calculate_npv(
            initial_investment=0, cash_flows=[1234.5], discount_rate=0.0
        ).interpretation

        assert REFERENCE_FRONTEND[1234.5] in interpretation
        assert _sans_forme_anglaise(interpretation) == []

    def test_montants_au_format_francais_npv_negative(self, service):
        interpretation = service.calculate_npv(
            initial_investment=1234.5, cash_flows=[0.0], discount_rate=0.0
        ).interpretation

        assert REFERENCE_FRONTEND[-1234.5] in interpretation
        assert _sans_forme_anglaise(interpretation) == []

    def test_montants_au_format_francais_seuil_de_rentabilite(self, service):
        interpretation = service.calculate_break_even(
            fixed_costs=37020, variable_cost_per_unit=20, price_per_unit=50
        ).interpretation

        # CA minimum (avec séparateur de milliers) ET marge unitaire (sans).
        assert REFERENCE_FRONTEND[61700.0] in interpretation
        assert REFERENCE_FRONTEND[30.0] in interpretation
        assert _sans_forme_anglaise(interpretation) == []

    @pytest.mark.asyncio
    async def test_le_texte_qui_atteint_l_ecran_est_deja_francais(self, client):
        """Le formatage n'est pas rattrapé en route : la carte affiche
        `interpretation` telle que l'API la rend."""
        reponse = await client.post(
            "/api/calc/npv",
            json={
                "initial_investment": 0,
                "cash_flows": [1234.5],
                "discount_rate": 0.0,
            },
        )

        assert reponse.status_code == 200
        interpretation = reponse.json()["interpretation"]
        assert REFERENCE_FRONTEND[1234.5] in interpretation
        assert _sans_forme_anglaise(interpretation) == []


class TestLInstrumentVoitLaFormeAnglaise:
    """Sans ces deux témoins, une assertion muette rendrait tout vert."""

    def test_les_milliers_a_l_anglaise_sont_vus(self):
        assert _sans_forme_anglaise("1,234.50 €")

    def test_l_euro_colle_est_vu(self):
        assert _sans_forme_anglaise("1 234,50€")
