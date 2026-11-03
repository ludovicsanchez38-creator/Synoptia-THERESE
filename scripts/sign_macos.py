#!/usr/bin/env python3
"""Signature macOS, de l'intérieur vers l'extérieur ; aucune valeur secrète affichée."""
from __future__ import annotations

import argparse
import base64
import binascii
import json
import os
import secrets
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTITLEMENTS = ROOT / 'src/frontend/src-tauri/Entitlements.plist'
# Certificat Developer ID Application exporté en P12 et identité de l'équipe.
APPLE_CERTIFICATE_SECRETS = ('APPLE_CERTIFICATE', 'APPLE_CERTIFICATE_PASSWORD', 'APPLE_SIGNING_IDENTITY', 'APPLE_TEAM_ID')
# Notarisation, voie recommandée en CI : clé d'API App Store Connect (.p8).
# Noms alignés sur Tauri (APPLE_API_KEY = identifiant de la clé, APPLE_API_ISSUER).
APPLE_API_SECRETS = ('APPLE_API_KEY', 'APPLE_API_ISSUER', 'APPLE_API_PRIVATE_KEY')
# Notarisation, voie de repli : identifiant Apple et mot de passe d'application.
APPLE_ID_SECRETS = ('APPLE_ID', 'APPLE_PASSWORD')
APPLE_SECRETS = APPLE_CERTIFICATE_SECRETS + APPLE_API_SECRETS + APPLE_ID_SECRETS
NOTARY_PROFILE = 'therese-notary'
MAGICS = {bytes.fromhex(h) for h in ('feedface', 'cefaedfe', 'feedfacf', 'cffaedfe', 'cafebabe', 'bebafeca', 'cafebabf', 'bfbafeca')}


def run(args, check=True):
    # Ne jamais afficher la commande, son stderr ou CalledProcessError : security
    # et notarytool reçoivent des informations d'authentification.
    result = subprocess.run([str(a) for a in args], text=True, capture_output=True)
    if check and result.returncode:
        raise RuntimeError(f'{args[0]} a échoué (code {result.returncode}) ; détails confidentiels non journalisés')
    return result.stdout + (result.stderr if args[0] == "codesign" and "--display" in args else "")


def apple_mode(values):
    """Renvoie 'api', 'apple-id', 'adhoc' (aucun secret) ou 'partiel'."""
    present = {name for name in APPLE_SECRETS if values.get(name)}
    if not present:
        return 'adhoc'
    certificate = present.issuperset(APPLE_CERTIFICATE_SECRETS)
    if certificate and present.issuperset(APPLE_API_SECRETS):
        return 'api'
    if certificate and present.issuperset(APPLE_ID_SECRETS):
        return 'apple-id'
    return 'partiel'


def missing_secrets(values):
    """Noms (jamais les valeurs) qui manquent pour la voie la plus avancée."""
    present = {name for name in APPLE_SECRETS if values.get(name)}
    missing = [name for name in APPLE_CERTIFICATE_SECRETS if name not in present]
    api = [name for name in APPLE_API_SECRETS if name not in present]
    apple_id = [name for name in APPLE_ID_SECRETS if name not in present]
    # La clé d'API est la voie documentée ; l'identifiant Apple n'est proposé
    # que s'il a déjà été commencé.
    return missing + (apple_id if present & set(APPLE_ID_SECRETS) and not present & set(APPLE_API_SECRETS) else api)


def apple_ready(values):
    return apple_mode(values) in ('api', 'apple-id')


def strict_signing(values):
    """Variable de dépôt SIGNATURE_OBLIGATOIRE=true : refuser toute release non signée."""
    return values.get('SIGNATURE_OBLIGATOIRE', '').strip().lower() == 'true'


def decode_api_key(value):
    """Contenu du fichier AuthKey_XXXX.p8, en clair (PEM) ou encodé en base64."""
    if '-----BEGIN PRIVATE KEY-----' in value:
        return value.strip().encode('ascii') + b'\n'
    try:
        data = base64.b64decode(''.join(value.split()), validate=True)
    except (binascii.Error, ValueError):
        raise ValueError('APPLE_API_PRIVATE_KEY : contenu du fichier .p8 (PEM) ou son encodage base64 attendu') from None
    if b'-----BEGIN PRIVATE KEY-----' not in data:
        raise ValueError('APPLE_API_PRIVATE_KEY : le contenu décodé n\'est pas une clé .p8') from None
    return data


def check_identity(keychain, identity, run=run):
    """Échoue avant PyInstaller si le P12 ne contient pas une identité Developer ID Application."""
    listing = run(['security', 'find-identity', '-v', '-p', 'codesigning', str(keychain)])
    wanted = identity.strip().casefold()
    for line in listing.splitlines():
        if wanted and wanted in line.casefold():
            if '"Developer ID Application:' not in line:
                raise ValueError('APPLE_SIGNING_IDENTITY ne désigne pas un certificat « Developer ID Application » : la notarisation le refuserait')
            return
    raise ValueError('APPLE_SIGNING_IDENTITY introuvable dans le certificat importé (nom exact ou empreinte SHA-1 attendus)')


