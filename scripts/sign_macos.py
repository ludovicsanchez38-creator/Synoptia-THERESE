#!/usr/bin/env python3
"""Signature macOS, de l'intérieur vers l'extérieur ; aucune valeur secrète affichée."""
from __future__ import annotations

import argparse
import base64
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTITLEMENTS = ROOT / 'src/frontend/src-tauri/Entitlements.plist'
APPLE_SECRETS = ('APPLE_CERTIFICATE', 'APPLE_CERTIFICATE_PASSWORD', 'APPLE_SIGNING_IDENTITY', 'APPLE_ID', 'APPLE_PASSWORD', 'APPLE_TEAM_ID')
MAGICS = {bytes.fromhex(h) for h in ('feedface', 'cefaedfe', 'feedfacf', 'cffaedfe', 'cafebabe', 'bebafeca', 'cafebabf', 'bfbafeca')}


def run(args):
    # Ne jamais afficher la commande, son stderr ou CalledProcessError : security
    # et notarytool reçoivent des informations d'authentification.
    result = subprocess.run([str(a) for a in args], text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f'{args[0]} a échoué (code {result.returncode}) ; détails confidentiels non journalisés')
    return result.stdout + (result.stderr if args[0] == "codesign" and "--display" in args else "")


def apple_ready(values):
    return all(values.get(name) for name in APPLE_SECRETS)


def prepare():
    ready = apple_ready(os.environ)
    identity = os.environ['APPLE_SIGNING_IDENTITY'] if ready else '-'
    if ready:
        directory = Path(os.environ['RUNNER_TEMP']) / 'therese-signing'
        directory.mkdir(mode=0o700, exist_ok=True)
        certificate = directory / 'certificate.p12'
        certificate.write_bytes(base64.b64decode(os.environ['APPLE_CERTIFICATE'], validate=True))
        certificate.chmod(0o600)
        keychain = directory / 'build.keychain-db'
        password = secrets.token_urlsafe(32)
        run(['security', 'create-keychain', '-p', password, str(keychain)])
        run(['security', 'set-keychain-settings', '-lut', '21600', str(keychain)])
        run(['security', 'unlock-keychain', '-p', password, str(keychain)])
        run(['security', 'import', str(certificate), '-k', str(keychain), '-P', os.environ['APPLE_CERTIFICATE_PASSWORD'], '-T', '/usr/bin/codesign', '-T', '/usr/bin/security'])
        run(['security', 'set-key-partition-list', '-S', 'apple-tool:,apple:,codesign:', '-s', '-k', password, str(keychain)])
        import shlex
        previous = shlex.split(run(['security', 'list-keychains', '-d', 'user']))
        run(['security', 'list-keychains', '-d', 'user', '-s', str(keychain), *previous])
        # Un profil évite de transmettre le mot de passe à chaque soumission.
        run(['xcrun', 'notarytool', 'store-credentials', 'therese-notary', '--apple-id', os.environ['APPLE_ID'], '--password', os.environ['APPLE_PASSWORD'], '--team-id', os.environ['APPLE_TEAM_ID'], '--keychain', str(keychain)])
        append_env('MACOS_SIGNING_KEYCHAIN', str(keychain))
        append_env('MACOS_SIGNING_TEAM_ID', os.environ['APPLE_TEAM_ID'])
    append_env('MACOS_SIGNING_IDENTITY', identity)
    append_env('MACOS_NOTARIZE', 'true' if ready else 'false')
    print('Signature Developer ID et notarisation activées.' if ready else 'Secrets Apple absents ou incomplets : signature ad hoc et vérification stricte activées.')


def append_env(name, value):
    if '\n' in value or '\r' in value:
        raise ValueError('Valeur multiligne interdite')
    with open(os.environ['GITHUB_ENV'], 'a', encoding='utf-8') as stream:
        stream.write(f'{name}={value}\n')


def is_macho(path):
    if path.is_symlink() or not path.is_file():
        return False
    with path.open('rb') as stream:
        return stream.read(4) in MAGICS


def sign_file(path, identity, entitlements, run=run):
    run(['codesign', '--force', '--sign', identity, '--options', 'runtime', '--entitlements', str(entitlements), '--timestamp' if identity != '-' else '--timestamp=none', str(path)])
    run(['codesign', '--verify', '--deep', '--strict', str(path)])


