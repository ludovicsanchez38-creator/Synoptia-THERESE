"""Enchaîner les portes après la référence complète, puis comparer les noms."""
import json
import subprocess
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
logs = root / '.recette-r6/logs'
reference = logs / 'avant-codes.json'
while not reference.exists() or len(json.loads(reference.read_text())) != 7:
    time.sleep(2)
print('Référence complète terminée ; lancement des sept portes après R6.', flush=True)
with (logs / 'apres-portes.log').open('w') as journal:
    subprocess.call([sys.executable, str(root / 'scripts/portes_r6.py'), 'apres'],
                    stdout=journal, stderr=subprocess.STDOUT)
with (logs / 'comparaison.log').open('w') as journal:
    code = subprocess.call([sys.executable, str(root / 'scripts/comparer_portes_r6.py')],
                           stdout=journal, stderr=subprocess.STDOUT)
print('Comparaison complète :', code, flush=True)
raise SystemExit(code)
