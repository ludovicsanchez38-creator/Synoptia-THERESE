"""Preuve hors réseau d'une absence de titulaire, sur des archives intégrales.

Les archives sont versionnées : chaque contrôle relit TOUS leurs fichiers, sans
extraction ni exécution. Les occurrences sans portée sur la crate restent visibles.
"""
from __future__ import annotations

import hashlib
import io
import json
import posixpath
import re
import tarfile
import tomllib
from copy import deepcopy
from functools import lru_cache
from pathlib import Path

STATUS = 'no-holder-named-upstream'
# Relecture indépendante du 29/10/2026 : ces neuf triplets uniquement.
OBJC2_COMMIT = '7b1abfd750a2cacaea71d6a56ecfb83cb7de560b'
OBJC2_TREE_SHA256 = 'a6685e9b30da4c2b9ed807e8344d7248447daf1d5ab5b7af4fa3755545f96a4d'
ALLOWED_ABSENCES = {
    ('objc2-app-kit', '0.3.2', OBJC2_COMMIT): OBJC2_TREE_SHA256,
    ('objc2-core-foundation', '0.3.2', OBJC2_COMMIT): OBJC2_TREE_SHA256,
    ('objc2-core-graphics', '0.3.2', OBJC2_COMMIT): OBJC2_TREE_SHA256,
    ('objc2-foundation', '0.3.2', OBJC2_COMMIT): OBJC2_TREE_SHA256,
    ('objc2-io-surface', '0.3.2', OBJC2_COMMIT): OBJC2_TREE_SHA256,
    ('objc2-osa-kit', '0.3.2', OBJC2_COMMIT): OBJC2_TREE_SHA256,
    ('objc2-quartz-core', '0.3.2', OBJC2_COMMIT): OBJC2_TREE_SHA256,
    ('objc2-ui-kit', '0.3.2', OBJC2_COMMIT): OBJC2_TREE_SHA256,
    ('objc2-web-kit', '0.3.2', OBJC2_COMMIT): OBJC2_TREE_SHA256,
}
PATTERNS = {
    'Copyright': r'Copyright',
    '©': r'©\s*(?:[12][0-9]{3}|[A-Za-z][A-Za-z .-]+)',
    '(c)/(C) année ou nom': r'\([cC]\)\s*(?:[12][0-9]{3}|[A-Za-z][A-Za-z .-]+)',
    'SPDX-FileCopyrightText': r'SPDX-FileCopyrightText',
    'Authors': r'\bAuthors\b',
    'Contributors/Maintainers': r'\b(?:Contributors|Maintainers)\b',
    'authors = (tous fichiers, dont Cargo.toml et Cargo.toml.orig)': r'\bauthors(?:\.workspace)?\s*=',
}
AUTHOR_FILE = re.compile(r'^(?:AUTHORS|CONTRIBUTORS|MAINTAINERS)(?:[._-].*)?$', re.I)
AUTHOR_HEADING = re.compile(
    r'^\s*(?:(?://[/!]?|/\*+|\*|#+)\s*)?(?:Authors|Contributors|Maintainers)\s*(?::|$)', re.I)


def sha(data):
    return hashlib.sha256(data).hexdigest()


@lru_cache(maxsize=32)
def members(raw):
    result = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:*') as archive:
        for item in archive:
            if item.isdir():
                continue
            if not item.isfile() and not item.issym():
                raise ValueError('Preuve contenant un membre non régulier')
            path = item.name.split('/', 1)[-1]
            if path in result:
                raise ValueError('Chemin dupliqué dans une preuve')
            result[path] = item.linkname.encode() if item.issym() else archive.extractfile(item).read()
    if not result:
        raise ValueError('Archive de preuve vide')
    return result


@lru_cache(maxsize=32)
def links(raw):
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:*') as archive:
        return {item.name.split('/', 1)[-1]: item.linkname for item in archive if item.issym()}


def scopes(path, symlinks):
    result = [path]
    for _ in range(len(symlinks) + 1):
        added = [posixpath.normpath(posixpath.join(posixpath.dirname(p), target))
                 for p, target in symlinks.items() if any(p.startswith(s + '/') or p == s for s in result)]
        if any(p.startswith('../') or p.startswith('/') for p in added):
            raise ValueError('Lien sortant de la preuve')
        new = sorted(set(added) - set(result))
        if not new:
            return result
        result.extend(new)
    raise ValueError('Liens de preuve cycliques')


def scan(files):
    hits = []
    for path, raw in sorted(files.items()):
        for number, line in enumerate(raw.decode('utf-8', errors='replace').splitlines(), 1):
            matched = [label for label, pattern in PATTERNS.items() if re.search(pattern, line, re.I)]
            if AUTHOR_FILE.fullmatch(posixpath.basename(path)) and line.strip():
                matched.append('Fichier d’auteurs')
            if matched:
                hits.append({'path': path, 'line': number, 'text': line, 'patterns': matched})
    # L'empreinte lie le relevé à tous les fichiers lus, y compris binaires/cachés.
    file_hashes = {path: sha(raw) for path, raw in sorted(files.items())}
    return {'files_read': len(files), 'files_sha256': file_hashes, 'hits': hits}


@lru_cache(maxsize=32)
def scanned(raw):
    return scan(members(raw))


