#!/usr/bin/env python3
"""Construction physique A/B proposée, sans lancement ou admission runtime.

Les entrées sont des preuves root physiques, jamais des valeurs d'un helper.
Ce fichier ne contient aucun import G1, subprocess, socket ou fallback Git.
La seule écriture future est l'émission exclusive d'une racine encore absente,
après vérification de l'autorisation externe de construction et des inputs.
"""
from __future__ import annotations

import argparse
import ast
import difflib
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

HERE = Path(__file__).resolve().parent
REPO = Path('/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE-c15-codex')
Q = REPO / '.app-loop/cycles/17/qualification'
ACTORS = frozenset(('/root', '/root/environment_routes', '/root/native_policy_review'))
PORTS = {'backend': 17593, 'frontend': 5173, 'cdp': 17594}
ROUND = re.compile(r'therese-(c17-direct-round-([ab])-[a-f0-9]{12})')
HEAD_RE = re.compile(r'[a-f0-9]{40}')
OLD_ROOT = '/private/tmp/therese-c17-wrapper-canary-eff7b4e4f24649dd8628503bc7bfc8b3'
OLD_SOURCE = '/private/tmp/therese-c17-wrapper-source-kGvU1hdx/source'
OLD_REPO = str(REPO)
OLD_HEAD = '2d69e30c9c6dd18823ee6102271876003a6a67cc'
RUNTIME_ENABLED = False
ADMISSION_TABLE: dict = {}


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def encoded(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + '\n').encode()


def planned_ref(path: Path, raw: bytes) -> dict:
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def checked(reference: dict) -> bytes:
    need(type(reference) is dict and set(reference) == {'path', 'sha256', 'bytes'}
         and type(reference['path']) is str and type(reference['sha256']) is str
         and re.fullmatch(r'[a-f0-9]{64}', reference['sha256'])
         and type(reference['bytes']) is int and reference['bytes'] >= 0, 'Ref SHA/bytes exacte requise')
    path = Path(reference['path'])
    need(path.is_absolute() and path.resolve(strict=True) == path and not path.is_symlink(),
         'Référence non canonique ou symlink')
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as stream:
        before = os.fstat(stream.fileno())
        need(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid(), 'Ref non régulière/owner')
        raw = stream.read()
        after = os.fstat(stream.fileno())
    named = path.lstat()
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
         (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
         and (named.st_dev, named.st_ino) == (before.st_dev, before.st_ino), 'Ref changée pendant lecture')
    need(planned_ref(path, raw) == reference, 'SHA/bytes différent')
    return raw


def reference(path: Path) -> dict:
    ref = planned_ref(path, path.read_bytes())
    checked(ref)
    return ref


def read_json(ref: dict) -> dict:
    value = json.loads(checked(ref))
    need(type(value) is dict, 'Objet JSON requis')
    return value


def once(text: str, before: str, after: str) -> str:
    need(text.count(before) == 1, 'Ancre non unique : ' + before[:90])
    return text.replace(before, after, 1)


def selected_definitions(raw: bytes, names: tuple[str, ...], namespace: dict) -> dict:
    """Exécute uniquement des fonctions standard-library nommées, pas un module.

    Utilisé pour les vérificateurs purs Git déjà relus. Aucun import ni corps
    main, aucune fonction capturant Git ou lançant un processus n'est sélectionné.
    """
    tree = ast.parse(raw)
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    need({node.name for node in nodes} == set(names), 'Définitions sélectionnées absentes')
    code = ast.Module(body=nodes, type_ignores=[])
    env = dict(namespace)
    exec(compile(ast.fix_missing_locations(code), '<selected-readonly-functions>', 'exec'), env)
    return env


def identity(request: dict) -> dict:
    root = Path(request['root'])
    match = ROUND.fullmatch(root.name)
    need(root.is_absolute() and root.parent == Path('/private/tmp') and match
         and '..' not in root.parts and str(root) == str(Path(str(root))), 'Racine A/B exacte requise')
    need(request['campaign'] == match[2].upper() and request['actor'] in ACTORS
         and type(request['expected_head']) is str and HEAD_RE.fullmatch(request['expected_head']),
         'Campagne/acteur/HEAD divergent')
    need(type(request.get('ports')) is dict and request['ports'] == PORTS
         and all(type(value) is int for value in request['ports'].values()), 'Ports QA hors table fermée')
    partner = request.get('other_round')
    need(type(partner) is dict and set(partner) == {'root', 'actor', 'campaign', 'expected_head'}
         and partner['actor'] in ACTORS and partner['actor'] != request['actor']
         and partner['expected_head'] == request['expected_head'], 'Deux acteurs réels distincts requis')
    other = Path(partner['root']); other_match = ROUND.fullmatch(other.name)
    need(other.parent == Path('/private/tmp') and other_match
         and other_match[2].upper() == partner['campaign']
         and {partner['campaign'], request['campaign']} == {'A', 'B'} and other != root,
         'Autre ronde A/B physique différente requise')
    source = Path(request['qa_source'])
    need(source.parent.parent == Path('/private/tmp') and source.name == 'source'
         and source.parent.name.startswith('therese-c17-direct-source-')
         and source.resolve(strict=True) == source, 'Source QA fraîche canonique requise')
    return {'actor': request['actor'], 'campaign': request['campaign'], 'round_id': match[1],
            'root': str(root), 'head': request['expected_head'], 'qa_source': str(source)}


