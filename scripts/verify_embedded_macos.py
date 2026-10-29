#!/usr/bin/env python3
"""Contrôle les signatures réellement enfermées dans le onefile PyInstaller."""
import argparse
import os
import tempfile
from pathlib import Path

from sign_macos import MAGICS, run


def verify_embedded(executable, directory, reader=None, command=run):
    if reader is None:
        from PyInstaller.archive.readers import CArchiveReader
        reader = CArchiveReader
    archive = reader(str(executable))
    count = 0
    directory.mkdir(parents=True, exist_ok=True)
    for name, entry in archive.toc.items():
        if entry[-1] != 'b':
            continue
        data = archive.extract(name)
        if not data or data[:4] not in MAGICS:
            continue
        # Un nom d'archive ne devient jamais un chemin d'extraction.
        target = directory / f'binary-{count}'
        target.write_bytes(data)
        command(['codesign', '--verify', '--deep', '--strict', str(target)])
        details = command(['codesign', '--display', '--verbose=4', '--entitlements', ':-', str(target)])
        if 'runtime' not in details or 'com.apple.security.cs.disable-library-validation' not in details:
            raise RuntimeError('Entitlements du moteur absents d’une bibliothèque embarquée')
        team = os.environ.get('MACOS_SIGNING_TEAM_ID')
        if team and f'TeamIdentifier={team}' not in details:
            raise RuntimeError('Team ID incorrecte dans une bibliothèque embarquée')
        count += 1
    if count == 0:
        raise RuntimeError('Aucun Mach-O embarqué trouvé ; vérification invalide')
    command(['codesign', '--verify', '--deep', '--strict', str(executable)])
    print(f'{count} bibliothèques/binaires embarqués : signatures vérifiées après compression/extraction.')
    return count


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable', type=Path)
    args = parser.parse_args()
    directory = Path(tempfile.mkdtemp(prefix='therese-signatures-', dir=os.environ.get('RUNNER_TEMP')))
    verify_embedded(args.executable, directory)
