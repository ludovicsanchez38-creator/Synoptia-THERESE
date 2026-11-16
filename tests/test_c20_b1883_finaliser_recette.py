"""La clôture R6 conserve l'échec de chacune de ses étapes, hors réseau."""

import json
import runpy
import shutil
from pathlib import Path
from unittest.mock import Mock

import pytest


@pytest.mark.parametrize(
    ("portes", "comparaison", "attendu"), [(1, 0, 1), (0, 1, 1), (1, 1, 1), (0, 0, 0)]
)
def test_finalisation_conserve_echec_portes(tmp_path, monkeypatch, portes, comparaison, attendu):
    source = Path(__file__).resolve().parents[1] / "scripts/finaliser_recette_r6.py"
    script = tmp_path / "scripts" / source.name
    script.parent.mkdir()
    shutil.copyfile(source, script)
    logs = tmp_path / ".recette-r6/logs"
    logs.mkdir(parents=True)
    (logs / "avant-codes.json").write_text(json.dumps(dict.fromkeys(range(7), 0)))
    appeler = Mock(side_effect=[portes, comparaison])
    monkeypatch.setattr("subprocess.call", appeler)

    with pytest.raises(SystemExit) as fin:
        runpy.run_path(str(script), run_name="__main__")

    assert appeler.call_count == 2
    assert Path(appeler.call_args_list[0].args[0][1]).name == "portes_r6.py"
    assert Path(appeler.call_args_list[1].args[0][1]).name == "comparer_portes_r6.py"
    assert fin.value.code == attendu