def source_inputs(request: dict, assets: dict) -> dict:
    """Recheck des raw root, tree reconstruit, blobs SHA1/modes/liens et HEAD.

    L'origine réelle des captures Git reste root externe. Le constructeur ne
    lance pas Git et n'infère pas la fraîcheur du seul mot PASS d'un JSON.
    """
    source = Path(request['qa_source']); head = request['expected_head']
    head_ref = request['git_head_ref']; commit_ref = request['git_commit_ref']; tree_ref = request['git_tree_ref']
    need(head_ref['path'] == str(source / '.git/HEAD') and checked(head_ref) == (head + '\n').encode(),
         'HEAD détaché différent du paramètre')
    commit, tree = checked(commit_ref), checked(tree_ref)
    oid = hashlib.sha1(b'commit ' + str(len(commit)).encode() + b'\0' + commit).hexdigest()
    need(oid == head, 'Commit brut différent du HEAD attendu')
    manifest = read_json(request['git_manifest_ref'])
    need(manifest.get('schema') == 'c17-root-fresh-git-source-manifest-v1'
         and manifest.get('status') == 'PASS' and manifest.get('head') == head
         and manifest.get('product_source_root') == str(source)
         and manifest.get('git_head_ref') == head_ref and manifest.get('git_tree_verified') is True,
         'Manifeste root Git autre source/HEAD')
    need(manifest.get('git_commit_ref') == commit_ref and manifest.get('git_tree_ref') == tree_ref,
         'Origines Git raw différentes du manifeste fourni')
    env = selected_definitions(checked(assets['source/git_snapshot.py']),
        ('need', 'object_id', 'parse_tree', 'tree_id'), {'hashlib': hashlib, 're': re})
    need(commit.split(b'\n', 1)[0] == b'tree ' + env['tree_id'](tree).encode(), 'Commit/tree raw non liés')
    verify = selected_definitions(checked(assets['definition-inputs/direct_round_admission.py']),
        ('need', 'checked_bytes', 'tree_rows', 'verify_files'),
        {'Path': Path, 'os': os, 'stat': stat, 'hashlib': hashlib, 're': re})
    verify['verify_files'](source, manifest, tree)
    need(all(Path(row['path']).lstat().st_nlink == 1 for row in manifest['files']),
         'Source Git liée par hardlink : isolation non démontrée')
    need(checked(head_ref) == (head + '\n').encode(), 'HEAD changé pendant recheck')
    rows = manifest['files']
    product = {str(Path(row['path']).relative_to(source)): row['sha256'] for row in rows
               if Path(row['path']).relative_to(source).parts[0] in ('src', 'tests', 'scripts')}
    frontend = {name: digest for name, digest in product.items()
                if name.startswith('src/frontend/') and not name.startswith('src/frontend/src-tauri/')}
    need(product and frontend, 'Tables produit/frontend vides')
    return {'manifest': manifest, 'commit': commit, 'tree': tree,
            'product_sources': product, 'frontend_qa_sources': frontend}


def dependency_inputs(request: dict, assets: dict) -> dict:
    # Les vrais audits Python149 et Node3/427 sont contrôlés par leur lecteur
    # effectif, et chaque ref .pth/lock/metadata/log est rehashée. Pas de claim
    # de rehash byte-level de tous les corps des dépendances.
    namespace = {'Path': Path, 'json': json, 'os': os, 'stat': stat, 're': re, 'hashlib': hashlib,
                 'need': need, 'REQUIRED_FRONTEND': ('vite','@vitejs/plugin-react','@tailwindcss/vite','vitest','react','react-dom'),
                 'REQUIRED_ROOT': ('playwright','playwright-core')}
    readers = selected_definitions(checked(assets['definition-inputs/prepare_ab_inputs.py']),
        ('sha','ref','checked_ref','node_versions','audit_python','audit_node'), namespace)
    source = Path(request['qa_source']); head = request['expected_head']
    python = readers['audit_python'](source, head, request['python_audit_ref'])
    node = readers['audit_node'](source, head, request['node_audit_ref'])
    audit = read_json(request['python_audit_ref'])
    site = source / '.venv-conforme/lib/python3.13/site-packages'
    declared = audit.get('pth', [])
    need(type(declared) is list and len({ref['path'] for ref in declared}) == len(declared)
         and {ref['path'] for ref in declared} == {str(path) for path in site.glob('*.pth')},
         'Ensemble .pth physique différent des références root préobservées')
    return {'python': python, 'node': node, 'body_parity_claimed': False}


