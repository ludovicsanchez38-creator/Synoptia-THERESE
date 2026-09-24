"""B-1120 : une seule règle de formule, à l'import comme à l'export.

L'import (SEC-017) désamorçait tout ce qui commence par « + » ou « - » :
« +33 6 12 34 56 78 » était enregistré « '+33 6 12 34 56 78 », et un budget
« -500 » devenait illisible, donc effacé. L'export (B-449) laissait passer
« +1+cmd|' /C calc'!A0 », parce qu'un chiffre suit le « + ». Règle arbitrée le
24/09 (docs/plans/2026-09-24-arbitrages-par-delegation.md) : « = », « @ »,
tabulation et retour chariot en tête sont désamorcés ; « + » et « - » ne le
sont que si la suite n'a pas la forme d'un nombre ou d'un téléphone.
"""

import pytest
from app.services.crm_export import _neutraliser_formule
from app.services.crm_import import _sanitize_field
from app.services.crm_utils import parse_budget

INTACTS = [
    "+33 6 12 34 56 78",
    "+33 (0)6 12 34 56 78",
    "-500",
    "-12.5",
    "+1 555-0100",
    "06/12/2026",
    "Bonjour",
]

FORMULES = [
    "=1+1",
    "@SUM(1+1)",
    "+1+cmd|' /C calc'!A0",
    "-2+3+cmd|' /C calc'!A0",
    "+A1",
    "-SUM(1)",
    "+33 6 12 34 56 78+cmd|' /C calc'!A0",
]


@pytest.mark.parametrize("valeur", INTACTS)
def test_import_ne_touche_pas_un_nombre_ou_un_telephone(valeur: str) -> None:
    assert _sanitize_field(valeur, "phone") == valeur


@pytest.mark.parametrize("valeur", INTACTS)
def test_export_ne_touche_pas_un_nombre_ou_un_telephone(valeur: str) -> None:
    assert _neutraliser_formule(valeur) == valeur


@pytest.mark.parametrize("valeur", FORMULES)
def test_import_desamorce_une_formule(valeur: str) -> None:
    assert _sanitize_field(valeur, "notes") == "'" + valeur


@pytest.mark.parametrize("valeur", [*FORMULES, "\t=1+1", "\r=1+1"])
def test_export_desamorce_une_formule(valeur: str) -> None:
    assert _neutraliser_formule(valeur) == "'" + valeur


def test_un_budget_negatif_importe_reste_un_nombre() -> None:
    assert parse_budget(_sanitize_field("-500", "budget")) == -500.0
