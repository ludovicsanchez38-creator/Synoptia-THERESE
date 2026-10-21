"""Finaliser la comparaison et le banc après la fin des portes complètes."""
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / '.recette-r4/logs'
SOURCES = {
 'avant-portes.log': ('avant', ['autonome', 'vitest', 'mypy', 'tsc', 'ruff', 'eslint']),
 'avant-rejeu-portes.log': ('avant', ['pytest']),
 'apres-front-portes.log': ('apres', ['autonome', 'vitest']),
 'apres-statique.log': ('apres', ['tsc', 'ruff', 'eslint']),
 'apres-portes.log': ('apres', ['pytest']),
}
while True:
 codes = {'avant': {}, 'apres': {}}
 manque = []
 for fichier, (phase, portes) in SOURCES.items():
  texte = (LOGS / fichier).read_text() if (LOGS / fichier).exists() else ''
  for porte in portes:
   resultat = re.findall(rf'^{phase} {porte} : (-?\d+)$', texte, re.M)
   if resultat:
    codes[phase][porte] = int(resultat[-1])
   else:
    manque.append(phase + ':' + porte)
 if not manque:
  break
 time.sleep(10)
print('Toutes les portes complètes sont terminées.', flush=True)
if any(valeur != 0 for portes in codes.values() for nom, valeur in portes.items() if nom != 'mypy'):
 print(json.dumps(codes, indent=2), flush=True)
 raise SystemExit('Une porte nécessite une correction ; aucun nouveau banc lancé.')
harnais = [sys.executable, str(ROOT / 'scripts/recette_r4_hors_reseau.py')]
with (LOGS / 'apres-mypy.log').open('w') as journal:
 codes['apres']['mypy'] = subprocess.call([*harnais, str(ROOT / '.venv/bin/python'),
     '-m', 'mypy', '-p', 'app', '--cache-dir=/dev/null'], stdout=journal, stderr=subprocess.STDOUT)
for phase, portes in codes.items():
 (LOGS / f'{phase}-codes.json').write_text(json.dumps(portes, indent=2))
with (LOGS / 'comparaison.log').open('w') as journal:
 comparaison = subprocess.call([sys.executable, str(ROOT / 'scripts/comparer_portes_r4.py')],
     stdout=journal, stderr=subprocess.STDOUT)
if comparaison:
 raise SystemExit('La comparaison indique une régression ; aucun nouveau banc lancé.')
print('Comparaison complète réussie ; banc local séquentiel.', flush=True)
banc = ROOT / '.recette-r4/banc-apres'
if banc.exists():
 numero = 1
 while banc.with_name(f'banc-apres-tentative-{numero}').exists():
  numero += 1
 banc.rename(banc.with_name(f'banc-apres-tentative-{numero}'))
with (LOGS / 'banc-apres-final.log').open('w') as journal:
 code_banc = subprocess.call([sys.executable, str(ROOT / 'scripts/banc_ollama_r4.py'), 'apres'],
     stdout=journal, stderr=subprocess.STDOUT)
(LOGS / 'banc-apres-code.json').write_text(json.dumps({'code': code_banc}))
print('Banc terminé, code', code_banc, flush=True)
raise SystemExit(code_banc)
