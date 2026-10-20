"""Reçu immédiat des échecs, complément du JUnit en fin de suite R1."""
from pathlib import Path
from typing import Any

_RACINE = Path(__file__).resolve().parents[1]
_PHASE = 'base' if Path.cwd().resolve() == _RACINE / 'recette-r1-base' else 'apres'
_RECU = _RACINE / f'.recette-r1/logs/{_PHASE}-pytest-echecs.log'


def pytest_runtest_logreport(report: Any) -> None:
    if report.failed:
        with _RECU.open('a', encoding='utf-8') as sortie:
            sortie.write(f'{report.nodeid} ({report.when})\n{report.longrepr}\n\n')
