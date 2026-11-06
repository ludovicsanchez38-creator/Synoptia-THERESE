#!/usr/bin/env python3
"""Contrôle les signatures réellement enfermées dans le onefile PyInstaller."""
import argparse
import os
import struct
import tempfile
from pathlib import Path

from sign_macos import MAGICS, run

ENTITLEMENT = 'com.apple.security.cs.disable-library-validation'
MH_EXECUTE = 2


def filetype(data):
    """Type Mach-O (MH_EXECUTE, MH_DYLIB, MH_BUNDLE…) du premier tranche ; None si illisible."""
    magic = data[:4]
    try:
        if magic in (bytes.fromhex('cafebabe'), bytes.fromhex('cafebabf')):
            # Binaire universel (gros-boutiste) : lire l'en-tête de la première tranche.
            offset = (struct.unpack_from('>I', data, 16)[0] if magic == bytes.fromhex('cafebabe')
                      else struct.unpack_from('>Q', data, 16)[0])
            return filetype(data[offset:]) if offset < len(data) else None
        order = '<' if magic in (bytes.fromhex('cefaedfe'), bytes.fromhex('cffaedfe')) else '>'
        return struct.unpack_from(order + 'I', data, 12)[0]
    except struct.error:
        return None


def verify_embedded(executable, directory, reader=None, command=run):
    if reader is None:
        from PyInstaller.archive.readers import CArchiveReader
        reader = CArchiveReader
    archive = reader(str(executable))
    count = 0
    failures = []
    directory.mkdir(parents=True, exist_ok=True)
    # Contrôler aussi un Mach-O rangé par erreur parmi les données (type x).
    for name in archive.toc:
        data = archive.extract(name)
        if not data or data[:4] not in MAGICS:
            continue
        # Un nom d'archive ne devient jamais un chemin d'extraction.
        target = directory / f'binary-{count}'
        target.write_bytes(data)
        count += 1
        try:
            command(['codesign', '--verify', '--deep', '--strict', str(target)])
        except RuntimeError:
            failures.append(f'{name} : signature invalide')
            continue
        details = command(['codesign', '--display', '--verbose=4', '--entitlements', ':-', str(target)])
        if 'runtime' not in details:
            failures.append(f'{name} : runtime durci absent')
        # codesign n'inscrit les entitlements que dans un exécutable : une
        # bibliothèque n'en porte jamais, le processus prend ceux du moteur.
        # Type illisible : on exige comme pour un exécutable (fermé par défaut).
        if filetype(data) in (MH_EXECUTE, None) and ENTITLEMENT not in details:
            failures.append(f'{name} : entitlements absents d’un exécutable embarqué')
        team = os.environ.get('MACOS_SIGNING_TEAM_ID')
        if team and f'TeamIdentifier={team}' not in details:
            failures.append(f'{name} : Team ID incorrecte')
    if count == 0:
        raise RuntimeError('Aucun Mach-O embarqué trouvé ; vérification invalide')
    command(['codesign', '--verify', '--deep', '--strict', str(executable)])
    outer = command(['codesign', '--display', '--verbose=4', '--entitlements', ':-', str(executable)])
    if 'runtime' not in outer or ENTITLEMENT not in outer:
        failures.append(f'{executable.name} : entitlements du moteur absents de l’exécutable')
    if failures:
        raise RuntimeError('Signatures refusées dans le moteur :\n' + '\n'.join(failures))
    print(f'{count} bibliothèques/binaires embarqués : signatures vérifiées après compression/extraction.')
    return count


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable', type=Path)
    args = parser.parse_args()
    directory = Path(tempfile.mkdtemp(prefix='therese-signatures-', dir=os.environ.get('RUNNER_TEMP')))
    verify_embedded(args.executable, directory)
