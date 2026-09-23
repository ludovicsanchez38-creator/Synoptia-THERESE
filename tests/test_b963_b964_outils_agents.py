"""B-963 et B-964 (cycle 11, 23/09/2026) : relevés des lecteurs de carte n°5 et n°6.

B-963 : régression du correctif B-962. GNU grep sort en code 2 dès qu'un seul
fichier est illisible, alors que sa sortie contient les correspondances
trouvées ailleurs. Depuis B-962, search_codebase jetait ces résultats et
montrait au modèle un chemin absolu dans le message d'erreur.

B-964 : le runtime exécutait l'outil nommé par le modèle sans le comparer au
schéma remis à l'agent. Katia reçoit des outils en lecture seule et un
exécuteur sans garde de branche sur le vrai dépôt : un `write_file` émis par
son modèle (modèle local, injection) y aurait écrit.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from app.services.agents.config import AgentConfig
from app.services.agents.runtime import AgentRuntime
from app.services.agents.tools import THERESE_TOOLS, ZEZETTE_TOOLS, AgentToolExecutor

permissions_posix = pytest.mark.skipif(
    sys.platform == "win32" or (hasattr(os, "geteuid") and os.geteuid() == 0),
    reason="chmod 000 ne rend pas un fichier illisible ici",
)


@permissions_posix
async def test_b963_un_fichier_illisible_ne_fait_pas_perdre_les_resultats(tmp_path: Path):
    (tmp_path / "a.py").write_text("cible = 1\n", encoding="utf-8")
    illisible = tmp_path / "b.py"
    illisible.write_text("cible = 2\n", encoding="utf-8")
    illisible.chmod(0)
    try:
        sortie = await AgentToolExecutor(str(tmp_path)).search_codebase("cible", "*.py")
    finally:
        illisible.chmod(0o644)
    assert "a.py:1:cible = 1" in sortie, sortie
    assert str(tmp_path) not in sortie, "aucun chemin absolu ne doit être montré au modèle"


async def test_b963_une_erreur_sans_resultat_ne_montre_pas_de_chemin_absolu(tmp_path: Path):
    (tmp_path / "a.py").write_text("x = [1]\n", encoding="utf-8")
    sortie = await AgentToolExecutor(str(tmp_path)).search_codebase("[", "*.py")
    assert sortie.startswith("Erreur"), sortie
    assert str(tmp_path) not in sortie, sortie


def _runtime(tmp_path: Path, schema: list[dict]) -> AgentRuntime:
    config = AgentConfig(id="katia", name="Katia", description="lecture seule")
    return AgentRuntime(config, AgentToolExecutor(str(tmp_path)), schema)


async def test_b964_un_outil_hors_schema_n_est_pas_execute(tmp_path: Path):
    runtime = _runtime(tmp_path, THERESE_TOOLS)
    sortie = await runtime._execute_tool("write_file", {"file_path": "piege.txt", "content": "écrit"})
    assert not (tmp_path / "piege.txt").exists(), "Katia a écrit dans le dépôt"
    assert "non autorisé" in sortie, sortie


async def test_b964_run_command_hors_schema_n_est_pas_lance(tmp_path: Path, monkeypatch):
    from app.services.agents import tools as module_outils

    lances: list[tuple] = []

    async def faux_exec(*args, **kwargs):
        lances.append(args)
        raise AssertionError("aucun processus ne doit partir")

    monkeypatch.setattr(module_outils.asyncio, "create_subprocess_exec", faux_exec)
    sortie = await _runtime(tmp_path, THERESE_TOOLS)._execute_tool("run_command", {"command": "ruff check"})
    assert lances == [] and "non autorisé" in sortie, sortie


async def test_b964_un_outil_du_schema_reste_execute(tmp_path: Path):
    (tmp_path / "LISEZMOI.md").write_text("titre\n", encoding="utf-8")
    sortie = await _runtime(tmp_path, THERESE_TOOLS)._execute_tool("list_directory", {"dir_path": "."})
    assert "LISEZMOI.md" in sortie, sortie
    ecrit = await _runtime(tmp_path, ZEZETTE_TOOLS)._execute_tool(
        "write_file", {"file_path": "ok.txt", "content": "oui"}
    )
    assert (tmp_path / "ok.txt").read_text(encoding="utf-8") == "oui", ecrit


# ---------------------------------------------------------------- B-965
# Ces tests simulaient la sortie de grep (préfixes de racine avec « / » ou « \ »).
# La recherche est faite en Python depuis le 23/09/2026 : ils vérifient le même
# comportement, aucun chemin absolu vers le modèle et le code cité intact, sur
# de vrais fichiers.


async def test_b965_aucune_forme_de_la_racine_n_atteint_le_modele(tmp_path: Path, monkeypatch):
    """Sixième revue Codex : aucune forme de la racine ne doit passer, ni dans
    les résultats ni dans le message d'un fichier illisible (le message
    d'OSError contient le chemin complet)."""
    from app.services.agents import tools as module_outils

    racine = str(tmp_path)
    (tmp_path / "a.py").write_text("cible = 1\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("cible = 2\n", encoding="utf-8")
    lire = module_outils._lire_octets

    def illisible(chemin: str, *args):
        if chemin.endswith("b.py"):
            raise PermissionError(13, "Permission denied", chemin)
        return lire(chemin, *args)

    monkeypatch.setattr(module_outils, "_lire_octets", illisible)
    formes = {racine, racine.replace("\\", "/"), racine.replace("/", "\\")}

    avec_resultat = await AgentToolExecutor(racine).search_codebase("cible", "*.py")
    assert "a.py:1:cible = 1" in avec_resultat, avec_resultat
    assert "(certains fichiers n'ont pas pu être lus)" in avec_resultat, avec_resultat
    assert not any(forme in avec_resultat for forme in formes), avec_resultat

    (tmp_path / "a.py").unlink()
    sans_resultat = await AgentToolExecutor(racine).search_codebase("cible", "*.py")
    assert sans_resultat.startswith("Erreur"), sans_resultat
    assert "Permission denied" in sans_resultat, sans_resultat
    assert not any(forme in sans_resultat for forme in formes), sans_resultat


async def test_b965_seul_le_prefixe_de_chemin_est_retire_pas_le_code(tmp_path: Path):
    """Septième revue Codex (R-2) : la racine citée DANS une ligne de code, ou un
    dossier voisin qui commence pareil, ne doit pas être réécrit."""
    depot = tmp_path / "repo"
    depot.mkdir()
    racine = str(depot)
    code = f"cache = '{racine}sitory/x' ; autre = '{racine}'"
    (depot / "a.py").write_text(code + "\n", encoding="utf-8")
    sortie = await AgentToolExecutor(racine).search_codebase("cache", "*.py")
    assert sortie == f"a.py:1:{code}", sortie


async def test_b965_le_chemin_relatif_s_ecrit_pareil_sur_tous_les_systemes(tmp_path: Path):
    """Remplace le test de la racine courte « / » : chemin relatif avec « / »
    sous Windows aussi, et le « / » du code laissé tel quel."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x = 8 / 2\n", encoding="utf-8")
    sortie = await AgentToolExecutor(str(tmp_path)).search_codebase("8 / 2", "*.py")
    assert sortie == "src/a.py:1:x = 8 / 2", sortie
