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
import shutil
import sys
from pathlib import Path

import pytest
from app.services.agents.config import AgentConfig
from app.services.agents.runtime import AgentRuntime
from app.services.agents.tools import THERESE_TOOLS, ZEZETTE_TOOLS, AgentToolExecutor

grep_requis = pytest.mark.skipif(shutil.which("grep") is None, reason="grep requis")
permissions_posix = pytest.mark.skipif(
    sys.platform == "win32" or (hasattr(os, "geteuid") and os.geteuid() == 0),
    reason="chmod 000 ne rend pas un fichier illisible ici",
)


@grep_requis
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


@grep_requis
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


class _GrepSimule:
    def __init__(self, sortie: str, erreur: str, code: int) -> None:
        self._sortie, self._erreur, self.returncode, self.pid = sortie, erreur, code, 4242

    async def communicate(self):
        return self._sortie.encode(), self._erreur.encode()


@pytest.mark.parametrize("separateur_de_grep", ["/", "\\"])
async def test_b965_aucune_forme_de_la_racine_n_atteint_le_modele(tmp_path: Path, monkeypatch, separateur_de_grep):
    """Sixième revue Codex : sous Windows, grep peut écrire la racine avec d'autres
    séparateurs que ceux de Python ; aucune forme ne doit passer."""
    from app.services.agents import tools as module_outils

    racine = str(tmp_path)
    variante = racine.replace("/", separateur_de_grep)
    grep = _GrepSimule(
        sortie=f"{variante}{separateur_de_grep}a.py:1:cible = 1\n",
        erreur=f"grep: {variante}{separateur_de_grep}b.py: Permission denied\n",
        code=2,
    )

    async def faux_exec(*args, **kwargs):
        return grep

    monkeypatch.setattr(module_outils.asyncio, "create_subprocess_exec", faux_exec)
    avec_resultat = await AgentToolExecutor(racine).search_codebase("cible", "*.py")
    assert "a.py:1:cible = 1" in avec_resultat, avec_resultat
    assert racine not in avec_resultat and variante not in avec_resultat, avec_resultat

    grep._sortie = ""
    sans_resultat = await AgentToolExecutor(racine).search_codebase("cible", "*.py")
    assert sans_resultat.startswith("Erreur"), sans_resultat
    assert "Permission denied" in sans_resultat, sans_resultat
    assert racine not in sans_resultat and variante not in sans_resultat, sans_resultat