def record(row, root, archive_path, tree_path, tree_url, commit):
    archive_raw, tree_raw = (root / archive_path).read_bytes(), (root / tree_path).read_bytes()
    crate, tree = members(archive_raw), members(tree_raw)
    vcs = json.loads(crate['.cargo_vcs_info.json'])
    return {'status': STATUS, 'package': row['id'], 'commit': commit,
            'archive': row['artifact'], 'archive_integrity': row['integrity'],
            'archive_file': archive_path, 'archive_sha256': sha(archive_raw),
            'tree_file': tree_path, 'tree_url': tree_url, 'tree_sha256': sha(tree_raw),
            'vcs_info_sha256': sha(crate['.cargo_vcs_info.json']),
            'path_in_vcs': vcs['path_in_vcs'], 'patterns': PATTERNS,
            'archive_scan': deepcopy(scanned(archive_raw)), 'tree_scan': deepcopy(scanned(tree_raw)),
            'tree_symlinks': links(tree_raw),
            'crate_tree_scopes': scopes(vcs['path_in_vcs'], links(tree_raw)),
            'notices': [{'path': n['path'], 'sha256': sha(n['text'].encode())} for n in row['notices']],
            'upstream_license_sha256': sha(tree['LICENSE.md']),
            'attributing_occurrences': {
                'archive': [h for h in scanned(archive_raw)['hits'] if applies(h, None, row['id'].split(':', 1)[1].split('@')[0])],
                'tree': [h for h in scanned(tree_raw)['hits'] if applies(h, scopes(vcs['path_in_vcs'], links(tree_raw)), row['id'].split(':', 1)[1].split('@')[0])]},
            'finding': "Zéro occurrence attribuant la crate. Les auteurs des autres crates et les copyrights de leurs outils ne s'étendent pas à cette crate. Le champ workspace.package.authors est une métadonnée distincte, non héritée ici."}


def applies(hit, scope, crate_name):
    path, text = hit['path'], hit['text']
    # Les noms d'API (NSCopyrightDocumentAttribute) ne sont pas des notices.
    if set(hit['patterns']) == {'Copyright'} and not re.search(r'\bcopyright\b', text, re.I):
        return False
    # « the authors » dans une phrase n'est pas une liste nominative.
    author_only = set(hit['patterns']) <= {'Authors', 'Contributors/Maintainers'}
    if author_only and not AUTHOR_HEADING.search(text):
        return False
    if scope is None:
        return True
    if path == 'Cargo.toml' and re.match(r'^\s*authors\s*=', text):
        return False  # métadonnée du workspace, vérifiée séparément, non héritée
    # Les autres crates/outils restent consignés dans tree_scan.hits.
    return (any(path.startswith(s + '/') or path == s
                for s in ([scope] if isinstance(scope, str) else scope))
            or '/' not in path or crate_name in text)


def verify(row, proof, root):
    try:
        identity = re.fullmatch(r'cargo:([^@/]+)@([^@/]+)', row['id'])
        if not identity:
            return False
        crate_name, version = identity.groups()
        reference = ALLOWED_ABSENCES.get((crate_name, version, proof['commit']))
        if reference is None or proof['tree_sha256'] != reference:
            return False
        if (proof['status'] != STATUS or proof['package'] != row['id'] or
                proof['archive'] != row['artifact'] or proof['archive_integrity'] != row['integrity'] or
                not re.fullmatch('[a-f0-9]{40}', proof['commit'])):
            return False
        for field in ('archive_file', 'tree_file'):
            path = Path(proof[field])
            if path.is_absolute() or '..' in path.parts:
                return False
        actual = record(row, root, proof['archive_file'], proof['tree_file'], proof['tree_url'], proof['commit'])
        if actual != proof or row['integrity'] != 'sha256:' + proof['archive_sha256']:
            return False
        crate = members((root / proof['archive_file']).read_bytes())
        tree = members((root / proof['tree_file']).read_bytes())
        vcs = json.loads(crate['.cargo_vcs_info.json'])
        if vcs['git']['sha1'] != proof['commit'] or not proof['tree_url'].endswith(proof['commit']):
            return False
        workspace = tomllib.loads(tree['Cargo.toml'].decode())['workspace']['package']
        for path in ('Cargo.toml', 'Cargo.toml.orig'):
            package = tomllib.loads(crate[path].decode())['package']
            package_version = package.get('version')
            if package_version == {'workspace': True}:
                package_version = workspace.get('version')
            if (package.get('name') != crate_name or package_version != version or
                    package.get('authors')):
                return False
        authors = workspace['authors']
        if authors != ['Mads Marquart <mads@marquart.dk>']:
            return False
        if not any(n['text'] == tree['LICENSE.md'].decode().strip() for n in row['notices']):
            return False
        crate_name = row['id'].split(':', 1)[1].split('@')[0]
        if any(applies(h, None, crate_name) for h in proof['archive_scan']['hits']):
            return False
        return not any(applies(h, proof['crate_tree_scopes'], crate_name) for h in proof['tree_scan']['hits'])
    except (KeyError, ValueError, OSError, tarfile.TarError, TypeError):
        return False


def accepted(row, sources, root):
    return row.get('attribution_status') == STATUS and any(
        p.get('status') == STATUS and p.get('package') == row['id'] and verify(row, p, root)
        for p in sources)


def statement(row, sources):
    proof = next(p for p in sources if p.get('status') == STATUS and p.get('package') == row['id'])
    return ("Aucun titulaire n'est nommé par le projet amont au commit " + proof['commit'] +
            '. Projet objc2, auteur déclaré du workspace : Mads Marquart.')
