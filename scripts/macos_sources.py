#!/usr/bin/env python3
"""Rejouer hors réseau les notices et versions des sources macOS relues.

Les archives sont des données : aucun membre n'est extrait ni exécuté.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tarfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import system_libraries

ROOT = Path(__file__).resolve().parents[1]


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def extract_notice(raw: bytes, extraction: str | dict) -> bytes:
    if extraction == 'whole file':
        return raw
    anchor = extraction.get('anchor', '').encode()
    start = extraction['start'].encode()
    end = extraction['end'].encode()
    base = raw.index(anchor) + len(anchor) if anchor else 0
    begin = raw.index(start, base)
    finish = raw.index(end, begin + len(start)) + len(end)
    return raw[begin:finish]


def verify_archive(archive_path: Path, proof: dict, root: Path) -> int:
    """Comparer l'archive, les membres et les notices locales aux octets amont."""
    if archive_path.stat().st_size != proof['size']:
        raise ValueError('Taille de l’archive amont différente : ' + archive_path.name)
    with archive_path.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != proof['sha256']:
            raise ValueError('Archive amont différente : ' + archive_path.name)
    expected = {entry['path']: entry for entry in proof['members']}
    if len(expected) != len(proof['members']):
        raise ValueError('Membre amont dupliqué')
    seen = set()
    with tarfile.open(archive_path, 'r:gz') as archive:
        for member in archive:
            if member.name not in expected:
                continue
            if member.name in seen or not member.isfile():
                raise ValueError('Membre amont ambigu : ' + member.name)
            entry = expected[member.name]
            raw = archive.extractfile(member).read()
            if len(raw) != entry['size'] or sha(raw) != entry['sha256']:
                raise ValueError('Membre amont différent : ' + member.name)
            notice = entry['notice']
            local = system_libraries.checked_file(root, notice)
            if extract_notice(raw, entry['extraction']) != local:
                raise ValueError('Notice amont différente : ' + notice['path'])
            seen.add(member.name)
    if seen != set(expected):
        raise ValueError('Membre amont manquant : ' + ', '.join(sorted(set(expected) - seen)))
    return len(seen)


def verify_build_script(source_archive: Path, proof: dict) -> list[str]:
    if source_archive.stat().st_size != proof['archive_size']:
        raise ValueError('Taille de l’archive CPython différente')
    with source_archive.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != proof['archive_sha256']:
            raise ValueError('Archive CPython différente du tag relu')
    found = []
    with tarfile.open(source_archive, 'r:gz') as archive:
        for member in archive:
            if member.name == proof['member']:
                if found or not member.isfile():
                    raise ValueError('BuildScript CPython ambigu')
                raw = archive.extractfile(member).read()
                if len(raw) != proof['size'] or sha(raw) != proof['sha256']:
                    raise ValueError('BuildScript CPython différent du tag relu')
                found.append(raw.decode('utf-8').splitlines())
    if len(found) != 1:
        raise ValueError('BuildScript CPython absent')
    return found[0]


def verify_sources(source_dir: Path, cpython_archive: Path, root: Path = ROOT) -> tuple[int, int]:
    catalog = system_libraries.load_catalog(root)
    mac = json.loads(system_libraries.checked_file(root, catalog['macos_evidence']))
    archives = mac['source_archives']
    if len(archives) != 4 or {a['id'] for a in archives} != {'xz', 'ncurses', 'sqlite', 'libmpdec'}:
        raise ValueError('Couverture des archives macOS différente de la preuve')
    cpython_notices = {n['path']: n for c in catalog['cpython']['macos_components']
                       for n in c['notices']}
    system_entries = {e['catalog_row']['notice']['path']: e for e in mac['libraries']}
    notices = {**cpython_notices, **{p: e['catalog_row']['notice']
                                     for p, e in system_entries.items()}}
    member_count = 0
    for record in archives:
        if Path(record['filename']).name != record['filename']:
            raise ValueError('Nom d’archive amont invalide')
        for member in record['members']:
            notice = member['notice']
            if notices.get(notice['path'], {}).get('sha256') != notice['sha256']:
                raise ValueError('Notice amont hors catalogue : ' + notice['path'])
            if notice['path'] in cpython_notices:
                declared = cpython_notices[notice['path']]
                upstream = declared['upstream']
                if (upstream['url'] != record['url'] or
                        upstream['archive_sha256'] != record['sha256'] or
                        upstream['member'] != member['path'].split('/', 1)[1] or
                        upstream['sha256'] != member['sha256'] or
                        upstream['size'] != member['size'] or
                        declared['extraction'] != member['extraction']):
                    raise ValueError('Provenance CPython macOS différente : ' + notice['path'])
            else:
                provenance = system_entries[notice['path']]['notice_provenance']
                if (provenance['archive_url'] != record['url'] or
                        provenance['archive_sha256'] != record['sha256'] or
                        provenance['member'] != member['path'] or
                        provenance['member_sha256'] != member['sha256'] or
                        provenance['size'] != member['size'] or
                        provenance['sha256'] != notice['sha256']):
                    raise ValueError('Provenance système macOS différente : ' + notice['path'])
        member_count += verify_archive(source_dir / record['filename'], record, root)
    lines = verify_build_script(cpython_archive, mac['cpython_build_source'])
    refs = [ref for c in catalog['cpython']['macos_components'] for ref in c['version_sources']]
    refs += [ref for entry in mac['libraries'] for ref in entry['version_sources']]
    if len(refs) != 6:
        raise ValueError('Provenance des versions macOS incomplète')
    by_id = {a['id']: a for a in archives}
    for ref in refs:
        source = mac['cpython_build_source']
        if any(ref[k] != source[v] for k, v in
               [('path', 'relative_member'), ('sha256', 'sha256'),
                ('size', 'size'), ('archive_sha256', 'archive_sha256')]) or ref['url'] != (
                    'https://raw.githubusercontent.com/python/cpython/v3.13.17/' + ref['path']):
            raise ValueError('Source de version macOS différente du tag CPython')
        first, last = ref['lines']
        if first < 1 or last > len(lines) or last < first:
            raise ValueError('Lignes de version macOS invalides')
        excerpt = '\n'.join(lines[first - 1:last])
        declaration = ref['declaration']
        if not all(value in excerpt for value in declaration.values()):
            raise ValueError('Déclaration de version macOS absente du BuildScript')
        archive_id = ref.get('source_archive')
        if archive_id:
            upstream = by_id[archive_id]
            if declaration['checksum'] != (upstream.get('md5') or upstream['sha256']):
                raise ValueError('Empreinte de source différente du BuildScript')
            if upstream.get('md5'):
                with (source_dir / upstream['filename']).open('rb') as stream:
                    if hashlib.file_digest(stream, 'md5').hexdigest() != upstream['md5']:
                        raise ValueError('MD5 XZ différent du BuildScript')
    return member_count, len(refs)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['verify-sources'])
    parser.add_argument('--source-directory', required=True, type=Path)
    parser.add_argument('--cpython-source-archive', required=True, type=Path)
    args = parser.parse_args()
    notices, versions = verify_sources(args.source_directory, args.cpython_source_archive)
    print(f'{notices} notices macOS rejouées depuis 4 archives ; '
          f'{versions} déclarations de version du BuildScript vérifiées')


if __name__ == '__main__':
    try:
        main()
    except (KeyError, ValueError, OSError, tarfile.TarError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
