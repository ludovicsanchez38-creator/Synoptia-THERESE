"""P-045 : le prédicat frontend (lib/effortOpenAI.ts) et le backend
(_uses_max_completion_tokens) partagent les mêmes témoins ; la liste des
modèles qui reçoivent l'effort sans outils suit le catalogue."""

from __future__ import annotations

import json
from pathlib import Path

TEMOINS = Path(__file__).resolve().parents[1] / "src/frontend/src/lib/effortOpenAI.temoins.json"


def test_les_temoins_partages_suivent_le_predicat_backend():
    from app.services.providers.openai import _uses_max_completion_tokens

    donnees = json.loads(TEMOINS.read_text(encoding="utf-8"))
    for modele, attendu in donnees["temoins"].items():
        assert _uses_max_completion_tokens(modele) is attendu, modele


def test_l_effort_sans_outils_n_est_transmis_qu_aux_modeles_du_catalogue():
    from app.services.modeles_catalogue import resoudre_effort

    donnees = json.loads(TEMOINS.read_text(encoding="utf-8"))
    for modele in donnees["effort_transmis_sans_outils"]:
        assert resoudre_effort(modele, "high", "openai") == "high", modele
    assert resoudre_effort("gpt-5.5", "high", "openai") is None
