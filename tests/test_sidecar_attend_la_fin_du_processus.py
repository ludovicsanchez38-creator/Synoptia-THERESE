"""Revue COCO 0.67 (05/09/2026) : à la fermeture, Uvicorn lâche son port AVANT
d'exécuter le nettoyage du lifespan (MCP, bases, synchronisations). B-448
arrêtait l'attente dès que le port n'écoutait plus, puis tuait le sidecar :
sur le build Linux onedir, le backend pouvait être interrompu en plein
nettoyage. Le sidecar doit être attendu jusqu'à sa vraie fin, dans le même
budget de cinq secondes.

Le code est en Rust : la garde lit la source, comme test_regression le fait
déjà pour lib.rs, et vérifie l'ordre des étapes.
"""

from __future__ import annotations

import re
from pathlib import Path

LIB_RS = Path(__file__).resolve().parents[1] / "src" / "frontend" / "src-tauri" / "src" / "lib.rs"


def _source() -> str:
    return LIB_RS.read_text(encoding="utf-8")


def test_le_drapeau_de_fin_existe_et_passe_a_vrai_a_la_terminaison():
    source = _source()
    assert "sidecar_termine: std::sync::atomic::AtomicBool" in source, "le drapeau de fin de processus manque à SidecarState"
    terminaison = source[source.index("CommandEvent::Terminated(payload)") :]
    terminaison = terminaison[: terminaison.index("handle_sidecar_termination(")]
    assert ".sidecar_termine" in terminaison and ".store(true" in terminaison, (
        "la branche Terminated ne lève pas le drapeau de fin"
    )


def test_le_kill_attend_la_vraie_fin_du_processus_dans_le_budget_de_cinq_secondes():
    source = _source()
    debut = source.index("while backend_ecoute_encore(port)")
    kill = source.index("let _ = child.kill();", debut)
    entre = source[debut:kill]
    assert re.search(r"while !state\s*\.sidecar_termine\s*\.load\(", entre), (
        "le port lâché ne suffit pas : il faut attendre la fin du processus avant child.kill()"
    )
    assert entre.count("Duration::from_secs(5)") == 2, "les deux attentes partagent le même budget de cinq secondes"


def test_le_drapeau_est_remis_a_faux_a_chaque_lancement_du_sidecar():
    source = _source()
    spawn = source[source.index("pub(crate) fn spawn_backend_sidecar(") :]
    spawn = spawn[: spawn.index("CommandEvent::Terminated(payload)")]
    assert re.search(r"sidecar_termine\s*\.store\(false", spawn), (
        "une relance du sidecar hériterait d'un drapeau déjà à vrai et serait tuée sans attente"
    )
