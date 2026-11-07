#!/usr/bin/env python3
"""Composants natifs de l'installeur NSIS de Windows : catalogue relu, notices, preuves.

tauri-bundler 2.8.1 (tauri-cli 2.10.1) télécharge la chaîne NSIS 3.11 et
nsis_tauri_utils 0.5.3 et les vérifie par SHA-1 (windows/nsis/mod.rs). makensis
copie leurs greffons tels quels dans l'installeur et dans le désinstalleur
($PLUGINSDIR), et bâtit les deux exécutables sur le même stub, dont il ne
réécrit que les en-têtes de taille et les ressources (icône, manifeste, version).

Ce qui est prouvé, fermé par défaut :
- chaque greffon a le nom ET l'empreinte d'un fichier des archives épinglées ;
- le stub de l'installeur a le code (.text, .rdata, .data), le point d'entrée et
  les sections du stub NSIS amont, et seule .text est exécutable ;
- le désinstalleur reconstitué par 7-Zip porte le même stub que l'installeur,
  octet pour octet hors ressources, le drapeau de désinstallation, aucune donnée
  au-delà de la longueur déclarée, et ne contient que des greffons inventoriés.
Décision de Ludo du 07/11/2026 (carte val-2026-11-07-28).
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import struct
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = 'licenses/nsis-installer.lock.json'
FIRSTHEADER = b'\xef\xbe\xad\xdeNullsoftInst'
FH_FLAGS_UNINSTALL = 1
SCN_MEM_EXECUTE = 0x20000000
LICENSES = {'Zlib', 'MIT OR Apache-2.0', 'Zlib AND CPL-1.0 (module LZMA, exception de liaison NSIS)'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checked_notice(root, notice):
    name = notice['path']
    path = root / name
    if (Path(name).is_absolute() or '..' in Path(name).parts or not name.startswith('licenses/installer-nsis/')
            or not path.resolve().is_relative_to(root.resolve())):
        raise ValueError('Chemin de notice NSIS invalide')
    raw = path.read_bytes()
    if sha(raw) != notice['sha256']:
        raise ValueError('Notice NSIS modifiée : ' + name)
    return raw


def tauri_cli(root):
    lock = json.loads((root / 'src/frontend/package-lock.json').read_text(encoding='utf-8'))
    return lock['packages']['node_modules/@tauri-apps/cli']['version']


def validate(catalog, root=ROOT):
    if catalog.get('schema') != 1:
        raise ValueError('Schéma NSIS inconnu')
    # Une autre version de Tauri épingle peut-être une autre chaîne NSIS : relire avant.
    if catalog['tauri_cli'] != tauri_cli(root):
        raise ValueError('tauri-cli a changé : relire la chaîne NSIS épinglée par son bundler')
    archives = {a['id']: a for a in catalog['archives']}
    if len(archives) != len(catalog['archives']):
        raise ValueError('Archive NSIS en double')
    for archive in archives.values():
        if (not archive['url'].startswith('https://github.com/tauri-apps/')
                or not re.fullmatch('[0-9a-f]{40}', archive['sha1'])
                or not re.fullmatch('[0-9a-f]{64}', archive['sha256'])):
            raise ValueError('Archive NSIS sans provenance vérifiable : ' + archive['id'])
    notices = {n['id']: n for n in catalog['notices']}
    for notice in notices.values():
        checked_notice(root, notice)
    names = [p['name'] for p in catalog['plugins']]
    if len(set(names)) != len(names):
        raise ValueError('Greffon NSIS en double')
    for row in catalog['plugins'] + [catalog['stub']]:
        archive = archives.get(row['archive'])
        if (archive is None or row['license'] not in LICENSES or not row['notices']
                or any(n not in notices for n in row['notices'])):
            raise ValueError('Composant NSIS sans archive, licence ou notice relue : ' + row.get('name', 'stub'))
    for row in catalog['plugins']:
        if not re.fullmatch('[0-9a-f]{64}', row['sha256']):
            raise ValueError('Empreinte de greffon invalide : ' + row['name'])
        # Sans membre, l'archive téléchargée EST le greffon.
        if not row['member'] and row['sha256'] != archives[row['archive']]['sha256']:
            raise ValueError('Greffon différent de son archive : ' + row['name'])
        if row['member'] and Path(row['member']).name != row['name']:
            raise ValueError('Greffon et membre d’archive de noms différents : ' + row['name'])
        if 'nsis_tauri_utils' in row['notices'] and row['license'] != 'MIT OR Apache-2.0':
            raise ValueError('Licence de nsis_tauri_utils différente de la notice')
    stub = catalog['stub']
    if (stub['code_sections'] != ['.text', '.rdata', '.data'] or not re.fullmatch('[0-9a-f]{64}', stub['code_sha256'])
            or stub['sections'][:3] != stub['code_sections']):
        raise ValueError('Stub NSIS sans empreinte de code relue')
    return catalog


def load_catalog(root=ROOT):
    return validate(json.loads((root / CATALOG).read_text(encoding='utf-8')), root)


def plugin(catalog, name, digest):
    """Greffon admis : même nom et même empreinte qu'un fichier des archives épinglées."""
    row = next((p for p in catalog['plugins'] if p['name'] == name and p['sha256'] == digest), None)
    if row is None:
        return None
    origin = 'nsis:' + row['archive'] + ('!' + row['member'] if row['member'] else '')
    return {'sha256': digest, 'origin': origin, 'license': row['license']}