def prepare():
    mode = apple_mode(os.environ)
    strict = strict_signing(os.environ)
    if mode == 'partiel':
        message = 'Secrets Apple incomplets, il manque : ' + ', '.join(missing_secrets(os.environ)) + '.'
        if strict:
            raise ValueError(message + ' SIGNATURE_OBLIGATOIRE=true : release refusée.')
        # Annotation visible dans le résumé du run : une saisie partielle ne passe pas inaperçue.
        print('::warning title=Signature macOS::' + message + ' Build signé ad hoc, non notarisé.')
    elif mode == 'adhoc' and strict:
        raise ValueError('SIGNATURE_OBLIGATOIRE=true mais aucun secret Apple : release refusée.')
    ready = mode in ('api', 'apple-id')
    identity = os.environ['APPLE_SIGNING_IDENTITY'] if ready else '-'
    if ready:
        directory = Path(os.environ['RUNNER_TEMP']) / 'therese-signing'
        directory.mkdir(mode=0o700, exist_ok=True)
        certificate = directory / 'certificate.p12'
        certificate.write_bytes(base64.b64decode(''.join(os.environ['APPLE_CERTIFICATE'].split()), validate=True))
        certificate.chmod(0o600)
        keychain = directory / 'build.keychain-db'
        password = secrets.token_urlsafe(32)
        run(['security', 'create-keychain', '-p', password, str(keychain)])
        run(['security', 'set-keychain-settings', '-lut', '21600', str(keychain)])
        run(['security', 'unlock-keychain', '-p', password, str(keychain)])
        run(['security', 'import', str(certificate), '-k', str(keychain), '-P', os.environ['APPLE_CERTIFICATE_PASSWORD'], '-T', '/usr/bin/codesign', '-T', '/usr/bin/security'])
        # Le P12 est dans le trousseau : plus besoin du fichier pendant le build.
        certificate.unlink()
        run(['security', 'set-key-partition-list', '-S', 'apple-tool:,apple:,codesign:', '-s', '-k', password, str(keychain)])
        previous = shlex.split(run(['security', 'list-keychains', '-d', 'user']))
        run(['security', 'list-keychains', '-d', 'user', '-s', str(keychain), *previous])
        check_identity(keychain, identity, run=run)
        # Un profil évite de transmettre la clé ou le mot de passe à chaque
        # soumission ; store-credentials vérifie les identifiants auprès d'Apple.
        if mode == 'api':
            key = directory / ('AuthKey_' + os.environ['APPLE_API_KEY'].strip() + '.p8')
            key.write_bytes(decode_api_key(os.environ['APPLE_API_PRIVATE_KEY']))
            key.chmod(0o600)
            run(['xcrun', 'notarytool', 'store-credentials', NOTARY_PROFILE, '--key', str(key), '--key-id', os.environ['APPLE_API_KEY'].strip(), '--issuer', os.environ['APPLE_API_ISSUER'].strip(), '--keychain', str(keychain)])
            key.unlink()
        else:
            run(['xcrun', 'notarytool', 'store-credentials', NOTARY_PROFILE, '--apple-id', os.environ['APPLE_ID'], '--password', os.environ['APPLE_PASSWORD'], '--team-id', os.environ['APPLE_TEAM_ID'], '--keychain', str(keychain)])
        append_env('MACOS_SIGNING_KEYCHAIN', str(keychain))
        append_env('MACOS_SIGNING_TEAM_ID', os.environ['APPLE_TEAM_ID'].strip())
    append_env('MACOS_SIGNING_IDENTITY', identity)
    append_env('MACOS_NOTARIZE', 'true' if ready else 'false')
    if ready:
        voie = 'clé d\'API App Store Connect' if mode == 'api' else 'identifiant Apple'
        print(f'Signature Developer ID et notarisation activées (notarisation par {voie}).')
    elif mode == 'adhoc':
        print('Aucun secret Apple : signature ad hoc et vérification stricte, sans notarisation.')


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


def notary_credentials():
    credentials = ['--keychain-profile', NOTARY_PROFILE]
    keychain = os.environ.get('MACOS_SIGNING_KEYCHAIN', '')
    if keychain:
        credentials += ['--keychain', keychain]
    return credentials


