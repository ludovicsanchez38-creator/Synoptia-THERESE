#!/usr/bin/env python3
"""Active la signature uniquement lorsque tous les secrets Microsoft sont présents."""
import json
import os
import sys
from pathlib import Path

SECRETS = ('AZURE_TENANT_ID', 'AZURE_CLIENT_ID', 'AZURE_CLIENT_SECRET', 'AZURE_SIGNING_ENDPOINT', 'AZURE_SIGNING_ACCOUNT', 'AZURE_CERTIFICATE_PROFILE')


def configuration(values, script):
    enabled = all(values.get(name) for name in SECRETS)
    overlay = {'bundle': {'windows': {'signCommand': {'cmd': 'pwsh', 'args': ['-NoProfile', '-NonInteractive', '-File', str(script), '%1']}}}} if enabled else {}
    return enabled, overlay


def diagnostic(values):
    """(message d'annotation ou None, refus) ; seuls les NOMS des secrets apparaissent."""
    present = [name for name in SECRETS if values.get(name)]
    strict = values.get('SIGNATURE_OBLIGATOIRE', '').strip().lower() == 'true'
    if len(present) == len(SECRETS):
        return None, False
    if present:
        missing = ', '.join(name for name in SECRETS if name not in present)
        message = f'Secrets Microsoft incomplets, il manque : {missing}.'
        return (message + (' SIGNATURE_OBLIGATOIRE=true : release refusée.' if strict else ' Build Windows non signé.')), strict
    if strict:
        return 'SIGNATURE_OBLIGATOIRE=true mais aucun secret Microsoft : release refusée.', True
    return None, False


if __name__ == '__main__':
    message, refuse = diagnostic(os.environ)
    if refuse:
        print(message, file=sys.stderr)
        sys.exit(1)
    if message:
        print('::warning title=Signature Windows::' + message)
    root = Path(__file__).resolve().parents[1]
    enabled, overlay = configuration(os.environ, root / 'scripts/sign_windows.ps1')
    (root / 'src/frontend/src-tauri/signing-ci.conf.json').write_text(json.dumps(overlay), encoding='utf-8')
    with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as stream:
        stream.write('enabled=' + str(enabled).lower() + '\n')
    print('Artifact Signing activé pour les fichiers accessibles.' if enabled else 'Secrets Microsoft absents ou incomplets : build non signé conservé.')
    print('LIMITATION : DLL/.pyd du moteur onefile inaccessibles à Artifact Signing ; migration Windows onedir nécessaire avant de revendiquer une signature complète.')
