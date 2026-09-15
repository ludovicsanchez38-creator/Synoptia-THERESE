"""B-851 (cycle 9) : `VariableResponse.updated_at` partait sans fuseau.

`_to_response` sérialisait `variable.updated_at.isoformat()` : un instant relu
de SQLite est naïf, la chaîne partait donc sans « Z » ni décalage et le
navigateur la lisait comme une heure locale (défaut B-216, déjà corrigé
ailleurs par l'alias `HorodatageUTC`).
"""

from __future__ import annotations

from datetime import datetime

from app.models.entities import Variable
from app.routers.variables import _to_response


def test_updated_at_porte_son_fuseau_en_json() -> None:
    relue_de_sqlite = Variable(
        name="ville",
        kind="text",
        value='"Manosque"',
        updated_at=datetime(2026, 9, 15, 10, 0, 0),  # naïf, comme relu de la base
    )
    charge = _to_response(relue_de_sqlite).model_dump(mode="json")
    assert charge["updated_at"].endswith(("Z", "+00:00")), charge["updated_at"]
    assert charge["updated_at"].startswith("2026-09-15T10:00:00")