def print_notary_log(submission, run=run):
    """Le journal d'Apple liste les fichiers refusés et la raison ; il ne contient aucun secret."""
    try:
        log = json.loads(run(['xcrun', 'notarytool', 'log', submission, *notary_credentials()], check=False) or '{}')
    except json.JSONDecodeError:
        print('Journal de notarisation illisible.')
        return
    print('Journal de notarisation : ' + str(log.get('statusSummary', 'sans résumé')))
    for issue in (log.get('issues') or [])[:50]:
        print(f"- {issue.get('severity', '?')} : {issue.get('path', '?')} : {issue.get('message', '?')}")


def submit(path, run=run):
    """Soumet à Apple et attend le verdict ; un refus imprime le journal puis échoue."""
    output = run(['xcrun', 'notarytool', 'submit', str(path), *notary_credentials(), '--wait', '--timeout', '60m', '--output-format', 'json'], check=False)
    try:
        result = json.loads(output or '{}')
    except json.JSONDecodeError:
        result = {}
    if result.get('status') != 'Accepted':
        if result.get('id'):
            print_notary_log(result['id'], run=run)
        raise RuntimeError(f'Notarisation refusée ou incomplète pour {Path(path).name} (statut : {result.get("status", "inconnu")}) ; aucun agrafage ni publication')
    return result.get('id')


def notarize(path, run=run):
    submit(path, run=run)
    run(['xcrun', 'stapler', 'staple', str(path)])
    run(['xcrun', 'stapler', 'validate', str(path)])


def check_distribution_signature(path, team, run=run):
    """Après notarisation : l'objet est signé Developer ID, par la bonne équipe, runtime renforcé."""
    details = run(['codesign', '--display', '--verbose=2', str(path)])
    if 'Authority=Developer ID Application:' not in details:
        raise RuntimeError(f'{Path(path).name} n\'est pas signé « Developer ID Application »')
    if team and f'TeamIdentifier={team}' not in details:
        raise RuntimeError(f'{Path(path).name} : Team ID inattendue')
    if Path(path).suffix == '.app' and 'runtime' not in details:
        raise RuntimeError(f'{Path(path).name} : runtime renforcé absent')
    for line in details.splitlines():
        if line.startswith(('Authority=', 'TeamIdentifier=', 'Timestamp=')):
            print(f'{Path(path).name} : {line}')


def check_updater_archive(archive, notarized, run=run):
    """L'archive de mise à jour doit contenir le bundle signé et, si notarisé, agrafé."""
    with tempfile.TemporaryDirectory(prefix='therese-updater-', dir=os.environ.get('RUNNER_TEMP')) as directory:
        run(['tar', '-xzf', str(archive), '-C', directory])
        apps = list(Path(directory).glob('*.app'))
        if len(apps) != 1:
            raise RuntimeError('L\'archive updater doit contenir exactement un bundle .app')
        run(['codesign', '--verify', '--deep', '--strict', '--verbose=2', str(apps[0])])
        if notarized:
            run(['xcrun', 'stapler', 'validate', str(apps[0])])
            run(['spctl', '--assess', '--type', 'execute', '--verbose', str(apps[0])])
    print(f'Archive updater vérifiée : {Path(archive).name}' + (' (signée, notarisée, ticket agrafé).' if notarized else ' (signature ad hoc).'))


def finish(bundle_dir):
    identity = os.environ.get('MACOS_SIGNING_IDENTITY', '-')
    notarized = os.environ.get('MACOS_NOTARIZE') == 'true'
    team = os.environ.get('MACOS_SIGNING_TEAM_ID', '')
    apps = list((bundle_dir / 'macos').glob('*.app'))
    if len(apps) != 1:
        raise ValueError('Un unique bundle .app est requis')
    app = apps[0]
    sign_tree(app, identity, run=run)
    # L'archive updater doit contenir exactement le bundle qui vient d'être signé.
    # Le DMG est reconstruit après la signature et l'agrafage du bundle.
    if notarized:
        archive = bundle_dir / 'notarization.zip'
        run(['ditto', '-c', '-k', '--keepParent', str(app), str(archive)])
        # Un ZIP n'est pas agrafable : soumettre, puis agrafer l'app.
        submit(archive, run=run)
        run(['xcrun', 'stapler', 'staple', str(app)])
        run(['xcrun', 'stapler', 'validate', str(app)])
        run(['spctl', '--assess', '--type', 'execute', '--verbose', str(app)])
        check_distribution_signature(app, team, run=run)
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
    if notarized:
        notarize(dmgs[0], run=run)
        run(['spctl', '--assess', '--type', 'open', '--context', 'context:primary-signature', '--verbose', str(dmgs[0])])
        check_distribution_signature(dmgs[0], team, run=run)
    archives = list((bundle_dir / 'macos').glob('*.app.tar.gz'))
    if len(archives) != 1:
        raise ValueError('Une unique archive updater macOS est requise')
    run(['tar', '-czf', str(archives[0]), '-C', str(app.parent), app.name])
    check_updater_archive(archives[0], notarized, run=run)
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
