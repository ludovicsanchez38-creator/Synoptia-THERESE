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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import attribution_evidence

ROOT = Path(__file__).resolve().parents[1]
LOCKS = ['package-lock.json', 'src/frontend/package-lock.json', 'src/frontend/src-tauri/Cargo.lock', 'uv.lock', 'licenses/native-components.lock.json', 'licenses/overrides.json', 'licenses/runtime-wheels.lock.json', 'licenses/attribution-sources.json']
INVENTORY = 'licenses/inventory.json'
OUTPUT = 'THIRD_PARTY_LICENSES'
SOURCE_AVAILABILITY = "Sources correspondantes : pièce jointe THERESE-sources-copyleft.tar.gz de la release de la même version, https://github.com/ludovicsanchez38-creator/Synoptia-THERESE/releases. Disponibilité : pendant toute la distribution des binaires, au minimum trois ans après leur dernière distribution et aussi longtemps qu'un support ou des pièces de rechange sont proposés pour cette version (engagement conservateur GPL-3.0, §6b ; fourniture par téléchargement simultané selon §6d)."


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


def declared_licenses(expression):
    """Toutes les licences nommées, même dans une alternative OR ou slash."""
    aliases = {
        'MIT License': 'MIT', 'NVIDIA Proprietary Software': 'LicenseRef-NVIDIA-Proprietary',
        'Apache': 'Apache-2.0', 'Apache 2.0': 'Apache-2.0',
        'Apache License 2.0': 'Apache-2.0', 'Apache 2.0 License': 'Apache-2.0',
        'Apache License, Version 2.0': 'Apache-2.0', 'PSF': 'PSF-2.0',
        'BSD-3': 'BSD-3-Clause', 'BSD 3-Clause OR Apache-2.0': 'BSD-3-Clause OR Apache-2.0',
    }
    expression = aliases.get(expression, expression)
    if expression.startswith('License ::'):
        names = {'MIT License': 'MIT', 'Apache Software License': 'Apache-2.0',
                 'BSD License': 'BSD', 'Mozilla Public License 2.0 (MPL 2.0)': 'MPL-2.0',
                 'GNU General Public License v2 (GPLv2)': 'GPL-2.0-or-later'}
        labels = [part.split('::')[-1].strip() for part in expression.split(';')]
        return {names.get(label, label) for label in labels}
    if expression.startswith('GPLv2-or-later with a special exception'):
        return {'GPL-2.0-or-later'}
    if expression.startswith('BSD license (see'):
        return {'BSD'}
    if expression in ('', 'Voir les notices originales', 'Voir notice amont',
                      'Voir le texte de la métadonnée License', 'Dual License'):
        return set()
    identifiers = re.findall(
        r'(?<![\w-])(?:Apache-2\.0|MIT(?:-CMU|-0)?|(?:0?BSD)(?:-[23]-Clause(?:-Clear)?)?|'
        r'(?:A?GPL|LGPL)-[23]\.\d(?:-only|-or-later|-with-GCC-exception)?|'
        r'Zlib|ISC|MPL-2\.0|Unlicense|Unicode-3\.0|OFL-1\.1|CC0-1\.0|CC-BY-4\.0|'
        r'Python-2\.0|PSF-2\.0|CNRI-Python|CDLA-Permissive-2\.0|BlueOak-1\.0\.0|'
        r'LLVM-exception|LicenseRef-NVIDIA-Proprietary)(?![\w-])', expression)
    remainder = expression
    for name in sorted(identifiers, key=len, reverse=True):
        remainder = remainder.replace(name, '')
    remainder = re.sub(r'\b(?:AND|OR|WITH)\b|[()/;\s]', '', remainder)
    if remainder:
        identifiers.append(remainder)
    return set(identifiers)


