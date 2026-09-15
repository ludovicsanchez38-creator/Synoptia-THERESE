"""B-824 (cycle 9) : `tempfile.mktemp` ne réserve pas le nom (course), le
générateur d'outils l'utilisait deux fois."""
from __future__ import annotations

from pathlib import Path

import app.services.skills.tool_installer as module


def test_plus_aucun_mktemp_dans_le_generateur() -> None:
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "tempfile.mktemp(" not in source
    assert source.count("NamedTemporaryFile(") == 2
