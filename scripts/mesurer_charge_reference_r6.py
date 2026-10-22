"""Rejouer la mesure R6 sur l'archive, avec ses propres fixtures et imports."""
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
instrument = root / '.recette-r6/instrument'
instrument.mkdir(parents=True, exist_ok=True)
texte = (root / 'tests/test_r6_charge_fournisseurs.py').read_text()
texte = texte.replace('    captures = []',
    "    assert '/.recette-r6/base/src/backend/' in llm.__file__\n    captures = []", 1)
destination = root / '.recette-r6/logs/charge-reference-fiable'
texte = texte.replace("Path(__file__).resolve().parents[1] / '.recette-r6/logs/charge'", f'Path({str(destination)!r})')
fichier = instrument / 'test_charge.py'
fichier.write_text(texte)
# Le conftest est celui de l'archive. Un test ciblé par chemin absolu dans
# tests/ du worktree chargerait son conftest et réinsérerait les sources courantes.
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/recette_r6_hors_reseau.py'),
    '--baseline', str(root / '.venv/bin/python'), '-m', 'pytest', str(fichier),
    '-p', 'tests.conftest', '-q', f'--junitxml={root}/.recette-r6/logs/r6-4-charge-reference-fiable.xml']))
