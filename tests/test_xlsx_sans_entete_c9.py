"""B-825 (cycle 9) : sans en-tête, la fusion du titre visait la colonne zéro."""
from __future__ import annotations

from openpyxl import Workbook

from app.services.skills.xlsx_generator import XlsxSkill


def test_un_tableau_sans_entete_s_ecrit_sans_exception(tmp_path) -> None:
    skill = XlsxSkill(tmp_path)
    ws = Workbook().active
    skill._add_data(ws, {"title": "Vide", "headers": [], "rows": [], "formulas": {}}, "Vide")
    assert ws.cell(row=1, column=1).value == "Vide"
