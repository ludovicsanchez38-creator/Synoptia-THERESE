#!/usr/bin/env python3
"""Composition native CPython revue sur les octets publiés, jamais sur un nom.

Le catalogue est fermé : un nouveau build/ABI doit être rapproché et relu.
Les empreintes lient chaque fichier aux composants, versions et notices originales.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = 'licenses/cpython-components.lock.json'
MACOS_PACKAGE_URL = 'https://www.python.org/ftp/python/3.13.17/python-3.13.17-macos11.pkg'
MACOS_PACKAGE_SHA256 = '3053592af66128269efab37fe7851a4894920b27c442aeec99ce4d34d17c07e3'
WINDOWS_MSI = {
    'core': '592af28b25b8142111b3600c82792f778ffb522b12768170a205fb90e40c72e8',
    'lib': '7d047ae8b57857e33c3827fe77b052297e61bdab6b3fd4fecd343c3c30e3a8ff',
    'exe': '985e3ce8b3f0a432fdadfa5aacac506635816c5d24a36fd6222b9e390da279d5',
}


def windows_msi_url(package):
    return 'https://www.python.org/ftp/python/3.13.17/amd64/' + package + '.msi'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(root, item):
    path = root / item['path']
    if (Path(item['path']).is_absolute() or '..' in Path(item['path']).parts or
            not path.resolve().is_relative_to(root.resolve())):
        raise ValueError('Chemin de preuve CPython invalide')
    raw = path.read_bytes()
    if sha(raw) != item['sha256']:
        raise ValueError('Preuve/notice CPython modifiée : ' + item['path'])
    return raw


def notice_files(catalog):
    notices = list(catalog['base_notices'])
    notices += [n for c in catalog['components'] + catalog['macos_components'] + catalog['windows_components']
                for n in c['notices']]
    return {n['path']: n for n in notices}.values()


def validate(catalog, root):
    evidence = json.loads(checked(root, catalog['evidence']))
    if (catalog.get('schema') != 1 or catalog.get('version') != '3.13.17' or
            catalog['version'] != evidence['version'] or
            catalog['upstream'] != evidence['upstream'] or
            catalog['components'] != evidence['components'] or
            catalog['files'] != [{k: v for k, v in f.items()
                                  if k not in ('incorporation_evidence', 'imported_symbols')}
                                 for f in evidence['files']]):
        raise ValueError('Composition CPython différente de la preuve relue')
    ids = {c['id'] for c in catalog['components']}
    hashes = {f['sha256'] for f in catalog['files']}
    if len(ids) != len(catalog['components']) or len(hashes) != len(catalog['files']):
        raise ValueError('Composant/fichier CPython dupliqué')
    used = set()
    for f in evidence['files']:
        if (not re.fullmatch('[0-9a-f]{64}', f['sha256']) or
                set(f['components']) != set(f['incorporation_evidence']) or
                not set(f['components']) <= ids):
            raise ValueError('Liaison composant/fichier CPython absente')
        used.update(f['components'])
    if used != ids:
        raise ValueError('Composant CPython sans preuve binaire')
    mac = json.loads(checked(root, catalog['macos_evidence']))
    if (mac.get('schema') != 1 or mac.get('version') != catalog['version'] or
            mac.get('upstream') != catalog['upstream'] or
            mac.get('binary_package_url') != MACOS_PACKAGE_URL or
            mac.get('binary_package_sha256') != MACOS_PACKAGE_SHA256 or
            mac.get('components') != catalog['macos_components'] or
            catalog['macos_files'] != [{k: v for k, v in f.items()
                                       if k not in ('incorporation_evidence', 'imported_symbols')}
                                      for f in mac['files']]):
        raise ValueError('Composition CPython macOS différente de la preuve relue')
    mac_ids = {c['id'] for c in catalog['macos_components']}
    if (len(mac_ids) != len(catalog['macos_components']) or mac_ids & ids or
            len({f['sha256'] for f in mac['files']}) != len(mac['files']) or
            len({f['path'] for f in mac['files']}) != len(mac['files']) or
            len(mac['files']) != 59 or mac['excluded']):
        raise ValueError('Couverture CPython macOS ambiguë')
    mac_used = set()
    for f in mac['files']:
        member = ('Versions/3.13/' + f['path'].removeprefix('Python.framework/Versions/3.13/')
                  if f['path'].startswith('Python.framework/Versions/3.13/') else
                  'Versions/3.13/lib/' + f['path'])
        if (f['platform'] != 'macOS' or f['name'] != Path(f['path']).name or
                f['binary_member'] != member or not re.fullmatch('[0-9a-f]{64}', f['sha256']) or
                f['size'] <= 0 or set(f['components']) != set(f['incorporation_evidence']) or
                not set(f['components']) <= ids | mac_ids):
            raise ValueError('Liaison composant/fichier CPython macOS absente')
        for proof in f['incorporation_evidence'].values():
            if not proof['defined_symbols'] or any('(undefined)' in s for s in proof['defined_symbols']):
                raise ValueError('Définition Mach-O absente')
        mac_used.update(set(f['components']) & mac_ids)
    if mac_used != mac_ids:
        raise ValueError('Composant CPython macOS sans preuve binaire')
    win = json.loads(checked(root, catalog['windows_evidence']))
    packages = win.get('binary_packages', [])
    if (win.get('schema') != 1 or win.get('version') != catalog['version'] or
            win.get('upstream') != catalog['upstream'] or
            {p['id']: (p['url'], p['sha256']) for p in packages} !=
            {key: (windows_msi_url(key), value) for key, value in WINDOWS_MSI.items()} or
            len(packages) != 3 or win.get('components') != catalog['windows_components'] or
            catalog['windows_files'] != [{k: v for k, v in f.items()
                                          if k not in ('incorporation_evidence', 'imported_symbols', 'pe_observation')}
                                         for f in win['files']] or win['excluded']):
        raise ValueError('Composition CPython Windows différente de la preuve relue')
    win_ids = {c['id'] for c in catalog['windows_components']}
    if (len(win_ids) != len(catalog['windows_components']) or win_ids & (ids | mac_ids) or
            len(win['files']) != 21 or len({f['sha256'] for f in win['files']}) != 21 or
            len({f['path'] for f in win['files']}) != 21):
        raise ValueError('Couverture CPython Windows ambiguë')
    win_used = set()
    for f in win['files']:
        package = ('core' if f['name'] in ('python313.dll', 'python3.dll') else 'lib')
        member = ('python.dll' if f['name'] == 'python313.dll' else
                  'python_stable.dll' if f['name'] == 'python3.dll' else
                  f['name'].replace('-', '_') if f['name'].endswith('.dll') else f['name'])
        if (f['platform'] != 'Windows' or f['path'] != f['name'] or
                f['binary_package_url'] != windows_msi_url(package) or
                f['binary_package_sha256'] != WINDOWS_MSI[package] or
                f['binary_member'] != member or f['size'] <= 0 or
                not re.fullmatch('[0-9a-f]{64}', f['sha256']) or
                set(f['components']) != set(f['incorporation_evidence']) or
                not set(f['components']) <= ids | mac_ids | win_ids or
                not f['pe_observation'].get('value')):
            raise ValueError('Liaison composant/fichier CPython Windows absente')
        for proof in f['incorporation_evidence'].values():
            source = proof['build_source']
            binary = proof['binary_observation']
            if (not source['path'].startswith('PCbuild/') or
                    not re.fullmatch('[0-9a-f]{64}', source['sha256']) or
                    source['line'] <= 0 or not source['declaration'] or
                    binary['kind'] not in {'ascii', 'utf16le', 'export'} or not binary['value']):
                raise ValueError('Preuve de composition PE absente')
        win_used.update(set(f['components']) & win_ids)
    if win_used != win_ids:
        raise ValueError('Composant CPython Windows sans preuve binaire')
    for c in catalog['components'] + catalog['macos_components'] + catalog['windows_components']:
        if not c['version'] or not c['license'] or not c['notices']:
            raise ValueError('Version/licence/notice CPython absente')
    for notice in notice_files(catalog):
        checked(root, notice)
    return catalog


def load(root=ROOT):
    return validate(json.loads((root / CATALOG).read_text(encoding='utf-8')), root)


def identify(digest, platform, catalog):
    row = next((f for f in catalog['files'] + catalog['macos_files'] + catalog['windows_files']
                if f['sha256'] == digest and f['platform'] == platform), None)
    if row is None:
        return None
    components = [c for c in catalog['components'] + catalog['macos_components'] + catalog['windows_components']
                  if c['id'] in row['components']]
    licenses = ['PSF-2.0', *sorted({c['license'] for c in components} - {'PSF-2.0'})]
    return {'origin': 'CPython@' + catalog['version'], 'license': ' AND '.join(licenses),
            'cpython_sha256': digest,
            'components': [{k: c[k] for k in ('id', 'name', 'version', 'license', 'notices')}
                           for c in components]}


def verify_record(record, platform, catalog):
    digest = record['sha256'] if platform == 'Linux' else record.get('source_sha256', record['sha256'])
    expected = identify(digest, platform, catalog)
    if expected is None:
        if record.get('origin', '').startswith(('CPython@', 'system:CPython@')) or 'cpython_sha256' in record:
            raise ValueError('Binaire CPython hors catalogue')
        return
    if (any(record.get(k) != v for k, v in expected.items()) or
            record.get('source_sha256', digest) != digest or
            (platform == 'Linux' and record['sha256'] != expected['cpython_sha256'])):
        raise ValueError('Composants/licences CPython absents ou différents de la preuve')


def render(root=ROOT, catalog=None):
    catalog = catalog if catalog is not None else load(root)
    lines = ['Composants tiers incorporés à CPython ' + catalog['version'],
             'Provenance : ' + catalog['upstream']['url'],
             'SHA-256 archive CPython : ' + catalog['upstream']['sha256'],
             'Catalogue fermé aux octets relus ; versions sans numéro amont : révision CPython indiquée.',
             'Les notices originales ci-dessous sont conservées sans modification.', '']
    for c in catalog['components'] + catalog['macos_components'] + catalog['windows_components']:
        lines += [c['name'] + ' — ' + c['version'], 'Licence : ' + c['license']]
        for f in catalog['files'] + catalog['macos_files'] + catalog['windows_files']:
            if c['id'] in f['components']:
                lines += ['Incorporé dans : ' + f['path'], 'SHA-256 : ' + f['sha256']]
        lines += ['Notices : ' + ', '.join(n['path'] for n in c['notices']), '']
    for n in sorted(notice_files(catalog), key=lambda n: n['path']):
        lines += ['=' * 72, n['path'], 'Source : ' + n['upstream']['url'],
                  'SHA-256 notice : ' + n['sha256'], checked(root, n).decode('utf-8').replace('\r\n', '\n'), '']
    return '\n'.join(lines)


def require_notices(root, catalog):
    # Comparer aussi la composition rendue, pas seulement une empreinte auto-déclarée.
    if render(root, catalog).encode() not in (root / 'THIRD_PARTY_LICENSES').read_bytes():
        raise ValueError('Notices des composants CPython absentes ou périmées')


def verify_sources(archive_path, root=ROOT):
    """Rejouer l'extraction des notices depuis l'archive amont exacte, sans exécuter."""
    catalog = load(root)
    evidence = json.loads(checked(root, catalog['evidence']))
    with archive_path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if digest != catalog['upstream']['sha256']:
        raise ValueError('Archive source CPython différente du tag relu')
    sources = {}
    with tarfile.open(archive_path) as archive:
        for member in archive:
            name = member.name.removeprefix('cpython-3.13.17/')
            if member.isfile() and name in evidence['source_files']:
                raw = archive.extractfile(member).read()
                ref = evidence['source_files'][name]
                if name in sources or sha(raw) != ref['sha256'] or len(raw) != ref['size']:
                    raise ValueError('Source CPython différente : ' + name)
                sources[name] = raw
    if set(sources) != set(evidence['source_files']):
        raise ValueError('Source CPython manquante')
    by_url = {ref['url']: sources[name] for name, ref in evidence['source_files'].items()}
    count = 0
    for n in notice_files(catalog):
        if n['upstream']['url'] not in by_url:
            continue  # CC0 complet : texte SPDX séparé, empreinté dans le catalogue.
        raw = by_url[n['upstream']['url']]
        if n['extraction'] != 'whole file':
            start, end = n['extraction']['start'].encode(), n['extraction']['end'].encode()
            begin = raw.index(start)
            raw = raw[begin:raw.index(end, begin) + len(end)]
        if raw != checked(root, n):
            raise ValueError('Notice CPython différente du texte amont : ' + n['path'])
        count += 1
    return len(sources), count


def verify_deb(path, root=ROOT):
    """Rapprochement sans installation/exécution du paquet historique exact."""
    catalog = load(root)
    evidence = json.loads(checked(root, catalog['evidence']))
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if digest != evidence['published_deb_sha256']:
        raise ValueError('SHA-256 du .deb différent de la v0.82.0 relue')
    expected = {f['path']: f for f in catalog['files']}
    found = set()
    with subprocess.Popen(['dpkg-deb', '--fsys-tarfile', str(path)], stdout=subprocess.PIPE) as proc:
        with tarfile.open(fileobj=proc.stdout, mode='r|') as archive:
            for member in archive:
                name = member.name.removeprefix('./')
                if not member.isfile():
                    continue
                if '/python3.13/lib-dynload/' not in name and not name.endswith('/libpython3.13.so.1.0'):
                    continue
                raw = archive.extractfile(member).read()
                if (name not in expected or name in found or sha(raw) != expected[name]['sha256'] or
                        len(raw) != expected[name]['size']):
                    raise ValueError('Octets CPython différents du catalogue : ' + name)
                found.add(name)
        if proc.wait() != 0:
            raise ValueError('Lecture du .deb impossible')
    if found != set(expected):
        raise ValueError('Fichiers CPython manquants du .deb')
    return catalog, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['check', 'complement', 'verify-sources'])
    parser.add_argument('--deb', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--source-archive', type=Path)
    args = parser.parse_args()
    if args.command == 'verify-sources':
        if not args.source_archive:
            parser.error('--source-archive requis')
        count, notices = verify_sources(args.source_archive)
        print(f'{count} fichiers source amont vérifiés ; {notices} notices extraites identiques')
        catalog = load()
    elif args.command == 'complement':
        if not args.deb or not args.output:
            parser.error('--deb et --output requis')
        catalog, digest = verify_deb(args.deb)
        text = ('THÉRÈSE v0.82.0 — complément de notices CPython incorporées\n'
                'SHA-256 du .deb vérifié : ' + digest + '\n'
                'Lecture sans installation ni exécution. Complément local à soumettre à Ludo.\n'
                'Les bibliothèques liées dynamiquement sont couvertes par le complément système.\n\n' + render())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(text)
        print(f'Complément : {len(text.encode())} octets ; SHA-256 {sha(text.encode())}')
    else:
        catalog = load()
        require_notices(ROOT, catalog)
    print(f'{len(catalog["files"])} fichiers CPython Linux ; {len(catalog["macos_files"])} macOS ; '
          f'{len(catalog["windows_files"])} Windows ; '
          f'{len(catalog["components"])} composants Linux ; {len(catalog["macos_components"])} macOS ; '
          f'{len(catalog["windows_components"])} Windows ; '
          f'{len(list(notice_files(catalog)))} notices originales')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
