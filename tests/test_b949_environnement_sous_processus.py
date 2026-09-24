"""B-949 (cycle 11, 23/09/2026) : sous Linux, le moteur figé prête ses
bibliothèques aux outils du poste.

Le bootloader PyInstaller onedir préfixe `LD_LIBRARY_PATH` avec le dossier
`_internal` du bundle et garde l'ancienne valeur dans `LD_LIBRARY_PATH_ORIG`.
Les outils lancés par les agents (grep, git, pytest, npm, ruff, make)
héritaient de cet environnement : ils chargeaient la libstdc++, l'OpenSSL et la
zlib du bundle au lieu de celles du système. Mesuré sur les bibliothèques du
.deb 0.74.0 publié : python3 et curl du système passent à OpenSSL 3.0.2 au lieu
de 3.0.13, et un binaire C++ récent refuse de démarrer (GLIBCXX_3.4.32 not
found). Preuves : `.app-loop/cycles/11/reproduce/`.

Les serveurs MCP ne sont pas concernés : ils reçoivent déjà un environnement
minimal (SEC-005).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from app.services.agents import git_service as module_git
from app.services.agents import tools as module_outils
from app.services.agents.git_service import GitService
from app.services.agents.tools import AgentToolExecutor
from app.services.sous_processus import environnement_outils_systeme

BUNDLE = "/usr/lib/THERESE/binaries/backend-libs/_internal"
ORIGINE = "/usr/local/lib/du-poste"


@pytest.fixture
def moteur_fige(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setenv("LD_LIBRARY_PATH", f"{BUNDLE}:{ORIGINE}")
    monkeypatch.setenv("LD_LIBRARY_PATH_ORIG", ORIGINE)


class TestEnvironnementOutilsSysteme:
    def test_sous_bundle_la_valeur_d_origine_est_rendue(self, moteur_fige):
        env = environnement_outils_systeme()
        assert env["LD_LIBRARY_PATH"] == ORIGINE
        assert "LD_LIBRARY_PATH_ORIG" not in env

    def test_sous_bundle_sans_valeur_d_origine_la_variable_disparait(self, monkeypatch):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setenv("LD_LIBRARY_PATH", BUNDLE)
        monkeypatch.delenv("LD_LIBRARY_PATH_ORIG", raising=False)
        assert "LD_LIBRARY_PATH" not in environnement_outils_systeme()

    def test_hors_bundle_l_environnement_du_developpeur_est_respecte(self, monkeypatch):
        monkeypatch.delattr(sys, "frozen", raising=False)
        monkeypatch.setenv("LD_LIBRARY_PATH", "/opt/choix/du/dev")
        assert environnement_outils_systeme()["LD_LIBRARY_PATH"] == "/opt/choix/du/dev"

    def test_les_ajouts_s_appliquent_et_os_environ_reste_intact(self, moteur_fige):
        env = environnement_outils_systeme(PYTHONDONTWRITEBYTECODE="1")
        assert env["PYTHONDONTWRITEBYTECODE"] == "1"
        assert os.environ["LD_LIBRARY_PATH"] == f"{BUNDLE}:{ORIGINE}"


# ------------------------------------------------------------ sites d'appel


class _Processus:
    returncode = 1
    pid = 4242

    async def communicate(self):
        return b"", b""


def _intercepter(monkeypatch, module) -> list[dict]:
    appels: list[dict] = []

    async def faux_exec(*args, **kwargs):
        appels.append(kwargs)
        return _Processus()

    monkeypatch.setattr(module.asyncio, "create_subprocess_exec", faux_exec)
    return appels


def _ld_effectif(kwargs: dict) -> str | None:
    env = kwargs.get("env")
    return (env if env is not None else dict(os.environ)).get("LD_LIBRARY_PATH")


async def test_la_recherche_des_agents_ne_lance_aucun_outil_du_poste(moteur_fige, monkeypatch, tmp_path: Path):
    """La recherche lançait grep ; elle est faite en Python depuis le 23/09/2026
    (CI Windows) : plus aucun outil du poste, donc rien à hériter du bundle."""
    appels = _intercepter(monkeypatch, module_outils)
    (tmp_path / "a.py").write_text("motif = 1\n", encoding="utf-8")
    sortie = await AgentToolExecutor(str(tmp_path)).search_codebase("motif", "*.py")
    assert sortie == "a.py:1:motif = 1", sortie
    assert appels == [], "la recherche ne doit lancer aucun processus"


async def test_les_commandes_autorisees_des_agents_n_heritent_pas_du_bundle(moteur_fige, monkeypatch, tmp_path: Path):
    """B-1153 : l'environnement de la commande est désormais construit en
    liste blanche ; le chemin des bibliothèques du bundle n'y figure pas."""
    from app.services.agents import bac_a_sable

    async def disponible():
        return None

    monkeypatch.setattr(bac_a_sable, "confinement_indisponible", disponible)
    appels = _intercepter(monkeypatch, module_outils)
    await AgentToolExecutor(str(tmp_path)).run_command("ruff check")
    assert appels, "la commande n'a pas été lancée"
    assert BUNDLE not in (_ld_effectif(appels[0]) or "")
    assert appels[0]["env"]["PYTHONDONTWRITEBYTECODE"] == "1"


async def test_git_des_agents_n_herite_pas_du_bundle(moteur_fige, monkeypatch, tmp_path: Path):
    appels = _intercepter(monkeypatch, module_git)
    await GitService(tmp_path)._run("status")
    assert appels, "git n'a pas été lancé"
    assert _ld_effectif(appels[0]) == ORIGINE
