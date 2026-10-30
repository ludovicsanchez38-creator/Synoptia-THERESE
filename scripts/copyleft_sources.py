#!/usr/bin/env python3
"""Vérifier hors réseau ou assembler les sources copyleft des composants verrouillés."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tarfile
import tomllib
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import third_party_licenses as licenses

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = 'licenses/copyleft-sources.json'
RETENTION = licenses.SOURCE_AVAILABILITY

# Dépendances revues pour les versions livrées. Une liste vide/modifiée dans le
# manifeste ne doit pas pouvoir faire disparaître les correctifs nécessaires.
AV_SUPPORT = ('PyAV-17.1.0-build-tree.tar.gz', 'pyav-ffmpeg-8.1.1-2-build-tree.tar.gz')
REQUIRED_SUPPORT = {
    **{f'native:{name}@python:av@17.1.0': AV_SUPPORT for name in (
        'alsa-lib', 'ffmpeg', 'gmp', 'libunistring', 'nettle-hogweed', 'gnutls', 'lame', 'x264', 'x265')},
    'native:libiconv@python:av@17.1.0': (*AV_SUPPORT, 'mingw-w64-libiconv-1.19-1.src.tar.zst'),
    'native:espeak-ng@python:piper-tts@1.4.2': ('piper-1.4.2-build-tree.tar.gz',),
    'python:piper-tts@1.4.2': ('piper-1.4.2-build-tree.tar.gz',),
    'python:setuptools@84.2.1': ('setuptools-84.2.1.tar.gz',),
}
# Le composant LGPL est embarqué dans setuptools ; sa source propre n'est pas
# le sdist du propriétaire. L'archive du propriétaire reste obligatoire ci-dessus.
EMBEDDED_PACKAGES = {'python:setuptools@84.2.1'}
SUPPORT_LOCKS = {'setuptools-84.2.1.tar.gz': 'python:setuptools@84.2.1'}
BINDING_FIELDS = ('version', 'packages', 'source', 'recipes', 'recipe_refs', 'required_supporting_sources')


def locked_sources(root):
    """Lire directement les sources et empreintes des verrous, sans inventaire."""
    result = {}
    for p in tomllib.loads((root / 'uv.lock').read_text(encoding='utf-8'))['package']:
        if p.get('sdist'):
            result[f"python:{p['name']}@{p['version']}"] = {
                'url': p['sdist']['url'], 'sha256': p['sdist']['hash'].removeprefix('sha256:'),
                'version': p['version']}
    for p in tomllib.loads((root / 'src/frontend/src-tauri/Cargo.lock').read_text(encoding='utf-8'))['package']:
        if p.get('source', '').startswith('registry+') and p.get('checksum'):
            result[f"cargo:{p['name']}@{p['version']}"] = {
                'url': f"https://static.crates.io/crates/{p['name']}/{p['name']}-{p['version']}.crate",
                'sha256': p['checksum'], 'version': p['version']}
    return result


def inventory_digest(rows):
    return hashlib.sha256(json.dumps(sorted(rows, key=lambda r: r['id']), sort_keys=True,
                                     ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def required(row):
    text = row['license'] + '\n' + '\n'.join(n['text'] for n in row['notices'])
    return bool(licenses.copyleft(text) or re.search(r'MPL-2\.0|Mozilla Public License', text, re.I))


def valid_resource(item, *, recipe=False):
    if not isinstance(item, dict):
        return False
    filename = item.get('filename', '')
    valid = (re.fullmatch(r'[a-f0-9]{64}', item.get('sha256', '')) and
             re.match(r'https://[^/]+/.+', item.get('url', '')) and filename and
             Path(filename).name == filename and filename not in ('.', '..') and
             '/' not in filename and '\\' not in filename)
    if recipe:
        commit = item.get('commit', '')
        valid = valid and re.fullmatch(r'[a-f0-9]{40}', commit) and commit in item['url']
    return bool(valid)


def verify_manifest(manifest, rows, root=None):
    errors = []
    source_locks = locked_sources(root or ROOT)
    proof_files = manifest.get('evidence_files', [])
    if not proof_files:
        errors.append('Références aux preuves de version absentes')
    proofs = {}
    for proof in proof_files:
        path = proof.get('path', '')
        if (not path.startswith('licenses/') or '..' in Path(path).parts or
                not re.fullmatch(r'[a-f0-9]{64}', proof.get('sha256', '')) or path in proofs):
            errors.append('Référence de preuve invalide : ' + path)
            continue
        proofs[path] = None
        if root is not None:
            if (not (root / path).is_file() or
                    licenses.digest((root / path).read_bytes()) != proof['sha256']):
                errors.append('Preuve de version absente ou modifiée : ' + path)
            else:
                proofs[path] = json.loads((root / path).read_text(encoding='utf-8'))
    by_id = {r['id']: r for r in rows}
    needed = {r['id'] for r in rows if required(r)}
    covered = set()
    if manifest.get('schema') != 1 or manifest.get('inventory_sha256') != inventory_digest(rows):
        errors.append('Manifeste périmé : empreinte de l’inventaire différente')
    names = set()
    support = {r.get('filename'): r for r in manifest.get('supporting_sources', [])}
    if len(support) != len(manifest.get('supporting_sources', [])):
        errors.append('Archive de construction dupliquée')
    # L'identité complète est portée par la preuve dont l'empreinte est contrôlée,
    # pas seulement par un nom qui pourrait masquer une autre archive valide.
    if root is not None:
        bindings = {}
        for proof in proofs.values():
            if proof is not None:
                bindings.update(proof.get('supporting_source_bindings', {}))
        for name in sorted(set(bindings) | set(support)):
            if name not in support or name not in bindings or support[name] != bindings[name]:
                errors.append('Archive de construction différente de la preuve : ' + str(name))
    for item in manifest.get('components', []):
        name = item.get('component', '?')
        if name in names:
            errors.append('Composant dupliqué : ' + name)
        names.add(name)
        packages = item.get('packages', [])
        if not packages or any(p not in by_id for p in packages):
            errors.append('Composant sans rattachement à l’inventaire : ' + name)
        covered.update(packages)
        refs = item.get('required_supporting_sources')
        mandatory = {ref for p in packages for ref in REQUIRED_SUPPORT.get(p, ())}
        if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs):
            errors.append('Références de construction absentes : ' + name)
            refs = []
        for ref in sorted(mandatory - set(refs)):
            errors.append('Référence de construction obligatoire absente : ' + name + ' — ' + ref)
        for ref in refs:
            if ref not in support:
                errors.append('Archive de construction requise absente : ' + name + ' — ' + ref)
        if item.get('status') != 'available':
            errors.append('Source manquante : ' + name + ' — ' + item.get('missing_reason', 'preuve absente'))
        if (not all(isinstance(item.get(k), str) and item[k].strip() for k in ('version', 'license', 'evidence'))
                or not valid_resource(item.get('source'))):
            errors.append('Version/source/preuve incomplète : ' + name)
        direct = [p for p in packages if p in source_locks and p not in EMBEDDED_PACKAGES]
        for package in direct:
            expected = source_locks[package]
            source = item.get('source') or {}
            if (any(source.get(k) != expected[k] for k in ('url', 'sha256')) or
                    item.get('version') != expected['version']):
                errors.append('Version/source différente du verrou : ' + name + ' — ' + package)
        evidence_refs = item.get('evidence_refs', [])
        recipe_refs = item.get('recipe_refs', [])
        if not isinstance(evidence_refs, list) or not isinstance(recipe_refs, list):
            errors.append('Références de preuve/recette invalides : ' + name)
            evidence_refs, recipe_refs = [], []
        if not direct and (not evidence_refs or not recipe_refs):
            errors.append('Source hors verrou sans références de preuve et de recette : ' + name)
        for ref in evidence_refs:
            if not isinstance(ref, str) or ref not in proofs:
                errors.append('Référence de preuve absente : ' + name)
            elif proofs[ref] is not None:
                binding = proofs[ref].get('source_bindings', {}).get(name)
                if binding != {key: item.get(key) for key in BINDING_FIELDS}:
                    errors.append('Source/recettes différentes de la preuve : ' + name)
        recipes = item.get('recipes', [])
        if any('/wheel-' in p or p.startswith('native:') for p in packages) and not recipes:
            errors.append('Recette de roue absente : ' + name)
        for recipe in recipes:
            if not valid_resource(recipe, recipe=True):
                errors.append('Recette non épinglée : ' + name)
            elif root is not None:
                local = recipe.get('local_path', '')
                if (not local.startswith('licenses/recipes/') or '..' in Path(local).parts or
                        not (root / local).is_file() or
                        licenses.digest((root / local).read_bytes()) != recipe['sha256']):
                    errors.append('Recette locale absente ou modifiée : ' + name)
        recipe_resources = {r.get('filename'): r for r in recipes}
        recipe_resources.update({r: support[r] for r in refs if r in support})
        if item.get('source'):
            recipe_resources[item['source'].get('filename')] = item['source']
        for ref in recipe_refs:
            if not isinstance(ref, dict) or ref.get('resource') not in recipe_resources:
                errors.append('Référence de recette absente : ' + name)
                continue
            if not re.fullmatch(r'[a-f0-9]{64}', ref.get('sha256', '')):
                errors.append('Empreinte de recette absente : ' + name)
            member = ref.get('member', '')
            if member and (Path(member).is_absolute() or '..' in Path(member).parts):
                errors.append('Chemin de recette invalide : ' + name)
            if not member and ref['resource'] not in {r['filename'] for r in recipes}:
                errors.append('Membre de recette absent : ' + name)
            if not member and ref.get('sha256') != recipe_resources[ref['resource']].get('sha256'):
                errors.append('Empreinte de recette contradictoire : ' + name)
    for item in manifest.get('exclusions', []):
        packages = item.get('packages', [])
        evidence = item.get('notices', [])
        if not packages or not item.get('reason') or not item.get('basis') or not evidence:
            errors.append('Exclusion sans justification et preuve')
        for key in packages:
            if key not in by_id or key in covered:
                errors.append('Exclusion inconnue ou contradictoire : ' + key)
                continue
            row = by_id[key]
            proofs = [p for p in evidence if p.get('package') == key]
            if not proofs or any(not any(n['path'] == p.get('path') and
                                        licenses.digest(n['text'].encode()) == p.get('sha256')
                                        for n in row['notices']) for p in proofs):
                errors.append('Notice de justification absente ou modifiée : ' + key)
            choice = item.get('selected_license')
            if item.get('basis') == 'alternative' and (
                    not choice or choice not in licenses.declared_licenses(row['license']) or
                    'OR' not in row['license'] or re.search(r'GPL|MPL', choice)):
                errors.append('Alternative non valable : ' + key)
            if item.get('basis') not in ('alternative', 'exception', 'not-distributed', 'notice-scope'):
                errors.append('Motif d’exclusion inconnu : ' + key)
            covered.add(key)
    for item in manifest.get('supporting_sources', []):
        if not valid_resource(item, recipe=bool(item.get('commit'))):
            errors.append('Archive de construction invalide : ' + item.get('filename', '?'))
        package = SUPPORT_LOCKS.get(item.get('filename'))
        if package and (package not in source_locks or any(
                item.get(k) != source_locks[package][k] for k in ('url', 'sha256'))):
            errors.append('Archive de construction différente du verrou : ' + package)
    for key in sorted(needed - covered):
        errors.append('Composant copyleft sans sources ni exclusion justifiée : ' + key)
    return errors


def download(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'THERESE-copyleft-sources/1'}), timeout=60) as response:
        return response.read()


def resources(manifest):
    items = list(manifest.get('supporting_sources', []))
    for entry in manifest['components']:
        if entry.get('source'):
            items.append(entry['source'])
        items.extend(entry.get('recipes', []))
    unique = {}
    for item in items:
        if not valid_resource(item):
            raise ValueError('Archive ou chemin invalide')
        name = item['filename']
        if name in unique and (unique[name]['sha256'], unique[name]['url']) != (item['sha256'], item['url']):
            raise ValueError('Deux archives portent le même nom : ' + name)
        unique[name] = item
    return list(unique.values())


def readme(manifest):
    lines = ['THÉRÈSE — Sources correspondantes des composants tiers', '', RETENTION, '',
             'Ce dossier accompagne exclusivement la release construite avec cet inventaire.',
             'copyleft-sources.json rattache chaque source aux archives binaires verrouillées.',
             'archives/ contient les archives amont inchangées, vérifiées par SHA-256.',
             'Les recettes épinglées et leurs archives de dépôt conservent aussi les correctifs',
             'appliqués par les fabricants des roues. Aucun code téléchargé n’a été exécuté.',
             'Les numéros de SONAME ne sont pas utilisés comme versions source.',
             'Les modalités de remplacement/reliaison des bibliothèques LGPL, notamment dans',
             'le moteur onefile, sont décrites dans la méthode de reconstruction ci-dessous.', '',
             'Correspondances :']
    for item in manifest['components']:
        source = item.get('source') or {}
        lines += ['', item['component'] + ' — ' + item.get('version', 'VERSION INCONNUE') + ' — ' + item['license'],
                  '  Entrées : ' + ', '.join(item['packages']),
                  '  Archive : ' + source.get('filename', 'MANQUANTE'),
                  '  Preuve : ' + item['evidence']]
        if item.get('status') != 'available':
            lines.append('  MANQUANT : ' + item.get('missing_reason', 'source non établie'))
        lines += ['  Recette : ' + r['filename'] for r in item.get('recipes', [])]
        lines += ['  Archive de construction obligatoire : ' + r
                  for r in item['required_supporting_sources']]
        lines += ['  Référence de recette : ' + r['resource'] + ('#' + r['member'] if r.get('member') else '')
                  for r in item.get('recipe_refs', [])]
        lines += ['  Fichier de preuve : ' + r for r in item.get('evidence_refs', [])]
    lines += ['', 'Entrées écartées :']
    for item in manifest.get('exclusions', []):
        lines.append(', '.join(item['packages']) + ' : ' + item['reason'])
    return '\n'.join(lines) + '\n\n' + (ROOT / 'licenses/LISEZMOI-SOURCES.txt').read_text(encoding='utf-8')


def checked_inventory(root):
    data = json.loads((root / licenses.INVENTORY).read_text(encoding='utf-8'))
    if data['locks'] != licenses.lock_digest(root):
        raise ValueError('Inventaire périmé par rapport aux verrous')
    licenses.validate_inventory(licenses.locked_packages(root), data['packages'], release=False)
    return data['packages']


def verify_recipe_members(manifest, archives):
    """Résoudre les recettes embarquées sans extraction ni exécution."""
    references = {}
    for item in manifest['components']:
        for ref in item.get('recipe_refs', []):
            if ref.get('member'):
                references.setdefault(ref['resource'], []).append(ref)
    for resource, refs in references.items():
        found = {}
        wanted = {ref['member'] for ref in refs}
        with tarfile.open(archives / resource, 'r:*') as archive:
            for member in archive:
                path = member.name.split('/', 1)[-1]
                if path in wanted:
                    if not member.isfile() or path in found:
                        raise ValueError('Membre de recette non régulier ou dupliqué : ' + path)
                    found[path] = licenses.digest(archive.extractfile(member).read())
        for ref in refs:
            if found.get(ref['member']) != ref['sha256']:
                raise ValueError('Membre de recette absent ou modifié : ' + resource + '#' + ref['member'])


def assemble(manifest, folder, root=ROOT):
    # Même garde pour les appels directs et la CLI, avant la première écriture.
    errors = verify_manifest(manifest, checked_inventory(root), root)
    if errors:
        raise ValueError('\n'.join(errors))
    items = resources(manifest)
    evidence = []
    for proof in manifest.get('evidence_files', []):
        path = proof.get('path', '')
        if not path.startswith('licenses/') or '..' in Path(path).parts:
            raise ValueError('Chemin de preuve invalide')
        raw = (root / path).read_bytes()
        if licenses.digest(raw) != proof.get('sha256'):
            raise ValueError('Preuve de version modifiée : ' + path)
        evidence.append((path, raw))
    folder.mkdir(parents=True, exist_ok=True)
    archives = folder / 'archives'
    archives.mkdir(exist_ok=True)
    if archives.is_symlink():
        raise ValueError('Dossier archives symbolique refusé')
    failures = []
    for item in items:
        path = archives / item['filename']
        if path.is_symlink():
            raise ValueError('Archive symbolique refusée')
        try:
            raw = path.read_bytes() if path.exists() else download(item['url'])
            if licenses.digest(raw) != item['sha256']:
                raise ValueError('SHA-256 incorrect : ' + item['filename'])
            path.write_bytes(raw)
            print('Vérifié : ' + item['filename'], flush=True)
        except (OSError, ValueError) as exc:
            failures.append(str(exc))
    if failures:
        raise ValueError('\n'.join(failures))
    verify_recipe_members(manifest, archives)
    for path, raw in evidence:
        target = folder / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    (folder / 'copyleft-sources.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    (folder / 'LISEZMOI-SOURCES.txt').write_text(readme(manifest), encoding='utf-8', newline='\n')
    return len(items), sum((archives / i['filename']).stat().st_size for i in items)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['verifier', 'assembler'])
    parser.add_argument('folder', type=Path, nargs='?')
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    manifest = json.loads((args.root / MANIFEST).read_text(encoding='utf-8'))
    errors = verify_manifest(manifest, checked_inventory(args.root), args.root)
    if errors:
        raise ValueError('\n'.join(errors))
    if args.command == 'assembler':
        if args.folder is None:
            parser.error('assembler exige un dossier')
        count, size = assemble(manifest, args.folder, root=args.root)
        print(f'{count} fichiers téléchargés/vérifiés ; {size} octets')
    print(f"Sources vérifiées : {len(manifest['components'])} composants ; aucune source manquante")


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