def verify_chrome(request: dict) -> dict:
    """Recheck fini du bundle QA entier, pas codesign ni xattr/cache personnel."""
    bundle = Path(request['copied_chrome'])
    need(bundle.name == 'Google Chrome.app' and bundle.parent.parent == Path('/private/tmp')
         and bundle.parent.name.startswith('therese-c17-chrome-qa-copy-')
         and bundle.resolve(strict=True) == bundle, 'Chrome doit être une copie QA explicite')
    expected = json.loads(checked(request['chrome_tree_ref']))
    need(type(expected) is list and len(expected) == 1339, 'Snapshot physique Chrome1339 requis')
    observed_paths = {''}
    for parent, directories, files in os.walk(bundle, followlinks=False):
        for name in directories + files:
            observed_paths.add(str((Path(parent) / name).relative_to(bundle)))
    need({row.get('relative') for row in expected} == observed_paths
         and len(observed_paths) == len(expected), 'Chrome fichiers/dossiers/liens extras ou absents')
    regular_files = []
    for row in expected:
        relative = row['relative']; path = bundle / relative
        need(relative == '' or (not Path(relative).is_absolute() and '..' not in Path(relative).parts),
             'Chemin Chrome hors bundle')
        before = path.lstat()
        need(all(getattr(before, 'st_' + key) == row[key] for key in ('uid', 'gid', 'dev', 'ino'))
             and stat.S_IMODE(before.st_mode) == row['mode'], 'Chrome identité/mode divergent')
        if row['type'] == 'directory':
            need(stat.S_ISDIR(before.st_mode), 'Dossier Chrome remplacé')
        elif row['type'] == 'symlink':
            need(stat.S_ISLNK(before.st_mode) and os.readlink(path) == row['target']
                 and not Path(row['target']).is_absolute() and path.resolve(strict=True).is_relative_to(bundle),
                 'Lien Chrome changé/sortant')
        else:
            need(row['type'] == 'file' and stat.S_ISREG(before.st_mode) and before.st_nlink == 1,
                 'Fichier Chrome remplacé/hardlink')
            ref = {key: row[key] for key in ('sha256', 'bytes')}; ref['path'] = str(path)
            checked(ref); regular_files.append(ref)
        after = path.lstat()
        need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
             (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), 'Chrome changé pendant scan')
    executable = bundle / 'Contents/MacOS/Google Chrome'
    need(executable.is_file() and os.access(executable, os.X_OK), 'Exécutable Chrome QA absent')
    signature = read_json(request['chrome_signature_ref'])
    need(signature.get('schema') == 'c17-root-independent-chrome-copy-recheck-v1'
         and signature.get('actor') == '/root' and signature.get('passed') is True
         and signature.get('copy') == str(bundle) and signature.get('copy_current_ref') == request['chrome_tree_ref']
         and signature.get('source_copy_byte_mode_uid_gid_links_equal') is True
         and signature.get('no_source_copy_hardlinks') is True
         and signature.get('runtime_admitted') is False and signature.get('FULL') is False,
         'Précondition signature root actuelle manquante')
    codesign = signature.get('strict_codesign', {})
    need(codesign.get('argv') == ['/usr/bin/codesign','--verify','--deep','--strict','--verbose=4',str(bundle)]
         and codesign.get('status') == 0 and codesign.get('signal') is None and codesign.get('error') is None,
         'Codesign exact root non vert')
    checked(codesign['stdout']); checked(codesign['stderr'])
    completed = datetime.fromisoformat(signature['completed_at'].replace('Z', '+00:00'))
    need(completed.tzinfo is not None and 0 <= (datetime.now(UTC) - completed).total_seconds() <= 120,
         'Signature fraîche requise, ancien recheck non transposable')
    return {'bundle': str(bundle), 'executable': str(executable), 'files': regular_files,
            'tree_ref': request['chrome_tree_ref'], 'signature_ref': request['chrome_signature_ref'],
            'native_runtime_qualified': False}


def authority(request: dict, ref: dict, asset_ref: dict) -> dict:
    """Aucune autorité n'est émise. L'appel MAIN doit attester l'origine outil.

    Ce lecteur impose une décision externe construct, son registre canonique,
    les origines/revue physiques et les pins effectifs. Les chaînes JSON ne
    prouvent pas à elles seules l'autorisation humaine ou l'auteur OS.
    """
    need(Path(ref['path']).is_relative_to(Q), 'Autorisation construction doit être externe sous Q')
    body = read_json(ref); ident = identity(request)
    need(body.get('schema') == 'c17-runtime78-successor-admission-v1'
         and body.get('phase') == 'construct' and body.get('provided_by') == '/root'
         and all(body.get(key) == value for key, value in (
             ('actor', ident['actor']), ('round_id', ident['round_id']), ('round_name', ident['campaign']),
             ('head', ident['head']), ('qa_root', ident['root']))), 'Décision externe construct A/B actuelle absente')
    need(body.get('constructor') == reference(Path(__file__)) and body.get('definition_assets') == asset_ref
         and body.get('construction_request') == request['request_ref'], 'Pins constructeur/inputs non revus')
    registry = read_json(body['identity_registry'])
    need(registry.get('schema') == 'c17-identity-registry-v1', 'Registre canonique manquant')
    for actor in (ident['actor'], request['other_round']['actor']):
        selected = [row for row in registry.get('actors', []) if row.get('actor') == actor]
        need(len(selected) == 1, 'Acteur réel non unique')
        origin = selected[0]['origin']
        if not Path(origin['path']).is_absolute():
            origin = dict(origin, path=str(REPO / origin['path']))
        observed = read_json(origin)
        need(observed.get('actor') == actor and observed.get('provided_by') == '/root'
             and observed.get('origin_kind') == 'collaboration_tool_call', 'Origine acteur physique manquante')
    checked(body['root_review_origin'])
    need(body.get('reviewed_profiles') == request['profiles']
         and body.get('source_proofs') == {key: request[key] for key in (
            'git_head_ref', 'git_manifest_ref', 'git_commit_ref', 'git_tree_ref', 'python_audit_ref', 'node_audit_ref')},
         'Profils/source/dépendances non joints à la revue externe')
    now = datetime.now(UTC)
    issued = datetime.fromisoformat(body['issued_at'].replace('Z', '+00:00'))
    expires = datetime.fromisoformat(body['expires_at'].replace('Z', '+00:00'))
    need(issued.tzinfo is not None and expires.tzinfo is not None and issued <= now < expires
         and 0 < (expires - issued).total_seconds() <= 3600, 'Autorisation construct périmée/non bornée')
    # Native Session/Chrome/RPC admission is deliberately NOT inferred here.
    return body