def firstheader(raw):
    """Premier en-tête NSIS aligné sur 512 octets, là où exehead le cherche."""
    index = raw.find(FIRSTHEADER)
    while index >= 0:
        offset = index - 4
        if offset > 0 and offset % 512 == 0 and len(raw) >= offset + 28:
            flags = int.from_bytes(raw[offset:offset + 4], 'little')
            length = int.from_bytes(raw[offset + 24:offset + 28], 'little')
            return offset, flags, length
        index = raw.find(FIRSTHEADER, index + 1)
    raise ValueError('En-tête NSIS introuvable')


def sections(stub):
    if stub[:2] != b'MZ':
        raise ValueError('Stub NSIS sans en-tête PE')
    header = int.from_bytes(stub[0x3c:0x40], 'little')
    if stub[header:header + 4] != b'PE\0\0':
        raise ValueError('Stub NSIS sans en-tête PE')
    count = int.from_bytes(stub[header + 6:header + 8], 'little')
    optional = int.from_bytes(stub[header + 20:header + 22], 'little')
    entry = int.from_bytes(stub[header + 24 + 16:header + 24 + 20], 'little')
    table = header + 24 + optional
    result = []
    for index in range(count):
        raw = stub[table + 40 * index:table + 40 * index + 40]
        if len(raw) != 40:
            raise ValueError('Table des sections du stub tronquée')
        virtual_size, virtual_address, raw_size, raw_pointer = struct.unpack('<IIII', raw[8:24])
        flags = int.from_bytes(raw[36:40], 'little')
        result.append({'name': raw[:8].rstrip(b'\0').decode('ascii', 'replace'), 'address': virtual_address,
                       'virtual_size': virtual_size, 'pointer': raw_pointer, 'size': raw_size, 'flags': flags})
    return entry, result


def verify_stub(stub, catalog):
    """Code, point d'entrée et sections du stub NSIS épinglé ; seule .text s'exécute."""
    expected = catalog['stub']
    entry, found = sections(stub)
    names = [s['name'] for s in found]
    if names != expected['sections']:
        raise ValueError('Sections du stub NSIS différentes de l’amont : ' + ', '.join(names))
    by_name = {s['name']: s for s in found}
    text = by_name['.text']
    if entry != expected['entry_point'] or not text['address'] <= entry < text['address'] + text['virtual_size']:
        raise ValueError('Point d’entrée du stub NSIS différent de l’amont')
    if [s['name'] for s in found if s['flags'] & SCN_MEM_EXECUTE] != ['.text']:
        raise ValueError('Section exécutable hors .text dans le stub NSIS')
    code = b''.join(stub[s['pointer']:s['pointer'] + s['size']] for s in (by_name[n] for n in expected['code_sections']))
    if sha(code) != expected['code_sha256']:
        raise ValueError('Code du stub NSIS différent de ' + expected['member'])
    return by_name['.rsrc']


def verify_installer_stub(installer_head, catalog):
    offset, flags, _ = firstheader(installer_head)
    if flags & FH_FLAGS_UNINSTALL:
        raise ValueError('L’installeur NSIS porte le drapeau de désinstallation')
    verify_stub(installer_head[:offset], catalog)
    return {'sha256': catalog['stub']['code_sha256'], 'origin': 'nsis:' + catalog['stub']['archive'] + '!'
            + catalog['stub']['member'] + ' (code)', 'license': catalog['stub']['license']}


