"""Conserve les sorties des vérifications C19-D dans le dossier autorisé."""
import os
import subprocess
import sys
import uuid
from pathlib import Path
root = Path(__file__).resolve().parent.parent
os.environ.update(TMPDIR=str(root / '.c19d/tmp'), PYTHONDONTWRITEBYTECODE='1',
                  THERESE_DATA_DIR=str(root / '.c19d/tmp' / ('data-' + uuid.uuid4().hex)),
                  npm_config_cache=str(root / '.c19d/tmp/npm'))
nom, *cmd = sys.argv[1:]
if any('pytest' in x for x in cmd):
    cmd += ['--cov=', '--no-cov', '-p', 'pytest_finish', '--timeout=30']
    os.environ['PYTHONPATH'] = str(root / '.c19d')
cwd = root / 'src/frontend' if cmd[0] == 'npx' else root
preuve = root / '.c19d/preuves' / (nom + '.log')
with preuve.open('w') as sortie:
    sortie.write('Commande : ' + ' '.join(cmd) + '\nDossier : ' + str(cwd) + '\n\n')
    sortie.flush()
    resultat = subprocess.Popen(cmd, cwd=cwd, text=True, stdout=sortie, stderr=subprocess.STDOUT)
    code = resultat.wait()
    sortie.write(f'\nCode de sortie : {code}\n')
print(preuve.read_text()[-6500:])
print(f'Sortie {code} ; preuve .c19d/preuves/{nom}.log')
sys.exit(code)