def contextualize(text: str, request: dict) -> str:
    """Chemins de définitions seulement, avec ledger de diff exhaustif."""
    root, source, head = request['root'], request['qa_source'], request['expected_head']
    for old, new in ((OLD_ROOT, root), (OLD_SOURCE, source),
            ('/private/tmp/therese-c17-full-suite-ps_tgzy5/source', source),
            ('/private/tmp/therese-c17-direct-b492bd9t/source', source),
            (OLD_REPO + '/node_modules/playwright', source + '/node_modules/playwright'),
            ('/private/tmp/therese-c17-web-j-of4457m6', root),
            ('/private/tmp/therese-c16-direct-round-a-o1tgb_2_', root)):
        text = text.replace(old, new)
    # Literal execution pins only. Origins and historical assertion IDs remain.
    text = text.replace('17493', '17593')
    text = text.replace("HEAD = '" + OLD_HEAD + "'", "HEAD = '" + head + "'")
    text = text.replace("HEAD='" + OLD_HEAD + "'", "HEAD=" + repr(head))
    text = text.replace("HEAD='b517daedc45480e5191eac5e37cdc6c2bf111cc4'", "HEAD=" + repr(head))
    text = text.replace("REPO=Path(" + repr(OLD_REPO) + ")", "REPO=Path(" + repr(source) + ")")
    text = text.replace('repo="' + OLD_REPO + '"', 'repo=' + json.dumps(source))
    text = text.replace("repo='" + OLD_REPO + "'", 'repo=' + repr(source))
    text = text.replace('couverture-ecran-c16.mjs', 'couverture-ecran-c17.mjs')
    return text


def derive_g1(text: str, request: dict) -> str:
    need(not any(isinstance(n, (ast.Import, ast.ImportFrom)) and any(a.name == 'uuid' for a in n.names)
                 for n in ast.parse(text).body), 'uuid déjà présent : nouvelle préimage requise')
    text = once(text, 'import time\n', 'import time\nimport uuid\n')
    text = once(text, 'HEAD = "542cc6f7b7ef764a7730a9b99918df5ac02d54f2"',
                'HEAD = ' + repr(request['expected_head']))
    chrome = str(Path(request['copied_chrome']) / 'Contents/MacOS/Google Chrome')
    text = once(text, 'CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")',
                'CHROME = Path(' + repr(chrome) + ')')
    text = text.replace('bundle = Path("/Applications/Google Chrome.app")',
                        'bundle = Path(' + repr(request['copied_chrome']) + ')')
    constants = {}
    for node in ast.parse(text).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try: constants[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError): pass
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            try: constants[node.target.id] = ast.literal_eval(node.value)
            except (ValueError, TypeError): pass
    need(constants.get('RUNTIME_ENABLED') is False and constants.get('OS_STARTUP_QUALIFIED') is False
         and constants.get('ADMISSION_TABLE') == {} and constants.get('WRAPPER_ADMISSION_TABLE') == {}
         and constants.get('AB_CHROME_PROFILE_NATIVE_QUALIFIED') is False
         and all(value is False for value in constants.get('CAPABILITIES', {'missing': True}).values()),
         'Les portes G1 doivent rester fermées')
    return text


def vite_texts(request: dict, product_text: str) -> tuple[str, str]:
    source, root = Path(request['qa_source']), Path(request['root'])
    front = source / 'src/frontend'; deps = front / 'node_modules'
    canonical = product_text
    for before, after in (("from 'vite'", 'from ' + json.dumps(str(deps / 'vite/dist/node/index.js'))),
            ("from '@vitejs/plugin-react'", 'from ' + json.dumps(str(deps / '@vitejs/plugin-react/dist/index.js'))),
            ("from '@tailwindcss/vite'", 'from ' + json.dumps(str(deps / '@tailwindcss/vite/dist/index.mjs'))),
            ("resolve(__dirname, 'src')", json.dumps(str(front / 'src')))):
        canonical = once(canonical, before, after)
    config = f'''import {{defineConfig, mergeConfig}} from {json.dumps(str(deps / 'vite/dist/node/index.js'))};
import canonical from {json.dumps(str(root / 'runtime/vite.canonique.mjs'))};
export default defineConfig(async () => {{
  const env = {{command: 'serve', mode: 'development'}};
  const cfg = await Promise.resolve(typeof canonical === 'function' ? canonical(env) : canonical);
  if (!cfg) throw new Error('Configuration Vite canonique absente');
  return mergeConfig(cfg, {{root: {json.dumps(str(front))}, envDir: {json.dumps(str(root / 'profiles/runtime'))},
    cacheDir: {json.dumps(str(root / 'runtime/vite-cache'))},
    server: {{host: '127.0.0.1', port: 5173, strictPort: true,
      fs: {{allow: [{json.dumps(str(source))}, {json.dumps(str(deps))}]}}}}
  }});
}});
'''
    return canonical, config


