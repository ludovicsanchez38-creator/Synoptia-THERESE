"""Exécuter les portes complètes R5, séparément et hors réseau."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
phase = sys.argv[1]
code = ROOT / '.recette-r5/base' if phase == 'avant' else ROOT
logs = ROOT / '.recette-r5/logs'
python = str(ROOT / '.venv/bin/python')
frontend = code / 'src/frontend'
commands = {
 'pytest': [python, '-m', 'pytest', 'tests/', '--ignore=tests/e2e', '-q', f'--junitxml={logs}/{phase}-pytest.xml'],
 'autonome': [python, '-m', 'pytest', 'src/backend/tests/', '-q', f'--junitxml={logs}/{phase}-autonome.xml'],
 'vitest': ['node', str(frontend / 'node_modules/vitest/vitest.mjs'), 'run', '--no-cache', '--root', str(frontend), '--reporter=default', '--reporter=json', f'--outputFile={logs}/{phase}-vitest.json'],
 'mypy': [python, '-m', 'mypy', '-p', 'app', '--cache-dir=/dev/null'],
 'tsc': ['node', str(frontend / 'node_modules/typescript/bin/tsc'), '--noEmit', '--project', str(frontend)],
 'ruff': [python, '-m', 'ruff', 'check', '--no-fix', 'src/backend'],
 'eslint': ['node', str(frontend / 'node_modules/eslint/bin/eslint.js'), str(frontend), '--no-fix'],
}
selection = sys.argv[2:] or list(commands)
if any(nom not in commands for nom in selection):
 raise SystemExit('Porte inconnue.')
suffixe = '-' + '-'.join(selection) if sys.argv[2:] else ''
recu = logs / f'{phase}-codes{suffixe}.json'
status = {}
for name, command in commands.items():
 if len(sys.argv) > 2 and name not in sys.argv[2:]:
  continue
 print(f'{phase} {name} : début', flush=True)
 # Vitest et ESLint doivent partir du frontend, y compris process.cwd().
 if name in ('eslint', 'vitest'):
  command = [python, '-c', 'import os,subprocess,sys; os.chdir(sys.argv[1]); raise SystemExit(subprocess.call(sys.argv[2:]))', str(frontend), *command]
 harness = [sys.executable, str(ROOT / 'scripts/recette_r5_hors_reseau.py')]
 if phase == 'avant':
  harness += ['--baseline']
 with (logs / f'{phase}-{name}.log').open('w') as log:
  status[name] = subprocess.call([*harness, *command], stdout=log, stderr=subprocess.STDOUT)
 recu.write_text(json.dumps(status, indent=2))
 print(f'{phase} {name} : {status[name]}', flush=True)

raise SystemExit(int(any(code != 0 for name, code in status.items() if name != "mypy")))