def sign_tree(root, identity, entitlements=ENTITLEMENTS, run=run):
    paths = [p for p in root.rglob('*') if is_macho(p) or (p.is_dir() and not p.is_symlink() and p.suffix in ('.app', '.framework', '.xpc'))] if root.is_dir() else []
    for path in sorted(paths, key=lambda p: (-len(p.parts), str(p))):
        sign_file(path, identity, entitlements, run)
    sign_file(root, identity, entitlements, run)
    print(f'Signature et vérification stricte : {len(paths) + 1} objets.')


def notarize(path, run=run):
    keychain = os.environ.get('MACOS_SIGNING_KEYCHAIN', '')
    credentials = ['--keychain-profile', 'therese-notary']
    if keychain:
        credentials += ['--keychain', keychain]
    result = json.loads(run(['xcrun', 'notarytool', 'submit', str(path), *credentials, '--wait', '--timeout', '45m', '--output-format', 'json']))
    if result.get('status') != 'Accepted':
        raise RuntimeError('Notarisation refusée ou incomplète ; aucun agrafage ni publication')
    run(['xcrun', 'stapler', 'staple', str(path)])
    run(['xcrun', 'stapler', 'validate', str(path)])


def finish(bundle_dir):
    identity = os.environ.get('MACOS_SIGNING_IDENTITY', '-')
    apps = list((bundle_dir / 'macos').glob('*.app'))
    if len(apps) != 1:
        raise ValueError('Un unique bundle .app est requis')
    app = apps[0]
    sign_tree(app, identity)
    # L'archive updater doit contenir exactement le bundle qui vient d'être signé.
    # Le DMG est reconstruit après la signature et l'agrafage du bundle.
    if os.environ.get('MACOS_NOTARIZE') == 'true':
        archive = bundle_dir / 'notarization.zip'
        run(['ditto', '-c', '-k', '--keepParent', str(app), str(archive)])
        # Un ZIP n'est pas agrafable : soumettre, puis agrafer l'app.
        result = json.loads(run(['xcrun', 'notarytool', 'submit', str(archive), '--keychain-profile', 'therese-notary', '--keychain', os.environ['MACOS_SIGNING_KEYCHAIN'], '--wait', '--timeout', '45m', '--output-format', 'json']))
        if result.get('status') != 'Accepted':
            raise RuntimeError('Notarisation du bundle refusée')
        run(['xcrun', 'stapler', 'staple', str(app)])
        run(['xcrun', 'stapler', 'validate', str(app)])
        run(['spctl', '--assess', '--type', 'execute', '--verbose', str(app)])
    dmgs = list((bundle_dir / 'dmg').glob('*.dmg'))
    if len(dmgs) != 1:
        raise ValueError('Un unique DMG est requis')
    # Conserver nom et lien Applications, sans réutiliser une image contenant une
    # ancienne signature. hdiutil copie les tickets déjà agrafés à l'application.
    import shutil
    staging = bundle_dir / 'dmg-content'
    staging.mkdir(exist_ok=False)
    shutil.copytree(app, staging / app.name, symlinks=True)
    (staging / 'Applications').symlink_to('/Applications')
    run(['hdiutil', 'create', '-ov', '-volname', 'THERESE', '-srcfolder', str(staging), '-format', 'UDZO', str(dmgs[0])])
    run(['codesign', '--force', '--sign', identity, '--timestamp' if identity != '-' else '--timestamp=none', str(dmgs[0])])
    run(['codesign', '--verify', '--deep', '--strict', str(dmgs[0])])
    if os.environ.get('MACOS_NOTARIZE') == 'true':
        notarize(dmgs[0])
        run(['spctl', '--assess', '--type', 'open', '--context', 'context:primary-signature', str(dmgs[0])])
    archives = list((bundle_dir / 'macos').glob('*.app.tar.gz'))
    if len(archives) != 1:
        raise ValueError('Une unique archive updater macOS est requise')
    run(['tar', '-czf', str(archives[0]), '-C', str(app.parent), app.name])
    print('Bundle, DMG et archive updater finalisés ; régénérer les signatures updater avant publication.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'tree', 'finish'])
    parser.add_argument('path', nargs='?', type=Path)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare()
    elif args.command == 'tree':
        sign_tree(args.path, os.environ.get('MACOS_SIGNING_IDENTITY', '-'))
    else:
        finish(args.path)


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