def license_covered(name, notices):
    # Chaque clause doit appartenir au même texte rattaché à cette entrée.
    # Les variantes typographiques des archives sont normalisées pour la recherche,
    # jamais dans les textes livrés.
    for notice in notices:
        text = re.sub(r'(?m)^\s*(?://|\*|#)\s?', '', notice['text'].lower())
        text = re.sub(r'\s+', ' ', text)
        if name in ('MIT', 'MIT-0'):
            clauses = ['permission is hereby granted', 'free of charge',
                       'without restriction', 'warranty', 'liable']
            if name == 'MIT':
                clauses += ['the above copyright notice', 'included in all copies']
        elif name == 'MIT-CMU':
            clauses = ['permission to use, copy, modify and distribute', 'without fee',
                       'permission notice appear in supporting', 'liable']
        elif name == 'Apache-2.0':
            clauses = ['terms and conditions for use, reproduction, and distribution',
                       '2. grant of copyright license', '3. grant of patent license',
                       '4. redistribution', '5. submission of contributions',
                       '6. trademarks', '7. disclaimer of warranty',
                       '8. limitation of liability', '9. accepting warranty or additional liability',
                       'end of terms and conditions']
        elif name in ('BSD', 'BSD-2-Clause', 'BSD-3-Clause', 'BSD-3-Clause-Clear'):
            clauses = ['redistribution and use', 'source', 'binary', 'conditions',
                       'provided', 'implied warranties', 'liable']
            if name.startswith('BSD-3-Clause'):
                clauses += ['endorse or promote']
            if name == 'BSD-3-Clause-Clear':
                clauses += ['no express or implied licenses to any party', 'patent rights']
        elif name in ('ISC', '0BSD'):
            clauses = ['permission to use, copy', 'for any purpose', 'software is provided', 'liable']
            if name == 'ISC':
                clauses += ['copyright notice', 'permission notice']
        elif name == 'Zlib':
            clauses = ['this software is provided', 'the origin of this software must not be misrepresented',
                       'altered source versions', 'this notice may not be removed']
        elif name.startswith(('GPL-', 'LGPL-', 'AGPL-')):
            family, version = name.split('-', 2)[:2]
            heading = {'GPL': 'gnu general public license', 'LGPL': 'gnu (?:lesser|library) general public license',
                       'AGPL': 'gnu affero general public license'}[family]
            number = version.removesuffix('.0')
            if not re.search(heading + r'.{0,120}?version ' + re.escape(number) + r'\b', text):
                continue
            clauses = (['6. revised versions of the gnu lesser general public license']
                       if family == 'LGPL' and version == '3.0' else ['end of terms and conditions'])
        elif name == 'MPL-2.0':
            clauses = ['mozilla public license', '2. license grants', '3. responsibilities',
                       '10. versions of the license']
        elif name == 'Unlicense':
            clauses = ['this is free and unencumbered software released into the public domain',
                       'warranty', 'liable']
        elif name == 'Unicode-3.0':
            clauses = ['unicode', 'permission is hereby granted', 'without restriction',
                       'copyright', 'warranty', 'liable']
        elif name == 'OFL-1.1':
            clauses = ['sil open font license', 'permission & conditions', 'termination', 'disclaimer']
        elif name == 'CC0-1.0':
            clauses = ['creative commons', '1. copyright and related rights', '2. waiver',
                       '3. public license fallback', '4. limitations and disclaimers']
        elif name == 'CC-BY-4.0':
            clauses = ['creative commons', 'section 2', 'section 8', 'disclaimer of warranties']
        elif name in ('Python-2.0', 'PSF-2.0'):
            clauses = ['python software foundation license', 'psf hereby grants',
                       'psf is making python available', 'this license agreement will automatically terminate']
        elif name == 'CNRI-Python':
            clauses = ['cnri hereby grants', 'cnri is making python', 'cnri shall not be liable',
                       'this license agreement shall be governed']
        elif name == 'LLVM-exception':
            clauses = ['llvm exception', 'as a result of your compiling your source code',
                       'you may redistribute such embedded portions']
        elif name == 'CDLA-Permissive-2.0':
            clauses = ['community data license agreement', 'a data recipient may use, modify, and share', '5. definitions']
        elif name == 'BlueOak-1.0.0':
            clauses = ['blue oak model license', 'each contributor licenses you', 'no liability']
        elif name == 'LicenseRef-NVIDIA-Proprietary':
            clauses = ['nvidia hereby grants you a non-exclusive', 'no warranties']
            if len(text) < 10000:
                continue
        else:
            return False
        if all(clause in text for clause in clauses):
            return True
    return False


def missing_licenses(row):
    return sorted(name for name in declared_licenses(row.get('license', ''))
                  if not license_covered(name, row['notices']))


GENERIC = re.compile(r'<(?:year|copyright holders?|name of (?:the )?author)>|'
                     r'\[(?:yyyy|year|copyright holders?|name of copyright owner)\]', re.I)