def payloads(request: dict, assets: dict, source: dict, deps: dict, chrome: dict) -> dict[str, bytes]:
    """Constructeur pur des octets. Aucun fichier ni future birth n'est émis."""
    ident = identity(request); root = Path(request['root']); qa = Path(request['qa_source'])
    result: dict[str, bytes] = {}; diffs = []; origins = []
    for target, ref in sorted(assets.items()):
        raw = checked(ref)
        if target.startswith('definition-inputs/'):
            continue
        text = raw.decode('utf-8')
        if target == 'g1/runtime_session.py':
            text = derive_g1(text, request)
        if target.endswith('ab_auxiliary_table.py'):
            text = once(text, 'CHROME_CANDIDATE_SHA256 = "5266a6b026b5eb8192e030b5c27cc0001b65fce97d5840a9979e16a0d4ac151d"',
                        'CHROME_CANDIDATE_SHA256 = ' + repr(request['profiles']['chrome']['sha256']))
            text = once(text, 'CHROME_CANDIDATE_BYTES = 1914',
                        'CHROME_CANDIDATE_BYTES = ' + str(request['profiles']['chrome']['bytes']))
            text = once(text, '"executable": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",',
                        '"executable": ' + repr(chrome['executable']) + ',')
        if target in ('g1/web.sb', 'g1/sql.sb', 'g1/chrome.sb'):
            text = checked(request['profiles'][Path(target).stem]).decode()
        if target == 'auxiliary-ports/runtime/aux_node.mjs':
            appendix = checked(assets['definition-inputs/aux_node-git.mjs']).decode().split(
                '// Fresh A/B metadata only:', 1)
            need(len(appendix) == 2 and 'export function ownedGitHead(' not in text, 'Port Git Node ambigu')
            text += '\n// Fresh A/B metadata only:' + appendix[1]
        if target not in ('g1/web.sb', 'g1/sql.sb', 'g1/chrome.sb'):
            text = contextualize(text, request)
        if target == 'complements/b1760-identites-historiques-completes.json':
            body = json.loads(raw)
            text = encoded({'current_species_required_per_round': body['current_species_required_per_round'],
                'historical_exports': [{key: row[key] for key in (
                    'obligation_id', 'historical_mode', 'historical_nodeid', 'candidate_species', 'mapping_limit')}
                    for row in body['historical_exports']],
                'definition_origin': ref, 'historical_results_not_imported': True}).decode()
        if target.endswith('.py'):
            ast.parse(text, filename=target)
        result[target] = text.encode()
        origins.append({'source': ref, 'target': str(root / target), 'kind': 'definition_only',
                        'old_result_imported': False})
        if target in ('g1/web.sb', 'g1/sql.sb', 'g1/chrome.sb'):
            origins[-1]['effective_profile_source'] = request['profiles'][Path(target).stem]
        if result[target] != raw:
            diff_name = 'construction-diffs/' + target.replace('/', '__') + '.diff'
            result[diff_name] = ''.join(difflib.unified_diff(raw.decode().splitlines(keepends=True),
                text.splitlines(keepends=True), fromfile=ref['path'], tofile=str(root / target))).encode()
            result['construction-preimages/' + target] = raw
            diffs.append(diff_name)
    # Seven identity-v2 anchors are ported from the actual old coverage text.
    coverage = result['runtime/couverture-ecran-c17.mjs'].decode()
    anchors = json.loads(checked(assets['runtime78-successor/identity-anchors.json']))
    need(len(anchors['anchors']) == 7, 'Sept ancres identité requises')
    identity_port = selected_definitions(checked(assets['runtime78-successor/identity_port.py']),
                                         ('port_identity_v2',), {})
    coverage = identity_port['port_identity_v2'](coverage, anchors)
    for row in anchors['anchors']:
        need(coverage.count(row['after']) == 1, 'Ancre identité v2 différente : ' + row['label'])
    result['runtime/couverture-ecran-c17.mjs'] = coverage.encode()
    result['auxiliary-ports/runtime/couverture-ecran-c17.mjs'] = coverage.encode()
    # Root QA source supplies Vite canonical bytes, not a historical repo config.
    canonical, vite = vite_texts(request, (qa / 'src/frontend/vite.config.ts').read_text())
    result['runtime/vite.canonique.mjs'] = canonical.encode()
    result['runtime/vite.runtime.config.mjs'] = vite.encode()
    config = dict(ident, cycle=17, repo=str(qa), runtime=str(root / 'runtime'),
        python=str(qa / '.venv-conforme/bin/python'), frontend_source=str(qa / 'src/frontend'),
        frontend_qa=str(qa / 'src/frontend'), frontend_dependencies=str(qa / 'src/frontend/node_modules'),
        playwright_dependencies=str(qa / 'node_modules'), product_sources=source['product_sources'],
        frontend_qa_sources=source['frontend_qa_sources'], ports={'backend': 17593, 'frontend': 5173},
        browser_cache=str(root / 'auxiliary/playwright-unused'), factory='tests.couverture.backend_offline:create_app',
        session_contract=request['session_contract_ref'], nested_capture_contract=request['rpc_contract_ref'],
        calibration_executed=False, product_scenarios_executed=False, native_tauri=False,
        external_IA=False, runtime_admission=None, FULL=False, release=False)
    # Version maps retain the installed/lock evidence shape expected by core.
    config['frontend_dep_versions'] = deps['node']['frontend_dep_versions']
    config['playwright_dep_versions'] = deps['node']['playwright_dep_versions']
    result['prepared-config.json'] = encoded(config)
    result['campaign-sentinel.txt'] = ('Campagne C17 ' + ident['round_id'] + '\n').encode()
    profile = root / 'profiles/runtime'
    stack = {'cycle': 17, 'status': 'prepared', 'repo': str(qa), 'head_at_preparation': ident['head'],
        'temporary_root': str(profile), 'home': str(profile / 'home'), 'data_dir': str(profile / 'data'),
        'backend': {'host': '127.0.0.1', 'port': 17593, 'log': str(root / 'runtime/backend-runtime.log')},
        'vite': {'host': '127.0.0.1', 'port': 5173, 'log': str(root / 'runtime/vite-runtime.log'),
                 'config': str(root / 'runtime/vite.runtime.config.mjs'), 'cache_dir': str(root / 'runtime/vite-cache')}}
    result['runtime/pile-reprise.json'] = encoded(stack)
    # prepare is now validation-only: Session exclusively owns start/stop.
    result['runtime/runtime.py'] = ("import json\nimport sys\nfrom pathlib import Path\n"
        "if sys.argv[1:] != ['prepare']:\n    raise SystemExit('Legacy start/stop interdit : Session exacte requise')\n"
        "root=Path(__file__).resolve().parent.parent\n"
        "config=json.loads((root/'prepared-config.json').read_text())\n"
        "data=json.loads((root/'runtime/pile-reprise.json').read_text())\n"
        "source=Path(config['qa_source'])\n"
        "assert data['status']=='prepared' and data['repo']==str(source)\n"
        "assert data['head_at_preparation']==config['head']\n"
        "assert (source/'.git/HEAD').read_bytes()==(config['head']+'\\n').encode()\n"
        "print(json.dumps({'status':'prepared','manifest':str(root/'runtime/pile-reprise.json')}))\n").encode()
    # root runtime/common is intentionally the same exact helper environment.
    result['runtime/common.py'] = result['auxiliary-ports/runtime/common.py']
    result['runtime/git_snapshot.py'] = result['source/git_snapshot.py']
    for name in ('calibrate-all.py', 'calibrate-test-runner.py', 'calibrate-screen.py', 'calibrate-browser.mjs'):
        result['runtime/' + name] = result['auxiliary-ports/runtime/' + name]
    # Attestation A/B is a fresh serialization of root-observed bytes, not an old receipt.
    result['authorization/git-commit.raw'] = source['commit']
    result['authorization/git-tree.raw'] = source['tree']
    result['authorization/head.stdout'] = (ident['head'] + '\n').encode()
    head_ref = request['git_head_ref']
    manifest = dict(source['manifest'], git_commit_ref=planned_ref(root / 'authorization/git-commit.raw', source['commit']),
        git_tree_ref=planned_ref(root / 'authorization/git-tree.raw', source['tree']))
    result['authorization/source-files.json'] = encoded(manifest)
    manifest_ref = planned_ref(root / 'authorization/source-files.json', result['authorization/source-files.json'])
    checkout = {'schema': 'c17-direct-round-source-checkout-v1', 'actor': ident['actor'],
        'round_id': ident['round_id'], 'head': ident['head'], 'qa_root': str(root),
        'round_name': ident['campaign'], 'git_head': ident['head'], 'product_source_root': str(qa),
        'git_tree_verified': True, 'git_head_ref': head_ref, 'source_manifest_ref': manifest_ref}
    result['authorization/source-checkout.json'] = encoded(checkout)
    checkout_ref = planned_ref(root / 'authorization/source-checkout.json', result['authorization/source-checkout.json'])
    git = {'schema': 'c17-wrapper-physical-git-snapshot-v1', 'source_root': str(qa), 'head': ident['head'],
        'head_stdout': planned_ref(root / 'authorization/head.stdout', result['authorization/head.stdout']),
        'commit_raw': manifest['git_commit_ref'], 'tree_raw': manifest['git_tree_ref'], 'physical_refs': [head_ref]}
    result['authorization/git-snapshot.json'] = encoded(git)
    git_ref = planned_ref(root / 'authorization/git-snapshot.json', result['authorization/git-snapshot.json'])
    table = selected_definitions(checked(assets['g1/ab_auxiliary_table.py']), ('expected_row',),
        {'Path': Path, 'JOBS': tuple(request['auxiliary_jobs']),
         'NAMES': {job: 'aux-chrome-' + job for job in request['auxiliary_jobs']},
         'RPC_JOBS': tuple(request['auxiliary_jobs'][:5]), 'DIRECT_SITES': tuple(request['direct_sites']),
         'DISABLED_ARGS': ['--disable-background-networking','--disable-component-update','--disable-sync']})
    contexts = {}; rows = {}
    for job in request['auxiliary_jobs']:
        row = table['expected_row'](root, job); row['executable'] = chrome['executable']; rows[job] = row
        body = {'schema': 'c17-ab-auxiliary-context-v1', 'scope': 'runtime78_exact_round',
            'root': str(root), 'actor': ident['actor'], 'round_id': ident['round_id'], 'round_name': ident['campaign'],
            'head': ident['head'], 'stage': job, 'product_source_root': str(qa),
            'source_checkout_ref': checkout_ref, 'git_snapshot_ref': git_ref, 'source_script': row['source_script']}
        name = 'auxiliary/' + row['name'] + '/context.json'
        result[name] = encoded(body); contexts[job] = planned_ref(root / name, result[name])
    result['authorization/auxiliary-definition-table.json'] = encoded({'jobs': rows, 'context_refs': contexts,
        'status': 'definitions_without_argv_env_birth_defaults_or_runtime_admission'})
    # Full bindings remain late/root; no owner PID, deadline, plan/enrollment or GO invented.
    result['authorization/rpc-construction-inputs.json'] = encoded({'schema': 'c17-full-rpc-construction-inputs-v1',
        'scope': 'definitions_only', 'source_checkout_ref': checkout_ref, 'git_snapshot_ref': git_ref,
        'context_refs': contexts, 'required_sites': 15, 'required_auxiliaries': 14,
        'sql_late_parents': ['B1753','B1760','B1753-power'], 'owner_identity': None,
        'plan': None, 'enrollments': [], 'runtime_admitted': False})
    result['authorization/chrome-files.json'] = encoded({'schema': 'c17-wrapper-chrome-bundle-files-v1',
        'bundle_root': request['copied_chrome'], 'files': chrome['files'], 'tree_origin': request['chrome_tree_ref']})
    api = read_json(request['session_contract_ref'])
    need(api.get('schema') == 'c17-runtime78-session-api-v1' and type(api.get('features')) is list,
         'Définition ABI Session exacte requise')
    api = dict(api, module=planned_ref(root / 'g1/runtime_session.py', result['g1/runtime_session.py']),
               runtime_admitted=False, OS_qualified=False, FULL=False)
    result['g1/api-contract.json'] = encoded(api)
    config['session_contract'] = planned_ref(root / 'g1/api-contract.json', result['g1/api-contract.json'])
    rpc_api = read_json(request['rpc_contract_ref'])
    need(request['rpc_contract_ref'] == assets['runtime78-successor/rpc-abi-contract.json']
         and rpc_api.get('schema') == 'c17-runtime78-root-owned-rpc-abi-v1'
         and rpc_api.get('descriptor_count') == 15 and rpc_api.get('sink_count') == 30
         and rpc_api.get('runtime_admitted') is False and rpc_api.get('qualified') == 0,
         'Contrat RPC fermé exact requis, aucune capacité transposée')
    rpc_api['reader'] = planned_ref(root / 'runtime78-successor/rpc_abi_reader.py',
                                  result['runtime78-successor/rpc_abi_reader.py'])
    result['runtime78-successor/rpc-abi-contract.json'] = encoded(rpc_api)
    config['nested_capture_contract'] = planned_ref(root / 'runtime78-successor/rpc-abi-contract.json',
                                                  result['runtime78-successor/rpc-abi-contract.json'])
    result['prepared-config.json'] = encoded(config)
    # Final-byte ledger, including generated prepare/aliases and late ABI pins.
    # Initial diffs above are overwritten IN MEMORY only, never an emitted raw.
    bases = {name: ref for name, ref in assets.items() if not name.startswith('definition-inputs/')}
    bases['runtime/runtime.py'] = assets['definition-inputs/runtime-before.py']
    bases['runtime/common.py'] = assets['auxiliary-ports/runtime/common.py']
    bases['runtime/git_snapshot.py'] = assets['source/git_snapshot.py']
    for name in ('calibrate-all.py', 'calibrate-test-runner.py', 'calibrate-screen.py', 'calibrate-browser.mjs'):
        bases['runtime/' + name] = assets['auxiliary-ports/runtime/' + name]
    diffs = []
    for name, ref in bases.items():
        original, final = checked(ref), result[name]
        if original != final:
            diff_name = 'construction-diffs/' + name.replace('/', '__') + '.diff'
            result[diff_name] = ''.join(difflib.unified_diff(original.decode().splitlines(keepends=True),
                final.decode().splitlines(keepends=True), fromfile=ref['path'], tofile=str(root / name))).encode()
            result['construction-preimages/' + name] = original
            diffs.append(diff_name)
    for name in ('runtime/runtime.py', 'runtime/common.py', 'runtime/git_snapshot.py'):
        origins.append({'source': bases[name], 'target': str(root / name), 'kind': 'derived_definition_only',
                        'old_result_imported': False})
    result['runtime78-successor/frozen-inputs.json'] = encoded({'schema': 'c17-runtime78-successor-frozen-inputs-v1',
        'sources': {str(root / name): hashlib.sha256(raw).hexdigest() for name, raw in result.items()},
        'all_readonly_definitions': True, 'no_J_M_C16_results_imported': True,
        'admitted_session_module': None, 'admitted_nested_capture_module': None})
    result['full-construction-origin.json'] = encoded({'schema': 'c17-full-construction-origins-v1',
        'definitions': origins, 'diffs': diffs, 'source_input_refs': {key: request[key] for key in (
            'git_manifest_ref','git_head_ref','git_commit_ref','git_tree_ref','python_audit_ref','node_audit_ref')},
        'runtime_admission': None, 'actual_running_manifest': None, 'round_qualified': False,
        'FULL': False, 'release': False, 'state_mutated': False})
    return result


