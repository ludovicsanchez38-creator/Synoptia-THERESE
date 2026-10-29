#!/usr/bin/env python3
"""Notices reproductibles depuis les verrous et les archives amont, sans installation.

refresh télécharge les archives verrouillées, collecte leurs textes et versionne un
instantané. generate/check sont hors réseau et vérifient couverture et empreintes.
Aucun code des paquets téléchargés n'est exécuté, aucune archive n'est extraite.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import re
import sys
import tarfile
import tomllib
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from email.parser import Parser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCKS = ['package-lock.json', 'src/frontend/package-lock.json', 'src/frontend/src-tauri/Cargo.lock', 'uv.lock', 'licenses/native-components.lock.json', 'licenses/overrides.json', 'licenses/runtime-wheels.lock.json', 'licenses/attribution-sources.json']
INVENTORY = 'licenses/inventory.json'
OUTPUT = 'THIRD_PARTY_LICENSES'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def lock_digest(root, paths=LOCKS):
    if paths is LOCKS:
        overrides = json.loads((root / 'licenses/overrides.json').read_text(encoding='utf-8'))
        paths = paths + sorted({n['local_path'] for o in overrides.values()
                                for n in o['notices'] if 'local_path' in n})
    return digest(b''.join(p.encode() + b'\0' + (root / p).read_bytes() for p in paths))


def copyleft(text):
    # La première ligne contient l'expression de licence déclarée. Dans les
    # textes, reconnaître les en-têtes, pas les renvois à l'AGPL dans la GPL.
    first = text.split('\n', 1)[0].upper()
    found = set(re.findall(r'(?<![A-Z])(AGPL|LGPL|GPL)(?:[-\s\d]|$)', first))
    headings = {
        'AGPL': r'GNU AFFERO GENERAL PUBLIC LICENSE',
        'LGPL': r'GNU (?:LESSER|LIBRARY) GENERAL PUBLIC LICENSE',
        'GPL': r'GNU GENERAL PUBLIC LICENSE',
    }
    for family, heading in headings.items():
        if re.search(r'^\s*' + heading + r'\s*$', text, re.I | re.M):
            found.add(family)
    return sorted(found)


def is_notice(name):
    p = Path(name)
    return bool(re.match(r'^(licen[sc]e|copying|copyright|notice|authors)([._-]|$)', p.name, re.I) or
                any(part.lower() in ('licenses', 'licences', 'license_files') for part in p.parts[:-1])) and p.suffix.lower() not in ('.py', '.rs', '.js', '.c', '.h', '.png', '.svg')


def locked_packages(root):
    rows = {}
    for lock in LOCKS[:2]:
        entries = json.loads((root / lock).read_text(encoding='utf-8'))['packages']
        for path, p in entries.items():
            if not path or p.get('link'):
                continue
            name = p.get('name') or path.split('node_modules/')[-1]
            key = f"npm:{name}@{p['version']}"
            archive = p
            if 'resolved' not in p and p.get('inBundle'):
                parent = path.rsplit('/node_modules/', 1)[0]
                archive = entries[parent]
                key += '/bundled-' + parent.split('node_modules/')[-1]
            row = {'id': key, 'artifact': archive['resolved'], 'integrity': archive['integrity'], 'license': p.get('license', '')}
            if key in rows and rows[key]['integrity'] != row['integrity']:
                raise ValueError(f'Archives contradictoires : {key}')
            rows[key] = row
    for p in tomllib.loads((root / LOCKS[2]).read_text(encoding='utf-8'))['package']:
        if 'source' not in p:
            continue
        if not p['source'].startswith('registry+') or not p.get('checksum'):
            raise ValueError(f"Source Cargo non gérée : {p['name']}")
        key = f"cargo:{p['name']}@{p['version']}"
        rows[key] = {'id': key, 'artifact': f"https://static.crates.io/crates/{p['name']}/{p['name']}-{p['version']}.crate", 'integrity': 'sha256:' + p['checksum'], 'license': ''}
    for p in tomllib.loads((root / LOCKS[3]).read_text(encoding='utf-8'))['package']:
        source = p.get('source', {})
        if source.get('editable') == '.' or source.get('virtual') == '.':
            continue  # Le projet lui-même, pas une dépendance tierce.
        if 'registry' not in source:
            raise ValueError(f"Source Python non gérée : {p['name']}")
        archive = p.get('sdist') or min(p.get('wheels', []), key=lambda w: w.get('size', sys.maxsize))
        key = f"python:{p['name']}@{p['version']}"
        rows[key] = {'id': key, 'artifact': archive['url'], 'integrity': archive['hash'], 'license': ''}
        # Les roues de ces composants portent aussi les licences des bibliothèques
        # natives redistribuées (FFmpeg/x264, espeak-ng, OpenBLAS, etc.). Union des
        # trois plateformes livrées ; les variantes CUDA ne sont pas embarquées.
        if p['name'] in ('av', 'piper-tts', 'numpy', 'scipy', 'ctranslate2', 'onnxruntime', 'pillow', 'cryptography', 'sqlcipher3'):
            candidates = [w for w in p.get('wheels', []) if re.search(r'(cp313|abi3|py3)', w['url']) and re.search(r'(win_amd64|macosx.*arm64|manylinux.*x86_64)', w['url'])]
            platforms = {}
            for w in candidates:
                platform = 'windows' if 'win_amd64' in w['url'] else 'macos' if 'macosx' in w['url'] else 'linux'
                platforms.setdefault(platform, w)
            for platform, wheel in platforms.items():
                k = key + '/wheel-' + platform
                rows[k] = {'id': k, 'artifact': wheel['url'], 'integrity': wheel['hash'], 'license': ''}
    for row in (json.loads((root / 'licenses/native-components.lock.json').read_text(encoding='utf-8')) +
                json.loads((root / 'licenses/runtime-wheels.lock.json').read_text(encoding='utf-8'))):
        if row['owner'] not in rows:
            raise ValueError('Supplément natif périmé : ' + row['id'])
        rows[row['id']] = row
    return sorted(rows.values(), key=lambda r: r['id'])


def fetch(url):
    import time
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'THERESE-license-collector/1'}), timeout=120) as response:
                return response.read()
        except Exception:
            if attempt == 3:
                raise
            time.sleep(attempt + 1)


def verify(data, integrity):
    if ':' in integrity:
        algo, expected = integrity.split(':', 1)
        actual = hashlib.new(algo, data).hexdigest()
    else:
        algo, expected = integrity.split('-', 1)
        actual = base64.b64encode(hashlib.new(algo, data).digest()).decode()
    if actual != expected:
        raise ValueError('Empreinte de l’archive incorrecte')


def archive_members(data):
    stream = io.BytesIO(data)
    if zipfile.is_zipfile(stream):
        with zipfile.ZipFile(stream) as archive:
            for name in sorted(archive.namelist()):
                if is_notice(name) or Path(name).name in ('METADATA', 'PKG-INFO', 'package.json', 'Cargo.toml'):
                    if not name.endswith('/'):
                        yield name, archive.read(name)
    else:
        stream.seek(0)
        with tarfile.open(fileobj=stream, mode='r:*') as archive:
            for member in sorted(archive.getmembers(), key=lambda m: m.name):
                if member.isfile() and (is_notice(member.name) or Path(member.name).name in ('PKG-INFO', 'package.json', 'Cargo.toml')):
                    yield member.name, archive.extractfile(member).read()


def has_license(notices):
    # Le nom du fichier ne prouve rien : AUTHORS peut contenir une vraie MIT,
    # LICENSE un simple renvoi. Reconnaître des clauses, jamais seulement un titre.
    for notice in notices:
        text = ' '.join(notice.get('text', '').lower().split())
        if re.search(r'\btodo\b', text):
            continue
        if ('permission is hereby granted' in text or 'permission to use, copy' in text) and ('warranty' in text or 'warranties' in text):
            return True
        if 'redistribution and use' in text and 'disclaimer' in text:
            return True
        if 'terms and conditions for use, reproduction, and distribution' in text and '9. accepting warranty or additional liability' in text:
            return True
        if 'gnu ' in text and 'end of terms and conditions' in text:
            return True
        if 'mozilla public license' in text and '10. versions of the license' in text:
            return True
        if 'this is free and unencumbered software released into the public domain' in text and 'warranty' in text:
            return True
        if 'this software is provided' in text and 'the origin of this software must not be misrepresented' in text:
            return True
        if 'do what the fuck you want to public license' in text and '0. you just do what the fuck you want to' in text:
            return True
        if 'creative commons' in text and (('2. waiver' in text and '4. limitations and disclaimers' in text) or
                                           ('section 2' in text and 'section 8' in text and 'disclaimer of warranties' in text)):
            return True
        if 'gnu lesser general public license' in text and '6. revised versions of the gnu lesser general public license' in text:
            return True
        if 'community data license agreement' in text and 'a data recipient may use, modify, and share' in text and '5. definitions' in text:
            return True
        if 'blue oak model license' in text and 'each contributor licenses you' in text and 'no liability' in text:
            return True
        if 'nvidia hereby grants you a non-exclusive' in text and 'no warranties' in text and len(text) > 10000:
            return True
    return False


def generic_attribution(text):
    # Les annexes normatives Apache/GNU expliquent comment appliquer la licence :
    # leurs exemples ne sont pas l'attribution du composant. Ne pas les réécrire.
    if re.search(r'APPENDIX:\s+How to apply the Apache License', text, re.I):
        text = re.sub(r'Copyright (?:\[yyyy\]|\d{4}) \[name of copyright owner\]', '', text, flags=re.I)
    if re.search(r'How to Apply These Terms to Your New (?:Programs|Libraries)', text, re.I):
        text = re.sub(r'<year>\s+<name of author>', '', text, flags=re.I)
    if 'Please replace <year> with the value from the FreeType version' in text:
        text = text.replace('copyright © <year> The FreeType', 'copyright © The FreeType')
        text = text.replace('Please replace <year>', 'Please replace the example year')
    return bool(re.search(r'<(?:year|copyright holders?|name of (?:the )?author)>|\[(?:yyyy|year|copyright holders?|name of copyright owner)\]', text, re.I))


def incomplete_attributions(rows):
    return [r['id'] for r in rows if r.get('attribution_missing') or
            any(generic_attribution(n['text']) for n in r['notices'])]


def collect(row, cache):
    snapshot = cache / (digest((row['id'] + row['integrity']).encode()) + '.json')
    if snapshot.exists():
        cached = json.loads(snapshot.read_text(encoding='utf-8'))
        if has_license(cached['notices']):
            return cached
    path = cache / digest(row['artifact'].encode())
    if path.exists():
        data = path.read_bytes()
    else:
        data = fetch(row['artifact'])
        verify(data, row['integrity'])
        path.write_bytes(data)
    verify(data, row['integrity'])
    if row.get('text_only'):
        return {**row, 'notices': [{'path': row['artifact'], 'text': data.decode().strip()}]}
    notices = []
    license_name = row.get('license', '')
    for name, content in archive_members(data):
        text = content.decode('utf-8', errors='replace').replace('\r\n', '\n').strip()
        if is_notice(name) and text:
            notices.append({'path': name, 'text': text})
        elif Path(name).name == 'package.json' and name.count('/') <= 1:
            meta = json.loads(text)
            lic = meta.get('license', '')
            license_name = lic if isinstance(lic, str) else lic.get('type', '')
        elif Path(name).name == 'Cargo.toml' and name.count('/') == 1:
            license_name = tomllib.loads(text).get('package', {}).get('license', '')
        elif Path(name).name in ('METADATA', 'PKG-INFO') and not license_name:
            meta = Parser().parsestr(text)
            license_name = meta.get('License-Expression') or meta.get('License') or '; '.join(c for c in meta.get_all('Classifier', []) if c.startswith('License ::'))
            if license_name and len(license_name) > 300:
                notices.append({'path': name + ':License', 'text': license_name})
                license_name = 'Voir le texte de la métadonnée License'
    result = {**row, 'license': license_name or 'Voir les notices originales', 'notices': notices}
    snapshot.write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8', newline='\n')
    return result


def validate_inventory(packages, rows, *, release=True):
    expected = {p['id']: p for p in packages}
    actual = {p['id']: p for p in rows}
    if len(actual) != len(rows) or set(expected) != set(actual):
        raise ValueError('Inventaire incomplet ou périmé : régénérer depuis les verrous')
    for key, row in actual.items():
        if not row.get('notices') or not has_license(row['notices']) or any(
                not n.get('text', '').strip() or re.search(r'\bTODO\b', n['text'], re.I) for n in row['notices']):
            raise ValueError(f'Licence sans texte : {key}')
        if any(row.get(field) != expected[key].get(field) for field in ('artifact', 'integrity')):
            raise ValueError(f'Archive périmée : {key}')
    if release and (missing := incomplete_attributions(rows)):
        raise ValueError('Livrable PROVISOIRE : attributions génériques ou manquantes : ' + ', '.join(missing))


def source_text(data, source):
    text = data.decode('utf-8')
    return (json.loads(text)['text'] if source.get('json_text') else text).strip()


def override_notices(override, root):
    notices = []
    for source in override['notices']:
        path = source.get('local_path') or source['url']
        data = (root / path).read_bytes() if 'local_path' in source else fetch(path)
        verify(data, source['integrity'])
        notices.append({'path': path, 'text': source_text(data, source)})
    return notices


def apply_override(row, override, root):
    notices = override_notices(override, root)
    if override.get('retain_archive_notices'):
        local_paths = {n['path'] for n in notices}
        notices = [n for n in row['notices'] if n['path'] not in local_paths] + notices
    return {**row, 'license': override['license'], 'notices': notices,
            'provenance': override['reason'], 'review_required': override.get('review_required', False),
            'attribution_missing': override.get('attribution_missing', False)}


def render(rows, fingerprint):
    missing = incomplete_attributions(rows)
    title = 'THÉRÈSE — Licences des composants tiers'
    if missing:
        title = 'PROVISOIRE — ' + title + ' — DIFFUSION REFUSÉE : attributions incomplètes'
    parts = [title, 'Empreinte des verrous : ' + fingerprint,
             'Inventaire conservateur : dépendances de production, de build, de test et variantes de plateformes verrouillées.',
             'La présence dans ce document ne signifie pas que le composant est embarqué.',
             'Les notices des roues natives sélectionnées complètent celles des sources.',
             'Code THÉRÈSE : https://github.com/ludovicsanchez38-creator/Synoptia-THERESE (tag de la version installée).',
             'Les liens d’archives ci-dessous identifient les sources amont ; ils ne remplacent pas la fourniture du code source correspondant des binaires GPL/LGPL.',
             'Les modèles de voix téléchargés séparément ne sont pas couverts par les verrous.', '']
    if missing:
        parts += ['Attributions à compléter : ' + ', '.join(missing), '']
    texts = {}
    for row in sorted(rows, key=lambda r: r['id']):
        flags = copyleft(row['license'] + '\n' + '\n'.join(n['text'] for n in row['notices']))
        parts += [row['id'], 'Licence déclarée : ' + row['license'], 'Archive : ' + row.get('artifact', ''), 'Intégrité : ' + row.get('integrity', '')]
        if row.get('review_required'):
            parts.append('REVUE REQUISE : ' + row['provenance'])
        if flags:
            parts.append('ATTENTION COPYLEFT : ' + ', '.join(flags))
        for n in sorted(row['notices'], key=lambda n: n['path']):
            h = digest(n['text'].encode())
            texts[h] = n['text']
            parts.append(f"Notice : {n['path']} — texte SHA256 {h}")
        parts.append('')
    for h, text in sorted(texts.items()):
        parts += ['=' * 72, 'TEXTE SHA256 ' + h, text, '']
    return '\n'.join(parts) + '\n'


def check_output(path, expected):
    if not path.is_file() or path.read_bytes() != expected.encode('utf-8'):
        raise ValueError(f'{path.name} absent ou périmé ; lancer python scripts/third_party_licenses.py generate')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['refresh', 'generate', 'check'])
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--cache', type=Path, default=ROOT / '.work-t2/cache/licenses')
    args = parser.parse_args()
    root = args.root
    packages = locked_packages(root)
    fingerprint = lock_digest(root)
    inventory = root / INVENTORY
    if args.command == 'refresh':
        args.cache.mkdir(parents=True, exist_ok=True)
        overrides_path = root / 'licenses/overrides.json'
        overrides = json.loads(overrides_path.read_text(encoding='utf-8')) if overrides_path.exists() else {}
        rows, errors = [], []
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = {pool.submit(collect, row, args.cache): row for row in packages}
            for future in as_completed(futures):
                row = futures[future]
                try:
                    result = future.result()
                    if row['id'] in overrides:
                        result = apply_override(result, overrides[row['id']], root)
                except Exception as exc:
                    errors.append(f"{row['id']} : {exc}")
                    continue
                rows.append(result)
                if len(rows) % 100 == 0:
                    print(f'{len(rows)}/{len(packages)} archives collectées', flush=True)
        if errors:
            raise ValueError('\n'.join(sorted(errors)))
        validate_inventory(packages, rows, release=False)
        inventory.parent.mkdir(exist_ok=True)
        inventory.write_text(json.dumps({'locks': fingerprint, 'packages': sorted(rows, key=lambda p: p['id'])}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    data = json.loads(inventory.read_text(encoding='utf-8'))
    overrides = json.loads((root / 'licenses/overrides.json').read_text(encoding='utf-8'))
    for row in data['packages']:
        if row['id'] in overrides:
            row['provenance'] = overrides[row['id']]['reason']
            row['review_required'] = overrides[row['id']].get('review_required', False)
            row['attribution_missing'] = overrides[row['id']].get('attribution_missing', False)
            for source in overrides[row['id']]['notices']:
                if 'local_path' in source:
                    raw = (root / source['local_path']).read_bytes()
                    verify(raw, source['integrity'])
                    if {'path': source['local_path'], 'text': source_text(raw, source)} not in row['notices']:
                        raise ValueError('Supplément absent ou périmé : ' + row['id'])
    if data['locks'] != fingerprint:
        raise ValueError('Verrous modifiés : lancer refresh et réviser les licences')
    validate_inventory(packages, data['packages'], release=args.command == 'check')
    expected = render(data['packages'], fingerprint)
    if args.command == 'check':
        check_output(root / OUTPUT, expected)
    else:
        (root / OUTPUT).write_text(expected, encoding='utf-8', newline='\n')
    flags = [(r['id'], copyleft(r['license'] + '\n' + '\n'.join(n['text'] for n in r['notices']))) for r in data['packages']]
    print(f'{len(packages)} archives ; {len(expected.encode())} octets de notices')
    for name, kinds in flags:
        if kinds:
            print('COPYLEFT', name, ', '.join(kinds))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