def verify_uninstaller(installer_head, uninstaller, catalog):
    """Désinstalleur bâti sur le stub de l'installeur : seules les ressources diffèrent."""
    stub_end, _, _ = firstheader(installer_head)
    offset, flags, length = firstheader(uninstaller)
    if not flags & FH_FLAGS_UNINSTALL:
        raise ValueError('uninstall.exe sans drapeau de désinstallation NSIS')
    if offset != stub_end:
        raise ValueError('Stub du désinstalleur de taille différente de celui de l’installeur')
    if offset + length != len(uninstaller):
        raise ValueError('Données en trop ou manquantes après l’en-tête du désinstalleur')
    stub, own = installer_head[:stub_end], uninstaller[:offset]
    resources = verify_stub(stub, catalog)
    if verify_stub(own, catalog) != resources:
        raise ValueError('Ressources du désinstalleur placées autrement que dans l’installeur')
    start, end = resources['pointer'], resources['pointer'] + resources['size']
    if stub[:start] != own[:start] or stub[end:] != own[end:]:
        raise ValueError('Stub du désinstalleur différent de celui de l’installeur hors ressources')
    return {'sha256': sha(uninstaller), 'origin': 'nsis:stub de l’installeur + désinstalleur de makensis',
            'license': catalog['stub']['license']}


def render_notices(root=ROOT):
    catalog = load_catalog(root)
    archives = {a['id']: a for a in catalog['archives']}
    lines = ['Installeur Windows NSIS — composants de l’empaqueteur, catalogue relu et contrôlé au build',
             'Épinglés par ' + catalog['pinned_by'] + ' (tauri-cli ' + catalog['tauri_cli'] + ').',
             'Contrôle de chaque installeur : empreinte de chaque greffon, code du stub, désinstalleur.', '']
    for archive in catalog['archives']:
        lines += ['Archive ' + archive['id'] + ' : ' + archive['url'],
                  'SHA-1 (épinglé par Tauri) : ' + archive['sha1'], 'SHA-256 : ' + archive['sha256'], '']
    for row in catalog['plugins']:
        lines += ['$PLUGINSDIR/' + row['name'] + ' — ' + archives[row['archive']]['id']
                  + (' — ' + row['member'] if row['member'] else ''),
                  'Licence : ' + row['license'] + (' (notice MIT retenue)' if row['license'] == 'MIT OR Apache-2.0' else ''),
                  'SHA-256 : ' + row['sha256'], '']
    stub = catalog['stub']
    lines += ['Stub de l’installeur et du désinstalleur — ' + stub['member'],
              'Licence : ' + stub['license'],
              'Le module de décompression LZMA de NSIS relève de la Common Public License 1.0 ; ses auteurs',
              'permettent d’y lier du code sans le soumettre à cette licence (« SPECIAL EXCEPTION FOR LZMA',
              'COMPRESSION MODULE », texte complet ci-dessous). Le module est livré sans modification ; ses',
              'sources sont celles de NSIS 3.11 (nsis-3.11-src.tar.bz2) :',
              'https://sourceforge.net/projects/nsis/files/NSIS%203/3.11/',
              'SHA-256 du code (.text, .rdata, .data) : ' + stub['code_sha256'], '']
    for notice in catalog['notices']:
        text = checked_notice(root, notice).decode('utf-8').replace('\r\n', '\n').strip()
        lines += ['=' * 72, notice['path'] + ' (' + notice['source'] + ')', text, '']
    return '\n'.join(lines) + '\n'


def reread(root=ROOT):
    """Relecture en ligne : archives amont, SHA-1 de Tauri, membres et stub."""
    catalog = load_catalog(root)
    data = {}
    for archive in catalog['archives']:
        with urllib.request.urlopen(archive['url'], timeout=120) as response:
            raw = response.read()
        if hashlib.sha1(raw).hexdigest() != archive['sha1'] or sha(raw) != archive['sha256']:
            raise ValueError('Archive amont différente du catalogue : ' + archive['id'])
        data[archive['id']] = raw
    members = zipfile.ZipFile(io.BytesIO(data['nsis-3.11']))
    for row in catalog['plugins']:
        raw = members.read(row['member']) if row['member'] else data[row['archive']]
        if sha(raw) != row['sha256']:
            raise ValueError('Greffon amont différent du catalogue : ' + row['name'])
    stub = members.read(catalog['stub']['member'])
    if sha(stub) != catalog['stub']['member_sha256']:
        raise ValueError('Stub amont différent du catalogue')
    verify_stub(stub, catalog)
    for notice in catalog['notices']:
        if notice['source'].startswith('nsis-3.11.zip!'):
            if sha(members.read(notice['source'].split('!', 1)[1])) != notice['sha256']:
                raise ValueError('Notice amont différente : ' + notice['id'])
        else:
            with urllib.request.urlopen(notice['source'], timeout=60) as response:
                if sha(response.read()) != notice['sha256']:
                    raise ValueError('Notice amont différente : ' + notice['id'])
    return len(catalog['plugins'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['check', 'relire'])
    args = parser.parse_args()
    if args.command == 'relire':
        print(f'{reread()} greffons, le stub et les notices identiques à l’amont épinglé par Tauri')
    else:
        catalog = load_catalog()
        print(f'{len(catalog["plugins"])} greffons NSIS et le stub {catalog["stub"]["member"]} relus')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
