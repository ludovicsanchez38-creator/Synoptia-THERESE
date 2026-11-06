#!/usr/bin/env python3
"""Rejouer hors réseau les MSI python.org et les notices sources Windows.

Les MSI, CAB, archives tar et PE sont des données. Aucun binaire n'est lancé.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cpython_components
import macos_sources
import system_libraries

ROOT = Path(__file__).resolve().parents[1]
CFB_MAGIC = bytes.fromhex('d0cf11e0a1b11ae1')
END = 0xfffffffe
FREE = 0xffffffff


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def msi_cab(raw: bytes) -> bytes:
    """Lire le flux CAB du conteneur OLE MSI sans installer son contenu."""
    if raw[:8] != CFB_MAGIC or struct.unpack_from('<H', raw, 28)[0] != 0xfffe:
        raise ValueError('Conteneur MSI OLE invalide')
    sector_size = 1 << struct.unpack_from('<H', raw, 30)[0]
    if sector_size not in (512, 4096):
        raise ValueError('Taille de secteur MSI invalide')
    def sector(index: int) -> bytes:
        start = (index + 1) * sector_size
        chunk = raw[start:start + sector_size]
        if len(chunk) != sector_size:
            raise ValueError('Secteur MSI tronqué')
        return chunk
    difat = [x for x in struct.unpack_from('<109I', raw, 76) if x != FREE]
    following = struct.unpack_from('<I', raw, 68)[0]
    count = struct.unpack_from('<I', raw, 72)[0]
    for _ in range(count):
        values = struct.unpack('<' + 'I' * (sector_size // 4), sector(following))
        difat.extend(x for x in values[:-1] if x != FREE)
        following = values[-1]
    fat = []
    for index in difat:
        fat.extend(struct.unpack('<' + 'I' * (sector_size // 4), sector(index)))
    def chain(start: int) -> bytes:
        output = bytearray()
        visited = set()
        index = start
        while index != END:
            if index in visited or index >= len(fat) or len(visited) > len(fat):
                raise ValueError('Chaîne MSI circulaire ou invalide')
            visited.add(index)
            output.extend(sector(index))
            index = fat[index]
        return bytes(output)
    directory_sector = struct.unpack_from('<I', raw, 48)[0]
    directory = chain(directory_sector)
    candidates = []
    for offset in range(0, len(directory), 128):
        entry = directory[offset:offset + 128]
        if len(entry) != 128 or entry[66] != 2:
            continue
        name_size = struct.unpack_from('<H', entry, 64)[0]
        name = entry[:name_size - 2].decode('utf-16le') if 2 <= name_size <= 64 else ''
        size = struct.unpack_from('<Q', entry, 120)[0]
        if size < 4096:
            continue
        start = struct.unpack_from('<I', entry, 116)[0]
        data = chain(start)[:size]
        if data[:4] == b'MSCF':
            candidates.append((name, data))
    if len(candidates) != 1:
        raise ValueError('Flux CAB MSI absent ou ambigu')
    return candidates[0][1]


def verify_source_refs(source_archive: Path, refs: list[dict], expected_sha: str) -> int:
    if system_libraries.file_sha(source_archive) != expected_sha:
        raise ValueError('Archive source CPython différente du tag relu')
    by_path = {ref['path'] for ref in refs}
    found = {}
    with tarfile.open(source_archive, 'r:gz') as archive:
        for member in archive:
            name = member.name.removeprefix('cpython-3.13.17/')
            if name in by_path:
                if name in found or not member.isfile():
                    raise ValueError('Source de build CPython ambiguë : ' + name)
                found[name] = archive.extractfile(member).read()
    if set(found) != by_path:
        raise ValueError('Source de build CPython absente')
    for ref in refs:
        raw = found[ref['path']]
        lines = raw.decode('utf-8-sig').splitlines()
        if (sha(raw) != ref['sha256'] or len(raw) != ref['size'] or
                ref['archive_sha256'] != expected_sha or
                ref['url'] != 'https://raw.githubusercontent.com/python/cpython/v3.13.17/' + ref['path'] or
                ref['line'] < 1 or ref['line'] > len(lines) or
                ref['declaration'] not in lines[ref['line'] - 1]):
            raise ValueError('Déclaration du build Windows différente : ' + ref['path'])
    return len(by_path)


def exported_names(path: Path) -> tuple[set[str], set[str]]:
    output = subprocess.run(['xcrun', 'llvm-objdump', '-p', str(path)], capture_output=True,
                            text=True, check=True).stdout
    block = output.split('Export Table:', 1)[-1] if 'Export Table:' in output else ''
    exports = {m.group(1) for line in block.splitlines()
               if (m := re.fullmatch(r'\s*\d+\s+0x[0-9a-f]+\s+(\S+)\s*', line))}
    imports = set(re.findall(r'DLL Name: (\S+)', output))
    return exports, imports


def verify_observation(raw: bytes, exports: set[str], observation: dict) -> None:
    kind, value = observation['kind'], observation['value']
    if kind == 'export':
        good = value in exports
    elif kind in ('ascii', 'utf16le'):
        good = value.encode('ascii' if kind == 'ascii' else 'utf-16le') in raw
    else:
        good = False
    if not good:
        raise ValueError('Observation PE absente : ' + value)


def verify_sources(msi_dir: Path, source_dir: Path, cpython_source_archive: Path,
                   root: Path = ROOT) -> tuple[int, int, int]:
    catalog = system_libraries.load_catalog(root)
    cp = catalog['cpython']
    win = json.loads(system_libraries.checked_file(root, catalog['windows_evidence']))
    cpy = json.loads(cpython_components.checked(root, cp['windows_evidence']))
    if win['binary_packages'] != cpy['binary_packages']:
        raise ValueError('MSI système et CPython différents')
    system_rows = {x['catalog_row']['sha256']: x for x in win['libraries']}
    all_rows = {x['sha256']: x for x in cpy['files']}
    all_rows.update({h: x['catalog_row'] for h, x in system_rows.items() if h not in all_rows})
    if len(all_rows) != 27:
        raise ValueError('Couverture des 27 fichiers python.org différente')
    notices = {n['path']: n for n in cpython_components.notice_files(cp)}
    notices.update({r['notice']['path']: r['notice'] for r in catalog['windows_libraries']})
    cpy_notices = {n['path']: n for component in cp['windows_components'] for n in component['notices']}
    system_notices = {entry['catalog_row']['notice']['path']: entry
                      for entry in win['libraries']}
    archives = win['source_archives']
    if (len(archives) != 7 or {a['id'] for a in archives} !=
            {'bzip2', 'xz', 'zlib', 'mpdecimal', 'libffi', 'openssl', 'sqlite'}):
        raise ValueError('Archives sources Windows incomplètes')
    notice_count = 0
    for record in archives:
        for member in record['members']:
            n = member['notice']
            if notices.get(n['path'], {}).get('sha256') != n['sha256']:
                raise ValueError('Notice Windows hors catalogue : ' + n['path'])
            if n['path'] in cpy_notices:
                declared = cpy_notices[n['path']]
                upstream = declared['upstream']
                if (upstream['url'] != record['url'] or upstream['archive_sha256'] != record['sha256'] or
                        upstream['member'] != member['path'].split('/', 1)[1] or
                        upstream['sha256'] != member['sha256'] or upstream['size'] != member['size'] or
                        declared['extraction'] != member['extraction']):
                    raise ValueError('Provenance CPython Windows différente : ' + n['path'])
            if n['path'] in system_notices:
                provenance = system_notices[n['path']]['notice_provenance']
                if (provenance['archive_url'] != record['url'] or
                        provenance['archive_sha256'] != record['sha256'] or
                        provenance['member'] != member['path'] or
                        provenance['member_sha256'] != member['sha256'] or
                        provenance['size'] != member['size'] or
                        provenance['sha256'] != n['sha256']):
                    raise ValueError('Provenance système Windows différente : ' + n['path'])
        folder = source_dir / ('amont' if record['id'] == 'sqlite' else 'amont-win')
        notice_count += macos_sources.verify_archive(folder / record['filename'], record, root)
    refs = []
    for c in cp['windows_components']:
        refs.extend(c['version_sources'])
    for f in cpy['files']:
        refs.extend(proof['build_source'] for proof in f['incorporation_evidence'].values())
    for entry in win['libraries']:
        refs.extend(entry.get('version_sources', []))
    build = win['cpython_build_sources']
    if (build['archive_sha256'] != cp['upstream']['sha256'] or
            build['archive_size'] != cpython_source_archive.stat().st_size or
            any(build['files'].get(ref['path']) != {'sha256': ref['sha256'], 'size': ref['size']}
                for ref in refs)):
        raise ValueError('Sources de build Windows différentes de la preuve')
    source_count = verify_source_refs(cpython_source_archive, refs, cp['upstream']['sha256'])
    msi_count = 0
    with tempfile.TemporaryDirectory(prefix='windows-msi-') as directory:
        work = Path(directory)
        for package in win['binary_packages']:
            pkg = package['id']
            msi = msi_dir / package['filename']
            if msi.stat().st_size != package['size'] or system_libraries.file_sha(msi) != package['sha256']:
                raise ValueError('MSI python.org différent : ' + package['filename'])
            cab = work / (pkg + '.cab')
            cab.write_bytes(msi_cab(msi.read_bytes()))
            members = [f for f in all_rows.values() if
                       f['binary_package_url'] == package['url']]
            if pkg == 'exe':
                members.append({'binary_member': 'LICENSE.txt', 'sha256': win['package_notice']['sha256'],
                                'size': (root / win['package_notice']['path']).stat().st_size})
            for row in members:
                member = row['binary_member']
                proc = subprocess.run(['cabextract', '-p', '-F', member, str(cab)],
                                      capture_output=True, check=True)
                raw = proc.stdout
                if len(raw) != row['size'] or sha(raw) != row['sha256']:
                    raise ValueError('Membre MSI différent : ' + member)
                if member == 'LICENSE.txt':
                    section = win['package_notice']['section']
                    extraction = win['package_notice']['extraction']
                    first = raw.index(extraction['start'].encode())
                    last = raw.index(extraction['end'].encode(), first)
                    if raw[first:last] != system_libraries.checked_file(root, section):
                        raise ValueError('Section Microsoft différente du MSI')
                    continue
                msi_count += 1
                native = work / (pkg + '-' + member)
                native.write_bytes(raw)
                exports, imports = exported_names(native)
                if 'pe_observation' in row:
                    verify_observation(raw, exports, row['pe_observation'])
                    for proof in row['incorporation_evidence'].values():
                        verify_observation(raw, exports, proof['binary_observation'])
                else:
                    verify_observation(raw, exports, system_rows[row['sha256']]['version_observation'])
                expected = {n.lower() for n in row.get('needed', []) if not n.endswith(' (différé)')}
                if expected and not expected <= {n.lower() for n in imports}:
                    raise ValueError('Imports PE différents du relevé : ' + member)
    if msi_count != 27:
        raise ValueError('Nombre de membres MSI différent')
    return msi_count, notice_count, source_count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['verify-sources'])
    parser.add_argument('--msi-directory', required=True, type=Path)
    parser.add_argument('--source-directory', required=True, type=Path)
    parser.add_argument('--cpython-source-archive', required=True, type=Path)
    args = parser.parse_args()
    files, notices, sources = verify_sources(args.msi_directory, args.source_directory,
                                             args.cpython_source_archive)
    print(f'{files} membres MSI python.org ; {notices} notices amont ; '
          f'{sources} sources de build CPython vérifiés')


if __name__ == '__main__':
    try:
        main()
    except (KeyError, ValueError, OSError, subprocess.CalledProcessError, tarfile.TarError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
