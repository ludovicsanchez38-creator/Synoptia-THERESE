"""B-797 (cycle 9) : la conversion `int(cell)` du repli Markdown mangeait le zéro
initial d'un code postal (« 04100 » devenait 4100)."""
from __future__ import annotations

from app.services.skills.xlsx_generator import XlsxSkill

TABLEAU = """| Ville | Code postal | Effectif |
|---|---|---|
| Manosque | 04100 | 12 |
| Digne | 04000 | 7 |
"""


def test_un_nombre_a_zero_initial_reste_un_texte(tmp_path) -> None:
    skill = XlsxSkill(tmp_path)
    tables = skill._parse_markdown_tables(TABLEAU)
    assert tables, "aucun tableau reconnu"
    lignes = tables[0]["rows"]
    assert lignes[0][1] == "04100"
    assert lignes[1][1] == "04000"
    assert lignes[0][2] == 12
