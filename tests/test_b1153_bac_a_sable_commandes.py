"""B-1153 : les commandes des agents s'exécutent confinées (macOS, V1).

Design : docs/plans/2026-09-24-b1153-bac-a-sable-commandes-agents.md (V5, GO).
L'avocat du diable de l'audit 0.75 avait écrit un `pytest.ini` avec
`--basetemp` hors du dépôt : `pytest -q` avait vidé ce dossier. Toute commande
permise exécute du code que l'agent peut écrire ; ces tests écrivent ce code
(un `conftest.py`) et vérifient ce que le confinement lui refuse.

Les cas confinés tournent sous macOS (Seatbelt) ; le refus tourne partout.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import os
import socket
import sys
from pathlib import Path

import pytest
from app.config import settings
from app.services.agents import bac_a_sable
from app.services.agents import tools as module_outils
from app.services.agents.tools import AgentToolExecutor

macos = pytest.mark.skipif(sys.platform != "darwin", reason="confinement V1 : macOS seulement")


@pytest.fixture(autouse=True)
def _sonde_neuve():
    bac_a_sable._oublier_la_sonde()
    yield
    bac_a_sable._oublier_la_sonde()


@pytest.fixture
def depot(tmp_path: Path, monkeypatch) -> Path:
    racine = tmp_path / "depot"
    racine.mkdir()
    (racine / "test_ok.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    # `pytest` doit être trouvable par la commande (liste blanche : PATH gardé).
    monkeypatch.setenv("PATH", f"{Path(sys.executable).parent}{os.pathsep}{os.environ.get('PATH', '')}")
    return racine


def _conftest(depot: Path, corps: str) -> None:
    """Code exécuté par pytest à la collecte : il écrit son rapport dans le dépôt."""
    (depot / "conftest.py").write_text(
        "import json, os, socket, subprocess\n"
        "from pathlib import Path\n"
        "rapport = {}\n"
        f"{corps}\n"
        "Path(__file__).with_name('rapport.json').write_text(json.dumps(rapport))\n",
        encoding="utf-8",
    )


def _rapport(depot: Path) -> dict:
    chemin = depot / "rapport.json"
    assert chemin.exists(), "le conftest n'a pas tourné (commande refusée ou pytest introuvable)"
    return json.loads(chemin.read_text(encoding="utf-8"))


async def _pytest(depot: Path) -> str:
    return await AgentToolExecutor(str(depot)).run_command("pytest -q")


# --------------------------------------------------------------- écriture


@macos
@pytest.mark.asyncio
async def test_le_cas_de_l_audit_ne_vide_plus_un_dossier_hors_du_depot(depot: Path, tmp_path: Path):
    dehors = tmp_path / "dehors"
    dehors.mkdir()
    temoin = dehors / "precieux.txt"
    temoin.write_text("à garder", encoding="utf-8")
    (depot / "pytest.ini").write_text(f"[pytest]\naddopts = --basetemp={dehors}\n", encoding="utf-8")
    # pytest ne vide --basetemp que si un test demande tmp_path, comme dans
    # la reproduction de l'audit.
    (depot / "test_ok.py").write_text("def test_ok(tmp_path):\n    assert tmp_path.exists()\n", encoding="utf-8")
    _conftest(depot, "rapport['lance'] = True")

    await _pytest(depot)

    assert _rapport(depot)["lance"], "la commande doit avoir tourné (sinon le test ne prouve rien)"
    assert temoin.read_text(encoding="utf-8") == "à garder"


@macos
@pytest.mark.asyncio
async def test_le_code_de_l_agent_n_ecrit_ni_dans_le_dossier_personnel_ni_dans_tmp(depot: Path):
    nom = f"therese-b1153-{os.getpid()}.txt"
    cibles = [Path.home() / nom, Path("/tmp") / nom]
    _conftest(
        depot,
        "for cible in " + repr([str(c) for c in cibles]) + ":\n"
        "    try:\n        Path(cible).write_text('x'); rapport[cible] = 'ECRIT'\n"
        "    except OSError as e:\n        rapport[cible] = e.errno\n",
    )
    try:
        await _pytest(depot)
        rapport = _rapport(depot)
        assert all(rapport[str(c)] in (1, 13) for c in cibles), rapport
    finally:
        for cible in cibles:
            cible.unlink(missing_ok=True)


@macos
@pytest.mark.asyncio
async def test_le_depot_et_le_dossier_temporaire_restent_ecrivables(depot: Path, monkeypatch):
    dossiers: list[Path] = []
    preparer = bac_a_sable.preparer_lancement

    def espion(parts, racine):
        lancement = preparer(parts, racine)
        dossiers.append(lancement.tmp)
        return lancement

    monkeypatch.setattr(bac_a_sable, "preparer_lancement", espion)
    _conftest(
        depot,
        "Path(__file__).with_name('ecrit.txt').write_text('ok')\n"
        "Path(os.environ['TMPDIR'], 'tmp.txt').write_text('ok')\n"
        "rapport['tmp'] = os.environ['TMPDIR']\n",
    )

    sortie = await _pytest(depot)

    assert sortie.startswith("Code retour : 0"), sortie
    assert (depot / "ecrit.txt").read_text() == "ok"
    assert dossiers and not dossiers[0].exists(), "le dossier temporaire de la commande doit être retiré"


# --------------------------------------------------------------- secrets


@macos
@pytest.mark.asyncio
async def test_l_environnement_du_moteur_ne_passe_pas(depot: Path, monkeypatch):
    monkeypatch.setenv("THERESE_DB_KEY", "cle-de-la-base")
    monkeypatch.setenv("FAUX_API_KEY", "sk-faux")
    monkeypatch.setenv("SSH_AUTH_SOCK", "/tmp/faux-agent.sock")
    _conftest(depot, "rapport['env'] = sorted(os.environ)")

    await _pytest(depot)

    vues = set(_rapport(depot)["env"])
    assert not {"THERESE_DB_KEY", "FAUX_API_KEY", "SSH_AUTH_SOCK"} & vues, vues


@macos
@pytest.mark.asyncio
@pytest.mark.parametrize("dossier_deplace", [False, True])
async def test_la_cle_maitresse_du_dossier_de_donnees_est_illisible(depot: Path, tmp_path: Path, monkeypatch, dossier_deplace):
    if dossier_deplace:
        monkeypatch.setattr(settings, "data_dir", tmp_path / "donnees-ailleurs")
    donnees = Path(settings.data_dir)
    donnees.mkdir(parents=True, exist_ok=True)
    cle = donnees / ".encryption_key-temoin"
    cle.write_text("SECRET", encoding="utf-8")
    _conftest(
        depot,
        f"try:\n    rapport['lu'] = Path({str(cle)!r}).read_text()\nexcept OSError as e:\n    rapport['lu'] = e.errno\n",
    )
    try:
        await _pytest(depot)
        assert _rapport(depot)["lu"] in (1, 13), "la commande a lu le dossier de données"
    finally:
        cle.unlink(missing_ok=True)


# --------------------------------------------------------------- réseau et processus


@macos
@pytest.mark.asyncio
async def test_aucune_connexion_locale_pas_meme_vers_un_port_ouvert(depot: Path):
    serveur = socket.socket()
    serveur.bind(("127.0.0.1", 0))
    serveur.listen(1)
    port = serveur.getsockname()[1]
    _conftest(
        depot,
        f"try:\n    socket.create_connection(('127.0.0.1', {port}), timeout=2); rapport['net'] = 'OUVERT'\n"
        "except OSError as e:\n    rapport['net'] = e.errno\n",
    )
    try:
        await _pytest(depot)
    finally:
        serveur.close()
    assert _rapport(depot)["net"] in (1, 13), _rapport(depot)


@macos
@pytest.mark.asyncio
async def test_un_processus_exterieur_ne_recoit_aucun_signal(depot: Path):
    temoin = await asyncio.create_subprocess_exec("/bin/sleep", "60")
    _conftest(
        depot,
        "enfant = subprocess.Popen(['/bin/sleep', '30']); enfant.kill(); enfant.wait(); rapport['enfant'] = 'OK'\n"
        f"try:\n    os.kill({temoin.pid}, 0); rapport['dehors'] = 'JOINT'\n"
        "except OSError as e:\n    rapport['dehors'] = e.errno\n",
    )
    try:
        await _pytest(depot)
        rapport = _rapport(depot)
    finally:
        temoin.kill()
        await temoin.wait()
    assert rapport["enfant"] == "OK"
    assert rapport["dehors"] == 1, rapport


# --------------------------------------------------------------- fail-closed


@macos
@pytest.mark.asyncio
async def test_un_confinement_inefficace_est_detecte_et_refuse(depot: Path, monkeypatch):
    monkeypatch.setattr(bac_a_sable, "PROFIL_SEATBELT", "(version 1)(allow default)")
    _conftest(depot, "rapport['lance'] = True")

    sortie = await _pytest(depot)

    assert sortie.startswith("Erreur : les commandes des agents sont désactivées"), sortie
    assert not (depot / "rapport.json").exists(), "rien ne doit tourner"


@pytest.mark.asyncio
@pytest.mark.parametrize("plateforme", ["linux", "win32"])
async def test_sans_confinement_disponible_rien_n_est_lance(tmp_path: Path, monkeypatch, plateforme):
    lances: list = []

    async def faux_exec(*args, **kwargs):
        lances.append(args)
        raise AssertionError("aucun processus ne doit partir")

    monkeypatch.setattr(sys, "platform", plateforme)
    monkeypatch.setattr(module_outils.asyncio, "create_subprocess_exec", faux_exec)

    sortie = await AgentToolExecutor(str(tmp_path)).run_command("pytest -q")

    assert lances == []
    assert sortie.startswith("Erreur : les commandes des agents sont désactivées sur ce système"), sortie
    assert "lire et modifier" in sortie


def test_run_command_ne_lance_rien_hors_du_confinement():
    source = inspect.getsource(AgentToolExecutor.run_command)
    assert source.count("create_subprocess_exec(") == 1
    assert "*lancement.argv" in source and "env=lancement.env" in source
    assert "confinement_indisponible()" in source.split("create_subprocess_exec(")[0]


def test_la_ci_joue_le_confinement_sur_macos():
    """Sans runner macOS, les garanties confinées ne seraient vérifiées que sur
    le poste du développeur : la CI (appelée par la release) les joue."""
    ci = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    bloc = ci[ci.index("bac-a-sable-macos:"):]
    bloc = bloc[: bloc.index("\n  # ") if "\n  # " in bloc else len(bloc)]
    assert "runs-on: macos-latest" in bloc
    assert "tests/test_b1153_bac_a_sable_commandes.py" in bloc
    assert "tests/test_b1153_git_de_mission_durci.py" in bloc
