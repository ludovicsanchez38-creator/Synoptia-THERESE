#!/usr/bin/env python3
"""Dernière étape : re-signer les octets finaux pour l'updater, puis les joindre au brouillon."""
import argparse
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def artifacts(bundle, platform):
    patterns = {
        'macOS': ('dmg/*.dmg', 'macos/*.app.tar.gz'),
        'Windows': ('nsis/*.exe', 'msi/*.msi'),
        'Linux': ('deb/*.deb',),
    }[platform]
    paths = []
    for pattern in patterns:
        matches = list(bundle.glob(pattern))
        if len(matches) != 1:
            raise ValueError(f'Un unique artefact {pattern} est requis')
        paths.extend(matches)
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle', type=Path)
    parser.add_argument('--platform', required=True, choices=['macOS', 'Windows', 'Linux'])
    args = parser.parse_args()
    bundle = args.bundle.resolve()
    paths = artifacts(bundle, args.platform)
    signing_env = {**os.environ, 'TAURI_PRIVATE_KEY': os.environ['TAURI_SIGNING_PRIVATE_KEY'], 'TAURI_PRIVATE_KEY_PASSWORD': os.environ.get('TAURI_SIGNING_PRIVATE_KEY_PASSWORD', '')}
    command = [shutil.which('node'), str(ROOT / 'src/frontend/node_modules/@tauri-apps/cli/tauri.js'), 'signer', 'sign']
    uploads = []
    for path in paths:
        if path.name.endswith('.app.tar.gz') and not path.name.endswith('_aarch64.app.tar.gz'):
            renamed = path.with_name(path.name.replace('.app.tar.gz', '_aarch64.app.tar.gz'))
            shutil.copyfile(path, renamed)
            path = renamed
        if path.suffix != '.dmg':
            result = subprocess.run([*command, str(path)], cwd=ROOT / 'src/frontend', env=signing_env, capture_output=True)
            if result.returncode:
                raise RuntimeError('Échec de signature updater ; publication annulée')
            signature = Path(str(path) + '.sig')
            if not signature.is_file() or not signature.read_text().strip():
                raise RuntimeError('Signature updater absente')
            uploads.append(signature)
        uploads.append(path)
    tag = os.environ['RELEASE_TAG']
    # Les trois runners peuvent créer le même brouillon : un perdant vérifie
    # qu'il existe réellement, sans masquer une erreur d'authentification.
    result = subprocess.run(['gh', 'release', 'view', tag], capture_output=True)
    if result.returncode:
        notes = bundle / 'release-notes.md'
        notes.write_text(os.environ['RELEASE_BODY'], encoding='utf-8')
        result = subprocess.run(['gh', 'release', 'create', tag, '--draft', '--prerelease', '--title', 'THÉRÈSE ' + tag, '--notes-file', str(notes)], capture_output=True)
        if result.returncode:
            subprocess.run(['gh', 'release', 'view', tag], check=True, capture_output=True)
    subprocess.run(['gh', 'release', 'upload', tag, '--clobber', *map(str, uploads)], check=True)
    print(f'{len(uploads)} fichiers finaux joints au brouillon après vérification.')


if __name__ == '__main__':
    main()