def attribution_text(text):
    # Uniquement le champ exemple immédiatement après le paragraphe normatif.
    # Aucun remplacement global : la même ligne dans AUTRE COMPOSANT reste visible.
    # Les espaces de mise en page RTF ne changent ni les lignes ni les champs.
    text = re.sub(r'\\(?:pard?|li\d+)\b', ' ', text)
    paragraph = 'APPENDIX: How to apply the Apache License to your work. To apply the Apache License to your work, attach the following boilerplate notice, with the fields enclosed by brackets "[]" replaced with your own identifying information. (Don\'t include the brackets!) The text should be enclosed in the appropriate comment syntax for the file format. We also recommend that a file or class name and description of purpose be included on the same "printed page" as the copyright notice for easier identification within third-party archives.'
    prefix = r'\s+'.join(re.escape(word) for word in paragraph.split())
    apache = re.compile(
        '(' + prefix + r'\s+)'
        r'(Copyright (?:\[yyyy\]|\d{4}) \[name of copyright owner\])'
        r'(?=\s+Licensed under the Apache License, Version 2\.0)', re.I)
    text = apache.sub(lambda m: m[1] + ' ' * len(m[2]), text)
    # Même limite pour les deux exemples GNU et le crédit pédagogique FreeType.
    gnu_examples = [
        (r'(the ["“]copyright["”] line and a pointer to where the full notice is found\.\s+'
         r"<one line to give the (?:program|library)'s name and a brief idea of what it does\.>\s+"
         r'Copyright \(C\) )(<year>\s+<name of author>)(?=\s+This (?:program|library) is free software)'),
        (r'(make it output a short notice like this when it starts in an interactive mode:\s+'
         r'<program> Copyright \(C\) )(<year>\s+<name of author>)'
         r'(?=\s+This program comes with ABSOLUTELY NO WARRANTY)'),
    ]
    for example in gnu_examples:
        # Les retours à la ligne restent en place pour les preuves par ligne.
        text = re.sub(example.replace(' ', r'\s+'), lambda m: m[1] + re.sub(r'[^\n]', ' ', m[2]), text, flags=re.I)
    freetype = (
        r'(encourage you to use the following text:\s+"""\s+'
        r'Portions of this software are copyright © )(<year>)'
        r'( The FreeType\s+Project \((?:www\.|https://)freetype.org\)\.\s+'
        r'All rights reserved\.\s+"""\s+Please replace )(<year>)'
        r'(?= with the value from the FreeType version you\s+actually use\.)')
    text = re.sub(freetype, lambda m: m[1] + ' ' * len(m[2]) + m[3] + ' ' * len(m[4]), text)
    return text


def generic_attribution(text):
    return bool(GENERIC.search(attribution_text(text)))


def upstream_verbatim(row, notice, sources):
    # Une preuve versionnée est attachée à l'archive ET à un fichier interne,
    # jamais à un supplément local ni à un texte partagé. Le hash porte sur
    # l'intégralité du texte livré ; les lignes ciblées doivent aussi correspondre.
    if notice['path'].startswith(('licenses/', 'http:', 'https:')):
        return False
    lines = notice['text'].splitlines()
    generic_numbers = {i for i, line in enumerate(attribution_text(notice['text']).splitlines(), 1)
                       if GENERIC.search(line)}
    for proof in sources:
        if (proof.get('status') != 'upstream-verbatim' or proof.get('package') != row['id'] or
                proof.get('archive') != row.get('artifact') or
                proof.get('archive_integrity') != row.get('integrity') or
                proof.get('path') != notice['path'] or
                proof.get('notice_sha256') != digest(notice['text'].encode())):
            continue
        if not all(re.fullmatch(r'[a-f0-9]{64}', proof.get(field, ''))
                   for field in ('archive_sha256', 'member_sha256')):
            continue
        if row.get('integrity', '').startswith('sha256:') and proof['archive_sha256'] != row['integrity'][7:]:
            continue
        ending = proof.get('line_ending', 'LF')
        prefix, suffix = proof.get('member_prefix', ''), proof.get('member_suffix', '')
        if ending not in ('LF', 'CRLF') or not isinstance(prefix, str) or not isinstance(suffix, str):
            continue
        member = prefix + notice['text'] + suffix
        if member.strip() != notice['text']:
            continue
        if ending == 'CRLF':
            member = member.replace('\n', '\r\n')
        if digest(member.encode('utf-8')) != proof['member_sha256']:
            continue
        evidence = proof.get('lines', [])
        if (len(evidence) == len(generic_numbers) and
                {line.get('notice_line') for line in evidence} == generic_numbers and
                all(isinstance(line.get('archive_line'), int) and line['archive_line'] == line['notice_line'] + prefix.count('\n') and
                    line.get('text') == lines[line['notice_line'] - 1] for line in evidence)):
            return True
    return False


def incomplete_attributions(rows, attribution_sources=(), root=ROOT):
    return [r['id'] for r in rows if ((r.get('attribution_missing') or r.get('attribution_status') == attribution_evidence.STATUS)
            and not attribution_evidence.accepted(r, attribution_sources, root)) or
            any(generic_attribution(n['text']) and not upstream_verbatim(r, n, attribution_sources)
                for n in r['notices'])]


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


