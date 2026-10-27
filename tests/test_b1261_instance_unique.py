"""B-1261 : un second lancement de THÉRÈSE rend la main à la fenêtre ouverte.

Audit du cycle 13, reproduit le 27/10/2026 sur la 0.81.1 installée : un second
lancement exécutait la chasse aux moteurs « zombies », trouvait le moteur VIVANT
de la première fenêtre et le tuait ; la première relançait le sien et tuait
celui de la seconde. Mesure : 2 processus, 4 moteurs tués, 7 démarrés, relances
jusqu'à 3/3. La chasse (`pgrep -f "backend.*--host.*127.0.0.1"`) tuait en plus
toute commande qui contenait ces mots : elle a tué le shell de la reproduction.

Ce que ces gardes vérifient (le comportement est exercé par les tests Rust de
lib.rs, exécutés en CI, et par la recette sur paquet) :
- le plugin d'instance unique est déclaré, sur une branche compatible avec le
  tauri verrouillé, et enregistré EN PREMIER (exigence du plugin) ;
- la chasse ne repose plus sur un motif de ligne de commande.
"""
import re
from pathlib import Path

TAURI = Path(__file__).resolve().parents[1] / "src/frontend/src-tauri"
LIB = (TAURI / "src/lib.rs").read_text(encoding="utf-8")


def test_le_plugin_est_declare_sur_la_branche_compatible():
    cargo = (TAURI / "Cargo.toml").read_text(encoding="utf-8")
    assert re.search(r'^tauri-plugin-single-instance = "~2\.4\.\d+"$', cargo, re.M), (
        "la 2.5 exige tauri 2.12 : un « 2 » nu monterait tout le framework au prochain verrou"
    )
    verrou = (TAURI / "Cargo.lock").read_text(encoding="utf-8")
    assert re.search(r'name = "tauri-plugin-single-instance"\nversion = "2\.4\.', verrou)


def test_le_plugin_est_enregistre_en_premier():
    chaine = LIB.split("tauri::Builder::default()", 1)[1]
    premier = chaine.split(".plugin(", 1)[1]
    assert premier.lstrip().startswith("tauri_plugin_single_instance::init"), (
        "le plugin d'instance unique doit précéder tous les autres"
    )


def test_le_second_lancement_rend_la_main_a_la_fenetre():
    rappel = LIB.split("tauri_plugin_single_instance::init", 1)[1].split("}))", 1)[0]
    for geste in ("unminimize", "show", "set_focus"):
        assert f".{geste}()" in rappel


def test_la_chasse_ne_vise_plus_un_motif_de_ligne_de_commande():
    assert 'pgrep' not in LIB.split("fn kill_zombie_backends", 1)[1].split("#[cfg(windows)]", 1)[0]
    assert "fn est_moteur_therese" in LIB and "pids_moteurs_therese()" in LIB


def test_les_tests_rust_tournent_en_ci():
    ci = (Path(__file__).resolve().parents[1] / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "cargo test --lib" in ci
