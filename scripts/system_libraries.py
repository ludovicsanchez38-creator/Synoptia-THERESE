#!/usr/bin/env python3
"""Inventorier les octets natifs réellement livrés ; refuser une origine non revue.

Le catalogue est une preuve versionnée, jamais une liste de noms autorisés.
Une évolution du runner exige un nouveau rapprochement SHA-256 et une revue des
notices/sources. Aucune licence n'est déduite d'un SONAME.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import importlib.metadata
import importlib.machinery
import json
import os
import re
import subprocess
import sys
import sysconfig
import tarfile
import urllib.request
from pathlib import Path

import cpython_components

ROOT = Path(__file__).resolve().parents[1]
CATALOG = 'licenses/system-libraries.lock.json'
BUILD = '.work-release/system-libraries.json'
ANALYSIS = '.work-release/pyinstaller-origins.json'
KNOWN = {'GPL-3.0-or-later', 'LGPL-2.1-or-later', 'GPL-3.0-or-later WITH GCC-exception-3.1',
         'bzip2-1.0.6', 'Apache-2.0', 'MIT', 'LicenseRef-Public-Domain', 'X11',
         'BSD-3-Clause', 'Zlib', 'PSF-2.0'}
REVIEWED_LICENSES = {'readline': 'GPL-3.0-or-later', 'gdbm': 'GPL-3.0-or-later',
    'glibc': 'LGPL-2.1-or-later', 'gcc-12': 'GPL-3.0-or-later WITH GCC-exception-3.1',
    'bzip2': 'bzip2-1.0.6', 'openssl': 'Apache-2.0', 'libffi': 'MIT',
    'xz-utils': 'LicenseRef-Public-Domain', 'ncurses': 'X11', 'sqlite3': 'LicenseRef-Public-Domain',
    'util-linux': 'BSD-3-Clause', 'zlib': 'Zlib', 'CPython': 'PSF-2.0'}
MAGICS = {b'\x7fELF', b'\xfe\xed\xfa\xce', b'\xce\xfa\xed\xfe', b'\xfe\xed\xfa\xcf',
          b'\xcf\xfa\xed\xfe', b'\xca\xfe\xba\xbe', b'\xbe\xba\xfe\xca', b'\xca\xfe\xba\xbf'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def native(head):
    return head[:4] in MAGICS or head[:2] == b'MZ'


def known_license(value):
    return bool(value and not re.search(r'unknown|NOASSERTION|inconnue|TODO', value, re.I))


def local(root, name):
    path = root / name
    if Path(name).is_absolute() or '..' in Path(name).parts or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Chemin de preuve invalide')
    return path


def checked_file(root, item):
    path = local(root, item['path'])
    raw = path.read_bytes()
    if sha(raw) != item['sha256']:
        raise ValueError('Preuve/notice modifiée : ' + item['path'])
    return raw


def validate_catalog(catalog, root):
    if catalog.get('schema') != 1:
        raise ValueError('Schéma système inconnu')
    evidence = json.loads(checked_file(root, catalog['evidence']))
    originals = evidence['bibliotheques']
    rows = catalog['libraries']
    names = {r['name'] for r in rows}
    if len(names) != len(rows) or names != set(originals) | {'libpython3.13.so.1.0'}:
        raise ValueError('Couverture du catalogue différente de la preuve')
    for row in rows:
        if (row['license'] != REVIEWED_LICENSES.get(row['source_package']) or
                row['license'] not in KNOWN) or not re.fullmatch('[0-9a-f]{64}', row['sha256']):
            raise ValueError('Licence/empreinte système inconnue : ' + row['name'])
        checked_file(root, row['notice'])
        if row['name'] in originals:
            original = originals[row['name']]
            for key, old in [('sha256', 'sha256_dans_le_deb'), ('package', 'paquet'),
                             ('version', 'version'), ('source_package', 'source'),
                             ('source_version', 'version'), ('binary_package_sha256', 'deb_sha256'),
                             ('binary_member', 'fichier')]:
                if row[key] != original[old]:
                    raise ValueError('Identité système différente de la preuve : ' + row['name'])
            if row['binary_package_url'] != 'https://archive.ubuntu.com/ubuntu/' + original['deb']:
                raise ValueError('URL du paquet différente de la preuve')
        elif (row['package'], row['version'], row['sha256']) != (
                'CPython', '3.13.17', 'a2402bd49cbfaa23e9cdeb7dde5feed0c21f3d915a84ee8d909b9d9d6b75560c'):
            raise ValueError('Identité CPython différente du complément relu')
        needs_source = ('GPL' in row['license'] and 'WITH GCC-exception-3.1' not in row['license'])
        if row['source_required'] != needs_source:
            raise ValueError('Obligation de sources contradictoire : ' + row['name'])
        if needs_source and not any(s['package'] == row['source_package'] and
                                   s['version'] == row['source_version'] for s in catalog['sources']):
            raise ValueError('Sources système absentes : ' + row['name'])
    expected = [{'package': s['paquet_source'], 'version': s['version'], 'filename': s['fichier'],
                 'url': s['url'].replace('http:', 'https:'), 'sha256': s['sha256'], 'size': s['octets']}
                for s in evidence['sources']]
    if catalog['sources'] != expected:
        raise ValueError('Sources système différentes de la preuve (dsc/orig/correctifs/signatures requis)')


def load_catalog(root=ROOT):
    catalog = json.loads((root / CATALOG).read_text(encoding='utf-8'))
    validate_catalog(catalog, root)
    catalog['cpython'] = cpython_components.load(root)
    return catalog


def render_notices(root=ROOT):
    catalog = load_catalog(root)
    lines = ['Bibliothèques système — catalogue relu et contrôlé au build',
             'Les versions ci-dessous constituent un catalogue conservateur ; les fichiers effectivement',
             'embarqués sont dans system-libraries.json et dans les preuves de chaque installeur.',
             'Sources exactes : THERESE-sources-systeme-linux.tar.gz, jointe à la même release.',
             'Les trois composants readline, gdbm et glibc y incluent les correctifs de distribution.', '']
    notices = {}
    for row in catalog['libraries']:
        lines += [row['name'] + ' — ' + row['package'] + ' ' + row['version'],
                  'Distribution : ' + row['distribution'], 'Licence : ' + row['license'],
                  'SHA-256 : ' + row['sha256'], 'Source : ' + row['source_package'] + ' ' + row['source_version']]
        if 'GPL' in row['license']:
            lines.append('ATTENTION COPYLEFT' + (' — exception GCC Runtime Library 3.1' if 'WITH' in row['license'] else ' — sources jointes'))
        notices[row['notice']['path']] = checked_file(root, row['notice']).decode('utf-8')
    # Les copyright Debian renvoient parfois aux common-licenses du système.
    for filename in ('GPL-2.0.json', 'GPL-3.0.txt', 'LGPL-2.0.txt', 'LGPL-2.1.txt', 'GCC-exception-3.1.txt'):
        path = root / 'licenses/supplements' / filename
        raw = path.read_text(encoding='utf-8')
        notices['licence complète/' + filename] = json.loads(raw)['text'] if filename.endswith('.json') else raw
    for path, text in sorted(notices.items()):
        lines += ['', '=' * 72, path, text]
    return '\n'.join(lines) + '\n\n' + cpython_components.render(root, catalog['cpython'])


def assemble_sources(folder, root=ROOT, cache=None):
    catalog = load_catalog(root)
    folder.mkdir(parents=True, exist_ok=False)
    for item in catalog['sources']:
        cached = cache / item['filename'] if cache else None
        if cached and cached.is_file():
            raw = cached.read_bytes()
        else:
            with urllib.request.urlopen(item['url'], timeout=60) as response:
                raw = response.read()
        if sha(raw) != item['sha256'] or len(raw) != item['size']:
            raise ValueError('Source système altérée : ' + item['filename'])
        target = folder / 'sources' / item['filename']
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(raw)
    for item in [catalog['evidence'], *[r['notice'] for r in catalog['libraries']]]:
        target = folder / item['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(checked_file(root, item))
    for item in [catalog['cpython']['evidence'], *cpython_components.notice_files(catalog['cpython'])]:
        target = folder / item['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(cpython_components.checked(root, item))
    (folder / cpython_components.CATALOG).write_bytes((root / cpython_components.CATALOG).read_bytes())
    (folder / 'system-libraries.lock.json').write_bytes((root / CATALOG).read_bytes())
    (folder / 'THIRD_PARTY_LICENSES-systeme-linux.txt').write_text(render_notices(root), encoding='utf-8')
    (folder / 'LISEZMOI-SOURCES.txt').write_bytes((root / 'licenses/LISEZMOI-SOURCES.txt').read_bytes())
    return len(catalog['sources']), sum(i['size'] for i in catalog['sources'])


def scan_tree(directory):
    if not directory.is_dir():
        raise ValueError('Dossier de binaires absent')
    result = {}
    for path in sorted(directory.rglob('*')):
        if path.is_symlink():
            if not path.resolve().is_relative_to(directory.resolve()) or not path.exists():
                raise ValueError('Lien de bibliothèque hors dossier : ' + path.name)
            if path.is_dir():
                raise ValueError('Répertoire symbolique à inventorier explicitement : ' + path.name)
        if path.is_file():
            with path.open('rb') as f:
                head = f.read(4)
            if native(head):
                result[path.relative_to(directory).as_posix()] = file_sha(path)
    return result


def verify_files(actual, records):
    if set(actual) != set(records):
        raise ValueError('Bibliothèque absente de l’inventaire ou du paquet : ' +
                         ', '.join(sorted(set(actual) ^ set(records))))
    for name, digest in actual.items():
        record = records[name]
        if digest != record.get('sha256'):
            raise ValueError('Bibliothèque modifiée : ' + name)
        if not known_license(record.get('license')) or not record.get('origin'):
            raise ValueError('Bibliothèque sans licence/origine connue : ' + name)


def run(args):
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode:
        raise ValueError('Rapprochement impossible : ' + args[0])
    return proc.stdout.strip()


def dpkg_identity(path):
    # dpkg peut enregistrer /lib alors que realpath renvoie /usr/lib (usrmerge).
    candidates = [str(path), str(path.resolve())]
    candidates += [s.removeprefix('/usr') for s in list(candidates) if s.startswith('/usr/lib/')]
    for candidate in dict.fromkeys(candidates):
        try:
            owner = run(['dpkg-query', '-S', candidate]).splitlines()[0].rsplit(': ', 1)[0]
            data = run(['dpkg-query', '-W', '-f=${Package}\t${Version}\t${source:Package}\t${source:Version}', owner])
            fields = data.split('\t')
            if len(fields) == 4:
                return tuple(fields)
        except ValueError:
            pass
    raise ValueError('Bibliothèque sans paquet de distribution : ' + path.name)


def match_system(path, digest, catalog, platform):
    cpython = cpython_components.identify(digest, platform, catalog['cpython'])
    if cpython:
        return cpython
    rows = [r for r in catalog['libraries'] if r['sha256'] == digest and r['platform'] == platform]
    if not rows:
        raise ValueError('Bibliothèque système hors catalogue : ' + path.name + ' SHA-256 ' + digest)
    row = rows[0]
    if row['package'] != 'CPython':
        identity = dpkg_identity(path) if platform == 'Linux' else None
        if identity != (row['package'], row['version'], row['source_package'], row['source_version']):
            raise ValueError('Version du paquet différente du catalogue : ' + path.name)
    return {'origin': 'system:' + row['package'] + '@' + row['version'], 'license': row['license'],
            'source_package': row['source_package'], 'source_version': row['source_version'],
            'source_required': row['source_required'], 'catalog_sha256': row['sha256']}


def record_analysis(entries, root=ROOT):
    """Appelé par le spec APRÈS Analysis, avant les transformations de PyInstaller."""
    origins = {}
    for name, source, kind in entries:
        path = Path(source)
        if kind == 'SYMLINK' or not path.is_file():
            continue
        with path.open('rb') as f:
            if not native(f.read(4)):
                continue
        record = {'path': str(path.resolve()), 'sha256': file_sha(path)}
        if name in origins and origins[name] != record:
            raise ValueError('Origine native ambiguë : ' + name)
        origins[name] = record
    target = root / ANALYSIS
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(origins, indent=2) + '\n', encoding='utf-8')


def distribution_files():
    result = {}
    for dist in importlib.metadata.distributions():
        name = re.sub(r'[-_.]+', '-', dist.metadata['Name']).lower()
        for file in dist.files or []:
            path = Path(dist.locate_file(file)).resolve()
            if file.hash and file.hash.mode == 'sha256':
                digest = base64.urlsafe_b64decode(file.hash.value + '=' * (-len(file.hash.value) % 4)).hex()
                result[path] = (name, dist.version, digest)
    return result


def classify(source, catalog, packages, installed, platform):
    path = Path(source['path'])
    if file_sha(path) != source['sha256']:
        raise ValueError('Origine modifiée après Analysis : ' + path.name)
    cpython = cpython_components.identify(source['sha256'], platform, catalog['cpython'])
    if cpython:
        return cpython
    owned = installed.get(path.resolve())
    if owned:
        name, version, digest = owned
        if digest != source['sha256']:
            raise ValueError('Bibliothèque différente du RECORD : ' + name)
        key = f'python:{name}@{version}'
        # Les roues CPU sont verrouillées séparément du sdist torch.
        candidates = [r for r in packages if r['id'] == key or r['id'].startswith(key + '/')]
        if not candidates and name == 'torch' and version.endswith('+cpu'):
            key = f'python:torch@{version.removesuffix("+cpu")}'
            candidates = [r for r in packages if r['id'].startswith(key + '/wheel-')]
        if not candidates or any(not known_license(r.get('license')) for r in candidates):
            raise ValueError('Paquet natif hors verrou/licence : ' + key)
        return {'origin': key, 'license': ' ; '.join(sorted({r['license'] for r in candidates})),
                'record_sha256': digest}
    # Un nom de module, un suffixe ABI et une version ne prouvent pas la composition.
    # Seuls les octets rapprochés ci-dessus autorisent l'attribution CPython.
    stdlib = Path(sysconfig.get_path('stdlib')).resolve()
    cpython = next(r for r in catalog['libraries'] if r['package'] == 'CPython')
    runtime_version = '.'.join(map(str, sys.version_info[:3]))
    relative = path.resolve().relative_to(stdlib).as_posix() if path.resolve().is_relative_to(stdlib) else ''
    extension_names = {name + suffix for name in sys.stdlib_module_names
                       for suffix in importlib.machinery.EXTENSION_SUFFIXES}
    if (relative.startswith('lib-dynload/') and '/' not in relative.removeprefix('lib-dynload/')
            and Path(relative).name in extension_names and runtime_version == cpython['version']):
        raise ValueError('Extension CPython hors catalogue de composition : ' + path.name)
    return match_system(path, source['sha256'], catalog, platform)


def onefile(executable):
    from PyInstaller.archive.readers import CArchiveReader
    archive = CArchiveReader(str(executable))
    result = {}
    for name, entry in archive.toc.items():
        raw = archive.extract(name)
        if raw and native(raw[:4]):
            result[name] = sha(raw)
    if not result:
        raise ValueError('Aucun binaire dans le moteur onefile')
    return result


def build_inventory(platform, root=ROOT):
    catalog = load_catalog(root)
    cpython_components.require_notices(root, catalog['cpython'])
    origins = json.loads((root / ANALYSIS).read_text(encoding='utf-8'))
    packages = json.loads((root / 'licenses/inventory.json').read_text(encoding='utf-8'))['packages']
    installed = distribution_files()
    base = root / 'src/frontend/src-tauri/binaries'
    if platform == 'Linux':
        actual = scan_tree(base / 'backend-libs')
    else:
        candidates = [p for p in base.glob('backend-*') if p.is_file()]
        if len(candidates) != 1:
            raise ValueError('Un unique moteur est requis')
        actual = onefile(candidates[0])
    if not actual:
        raise ValueError('Aucun fichier natif à inventorier')
    records = {}
    failures = []
    by_source_hash = {}
    for source in origins.values():
        by_source_hash.setdefault(source['sha256'], source)
    for name, digest in actual.items():
        if platform == 'Linux' and name == 'backend':
            records[name] = {'sha256': digest, 'origin': 'THERESE/PyInstaller bootloader',
                             'license': 'GPL-2.0-or-later WITH Bootloader-exception'}
            continue
        key = name.removeprefix('_internal/')
        source = origins.get(key) or by_source_hash.get(digest)
        try:
            if source is None:
                raise ValueError('Binaire sans origine Analysis : ' + name)
            record = classify(source, catalog, packages, installed, platform)
            if platform == 'Linux' and digest != source['sha256']:
                raise ValueError('Octets Linux transformés après Analysis : ' + name)
            records[name] = {'sha256': digest, 'source_sha256': source['sha256'], **record}
        except ValueError as exc:
            failures.append(name + ' : ' + str(exc))
            records[name] = {'sha256': digest, 'license': 'UNKNOWN', 'origin': 'à rapprocher'}
            if platform == 'Linux' and source:
                try:
                    records[name]['candidate_dpkg'] = dpkg_identity(Path(source['path']))
                except ValueError:
                    pass
    if failures:
        draft = root / '.work-release/system-libraries-unreviewed.json'
        draft.write_text(json.dumps({'platform': platform, 'files': records, 'errors': failures},
                                    ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        raise ValueError('Inventaire incomplet, release refusée (system-libraries-unreviewed.json) :\n' +
                         '\n'.join(failures))
    verify_files(actual, records)
    manifest = {'schema': 1, 'platform': platform, 'catalog_sha256': file_sha(root / CATALOG),
                'cpython_catalog_sha256': file_sha(root / cpython_components.CATALOG),
                'notices_sha256': file_sha(root / 'THIRD_PARTY_LICENSES'), 'files': records}
    (root / BUILD).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{len(records)} fichiers natifs inventoriés ; {sum(r["origin"].startswith("system:") for r in records.values())} fichiers système.')
    return manifest


def load_build(root=ROOT):
    manifest = json.loads((root / BUILD).read_text(encoding='utf-8'))
    catalog = load_catalog(root)
    cpython_components.require_notices(root, catalog['cpython'])
    if (manifest.get('schema') != 1 or manifest.get('catalog_sha256') != file_sha(root / CATALOG)
            or manifest.get('cpython_catalog_sha256') != file_sha(root / cpython_components.CATALOG)
            or manifest.get('notices_sha256') != file_sha(root / 'THIRD_PARTY_LICENSES')):
        raise ValueError('Inventaire du build périmé')
    verify_files({n: r['sha256'] for n, r in manifest['files'].items()}, manifest['files'])
    for record in manifest['files'].values():
        cpython_components.verify_record(record, manifest['platform'], catalog['cpython'])
        if record['origin'].startswith('system:'):
            row = next((r for r in catalog['libraries'] if r['sha256'] == record.get('catalog_sha256')), None)
            if (row is None or record['license'] != row['license'] or
                    record.get('source_required') != row['source_required'] or
                    record.get('source_package') != row['source_package'] or
                    record.get('source_version') != row['source_version'] or
                    record['origin'] != 'system:' + row['package'] + '@' + row['version'] or
                    (manifest['platform'] == 'Linux' and record['sha256'] != row['sha256'])):
                raise ValueError('Entrée système différente du catalogue')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['check', 'inventory', 'assemble-sources'])
    parser.add_argument('folder', type=Path, nargs='?')
    parser.add_argument('--platform', choices=['Linux', 'macOS', 'Windows'])
    parser.add_argument('--cache', type=Path)
    args = parser.parse_args()
    if args.command == 'inventory':
        if not args.platform:
            parser.error('--platform requis')
        build_inventory(args.platform)
    elif args.command == 'assemble-sources':
        if not args.folder:
            parser.error('dossier requis')
        count, size = assemble_sources(args.folder, cache=args.cache)
        print(f'{count} ressources source système ; {size} octets vérifiés')
    else:
        data = load_catalog()
        cpython_components.require_notices(ROOT, data['cpython'])
        print(f'{len(data["libraries"])} bibliothèques système ; {len(data["sources"])} ressources source')
        print(f'{len(data["cpython"]["files"])} fichiers CPython ; {len(data["cpython"]["components"])} composants incorporés')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