def validate_inventory(packages, rows, *, release=True, attribution_sources=(), root=ROOT):
    expected = {p['id']: p for p in packages}
    actual = {p['id']: p for p in rows}
    if len(actual) != len(rows) or set(expected) != set(actual):
        raise ValueError('Inventaire incomplet ou périmé : régénérer depuis les verrous')
    for key, row in actual.items():
        if not row.get('notices') or not has_license(row['notices']) or any(
                not n.get('text', '').strip() or re.search(r'\bTODO\b', n['text'], re.I) for n in row['notices']):
            raise ValueError(f'Licence sans texte : {key}')
        if missing := missing_licenses(row):
            raise ValueError(f'Licences déclarées sans texte intégral : {key} : {", ".join(missing)}')
        if any(row.get(field) != expected[key].get(field) for field in ('artifact', 'integrity')):
            raise ValueError(f'Archive périmée : {key}')
    if release and (missing := incomplete_attributions(rows, attribution_sources, root)):
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
        notices.append({'path': source.get('archive_path', path), 'text': source_text(data, source)})
    return notices


def apply_override(row, override, root):
    notices = override_notices(override, root)
    if override.get('retain_archive_notices'):
        local_paths = {n['path'] for n in notices}
        notices = [n for n in row['notices'] if n['path'] not in local_paths] + notices
    return {**row, 'license': override['license'], 'notices': notices,
            'provenance': override['reason'], 'review_required': override.get('review_required', row.get('review_required', False)),
            'attribution_missing': override.get('attribution_missing', row.get('attribution_missing', False)),
            'attribution_status': override.get('attribution_status', row.get('attribution_status', ''))}


def render(rows, fingerprint, attribution_sources=(), root=ROOT):
    missing = incomplete_attributions(rows, attribution_sources, root)
    title = 'THÉRÈSE — Licences des composants tiers'
    if missing:
        title = 'PROVISOIRE — ' + title + ' — DIFFUSION REFUSÉE : attributions incomplètes'
    parts = [title, SOURCE_AVAILABILITY, 'Empreinte des verrous : ' + fingerprint,
             'Inventaire conservateur : dépendances de production, de build, de test et variantes de plateformes verrouillées.',
             'La présence dans ce document ne signifie pas que le composant est embarqué.',
             'Les notices des roues natives sélectionnées complètent celles des sources.',
             'Code THÉRÈSE : https://github.com/ludovicsanchez38-creator/Synoptia-THERESE (tag de la version installée).',
             'Les modèles de voix téléchargés séparément ne sont pas couverts par les verrous.', '']
    if missing:
        parts += ['Attributions à compléter : ' + ', '.join(missing), '']
    texts = {}
    absence_mentions = []
    for row in sorted(rows, key=lambda r: r['id']):
        flags = copyleft(row['license'] + '\n' + '\n'.join(n['text'] for n in row['notices']))
        parts += [row['id'], 'Licence déclarée : ' + row['license'], 'Archive : ' + row.get('artifact', ''), 'Intégrité : ' + row.get('integrity', '')]
        if any(upstream_verbatim(row, n, attribution_sources) for n in row['notices']):
            parts.append('STATUT : texte amont reproduit tel quel — preuves dans licenses/attribution-sources.json')
        if attribution_evidence.accepted(row, attribution_sources, root):
            parts.append('STATUT : aucun titulaire nommé en amont — preuves dans licenses/attribution-sources.json')
            absence_mentions += [row['id'], attribution_evidence.statement(row, attribution_sources), '']
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
    if absence_mentions:
        parts += ['Mentions factuelles d’absence de titulaire nommé en amont', ''] + absence_mentions
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
            row['review_required'] = overrides[row['id']].get('review_required', row.get('review_required', False))
            row['attribution_status'] = overrides[row['id']].get('attribution_status', row.get('attribution_status', ''))
            row['attribution_missing'] = overrides[row['id']].get('attribution_missing', row.get('attribution_missing', False))
            for source in overrides[row['id']]['notices']:
                if 'local_path' in source:
                    raw = (root / source['local_path']).read_bytes()
                    verify(raw, source['integrity'])
                    if {'path': source.get('archive_path', source['local_path']), 'text': source_text(raw, source)} not in row['notices']:
                        raise ValueError('Supplément absent ou périmé : ' + row['id'])
    if data['locks'] != fingerprint:
        raise ValueError('Verrous modifiés : lancer refresh et réviser les licences')
    proof_path = root / 'licenses/attribution-sources.json'
    sources = json.loads(proof_path.read_text(encoding='utf-8')) if proof_path.exists() else []
    validate_inventory(packages, data['packages'], release=args.command == 'check', attribution_sources=sources, root=root)
    expected = render(data['packages'], fingerprint, attribution_sources=sources, root=root)
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