def inputs(request_ref: dict, authority_ref: dict) -> tuple[dict, dict[str, bytes]]:
    request = read_json(request_ref); request['request_ref'] = request_ref
    need(request.get('schema') == 'c17-full-ab-construction-request-v1', 'Requête construction FULL exacte absente')
    ident = identity(request); root = Path(ident['root'])
    need(not root.exists() and not root.is_symlink(), 'Racine déjà présente : aucun remplacement/reprise automatique')
    asset_ref = reference(HERE / 'assets.json'); inventory = read_json(asset_ref)
    assets = inventory['assets']; need(len(assets) == 88, 'Table définitions changée')
    for ref in assets.values(): checked(ref)
    authority(request, authority_ref, asset_ref)  # BEFORE any allocation.
    need(set(request.get('profiles', {})) == {'web','sql','chrome'}, 'Trois profils relus exacts requis')
    for ref in request['profiles'].values(): checked(ref)
    checked(request['session_contract_ref']); checked(request['rpc_contract_ref'])
    source = source_inputs(request, assets); deps = dependency_inputs(request, assets); chrome = verify_chrome(request)
    # Table fourteen closed from the actual source, not request-provided arbitrary names.
    tree = ast.parse(checked(assets['g1/ab_auxiliary_table.py']))
    env = {'Path': Path, 're': re}
    constants = [n for n in tree.body if isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id in ('RPC_JOBS','DIRECT_SITES','JOBS') for t in n.targets)]
    exec(compile(ast.Module(body=constants, type_ignores=[]), '<aux-table-constants>', 'exec'), env)
    request['auxiliary_jobs'] = list(env['JOBS']); request['direct_sites'] = list(env['DIRECT_SITES'])
    outputs = payloads(request, assets, source, deps, chrome)
    need(all(not Path(name).is_absolute() and '..' not in Path(name).parts for name in outputs), 'Destination hors racine')
    need(not any(name.startswith(('ledger/', 'coverage/', 'runtime/calibration/')) for name in outputs),
         'Ancienne preuve/runtime copiée comme résultat')
    # Recheck inputs after expensive rendering and before allocation.
    source_inputs(request, assets); dependency_inputs(request, assets); verify_chrome(request)
    for ref in assets.values(): checked(ref)
    authority(request, authority_ref, asset_ref)
    return request, outputs


