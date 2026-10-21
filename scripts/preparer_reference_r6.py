"""Archive locale de référence, avec index Git pour les tests de balayage.

À lancer dans le harnais hors réseau. Refuse d'écraser une référence existante.
"""
import io
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '.recette-r6/base'
REFERENCE = 'a1a1f3a3'
if BASE.exists():
    raise SystemExit('La référence existe déjà : conserve-la ou déplace-la dans le worktree avant de recommencer.')
BASE.mkdir(parents=True)
archive = subprocess.check_output(['git', 'archive', REFERENCE], cwd=ROOT)
with tarfile.open(fileobj=io.BytesIO(archive)) as source:
    source.extractall(BASE, filter='data')
for destination, origine in [(BASE / '.venv', ROOT / '.venv'),
                              (BASE / 'src/frontend/node_modules', ROOT / 'src/frontend/node_modules')]:
    destination.symlink_to(origine, target_is_directory=True)
subprocess.run(['git', 'init', '--quiet', str(BASE)], check=True)
paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', '-z', REFERENCE], cwd=ROOT)
liste = ROOT / '.recette-r6/index-reference-paths'
liste.write_bytes(paths)
subprocess.run(['git', '-C', str(BASE), '--literal-pathspecs', 'add', '-f',
                f'--pathspec-from-file={liste}', '--pathspec-file-nul'], check=True)
print('Référence locale préparée avec son index Git.')
