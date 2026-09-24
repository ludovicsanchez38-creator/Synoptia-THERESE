"""P-100 (acceptée par Ludo le 24/09/2026, B-959 différé du cycle 11) :
`run_command` ne contrôlait que le premier mot pour pytest, vitest et ruff.
`pytest --basetemp=<dossier>` vide le dossier visé, `ruff format <chemin>`
réécrit hors du dépôt, `vitest --dir /` parcourt le disque.

Règle : chemins relatifs résolus DANS le dépôt, et courte liste de drapeaux
(pytest -q -v -vv -x --tb=short|line|no -k <expr> ; vitest run -t <nom> ;
ruff check --fix). Tout le reste est refusé avec un message, sans rien
lancer. Aussi B-1052 : `npm run typecheck` était autorisé sans exister.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from app.services.agents import tools as module_outils
from app.services.agents.tools import AgentToolExecutor


class _Processus:
    returncode = 0
    pid = 4242

    async def communicate(self):
        return b"ok", b""


@pytest.fixture
def lances(monkeypatch) -> list[tuple]:
    """Ces tests portent sur la garde des ARGUMENTS : le confinement (B-1153,
    tests dédiés) est remplacé par un lanceur transparent, sur toute
    plateforme."""
    from app.services.agents import bac_a_sable

    appels: list[tuple] = []

    async def faux_exec(*args, **kwargs):
        appels.append(args)
        return _Processus()

    async def disponible():
        return None

    monkeypatch.setattr(module_outils.asyncio, "create_subprocess_exec", faux_exec)
    monkeypatch.setattr(bac_a_sable, "confinement_indisponible", disponible)
    monkeypatch.setattr(
        bac_a_sable, "preparer_lancement", lambda parts, depot: bac_a_sable.Lancement(argv=list(parts), env={})
    )
    return appels


@pytest.fixture
def depot(tmp_path: Path) -> Path:
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text("def test_a():\n    pass\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    return tmp_path


@pytest.mark.parametrize(
    "commande",
    [
        "pytest --basetemp=/home/quelquun/Documents",
        "pytest --basetemp /tmp/x",
        "pytest -p mon_plugin",
        "pytest -c /etc/pytest.ini",
        "pytest /etc",
        "pytest ../autre_depot",
        "pytest tests/../../ailleurs",
        "pytest ~/Documents",
        "ruff format /etc",
        "ruff format src",
        "ruff check --config /tmp/ruff.toml src",
        "ruff check /etc",
        "vitest run --dir /",
        "vitest --config /tmp/v.config.ts",
        "vitest run --root /",
        "vitest watch",
        "npm run typecheck",
        # Lecteur G2 (dernière passe c12) : fichier d'arguments de pytest, et
        # valeur de -k / -t qui est en fait une option.
        "pytest @args.txt",
        "pytest tests @args.txt",
        "vitest run -t --dir=/",
        "pytest -k --basetemp=/tmp/x",
    ],
)
async def test_un_argument_hors_regle_est_refuse_sans_rien_lancer(depot: Path, lances: list, commande: str):
    sortie = await AgentToolExecutor(str(depot)).run_command(commande)
    assert lances == [], f"lancé : {lances}"
    assert sortie.startswith("Erreur"), sortie


@pytest.mark.parametrize(
    "commande",
    [
        "pytest",
        "pytest tests/",
        "pytest -q tests/test_a.py",
        "pytest -x -v tests/test_a.py::test_a",
        "pytest -k parcours_complet --tb=short tests",
        "vitest run",
        "vitest run src -t focus",
        "ruff check",
        "ruff check --fix src tests",
        "npm test",
        "npm run lint",
        "make test-backend",
    ],
)
async def test_les_commandes_promises_aux_agents_passent_telles_quelles(depot: Path, lances: list, commande: str):
    sortie = await AgentToolExecutor(str(depot)).run_command(commande)
    assert lances == [tuple(commande.split())], sortie
    assert sortie.startswith("Code retour : 0"), sortie


async def test_le_refus_dit_ce_qui_est_permis(depot: Path, lances: list):
    sortie = await AgentToolExecutor(str(depot)).run_command("pytest --basetemp=/tmp/x")
    assert "--basetemp" in sortie
    assert "-k" in sortie and "-q" in sortie, sortie
