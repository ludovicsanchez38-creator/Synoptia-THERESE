"""Gardes statiques de la passe 7 ; seul le cliquet global exécute mypy."""

import ast
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]


def _arbre(fichier):
    return ast.parse((RACINE / fichier).read_text(encoding="utf-8"))


def _fonction(fichier, nom):
    return next(
        noeud for noeud in ast.walk(_arbre(fichier))
        if isinstance(noeud, (ast.FunctionDef, ast.AsyncFunctionDef)) and noeud.name == nom
    )


def test_reponse_mission_annote_le_contrat_asgi():
    fonction = _fonction("src/backend/app/routers/agents.py", "__call__")
    annotations = {
        argument.arg: ast.unparse(argument.annotation) if argument.annotation else None
        for argument in fonction.args.args if argument.arg != "self"
    }
    assert annotations == {"scope": "Scope", "receive": "Receive", "send": "Send"}
    assert fonction.returns is not None and ast.unparse(fonction.returns) == "None"


def test_signalement_crm_type_les_cles_et_valeurs_des_dictionnaires():
    fonction = _fonction("src/backend/app/routers/crm.py", "_signaler_ligne_invalide")
    annotations = {
        argument.arg: ast.unparse(argument.annotation)
        for argument in fonction.args.args if argument.arg in {"stats", "row"}
    }
    assert annotations == {"stats": "dict[str, Any]", "row": "dict[str, Any]"}


@pytest.mark.parametrize(("fichier", "nom", "type_attendu"), [
    ("src/backend/app/routers/data.py", "_valeur_de_preference_exportable", "str"),
    ("src/backend/app/services/rgpd_auto.py", "purge_contact_vector", "int"),
])
def test_retour_externe_passe_par_une_valeur_annotee(fichier, nom, type_attendu):
    fonction = _fonction(fichier, nom)
    valeurs_typees = {
        noeud.target.id for noeud in ast.walk(fonction)
        if isinstance(noeud, ast.AnnAssign) and isinstance(noeud.target, ast.Name)
        and ast.unparse(noeud.annotation) == type_attendu and noeud.value is not None
    }
    assert any(
        isinstance(noeud, ast.Return) and isinstance(noeud.value, ast.Name)
        and noeud.value.id in valeurs_typees
        for noeud in ast.walk(fonction)
    ), f"{nom} retourne une valeur externe sans annotation {type_attendu}"


def test_cache_agenda_ecarte_none_par_une_vraie_branche():
    fonction = _fonction("src/backend/app/routers/calendar.py", "_evenement_en_cache")
    resolution = next(noeud for noeud in fonction.body if isinstance(noeud, ast.If))
    garde = next(noeud for noeud in resolution.body if isinstance(noeud, ast.If))
    assert any(
        isinstance(noeud, ast.Compare) and isinstance(noeud.left, ast.Name)
        and noeud.left.id == "calendrier" and len(noeud.ops) == 1
        and isinstance(noeud.ops[0], ast.Is)
        and isinstance(noeud.comparators[0], ast.Constant)
        and noeud.comparators[0].value is None
        for noeud in ast.walk(garde.test)
    ), "Le cache doit écarter explicitement le calendrier None avant de lire provider"
    assert any(
        isinstance(noeud, ast.Return) and isinstance(noeud.value, ast.Constant)
        and noeud.value.value is None for noeud in garde.body
    )


def test_regressions_export_ne_relancent_pas_mypy():
    arbre = _arbre("tests/test_c20_r6_export_config.py")
    imports = []
    for noeud in ast.walk(arbre):
        if isinstance(noeud, ast.ImportFrom):
            imports.append(noeud.module or "")
        elif isinstance(noeud, ast.Import):
            imports.extend(alias.name for alias in noeud.names)
    imports_mypy = [nom for nom in imports if nom == "mypy" or nom.startswith("mypy.")]
    assert not imports_mypy, f"Un test d'export relance mypy : {imports_mypy}"
