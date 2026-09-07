"""Sentinelles STRUCTURELLES : ce que cette suite ne peut pas exécuter (B-039, B-332).

Le point d'entrée PyInstaller (`src/backend/main.py`), le spec PyInstaller, la
coque Rust (`lib.rs`) et la configuration Tauri ne tournent pas dans pytest.
Les gardes ci-dessous lisent leur STRUCTURE (arbre syntaxique Python, JSON
parsé, jetons du source Rust), jamais des sous-chaînes libres : un
reformatage, un renommage de variable ou un commentaire ne les trompent pas.

Ce qu'elles prouvent : que la structure attendue est en place. Ce qu'elles ne
prouvent pas : le comportement à l'exécution, qui relève de la recette dans
l'application packagée. Les anciens tests textuels de `test_regression.py`
(BUG-002, 003, 005, 007, 008, 009, 013, 017, 020, 042, 069, 110, port fixe)
sont remplacés ici.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
BACKEND = RACINE / "src" / "backend"
MAIN_PY = BACKEND / "main.py"
APP_MAIN_PY = BACKEND / "app" / "main.py"
SPEC = BACKEND / "backend.spec"
LIB_RS = RACINE / "src" / "frontend" / "src-tauri" / "src" / "lib.rs"
TAURI_CONF = RACINE / "src" / "frontend" / "src-tauri" / "tauri.conf.json"


def _arbre(chemin: Path) -> ast.Module:
    return ast.parse(chemin.read_text(encoding="utf-8"), filename=str(chemin))


def _appels(arbre: ast.AST, attribut: str) -> list[ast.Call]:
    return [
        n for n in ast.walk(arbre)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == attribut
    ]


def _fonction(arbre: ast.AST, nom: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for n in ast.walk(arbre):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == nom:
            return n
    pytest.fail(f"fonction {nom} introuvable")


def _mot_cle(appel: ast.Call, nom: str):
    for kw in appel.keywords:
        if kw.arg == nom:
            return kw.value
    return None


# ---------------------------------------------------------------- point d'entrée


class TestPointDEntree:
    def test_le_port_et_l_hote_sont_des_arguments_avec_17293_par_defaut(self):
        options = {}
        for appel in _appels(_arbre(MAIN_PY), "add_argument"):
            if appel.args and isinstance(appel.args[0], ast.Constant):
                defaut = _mot_cle(appel, "default")
                options[appel.args[0].value] = defaut.value if isinstance(defaut, ast.Constant) else None
        assert "--host" in options
        assert options.get("--port") == 17293, options

    def test_freeze_support_precede_l_import_de_l_application(self):
        arbre = _arbre(MAIN_PY)
        freeze = [n.lineno for n in _appels(arbre, "freeze_support")]
        imports = [
            n.lineno for n in ast.walk(arbre)
            if isinstance(n, ast.ImportFrom) and n.module == "app.main"
        ]
        assert freeze and imports, (freeze, imports)
        assert min(freeze) < min(imports), "freeze_support() doit précéder l'import de l'application (BUG-008)"

    def test_le_tueur_de_zombies_nettoie_le_verrou_qdrant(self):
        fonction = _fonction(_arbre(MAIN_PY), "_kill_zombie_backends")
        constantes = {n.value for n in ast.walk(fonction) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        assert ".lock" in constantes, "le verrou Qdrant doit être visé"
        assert _appels(fonction, "unlink"), "le verrou doit être supprimé (BUG-003)"

    def test_le_prechargement_des_embeddings_ne_bloque_pas_le_demarrage(self):
        arbre = _arbre(APP_MAIN_PY)
        dans_create_task = False
        for appel in _appels(arbre, "create_task"):
            for enfant in ast.walk(appel):
                if isinstance(enfant, ast.Name) and "preload_embedding" in enfant.id:
                    dans_create_task = True
        assert dans_create_task, "preload_embedding_model doit partir en tâche de fond (BUG-020)"
        # Dans le corps DIRECT du lifespan (sans descendre dans les fonctions
        # internes, qui sont précisément les tâches de fond), aucun await du préchargement.
        lifespan = _fonction(arbre, "lifespan")

        def _awaits_directs(noeud):
            for enfant in ast.iter_child_nodes(noeud):
                if isinstance(enfant, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                    continue
                if isinstance(enfant, ast.Await):
                    yield enfant
                yield from _awaits_directs(enfant)

        for attente in _awaits_directs(lifespan):
            for enfant in ast.walk(attente.value):
                if isinstance(enfant, ast.Name) and "preload_embedding" in enfant.id:
                    pytest.fail("preload_embedding_model est attendu directement dans le lifespan : le serveur HTTP ne répondrait qu'après")

    def test_le_profil_precharge_au_demarrage_ne_touche_pas_au_trousseau(self):
        arbre = _arbre(APP_MAIN_PY)
        appels = [a for a in ast.walk(arbre) if isinstance(a, ast.Call) and _mot_cle(a, "allow_decrypt") is not None]
        assert appels, "le préchargement du profil doit passer allow_decrypt (BUG-013)"
        assert all(_mot_cle(a, "allow_decrypt").value is False for a in appels), (
            "au démarrage, allow_decrypt doit valoir False pour ne pas ouvrir le Keychain"
        )


class TestSpecPyInstaller:
    def test_ni_strip_ni_upx_sur_les_binaires(self):
        arbre = _arbre(SPEC)
        appels = [a for a in ast.walk(arbre) if isinstance(a, ast.Call) and (_mot_cle(a, "strip") is not None or _mot_cle(a, "upx") is not None)]
        assert appels, "le spec doit régler strip/upx explicitement (BUG-005)"
        for a in appels:
            for nom in ("strip", "upx"):
                valeur = _mot_cle(a, nom)
                if isinstance(valeur, ast.Constant):
                    assert valeur.value is False, f"{nom} doit rester à False (DLL Windows, .so Linux)"
                # Une expression (condition sur la plateforme) est acceptée : elle
                # dit explicitement où strip est permis.


class TestGardesDeCode:
    @pytest.mark.parametrize("module", ["openrouter.py", "anthropic.py", "ollama.py"])
    def test_aucun_except_imbrique_ne_masque_la_variable_d_erreur(self, module):
        arbre = _arbre(BACKEND / "app" / "services" / "providers" / module)
        for gestionnaire in ast.walk(arbre):
            if not isinstance(gestionnaire, ast.ExceptHandler) or not gestionnaire.name:
                continue
            for interne in ast.walk(gestionnaire):
                if interne is not gestionnaire and isinstance(interne, ast.ExceptHandler) and interne.name == gestionnaire.name:
                    pytest.fail(f"{module}:{interne.lineno} réutilise `{interne.name}` dans un except imbriqué (BUG-069)")

    def test_les_skills_fichier_disposent_d_au_moins_16384_jetons(self):
        arbre = _arbre(BACKEND / "app" / "routers" / "skills.py")
        valeurs = [
            n.value for n in ast.walk(arbre)
            if isinstance(n, ast.Constant) and isinstance(n.value, int) and n.value >= 16384
        ]
        assert valeurs, "le plafond de sortie des skills fichier doit atteindre 16384 jetons (BUG-042)"


# ---------------------------------------------------------------- coque Rust et Tauri


class TestCoqueRust:
    """Le source Rust n'est pas analysable ici : on lit ses jetons de chaîne."""

    @pytest.fixture(scope="class")
    def rust(self):
        return LIB_RS.read_text(encoding="utf-8")

    def test_le_port_est_fixe(self, rust):
        assert "17293" in rust
        assert "find_free_port" not in rust and "TcpListener::bind" not in rust

    def test_le_repli_tasklist_vient_apres_wmic(self, rust):
        wmic, tasklist = rust.find('"wmic"'), rust.find('"tasklist"')
        assert 0 < wmic < tasklist, "tasklist est le repli de wmic (Windows 11 25H2+, BUG-009)"
        assert re.search(r"from_secs\((2|3)\)", rust), "attendre après taskkill pour libérer les handles"

    def test_le_dossier_temporaire_est_redirige_pour_le_sidecar(self, rust):
        for variable in ('"TMPDIR"', '"TEMP"', '"TMP"'):
            assert variable in rust, f"{variable} doit être redirigé vers le dossier runtime (BUG-017)"
        assert "create_dir_all" in rust


class TestConfigurationTauri:
    def test_la_mise_a_jour_windows_est_en_mode_passive(self):
        conf = json.loads(TAURI_CONF.read_text(encoding="utf-8"))
        updater = conf["plugins"]["updater"]
        assert updater["windows"]["installMode"] == "passive", "quiet échoue en silence sans droits admin (BUG-110)"
        assert updater["endpoints"], "un point de publication doit être déclaré"
        assert updater.get("pubkey"), "la clé de signature doit être embarquée"