def write_new(root: Path, relative: str, raw: bytes) -> None:
    path = root / relative
    need(path.is_relative_to(root) and not path.is_symlink(), 'Destination hors racine/symlink')
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    for parent in path.parents:
        if parent == root.parent: break
        need(not parent.is_symlink() and parent.resolve(strict=True) == parent, 'Parent redirigé')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())


def construct(request_ref: dict, authority_ref: dict) -> dict:
    request, outputs = inputs(request_ref, authority_ref)
    authority_body = read_json(authority_ref)
    initial_constructor = authority_body['constructor']
    need(reference(Path(__file__)) == initial_constructor, 'Constructeur modifié avant allocation')
    root = Path(request['root']); root.mkdir(mode=0o700)  # exact absent root only.
    for relative in ('profiles/runtime/home','profiles/runtime/data','profiles/runtime/test-data',
            'profiles/runtime/logs-data','profiles/runtime/tmp','bootstrap-home','bootstrap-tmp',
            'session-events','session-rpc/request','session-rpc/ack','session-rpc/cancel',
            'session-rpc/enrollment','session-rpc/envelope','ledger','coverage','complements/runs',
            'runtime/calibration','auxiliary/playwright-unused','runtime/vite-cache'):
        (root / relative).mkdir(parents=True, mode=0o700, exist_ok=True)
    for job in request['auxiliary_jobs']:
        (root / 'auxiliary' / ('aux-chrome-' + job) / 'profile').mkdir(mode=0o700, parents=True)
    for relative, raw in outputs.items(): write_new(root, relative, raw)
    actual = {name: reference(root / name) for name in outputs}
    need(all(actual[name] == planned_ref(root / name, raw) for name, raw in outputs.items()), 'Émission différente des octets fermés')
    assets_ref = reference(HERE / 'assets.json'); assets = read_json(assets_ref)['assets']
    source_inputs(request, assets); dependency_inputs(request, assets); verify_chrome(request)
    for ref in assets.values(): checked(ref)
    authority(request, authority_ref, assets_ref)
    need(reference(Path(__file__)) == initial_constructor, 'Constructeur modifié après émission')
    # No go.json, slot or admitted flags are manufactured by this constructor.
    receipt = {'schema': 'c17-full-physical-construction-v1', 'root': str(root),
        'actor': request['actor'], 'round_id': root.name.removeprefix('therese-'),
        'head': request['expected_head'], 'constructor': initial_constructor,
        'request': request_ref, 'external_construction_authority': authority_ref, 'outputs': actual,
        'runtime_admission': None, 'owner_context_deferred_to_live_root': True,
        'FULL': False, 'release': False, 'runtime_started': False, 'state_mutated': False}
    write_new(root, 'full-physical-construction.json', encoded(receipt))
    return reference(root / 'full-physical-construction.json')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request-ref', required=True, help='JSON exact path/sha256/bytes')
    parser.add_argument('--authority-ref', required=True, help='Ref décision construct root externe actuelle')
    parser.add_argument('--construct', action='store_true')
    args = parser.parse_args()
    request_ref, authority_ref = json.loads(args.request_ref), json.loads(args.authority_ref)
    if not args.construct:
        request, outputs = inputs(request_ref, authority_ref)
        print(json.dumps({'status':'inputs_verified_not_allocated_not_runtime_admitted',
            'root':request['root'], 'outputs':len(outputs), 'runtime_enabled':False, 'FULL':False}))
        return 0
    print(json.dumps(construct(request_ref, authority_ref)))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, TypeError, KeyError, OSError) as error:
        print(json.dumps({'status':'construction_refused_before_runtime', 'error':str(error), 'FULL':False}), file=sys.stderr)
        raise SystemExit(2)
