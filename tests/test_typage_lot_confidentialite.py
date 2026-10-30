"""Les quatre diagnostics mypy ajoutés par le lot confidentialité restent corrigés (correctifs 0.83).

Le cliquet de la CI ne compare que le total à `MYPY_BASELINE` : une erreur
retirée ailleurs masquerait le retour de l'une d'elles. Même commande que le
job mypy, limitée aux quatre fichiers (une dizaine de secondes).

Rappel du piège : `src/backend/__init__.py` fait nommer ces fichiers
`backend.app.…` par mypy, alors que le code importe `app.…` ; avec
`--ignore-missing-imports`, tout symbole importé ainsi vaut `Any`.
"""
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
DIAGNOSTICS = {
    'src/backend/app/routers/chat.py': 'Need type annotation for "inline_cmds"',
    'src/backend/app/services/consentements.py': 'Class cannot subclass "ErreurPourEcran"',
    'src/backend/app/services/memory_cards.py': 'Returning Any from function declared to return "bool"',
    'src/backend/app/services/email_response_generator.py': 'Returning Any from function declared to return "str"',
}


@pytest.mark.skipif(importlib.util.find_spec('mypy') is None, reason='mypy requis (groupe dev)')
def test_les_quatre_diagnostics_du_lot_confidentialite_ne_reviennent_pas():
    resultat = subprocess.run(
        [sys.executable, '-m', 'mypy', *DIAGNOSTICS, '--ignore-missing-imports',
         '--no-error-summary', f'--cache-dir={os.devnull}'],
        cwd=RACINE, capture_output=True, text=True, timeout=600, check=False,
    )
    sortie = resultat.stdout + resultat.stderr
    assert 'INTERNAL ERROR' not in sortie and 'Traceback' not in sortie, sortie[-2000:]
    assert ' error:' in sortie, 'mypy n’a rien rendu : la mesure ne prouve rien'
    revenus = [ligne for ligne in sortie.splitlines()
               for fichier, message in DIAGNOSTICS.items()
               if ligne.startswith(fichier + ':') and message in ligne]
    assert revenus == []
