#!/usr/bin/env python3
"""Construction exclusive WRAPPER_CANARY ; jamais de Session ou workload.

Le GO outil de préparation reste externe. Les seuls imports QA sont les
constructeurs/renders purs épinglés. Le seul sous-processus de construction
est Node VM pour le corps Playwright defaultArgs, sans navigateur ni paquet
Node importé. Aucun runtime n'est lancé par ce script.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, UTC
import difflib
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tomllib

PREP = Path('/private/tmp/therese-c17-rpc-integration-UctqC8UG')
QA = Path('/private/tmp/therese-c17-wrapper-source-kGvU1hdx/source')
PROOFS = QA.parent / 'proofs'
HEAD = '2d69e30c9c6dd18823ee6102271876003a6a67cc'
FUTURE_ROOT = Path('/private/tmp/therese-c17-wrapper-canary-8612f55886284332a3ac6a7bc9615021')
NODE = Path('/Users/synoptia/.nvm/versions/node/v22.19.0/bin/node')
PYTHON_PHYSICAL = Path('/Users/synoptia/.local/share/uv/python/cpython-3.13.5-macos-aarch64-none/bin/python3.13')
SOURCE_MANIFEST_SHA = '0904574e2b35b523b8454b33156f595f05a62e21609453a65db59ae516423b89'
PYTHON_METADATA_SHA = '5e32c122a845df3f598258b39dd18e150d50f26104f350d25756449fabcebf82'
WEB = {'path': '/private/tmp/therese-c17-web-root-metadata-POjxSafe/web.sb',
       'sha256': '51ff2e21500393704ea8709fb9bd177dc1f88793d1e92d09c68be70d905807ff', 'bytes': 1780}
CHROME_UI_PROFILE = {'path': '/private/tmp/therese-c17-chrome-ui-exact-LvZDmsDL/chrome.sb',
                     'sha256': '5bd845c92b4466733c02749bbc12635426a9ed6be36ad3265f954367afd6fb1d', 'bytes': 1416}
CHROME_UNIX_PREIMAGE = {'path': '/private/tmp/therese-c17-chrome-unixbind-PUUOvY00/preimage-chrome.sb',
                        'sha256': '5bd845c92b4466733c02749bbc12635426a9ed6be36ad3265f954367afd6fb1d', 'bytes': 1416}
CHROME_UNIX_PROFILE = {'path': '/private/tmp/therese-c17-chrome-unixbind-PUUOvY00/chrome.sb',
                       'sha256': '9c6d17def6fa847f0740bb2398d52a8ef6dfc3a8279563dd1bda815d7892e872', 'bytes': 1698}
CHROME_ROOTDOMAIN_PREIMAGE = {'path': '/private/tmp/therese-c17-chrome-rootdomain-h5whIv/preimage-chrome.sb',
                              'sha256': '9c6d17def6fa847f0740bb2398d52a8ef6dfc3a8279563dd1bda815d7892e872', 'bytes': 1698}
CHROME_ROOTDOMAIN_PROFILE = {'path': '/private/tmp/therese-c17-chrome-rootdomain-h5whIv/chrome.sb',
                  'sha256': '5266a6b026b5eb8192e030b5c27cc0001b65fce97d5840a9979e16a0d4ac151d', 'bytes': 1914}
CHROME_UNIX_INDEX = Path('/private/tmp/therese-c17-chrome-unixbind-PUUOvY00/INDEX.json')
CHROME_ROOTDOMAIN_INDEX = Path('/private/tmp/therese-c17-chrome-rootdomain-h5whIv/INDEX.json')
CHROME_V8_PROFILE = {'path': '/private/tmp/therese-c17-fresh-wrapper-builder-v7-cnR8Hm/profile/chrome.sb',
                     'sha256': 'c9101b2a356679057f3e116c72a2546f51e851ee997e404c6120cb59627580e8', 'bytes': 1949}
CHROME_PREIMAGE_PROFILE = {'path': '/private/tmp/therese-c17-fresh-wrapper-builder-v10-ynPAzC/profile/chrome.sb',
                  'sha256': '19808ee2cac3169e9fb8c71c24385bcbb97f924c5ed785f4651817ecaa179b0c', 'bytes': 2067}
CHROME_PREVIOUS_PROFILE = {'path': '/private/tmp/therese-c17-wrapper-profile-three-builder-G8n4Ef/profile/chrome.sb',
                           'sha256': 'bee3c2e780e58cbc80ed7e37d64115adf08997aab39dae8f11b56050785633a9', 'bytes': 2375}
CHROME_MAIN12_PROFILE = {'path': '/private/tmp/therese-c17-wrapper12-metadata-parent-MtcoJZ/profile/chrome.sb',
                         'sha256': '980b12368975718d33dba1572ce94da04ca378ca827df1be10a1ed15a7104cdb', 'bytes': 2439}
CHROME_GETCONF_PROFILE = {'path': '/private/tmp/therese-c17-getconf-dirhelper-XeZCB9/profiles/dirhelper.sb',
                          'sha256': '2ecae3a24ec871a44827b3f712ced1ef5e84d8f778906c37b3a5b51bb374dcdf', 'bytes': 2499}
CHROME_PROFILE = {'path': '/private/tmp/therese-c17-wrapper13-dirhelper-P5WQpQ/profile/chrome.sb',
                  'sha256': '2ecae3a24ec871a44827b3f712ced1ef5e84d8f778906c37b3a5b51bb374dcdf', 'bytes': 2499}
CHROME_INDEX = Path('/private/tmp/therese-c17-fresh-wrapper-builder-v7-cnR8Hm/profile/INDEX.json')
WITNESS = Path('/private/tmp/therese-c17-test-runner-boundary-eUIHsp')
WITNESS_FILES = ('source/runner_boundary.py', 'INDEX.json', 'tests/test_runner_boundary.py',
                 'proofs/pure-test-receipt.json', 'proofs/returned-output.log',
                 'diffs/calibrate-test-runner.py.diff', 'diffs/wrapper_blueprint.py.diff')
OBSERVABILITY = Path('/private/tmp/therese-c17-rpc-cause-observability-NRYrmF')
OBSERVABILITY_INDEX_SHA = '604e4e02062dd37cafbf9e67b2545b7697bad70a7aeac2825598cefaa63d7596'
OBSERVABILITY_NAMES = ('rpc_protocol.py', 'rpc_client.py', 'rpc_dispatcher.py', 'session_rpc_adapter.py')
OBSERVABILITY_HELPER = 'rpc_diagnostics.py'
OBSERVABILITY_HELPER_SHA = 'ae86d9b538429ca2f168cc386ea7a6e4d05ddad4e8b9f926a29dfbb4f5533058'
INDEX_PINS = {
    PREP / 'successor/SUCCESSOR-RPC-INDEX.json': '9b6daaf60d095fbfda38efae717191147cf2dc90881ffff2566166fc90cfc737',
    PREP / 'support-v2/SUPPORT-V2-INDEX.json': '60c2de8a956434d3dc395ad9b93ec9c6be24691922f8a0c97471ae8eb0fb525d',
    PREP / 'g1-review-26/INDEX.json': '0138215a9d5e5d20b9033bc8e6ee0887ffc8423a6a163108bc7daae38e797737',
    PREP / 'auxiliary/INDEX.json': 'dbc5a8ec553333715d9c858441b683a1695a3bfa2328ddcc1d90cd4dbb049bd7',
    PREP / 'coordinator/COORDINATOR-INDEX.json': '0ce723809e99a066c4581fb70930d057ee3aa117c8a5c52b2e96eeabfd1a28e3',
    Path('/private/tmp/therese-c17-web-root-metadata-POjxSafe/INDEX.json'): '6081b027d60263f3785b8c3462963021f9c362a3e7f411b2b98c4118a3b2b4cb',
    Path('/private/tmp/therese-c17-chrome-ui-exact-LvZDmsDL/INDEX.json'): 'd1205f29371042b801bdd92293a03287b4fd8f0bf10aecd0b1ccd3442ce0a46e',
    CHROME_UNIX_INDEX: '5f2a3e941e5c66e43c64a9970e528228ea68cc49586ccb5cb6134216c6611bd5',
    CHROME_ROOTDOMAIN_INDEX: 'c0f542c377d37efd8e88103e2d760fdc126b785793f167755a319f0f5fb8d3c6',
    CHROME_INDEX: '64636dce1646b3bb8bf67489bf1c9cf90cb6bd562037d84ff569e67fff3797f6',
    WITNESS / 'INDEX.json': '771565210b1ab41ca7e5a43c89fa63a034c57872515a698a12161e47adfe11b7',
    OBSERVABILITY / 'INDEX.json': OBSERVABILITY_INDEX_SHA,
}
CORE_G1 = ('runtime_session.py', 'runtime_bounds.py', 'relay_protocol.py',
           'root_stage_relay.py', 'runtime_launch_gate.py', 'sql.sb', 'web.sb', 'chrome.sb', 'lsof_gate.py')
CORE_TRANSPORT = ('session_rpc_adapter.py', 'rpc_protocol.py', 'rpc_client.py',
                  'rpc_dispatcher.py', 'rpc_peer.py', 'rpc_unix.py')
CHROME_BUNDLE = Path('/private/tmp/therese-c17-chrome-qa-copy-RoZmwsja/Google Chrome.app')
CHROME = CHROME_BUNDLE / 'Contents/MacOS/Google Chrome'
FRAMEWORK = CHROME_BUNDLE / 'Contents/Frameworks/Google Chrome Framework.framework/Versions/154.0.8037.99/Google Chrome Framework'
G1_PREIMAGE_SHA = 'f8e9daacbb9b88b628aeefbd33ba86df45135eba571241c26d3d5721b3a4e781'
G1_QA_PATHS_SHA = '8e179d5c5ed073d36accbe33714756dfa6d07b6e196a42fb97dff9fba3ad1e72'
CHROME_CONTRACT_PREIMAGE_SHA = '26e8374a23b7f67a5c45cbc457156bfd15735cd2578ca0fd7990b3df989630db'
CHROME_CONTRACT_QA_REF = {'path': '/private/tmp/therese-c17-fresh-wrapper-builder-v8-pB5tPP/preview/chrome_contract-qa.py',
                         'sha256': '7922a13bdc239338ea9dedf37bf06ef1c91931b77a5275a2db6007d89a9a42ba', 'bytes': 4118}
CHROME_QA_COPY_REF = {'path': '/private/tmp/therese-c17-chrome-qa-copy-RoZmwsja/v3-receipt.json',
                      'sha256': 'f97793cb43454051da734685185cb5d4e5b5ffbabc516580287195ef3d32993c', 'bytes': 17160}
JOBS = ('rpc-all-runtime_ui-visual_capture-network_capture', 'rpc-screen-negative',
        'rpc-screen-positive-visual', 'rpc-screen-positive-network', 'rpc-screen-restored')
OLD_SQL_SHA = 'b1d4e8ab0b01f18066bdc8b1cf09989a90e8bbd517230f2d07e5a8efe14a2a7d'
HISTORICAL_IPS = {'path': '/Users/synoptia/Library/Logs/DiagnosticReports/Google Chrome-2026-10-08-143832.000.ips',
                  'sha256': '2e1d81e295a1a75af7498e1698b4284c53206f7a031058ebd3331aad6fc8a3b3', 'bytes': 31835}
ARCHIVED_IPS = Path('/private/tmp/therese-c17-root-close6-I9BhiHpZ/chrome25577.ips')
HISTORICAL_EVIDENCE = {'path': '/private/tmp/therese-c17-chrome-rootdomain-h5whIv/EVIDENCE.json',
                       'sha256': '57253794719541add1642bc011ff0437248eb922eb798ec4b6132a8ff81c5f6a', 'bytes': 803}
HISTORICAL_REPLAYS = {
    Path('/private/tmp/therese-c17-root-v10-71-replay-v3-zRFPBqd5/receipt.json'):
        {'sha256': 'c0864b435265a4c485c78837207184d3964e966689eb97785fe3ab4ff9e3f8e5',
         'bytes': 68793, 'source_refs': 307, 'passed': True, 'errors': 0},
    Path('/private/tmp/therese-c17-root-v10-71-replay-v2-eaECHtDi/receipt.json'):
        {'sha256': '1955d363f88493a62d6423baeed094f10ab53fbb6ced7eaac94251ba73cdfb57',
         'bytes': 66947, 'source_refs': 303, 'passed': False, 'errors': 3},
}


def need(ok, why):
    if not ok:
        raise ValueError(why)


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2) + '\n').encode()


def regular_bytes(path: Path, limit=20_000_000):
    path = Path(path)
    need(path.is_absolute() and not path.is_symlink() and path.resolve(strict=True) == path, 'Alias source : ' + str(path))
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as stream:
        before = os.fstat(stream.fileno())
        need(stat.S_ISREG(before.st_mode) and before.st_size <= limit, 'Source non régulière/trop grande')
        raw = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    named = path.lstat()
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
         (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) and
         (named.st_dev, named.st_ino) == (before.st_dev, before.st_ino), 'Source changée en lecture')
    return raw


def reference(path: Path):
    """Hash streaming pour les deux binaires Chrome, sans import/exécution."""
    path = Path(path)
    need(path.is_absolute() and not path.is_symlink() and path.resolve(strict=True) == path, 'Alias référence')
    digest = hashlib.sha256()
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as stream:
        before = os.fstat(stream.fileno())
        need(stat.S_ISREG(before.st_mode), 'Référence non régulière')
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
        after = os.fstat(stream.fileno())
    named = path.lstat()
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
         (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) and
         (named.st_dev, named.st_ino) == (before.st_dev, before.st_ino), 'Référence changée')
    return {'path': str(path), 'sha256': digest.hexdigest(), 'bytes': before.st_size}


def checked(ref):
    need(type(ref) is dict and set(ref) == {'path', 'sha256', 'bytes'}
         and type(ref['path']) is str and re.fullmatch('[a-f0-9]{64}', ref['sha256'])
         and type(ref['bytes']) is int and ref['bytes'] >= 0, 'Ref SHA/bytes exacte obligatoire')
    raw = regular_bytes(Path(ref['path']))
    need(len(raw) == ref['bytes'] and hashlib.sha256(raw).hexdigest() == ref['sha256'], 'Ref modifiée : ' + ref['path'])
    return raw


def json_checked(ref):
    value = json.loads(checked(ref))
    need(type(value) is dict, 'Objet JSON obligatoire')
    return value


def future_root(root: Path):
    root = Path(root)
    need(root == FUTURE_ROOT and root.is_absolute() and root.parent == Path('/private/tmp')
         and re.fullmatch(r'therese-c17-wrapper-canary-[a-z0-9_]{8,64}', root.name)
         and root.parent.resolve(strict=True) == root.parent
         and not root.exists() and not root.is_symlink(), 'Root neuf canonique absent requis')
    return root


def gather_pins(value, relative_root=PREP, pointer=''):
    if isinstance(value, list):
        for index, item in enumerate(value):
            yield from gather_pins(item, relative_root, pointer + '/' + str(index))
    elif isinstance(value, dict):
        if isinstance(value.get('path'), str) and re.fullmatch('[a-f0-9]{64}', str(value.get('sha256', ''))):
            path = Path(value['path'])
            if not path.is_absolute():
                path = relative_root / path
            yield path, value['sha256'], value.get('bytes'), pointer
        else:
            for key, item in value.items():
                escaped = str(key).replace('~', '~0').replace('/', '~1')
                yield from gather_pins(item, relative_root, pointer + '/' + escaped)


def historical_ips_archive(origin: Path, pointer: str, value: dict) -> tuple[dict, dict]:
    """Trois seules observations anciennes : octets archivés, jamais une ref live au chemin absent."""
    need(type(value) is dict and value == HISTORICAL_IPS, 'Triple IPS historique différent')
    if origin == CHROME_ROOTDOMAIN_INDEX:
        need(pointer == '/origin_refs/4' and reference(origin) ==
             {'path': str(origin), 'sha256': INDEX_PINS[origin], 'bytes': 2605},
             'Index/pointeur IPS historique différent')
        evidence = json_checked(HISTORICAL_EVIDENCE)
        need(evidence.get('diagnostic_only') is True and evidence.get('chrome_pid') == 25577
             and evidence.get('origin_crash_report') == HISTORICAL_IPS['path'],
             'IPS historique hors diagnostic')
        kind, passed, errors = 'diagnostic_index', None, None
    else:
        expected = HISTORICAL_REPLAYS.get(origin)
        need(expected is not None and pointer == '/source_refs/267', 'Origine/pointeur IPS non autorisé')
        need(reference(origin) == {'path': str(origin), 'sha256': expected['sha256'],
                                   'bytes': expected['bytes']}, 'Rejeu historique changé')
        receipt = json.loads(regular_bytes(origin))
        need(receipt.get('schema') == 'c17-root-v10-71-pure-replay-v1'
             and receipt.get('actor') == '/root' and receipt.get('tests') == 71
             and receipt.get('unchanged') is True and receipt.get('passed') is expected['passed']
             and receipt.get('errors') == expected['errors'] and receipt.get('failures') == 0
             and receipt.get('skipped') == 0 and receipt.get('root_built') is False
             and receipt.get('G1_imported') is False and receipt.get('native_workload_executed') is False
             and receipt.get('FULL') is False and receipt.get('release') is False
             and receipt.get('forbidden_attempts') == []
             and type(receipt.get('source_refs')) is list
             and len(receipt['source_refs']) == expected['source_refs']
             and receipt['source_refs'][267] == HISTORICAL_IPS,
             'Rejeu pur historique réétiqueté')
        if expected['passed']:
            red = next(path for path, row in HISTORICAL_REPLAYS.items() if row['passed'] is False)
            need(receipt.get('fixture_entries_after_cleanup') == []
                 and receipt.get('earlier_red_receipt_ref') ==
                 {'path': str(red), 'sha256': HISTORICAL_REPLAYS[red]['sha256'],
                  'bytes': HISTORICAL_REPLAYS[red]['bytes']},
                 'Rejeu vert détaché du rouge')
        kind, passed, errors = ('pure_replay_green' if expected['passed'] else 'pure_replay_red',
                                expected['passed'], expected['errors'])
    try:
        Path(HISTORICAL_IPS['path']).lstat()
    except FileNotFoundError:
        pass
    else:
        need(False, 'Ancien chemin IPS présent ; résolution archivale refusée')
    archived_stat = ARCHIVED_IPS.lstat()
    need(stat.S_ISREG(archived_stat.st_mode) and archived_stat.st_uid == 501
         and archived_stat.st_gid == 0 and archived_stat.st_mode == 0o100600
         and archived_stat.st_nlink == 1 and ARCHIVED_IPS.resolve(strict=True) == ARCHIVED_IPS,
         'Copie IPS archivale non canonique')
    archive_ref = reference(ARCHIVED_IPS)
    need(archive_ref['sha256'] == HISTORICAL_IPS['sha256']
         and archive_ref['bytes'] == HISTORICAL_IPS['bytes'], 'Octets IPS archivés différents')
    observation = {'origin': str(origin), 'pointer': pointer, 'kind': kind,
                   'old_path': HISTORICAL_IPS['path'], 'old_path_absent': True,
                   'old_sha256': HISTORICAL_IPS['sha256'], 'old_bytes': HISTORICAL_IPS['bytes'],
                   'archive_path': str(ARCHIVED_IPS), 'archive_sha256': archive_ref['sha256'],
                   'archive_bytes': archive_ref['bytes'], 'archive_uid': archived_stat.st_uid,
                   'archive_gid': archived_stat.st_gid, 'archive_mode': archived_stat.st_mode,
                   'archive_nlink': archived_stat.st_nlink, 'passed': passed, 'errors': errors,
                   'runtime_qualification': False, 'close6_receipt_provenance_claimed': False}
    return archive_ref, observation


def validate_indexes():
    pins, documents, observations = {}, {}, []
    for path, digest in INDEX_PINS.items():
        row = reference(path)
        need(row['sha256'] == digest, 'Index changé : ' + str(path))
        documents[path] = json.loads(regular_bytes(path))
        pins[str(path)] = row
        relative_root = path.parent if path in {CHROME_UNIX_INDEX, CHROME_ROOTDOMAIN_INDEX, CHROME_INDEX} else PREP
        for source, sha, size, pointer in gather_pins(documents[path], relative_root):
            if str(source) == HISTORICAL_IPS['path']:
                actual, observation = historical_ips_archive(path, pointer,
                    {'path': str(source), 'sha256': sha, 'bytes': size})
                observations.append(observation)
            else:
                actual = reference(source)
            need(actual['sha256'] == sha and (size is None or actual['bytes'] == size), 'Pin index changé : ' + str(source))
            need(actual['path'] not in pins or pins[actual['path']] == actual, 'Index contradictoires')
            pins[actual['path']] = actual
    for replay in HISTORICAL_REPLAYS:
        receipt = json.loads(regular_bytes(replay))
        archive_ref, observation = historical_ips_archive(replay, '/source_refs/267',
                                                          receipt['source_refs'][267])
        observations.append(observation)
        pins[str(replay)] = reference(replay)
        need(str(ARCHIVED_IPS) not in pins or pins[str(ARCHIVED_IPS)] == archive_ref,
             'Copie IPS historique contradictoire')
        pins[str(ARCHIVED_IPS)] = archive_ref
    need(len(observations) == 3 and len({(o['origin'], o['pointer']) for o in observations}) == 3,
         'Trois observations IPS exactes requises')
    return pins, documents, observations


def load_pure(name, path, aliases=None):
    """Imports explicites des définitions seulement, jamais g1/runtime_session."""
    need(name not in {'runtime_session', 'runtime', 'app'} and '/g1' not in str(path), 'Import instrument runtime interdit')
    if aliases:
        sys.modules.update(aliases)
    spec = importlib.util.spec_from_file_location(name, path)
    need(spec is not None and spec.loader is not None, 'Module pur absent')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    need(not any(key == 'runtime_session' or key == 'app' or key.startswith('app.') for key in sys.modules), 'Import runtime interdit')
    return module


def verify_pth_snapshot(pth, metadata_raw):
    need(hashlib.sha256(metadata_raw).hexdigest() == PYTHON_METADATA_SHA, 'Baseline metadata Python changé')
    metadata = json.loads(metadata_raw)
    need(metadata.get('head') == HEAD and metadata.get('qa_source') == str(QA)
         and metadata.get('status') == 'PASS' and len(metadata.get('pth', [])) == 4
         and pth == {item['path']: item for item in metadata['pth']}, 'Ensemble/ref pth exact changé')


def deps_check():
    """Même contrôle metadata/locks que les audits root, sans import paquet."""
    norm = lambda name: re.sub('[-_.]+', '-', name).lower()
    versions = {}
    for item in tomllib.loads(regular_bytes(QA / 'uv.lock').decode())['package']:
        versions.setdefault(norm(item['name']), set()).add(item['version'])
    site = QA / '.venv-conforme/lib/python3.13/site-packages'
    rows = []
    for dist in importlib.metadata.distributions(path=[str(site)]):
        name, version = dist.metadata.get('Name'), dist.version
        need(name and version in versions.get(norm(name), set()), 'Distribution Python hors lock')
        rows.append((name, version))
    need(len(rows) == 149 and len({norm(name) for name, _ in rows}) == 149, '149 distributions distinctes requises')
    pth = {str(p): reference(p) for p in sorted(site.glob('*.pth'))}
    metadata_raw = regular_bytes(PROOFS / 'python-metadata-result.json')
    verify_pth_snapshot(pth, metadata_raw)
    node_rows = []
    for directory in (QA, QA / 'src/frontend'):
        lock = json.loads(regular_bytes(directory / 'package-lock.json'))
        installed = optional = 0
        for name, entry in lock['packages'].items():
            if not name or 'node_modules/' not in name:
                continue
            target = directory / name / 'package.json'
            need(target.is_relative_to(directory), 'Metadata npm hors racine')
            if not target.exists():
                need(entry.get('optional') is True and not target.is_symlink(), 'Paquet npm absent')
                optional += 1
                continue
            physical = target.resolve(strict=True)
            need(physical.is_relative_to(directory / 'node_modules'), 'Metadata npm hors QA')
            need(json.loads(regular_bytes(physical))['version'] == entry['version'], 'Version npm hors lock')
            installed += 1
        node_rows.append({'root': str(directory), 'installed': installed,
                          'missing_optional': optional, 'lock_ref': reference(directory / 'package-lock.json')})
    need([r['installed'] for r in node_rows] == [3, 427] and
         [r['missing_optional'] for r in node_rows] == [1, 86], 'Inventory npm distinct du gel physique')
    need((QA / '.venv-conforme/bin/python').resolve(strict=True) == PYTHON_PHYSICAL, 'Python QA autre runtime physique')
    guard = site / 'urllib3/util/connection.py'
    need(reference(guard)['sha256'] == '412d8dab54efff6c201501e71e66b67c71563272b3ac1b046f85125349a26d2e', 'Guard urllib3 changé')
    return {'python_count': len(rows), 'python_lock_ref': reference(QA / 'uv.lock'),
            'pth': pth, 'pth_baseline_ref': reference(PROOFS / 'python-metadata-result.json'),
            'node': node_rows, 'urllib3_ref': reference(guard),
            'metadata_only_not_runtime_qualification': True,
            'all_dependency_package_bodies_rehashed': False,
            'byte_level_dependency_copy_parity_newly_qualified': False}


def assignment_delta(source: str, name: str, expected, replacement):
    """Remplace une seule valeur, puis prouve l'égalité AST de tout le reste."""
    tree = ast.parse(source)
    matches = []
    for node in tree.body:
        target = node.target if isinstance(node, ast.AnnAssign) else (
            node.targets[0] if isinstance(node, ast.Assign) and len(node.targets) == 1 else None)
        if isinstance(target, ast.Name) and target.id == name:
            matches.append(node)
    need(len(matches) == 1 and ast.literal_eval(matches[0].value) == expected, 'Ancre AST exacte absente : ' + name)
    node = matches[0].value
    lines = source.splitlines(keepends=True)
    begin = sum(len(s.encode()) for s in lines[:node.lineno - 1]) + node.col_offset
    end = sum(len(s.encode()) for s in lines[:node.end_lineno - 1]) + node.end_col_offset
    raw = source.encode()
    derived = (raw[:begin] + repr(replacement).encode() + raw[end:]).decode()
    other = ast.parse(derived)
    def cleared(document):
        for candidate in document.body:
            target = candidate.target if isinstance(candidate, ast.AnnAssign) else (
                candidate.targets[0] if isinstance(candidate, ast.Assign) and len(candidate.targets) == 1 else None)
            if isinstance(target, ast.Name) and target.id == name:
                candidate.value = ast.Constant(value=None)
        return ast.dump(document, include_attributes=False)
    need(cleared(tree) == cleared(other), 'Autre delta AST interdit')
    return derived


def wrapper_slot(root):
    return {root.name: {'decision_path': str(root / 'decision.json'), 'binding_path': str(root / 'binding.json'),
        'actor': '/root', 'round_id': root.name, 'round_name': 'WRAPPER_CANARY', 'qa_root': str(root),
        'head': HEAD, 'product_source_root': str(QA), 'qa_python': str(QA / '.venv-conforme/bin/python')}}


def runner_events_delta(source: str) -> str:
    """Ajoute un seul parent QA ; tout autre AST du runner doit rester égal."""
    before = ast.parse(source)
    functions = [node for node in before.body if isinstance(node, ast.FunctionDef)
                 and node.name == 'prepare_qa_directories']
    need(len(functions) == 1, 'Fonction parents QA exacte absente')
    loops = [node for node in functions[0].body if isinstance(node, ast.For)
             and isinstance(node.target, ast.Name) and node.target.id == 'folder']
    need(len(loops) == 1 and isinstance(loops[0].iter, ast.Tuple)
         and len(loops[0].iter.elts) == 10, 'Table parents QA initiale différente')
    expected = ast.parse('root / "session-rpc"', mode='eval').body
    need(ast.dump(loops[0].iter.elts[0], include_attributes=False)
         == ast.dump(expected, include_attributes=False), 'Ancre session-rpc différente')
    anchor = '    for folder in (root / "session-rpc", root / "output", root / "runtime/calibration",\n'
    need(source.count(anchor) == 1, 'Ancre textuelle parents QA non unique')
    derived = source.replace(anchor,
        '    for folder in (root / "session-events", root / "session-rpc", root / "output", root / "runtime/calibration",\n', 1)
    after = ast.parse(derived)
    function = next(node for node in after.body if isinstance(node, ast.FunctionDef)
                    and node.name == 'prepare_qa_directories')
    loop = next(node for node in function.body if isinstance(node, ast.For)
                and isinstance(node.target, ast.Name) and node.target.id == 'folder')
    need(len(loop.iter.elts) == 11 and ast.dump(loop.iter.elts[0], include_attributes=False)
         == ast.dump(ast.parse('root / "session-events"', mode='eval').body, include_attributes=False),
         'Seul nouveau parent session-events requis')
    loop.iter.elts.pop(0)
    need(ast.dump(before, include_attributes=False) == ast.dump(after, include_attributes=False),
         'Autre delta AST runner interdit')
    return derived


def validate_closed_g1(raw):
    values = {}
    for node in ast.parse(raw).body:
        target = node.target if isinstance(node, ast.AnnAssign) else (
            node.targets[0] if isinstance(node, ast.Assign) and len(node.targets) == 1 else None)
        if isinstance(target, ast.Name) and target.id in {'RUNTIME_ENABLED', 'OS_STARTUP_QUALIFIED', 'CAPABILITIES', 'ADMISSION_TABLE', 'WRAPPER_ADMISSION_TABLE'}:
            values[target.id] = ast.literal_eval(node.value)
    need(values.get('RUNTIME_ENABLED') is False and values.get('OS_STARTUP_QUALIFIED') is False
         and type(values.get('CAPABILITIES')) is dict and not any(values['CAPABILITIES'].values())
         and values.get('ADMISSION_TABLE') == {} and values.get('WRAPPER_ADMISSION_TABLE') == {}, 'Base G1 non fermée')


class Emitter:
    def __init__(self, root):
        self.root, self.outputs = root, {}
    def write(self, relative, raw):
        path = self.root / relative
        need(type(raw) is bytes and path.is_relative_to(self.root) and '..' not in Path(relative).parts
             and not path.exists() and not path.is_symlink(), 'Sortie déjà présente/hors root')
        for parent in path.parents:
            if parent == self.root.parent:
                break
            need(not parent.is_symlink(), 'Parent de sortie alias')
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        need(path.parent.resolve(strict=True) == path.parent, 'Parent non canonique')
        with os.fdopen(os.open(path, os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_WRONLY, 0o600), 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        row = reference(path)
        self.outputs[str(path)] = row
        return row
    def json(self, relative, value):
        return self.write(relative, encoded(value))


NODE_DEFAULTS_VM = r'''
import vm from 'node:vm';
import fs from 'node:fs';
const input=JSON.parse(fs.readFileSync(0,'utf8'));
const need=(ok,why)=>{if(!ok)throw Error(why);};
const code=input.chromium;
const from=code.indexOf('  async defaultArgs(options, isPersistent, userDataDir) {');
const to=code.indexOf('  async waitForReadyState(options, browserLogsCollector) {',from);
need(from>0&&to>from&&code.indexOf('  async defaultArgs(options, isPersistent, userDataDir) {',from+1)===-1,'Methods ambiguous');
const switches=vm.createContext({module:{exports:{}},process:{env:{}},Boolean,Object});
new vm.Script(input.switches).runInContext(switches,{timeout:500});
const ctx=vm.createContext({import_chromiumSwitches:{chromiumSwitches:switches.module.exports.chromiumSwitches},
 import_os:{default:{platform:()=> 'darwin'}},import_utils:{hasGpuMac:()=>input.has_gpu_mac},process:{env:{}},URL,Error});
const defaults=new vm.Script('(new (class Defaults {\n'+code.slice(from,to)+'\n})())').runInContext(ctx,{timeout:500});
const rows={};
for(const item of input.jobs){
 const args=await defaults.defaultArgs({...item.original_options,cdpPort:17594},false,item.profile);
 const argv=[input.executable,...Array.from(args),'--remote-debugging-address=127.0.0.1'];
 need(!argv.includes('--no-sandbox')&&!argv.includes('--remote-debugging-pipe')&&!argv.some(a=>a.startsWith('--headless'))&&
 argv.filter(a=>a.startsWith('--user-data-dir=')).length===1,'Original options lost');
 rows[item.job]=argv;
}
process.stdout.write(JSON.stringify(rows));
'''


def chrome_prepare(emitter, chrome_contract, gpu_ref, chrome_qa_copy_ref):
    root = emitter.root
    source_files = [QA / 'node_modules/playwright-core/lib/server/chromium/chromium.js',
        QA / 'node_modules/playwright-core/lib/server/chromium/chromiumSwitches.js',
        QA / 'node_modules/playwright-core/lib/server/utils/hostPlatform.js']
    refs = [reference(p) for p in source_files]
    raw_gpu = checked(gpu_ref)
    need(b'Metal: Supported' in raw_gpu, 'Observation GPU physique Metal absente')
    local_gpu = emitter.write('proofs/system-profiler-displays.raw', raw_gpu)
    rows = chrome_contract.plan(root)['jobs']
    need(set(rows) == set(JOBS) and all(row['executable'] == str(CHROME) for row in rows.values()),
         'Helper/descriptors Chrome executable hors cible QA exacte')
    input_ = {'chromium': regular_bytes(source_files[0]).decode(), 'switches': regular_bytes(source_files[1]).decode(),
        'has_gpu_mac': True, 'executable': str(CHROME),
        'jobs': [{'job': job, 'original_options': rows[job]['original_options'], 'profile': rows[job]['profile']} for job in JOBS]}
    # Seule VM de définition. Ne charge pas Playwright, Chromium, G1, ni serveur.
    result = subprocess.run([str(NODE), '--input-type=module', '--eval', NODE_DEFAULTS_VM],
        input=json.dumps(input_), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=str(root), env={'PATH': '/usr/bin:/bin', 'HOME': str(root), 'TMPDIR': str(root),
                           '__CF_USER_TEXT_ENCODING': f'0x{os.getuid():X}:0:0'}, timeout=10)
    emitter.write('proofs/chrome-defaults-vm.stdout', result.stdout.encode())
    emitter.write('proofs/chrome-defaults-vm.stderr', result.stderr.encode())
    need(result.returncode == 0, 'VM defaultArgs refusée ; aucun runtime créé')
    argv_rows = json.loads(result.stdout)
    need(set(argv_rows) == set(JOBS), 'Table cinq Chrome différente')
    for job in JOBS:
        row = rows[job]
        folder = root / 'auxiliary' / row['name']
        for sub in ('profile', 'home', 'tmp'):
            (folder / sub).mkdir(parents=True, mode=0o700, exist_ok=False)
        argv = argv_rows[job]
        need(type(argv) is list and all(type(a) is str for a in argv)
             and argv[0] == row['executable'] == str(CHROME) and '--user-data-dir=' + row['profile'] in argv
             and '--remote-debugging-port=17594' in argv, 'argv Chrome dérivé incorrect')
        launch_ref = emitter.json('auxiliary/' + row['name'] + '/launch-defaults.json', {
            'schema': 'c17-wrapper-chrome-launch-defaults-v1', 'original_options': row['original_options'],
            'executable': str(CHROME), 'argv': argv, 'sources': refs, 'has_gpu_mac': True,
            'gpu_observation_ref': local_gpu, 'gpu_observation_origin_ref': gpu_ref,
            'method': 'installed Playwright defaultArgs and _innerDefaultArgs exact source bodies, pure vm',
            'cdp_difference': 'cdpPort17594 replaces default pipe; loopback address appended, isPersistent remains false',
            'runtime_executed': False, 'OS_qualified': False})
        env = {'__CF_USER_TEXT_ENCODING': f'0x{os.getuid():X}:0:0',
            'PATH': str(NODE.parent) + ':/usr/bin:/bin:/usr/sbin:/sbin', 'HOME': str(folder / 'home'),
            'CFFIXED_USER_HOME': str(folder / 'home'), 'TMPDIR': str(folder / 'tmp'),
            'LANG': 'en_US.UTF-8', 'LC_ALL': 'en_US.UTF-8', 'PYTHONNOUSERSITE': '1', 'PYTHONDONTWRITEBYTECODE': '1',
            'PYTHONPATH': str(QA) + ':' + str(QA / 'src/backend')}
        row.update(launch_defaults_ref=launch_ref, argv=argv, env=env, cwd=str(root), deadline=50)
    need([reference(p) for p in source_files] == refs, 'Sources Playwright mutées')
    files_ref = emitter.json('authorization/chrome-files.json', {'schema': 'c17-wrapper-chrome-bundle-files-v1',
        'bundle_root': str(CHROME_BUNDLE), 'files': [reference(CHROME), reference(FRAMEWORK)],
        'chrome_qa_copy_ref': chrome_qa_copy_ref,
        'runtime_executed': False, 'signature_verified_at_preparation': True})
    manifest_ref = emitter.json('authorization/chrome-preparation.json', {
        'schema': 'c17-wrapper-chrome-physical-preparation-v1', 'root': str(root), 'source': str(QA), 'head': HEAD,
        'auxiliary_descriptors': rows, 'chrome_files_ref': files_ref, 'sources': refs,
        'runtime_executed': False, 'OS_qualified': False, 'FULL': False, 'release': False})
    return rows, files_ref, manifest_ref


def checked_rootdomain_successor(chrome_ref):
    """Chaîne G1 -> UI -> Unix local -> RootDomainUserClient, avant allocation."""
    need(chrome_ref == CHROME_ROOTDOMAIN_PROFILE, 'Seul successor Chrome RootDomainUserClient exact admis')
    before = regular_bytes(PREP / 'g1-26/chrome.sb')
    ui = checked(CHROME_UI_PROFILE)
    unix = checked(CHROME_UNIX_PROFILE)
    after = checked(chrome_ref)
    need(hashlib.sha256(before).hexdigest() ==
         'c9c0f37425f0ec94045f9094e282051c7ee602193174170133f779a0c6f6abde',
         'Préimage Chrome différent')
    anchor = '(allow file-read-metadata (literal "/private") (literal "/private/tmp"))'
    replacement = (
        '(allow file-read-metadata (literal "/") (literal "/Applications") (literal "/private") (literal "/private/tmp"))\n'
        '(allow file-read-metadata (literal "/etc") (literal "/tmp") (literal "/var")\n'
        '  (literal (param "QA_ROOT")))\n'
        '(allow mach-lookup\n'
        '  (global-name "com.apple.coreservices.launchservicesd")\n'
        '  (global-name "com.apple.windowserver.active"))'
    )
    old_comment = (
        '; Pas de mach-lookup inventé, AppleEvents, HOME réel, profil Chrome personnel,\n'
        '; bind/Unix libre ou sortie Internet. Un refus Mach réel exige diagnostic/revue.'
    )
    new_comment = (
        '; Deux lookups UI exacts issus du diagnostic ROOT4 ; aucun Mach global,\n'
        '; AppleEvents, HOME réel, presse-papiers, profil personnel ou sortie Internet.'
    )
    old = before.decode()
    need(old.count(anchor) == old.count(old_comment) == 1
         and old.replace(anchor, replacement, 1).replace(old_comment, new_comment, 1).encode() == ui
         and len(ui) - len(before) == 262,
         'Delta Chrome hors des deux noms Mach et metadata/commentaire exacts')
    need(checked(CHROME_UNIX_PREIMAGE) == ui, 'Préimage Unix différente du profil UI exact')
    unix_anchor = (
        '(allow network-bind network-inbound (local ip "localhost:17594"))\n'
        '(allow network-outbound (remote ip "localhost:17593") (remote ip "localhost:5173"))\n'
    )
    unix_delta = (
        '; ROOT5 : ProcessSingleton bind() sur TMP_ROOT/com.google.Chrome.*/SingletonSocket\n'
        '; a échoué EPERM. AF_UNIX + bind local restent bornés au TMP_ROOT privé exact.\n'
        '(allow system-socket (socket-domain AF_UNIX))\n'
        '(allow network-bind (local unix-socket (subpath (param "TMP_ROOT"))))\n'
    )
    need(ui.decode().count(unix_anchor) == 1
         and ui.decode().replace(unix_anchor, unix_anchor + unix_delta, 1).encode() == unix
         and len(unix) - len(ui) == 282,
         'Delta Chrome hors du bind Unix local TMP_ROOT exact')
    need(checked(CHROME_ROOTDOMAIN_PREIMAGE) == unix, 'Préimage RootDomain différente du profil Unix exact')
    iokit_anchor = '(allow network-bind (local unix-socket (subpath (param "TMP_ROOT"))))\n'
    iokit_delta = (
        '; ROOT6 : le noyau refuse cette classe précise à Chrome PID 25577\n'
        "; immédiatement avant l'échec IONotificationPortGetRunLoopSource.\n"
        '(allow iokit-open-user-client (iokit-user-client-class "RootDomainUserClient"))\n'
    )
    need(unix.decode().count(iokit_anchor) == 1
         and unix.decode().replace(iokit_anchor, iokit_anchor + iokit_delta, 1).encode() == after
         and len(after) - len(unix) == 216,
         'Delta Chrome hors de RootDomainUserClient exact')
    return old, after.decode()



def checked_chrome_v8_successor(chrome_ref):
    """Même chaîne historique, puis un seul subpath de bundle QA exact."""
    need(chrome_ref == CHROME_V8_PROFILE, 'Seul successor Chrome RootDomainUserClient QA exact admis')
    before, rootdomain = checked_rootdomain_successor(CHROME_ROOTDOMAIN_PROFILE)
    anchor = '(subpath "/Applications/Google Chrome.app")'
    after = checked(chrome_ref).decode()
    need(rootdomain.count(anchor) == 1
         and rootdomain.replace(anchor, '(subpath "' + str(CHROME_BUNDLE) + '")', 1) == after,
         'Delta Chrome hors du seul subpath QA exact')
    return before, after


def checked_chrome_successor(chrome_ref):
    """Chaîne MAIN12 intacte, puis seul lookup dirhelper mesuré par getconf."""
    need(chrome_ref == CHROME_PROFILE, 'Seule proposition Chrome dirhelper exacte admise')
    before, v8 = checked_chrome_v8_successor(CHROME_V8_PROFILE)
    metadata = '(allow file-read-metadata (literal "/") (literal "/Applications") (literal "/private") (literal "/private/tmp"))'
    metadata_v9 = ('(allow file-read-metadata (literal "/") (literal "/Applications") (literal "/private") (literal "/private/tmp")\n'
                   '  (literal "/private/tmp/therese-c17-chrome-qa-copy-RoZmwsja"))')
    data = '(allow file-read-data (literal "/"))'
    data_v9 = ('(allow file-read-data (literal "/") (literal "/private/tmp")\n'
               '  (literal (param "QA_ROOT")))')
    need(v8.count(metadata) == v8.count(data) == 1, 'Ancres lectures V8 absentes/dupliquées')
    expected = v8.replace(metadata, metadata_v9, 1).replace(data, data_v9, 1)
    after = checked(CHROME_PREIMAGE_PROFILE).decode()
    need(after == expected, 'Delta Chrome hors des trois lectures littérales de répertoires')
    # Proposition diagnostic_only : trois refus kernel réels, causalité non prouvée.
    previous = checked(CHROME_PREVIOUS_PROFILE).decode()
    delta = (
        '; ROOT10 diagnostic_only : refus ciblés, causalité non prouvée, profil non admis.\n'
        '(allow mach-lookup (global-name "com.apple.CARenderServer"))\n'
        '(allow iokit-open-user-client (iokit-user-client-class "IOSurfaceRootUserClient"))\n'
        '(allow iokit-open-user-client (iokit-user-client-class "AGXDeviceUserClient"))\n'
    )
    need(previous == after + delta, 'Préimage MAIN11 Chrome différente')
    main12 = checked(CHROME_MAIN12_PROFILE).decode()
    auxiliary_delta = '(allow file-read-metadata (literal (param "AUXILIARY_PARENT")))\n'
    need(main12 == previous + auxiliary_delta
         and main12.count(auxiliary_delta) == 1,
         'Préimage MAIN12 hors metadata du parent auxiliaire exact')
    candidate = checked(chrome_ref).decode()
    dirhelper_delta = '(allow mach-lookup (global-name "com.apple.bsd.dirhelper"))\n'
    need(candidate == main12 + dirhelper_delta
         and candidate.count(dirhelper_delta) == 1
         and checked(CHROME_GETCONF_PROFILE).decode() == candidate,
         'Delta Chrome hors du seul lookup dirhelper mesuré par getconf')
    return before, candidate


def g1_chrome_copy_delta(source: str) -> str:
    """Deux valeurs Path exactes, puis égalité AST complète du reste."""
    need(hashlib.sha256(source.encode()).hexdigest() == G1_PREIMAGE_SHA,
         'Préimage G1 effective différente')
    before = ast.parse(source)
    targets = []
    for node in before.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id == 'CHROME':
                targets.append((node.value, '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', str(CHROME)))
        if isinstance(node, ast.FunctionDef) and node.name == 'validate_auxiliary_binding':
            for entry in node.body:
                if isinstance(entry, ast.Assign) and len(entry.targets) == 1 and isinstance(entry.targets[0], ast.Name) and entry.targets[0].id == 'bundle':
                    targets.append((entry.value, '/Applications/Google Chrome.app', str(CHROME_BUNDLE)))
    need(len(targets) == 2, 'Deux ancres G1 Chrome exactes requises')
    positions = []
    lines = source.splitlines(keepends=True)
    for node, expected, replacement in targets:
        need(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'Path'
             and len(node.args) == 1 and not node.keywords and isinstance(node.args[0], ast.Constant)
             and node.args[0].value == expected, 'Valeur G1 Chrome autre que la préimage exacte')
        value = node.args[0]
        begin = sum(len(s.encode()) for s in lines[:value.lineno - 1]) + value.col_offset
        end = sum(len(s.encode()) for s in lines[:value.end_lineno - 1]) + value.end_col_offset
        positions.append((begin, end, replacement))
        node.args[0] = ast.Constant(value=None)
    raw = source.encode()
    for begin, end, replacement in sorted(positions, reverse=True):
        raw = raw[:begin] + repr(replacement).encode() + raw[end:]
    derived = raw.decode()
    after = ast.parse(derived)
    changed = []
    for node in after.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'CHROME':
            changed.append(node.value)
        if isinstance(node, ast.FunctionDef) and node.name == 'validate_auxiliary_binding':
            changed.extend(entry.value for entry in node.body if isinstance(entry, ast.Assign) and len(entry.targets) == 1
                           and isinstance(entry.targets[0], ast.Name) and entry.targets[0].id == 'bundle')
    need(len(changed) == 2, 'Deux valeurs G1 QA dérivées requises')
    for node in changed:
        node.args[0] = ast.Constant(value=None)
    need(ast.dump(before, include_attributes=False) == ast.dump(after, include_attributes=False),
         'Autre delta AST G1 interdit')
    validate_closed_g1(derived)
    return derived


def checked_chrome_qa_copy(receipt_ref):
    """Référence root réelle obligatoire ; aucun codesign ni retrait dans ce builder."""
    need(receipt_ref == CHROME_QA_COPY_REF, 'Seule preuve réelle root de la copie QA exacte admise')
    proof = json_checked(receipt_ref)
    need(proof.get('schema') == 'c17-root-independent-chrome-copy-v1'
         and proof.get('actor') == '/root' and proof.get('scope') == 'owned_TMP_copy_only_no_browser_launch'
         and proof.get('passed') is True and proof.get('source') == '/Applications/Google Chrome.app'
         and proof.get('target') == str(CHROME_BUNDLE)
         and proof.get('runtime_admitted') is False and proof.get('FULL') is False and proof.get('release') is False
         and all(proof.get(flag) is True for flag in ('byte_mode_link_equal', 'source_unchanged',
             'no_hardlinks_to_source', 'all_non_finderinfo_copy_baseline_attrs_unchanged', 'quarantine_preserved')),
         'Copie QA réelle/intégrité/metadonnées exacte absente')
    for name in ('source_before', 'source_after', 'copy_manifest', 'provenance_delta_ref', 'script'):
        checked(proof[name])
    need(proof['source_before']['sha256'] == proof['source_after']['sha256']
         and proof['source_before']['bytes'] == proof['source_after']['bytes'], 'Source Chrome avant/après non identique')
    removed = proof.get('sole_xattr_type_removed', {})
    need(removed.get('name') == 'com.apple.FinderInfo' and type(removed.get('count')) is int
         and removed['count'] > 0, 'Retrait autre que FinderInfo fini exact')
    checked(removed['original_values'])
    checked(removed['exact_canonical_targets'])
    files = proof.get('files')
    need(isinstance(files, list) and len(files) == 2
         and {row.get('path') for row in files} == {str(CHROME), str(FRAMEWORK)}
         and all(reference(Path(row['path'])) == row for row in files),
         'Deux binaires QA de la preuve ne correspondent pas aux fichiers physiques')
    strict = [call for call in proof.get('calls', []) if call.get('name') == 'copy-strict-deep']
    need(len(strict) == 1 and strict[0].get('exe') == '/usr/bin/codesign'
         and strict[0].get('args') == ['--verify', '--deep', '--strict', '--verbose=4', str(CHROME_BUNDLE)]
         and strict[0].get('status') == 0 and strict[0].get('signal') is None
         and strict[0].get('error') is None, 'Strict profond QA réel vert requis')
    out, err = checked(strict[0]['stdout']), checked(strict[0]['stderr'])
    text = out + b'\n' + err
    need((str(CHROME_BUNDLE) + ': valid on disk').encode() in text
         and (str(CHROME_BUNDLE) + ': satisfies its Designated Requirement').encode() in text,
         'Bruts strict QA sans validation exacte de la cible')
    return proof | {'fresh_physical_revalidation': verify_chrome_qa_tree(proof)}


def chrome_contract_qa_delta(source: str) -> str:
    """Une seule constante CHROME ; fonctions et table métier inchangées."""
    need(hashlib.sha256(source.encode()).hexdigest() == CHROME_CONTRACT_PREIMAGE_SHA,
         'Préimage helper Chrome différente')
    derived = assignment_delta(source, 'CHROME',
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', str(CHROME))
    return derived


def g1_chrome_executable_guard(source: str) -> str:
    """Après les deux Path V7, ajouter une seule égalité descriptor/exécutable."""
    need(hashlib.sha256(source.encode()).hexdigest() == G1_QA_PATHS_SHA,
         'Préimage G1 QA paths différente')
    anchor = 'require(isinstance(row["argv"], list) and row["argv"] and row["argv"][0] == str(CHROME)'
    replacement = anchor + '\n                and row["executable"] == str(CHROME)'
    need(source.count(anchor) == 1 and replacement not in source, 'Ancre égalité executable G1 non unique')
    derived = source.replace(anchor, replacement, 1)
    need(derived.replace(replacement, anchor, 1) == source, 'Delta garde G1 hors égalité exacte')
    ast.parse(derived)
    validate_closed_g1(derived)
    return derived


def g1_auxiliary_parent_delta(source: str) -> str:
    """Paramètre chrome seul, dérivé de root/auxiliary canonique ; aucune clé libre."""
    anchor = '            extra.extend(["-D", key + "=" + value])\n    else:\n'
    addition = (
        '            extra.extend(["-D", key + "=" + value])\n'
        '        auxiliary_parent = root / "auxiliary"\n'
        '        require(auxiliary_parent.resolve(strict=True) == auxiliary_parent\n'
        '                and child_path(root, auxiliary_parent) == auxiliary_parent,\n'
        '                "Parent auxiliaire Chrome hors QA exact")\n'
        '        extra.extend(["-D", "AUXILIARY_PARENT=" + str(auxiliary_parent)])\n'
        '    else:\n'
    )
    need(source.count(anchor) == 1 and addition not in source,
         'Ancre paramètres Chrome G1 non unique')
    derived = source.replace(anchor, addition, 1)
    need(derived.replace(addition, anchor, 1) == source,
         'Delta G1 hors paramètre parent auxiliaire exact')
    ast.parse(derived)
    validate_closed_g1(derived)
    return derived


def chrome_tree_manifest(base: Path) -> list[dict]:
    """Lecture fraîche sans suivre les liens ; signatures vérifiées après le scan."""
    base = Path(base)
    need(base.is_absolute() and base.resolve(strict=True) == base and not base.is_symlink()
         and base.is_dir(), 'Racine Chrome non canonique')
    rows, signatures = [], {}
    def signature(st):
        return (st.st_dev, st.st_ino, st.st_mode, st.st_uid, st.st_gid,
                st.st_size, st.st_mtime_ns, st.st_ctime_ns, st.st_nlink)
    def visit(relative):
        path = base / relative
        before = path.lstat()
        row = {'relative': relative, 'mode': stat.S_IMODE(before.st_mode),
               'uid': before.st_uid, 'gid': before.st_gid, 'dev': before.st_dev, 'ino': before.st_ino}
        names = None
        if stat.S_ISLNK(before.st_mode):
            row.update(type='symlink', target=os.readlink(path))
            target = path.resolve(strict=True)
            need(target.is_relative_to(base), 'Lien Chrome hors bundle')
        elif stat.S_ISDIR(before.st_mode):
            need(path.resolve(strict=True) == path, 'Dossier Chrome devenu alias')
            row['type'] = 'directory'
            names = sorted(os.listdir(path))
        else:
            need(stat.S_ISREG(before.st_mode) and path.resolve(strict=True) == path,
                 'Type/alias Chrome inattendu')
            digest = hashlib.sha256()
            with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as stream:
                opened = os.fstat(stream.fileno())
                need(signature(opened) == signature(before), 'Fichier Chrome changé à ouverture')
                while chunk := stream.read(1024 * 1024):
                    digest.update(chunk)
                need(signature(os.fstat(stream.fileno())) == signature(opened), 'Fichier Chrome changé en lecture')
            row.update(type='file', bytes=before.st_size, sha256=digest.hexdigest())
        rows.append(row)
        signatures[relative] = signature(before)
        if names is not None:
            for name in names:
                need(name not in ('', '.', '..') and '/' not in name, 'Nom Chrome invalide')
                visit(relative + '/' + name if relative else name)
            need(sorted(os.listdir(path)) == names, 'Entrées Chrome changées pendant scan')
        need(signature(path.lstat()) == signature(before), 'Métadonnées Chrome changées pendant scan')
        if row['type'] == 'symlink':
            need(os.readlink(path) == row['target'], 'Cible lien Chrome changée')
    visit('')
    for row in rows:
        path = base / row['relative']
        need(signature(path.lstat()) == signatures[row['relative']], 'Entrée Chrome changée après scan')
        if row['type'] == 'symlink':
            need(os.readlink(path) == row['target'], 'Cible Chrome changée après scan')
    return rows


def checked_chrome_manifest(rows: list, *, entries: int) -> dict[str, dict]:
    need(type(entries) is int and entries > 0 and type(rows) is list and len(rows) == entries,
         'Nombre manifest Chrome différent')
    result = {}
    common = {'relative', 'mode', 'uid', 'gid', 'dev', 'ino', 'type'}
    for row in rows:
        need(type(row) is dict and row.get('type') in ('file', 'directory', 'symlink'),
             'Type manifest Chrome invalide')
        fields = common | ({'bytes', 'sha256'} if row['type'] == 'file'
                           else {'target'} if row['type'] == 'symlink' else set())
        need(set(row) == fields and type(row['relative']) is str
             and (row['relative'] == '' or (not Path(row['relative']).is_absolute()
                  and all(part not in ('', '.', '..') for part in row['relative'].split('/'))))
             and row['relative'] not in result, 'Manifest Chrome doublonné/hors chemins')
        need(all(type(row[k]) is int and row[k] >= 0 for k in ('mode', 'uid', 'gid', 'dev', 'ino'))
             and row['mode'] <= 0o7777, 'Mode/UID/GID manifest Chrome invalides')
        if row['type'] == 'file':
            need(type(row['bytes']) is int and row['bytes'] >= 0
                 and type(row['sha256']) is str and re.fullmatch('[a-f0-9]{64}', row['sha256']),
                 'Taille/SHA manifest Chrome invalides')
        if row['type'] == 'symlink':
            need(type(row['target']) is str and row['target'], 'Cible manifest Chrome absente')
        result[row['relative']] = row
    need(result.get('', {}).get('type') == 'directory', 'Racine manifest Chrome absente')
    for relative in result.keys() - {''}:
        parent = str(Path(relative).parent)
        parent = '' if parent == '.' else parent
        need(result.get(parent, {}).get('type') == 'directory', 'Parent manifest Chrome absent/non dossier')
    return result


def verify_chrome_tree_pair(source: Path, target: Path, source_rows: list, copy_rows: list, *, entries: int) -> dict:
    """Comparer deux snapshots archivés à deux arbres vivants, sans signature nouvelle."""
    expected_source = checked_chrome_manifest(source_rows, entries=entries)
    expected_copy = checked_chrome_manifest(copy_rows, entries=entries)
    need(set(expected_source) == set(expected_copy), 'Arbres Chrome source/copie différents')
    clean = lambda row: {k: v for k, v in row.items() if k not in ('dev', 'ino')}
    need(all(clean(expected_source[key]) == clean(expected_copy[key]) for key in expected_source),
         'Baseline source/copie Chrome octets/modes/liens différente')
    observed_source = checked_chrome_manifest(chrome_tree_manifest(source), entries=entries)
    observed_copy = checked_chrome_manifest(chrome_tree_manifest(target), entries=entries)
    need(observed_source == expected_source, 'Source Chrome actuelle différente du manifest')
    need(observed_copy == expected_copy, 'Copie Chrome actuelle différente du manifest')
    source_inodes = {(row['dev'], row['ino']) for row in observed_source.values() if row['type'] == 'file'}
    need(not any((row['dev'], row['ino']) in source_inodes for row in observed_copy.values()
                 if row['type'] == 'file'), 'Hardlink Chrome actuel vers source')
    counts = {kind: sum(row['type'] == kind for row in observed_copy.values())
              for kind in ('file', 'directory', 'symlink')}
    return {'schema': 'c17-chrome-copy-fresh-filesystem-observation-v1',
        'source': str(source), 'target': str(target), 'observed_at_utc': datetime.now(UTC).isoformat(),
        'entries': entries, 'types': counts, 'source_manifest_equal': True, 'copy_manifest_equal': True,
        'all_bytes_modes_UID_GID_links_equal': True, 'source_and_copy_inodes_match_archived_snapshots': True,
        'no_hardlinks_to_source': True,
        'source_snapshot_sha256': hashlib.sha256(encoded(source_rows)).hexdigest(),
        'copy_snapshot_sha256': hashlib.sha256(encoded(copy_rows)).hexdigest(),
        'codesign_reexecuted': False, 'xattrs_currently_measured': False, 'runtime_qualified': False,
        'limit': 'Read-only finite scan with before/after stat checks, not an atomic hostile-filesystem snapshot.'}


def verify_chrome_qa_tree(proof: dict) -> dict:
    need(proof.get('source') == '/Applications/Google Chrome.app'
         and proof.get('target') == str(CHROME_BUNDLE) and proof.get('entries') == 1339,
         'Arbres source/copie réels exacts requis')
    source = json.loads(checked(proof['source_after']))
    copy = json.loads(checked(proof['copy_manifest']))
    result = verify_chrome_tree_pair(Path(proof['source']), CHROME_BUNDLE, source, copy, entries=1339)
    return result | {'source_manifest_ref': proof['source_after'], 'copy_manifest_ref': proof['copy_manifest'],
                     'root_copy_receipt_ref': CHROME_QA_COPY_REF}


def verify_observability():
    """Vérifie les quatre dérivations exactes de ROOT9 avant toute allocation."""
    index_path = OBSERVABILITY / 'INDEX.json'
    need(reference(index_path)['sha256'] == OBSERVABILITY_INDEX_SHA,
         'Gel diagnostic différent')
    index = json.loads(regular_bytes(index_path))
    need(index.get('scope') == 'WRAPPER_ROOT9_transport_diagnostic_only'
         and index.get('integration_not_done', {}).get('AB_composite_used') is False,
         'Diagnostic ROOT9 seul requis')
    origins_path = OBSERVABILITY / 'ORIGINS.json'
    origins = json.loads(regular_bytes(origins_path))
    need(origins.get('scope') == 'WRAPPER_ROOT9_transport_diagnostic_only'
         and origins.get('no_AB_composite_used') is True
         and len(origins.get('origin_byte_exact', [])) == 4,
         'Quatre origines ROOT9/transport26 requises')
    index_refs = {row['path']: row for row in index['refs']}
    need(index_refs.get(str(origins_path)) == reference(origins_path),
         'ORIGINS non épinglé par le gel diagnostic')
    rows = {}
    root9 = Path('/private/tmp/therese-c17-wrapper-canary-42f8fa9d995e4ba291d179d86ae2b192')
    for row in origins['origin_byte_exact']:
        name = Path(row['candidate']['path']).name
        need(name in OBSERVABILITY_NAMES and name not in rows,
             'Candidat diagnostic hors des quatre sources exactes')
        expected = {'baseline': PREP / 'transport-26/source' / name,
                    'ROOT9': root9 / 'source' / name,
                    'preimage': OBSERVABILITY / 'preimages' / name,
                    'candidate': OBSERVABILITY / 'source' / name}
        for key, path in expected.items():
            need(row[key] == reference(path), 'Origine diagnostic différente : ' + key + '/' + name)
        need({(row[key]['sha256'], row[key]['bytes']) for key in ('baseline', 'ROOT9', 'preimage')}
             == {(row['baseline']['sha256'], row['baseline']['bytes'])},
             'Préimage transport26/ROOT9 divergente : ' + name)
        diff_path = OBSERVABILITY / 'diffs' / (name + '.diff')
        diff = ''.join(difflib.unified_diff(
            regular_bytes(expected['preimage']).decode().splitlines(True),
            regular_bytes(expected['candidate']).decode().splitlines(True),
            fromfile='preimages/' + name, tofile='source/' + name)).encode()
        need(diff == regular_bytes(diff_path) and index_refs.get(str(diff_path)) == reference(diff_path),
             'Delta diagnostic différent : ' + name)
        ast.parse(regular_bytes(expected['candidate']).decode(), filename=str(expected['candidate']))
        rows[name] = {'preimage': row['preimage'], 'candidate': row['candidate'],
                      'diff': reference(diff_path), 'preimage_bytes': regular_bytes(expected['preimage']),
                      'candidate_bytes': regular_bytes(expected['candidate'])}
    need(set(rows) == set(OBSERVABILITY_NAMES), 'Quatre dérivations diagnostic incomplètes')
    helper = OBSERVABILITY / 'source' / OBSERVABILITY_HELPER
    need(reference(helper)['sha256'] == OBSERVABILITY_HELPER_SHA
         and index_refs.get(str(helper)) == reference(helper),
         'Cinquième module de diagnostic non exact')
    ast.parse(regular_bytes(helper).decode(), filename=str(helper))
    return {'rows': rows, 'helper_ref': reference(helper), 'helper_bytes': regular_bytes(helper),
            'index_ref': reference(index_path), 'origins_ref': reference(origins_path)}


def derive_diagnostic_overlay(overlay, root, diagnostic):
    """Porte les deux protocoles/clients actifs et les deux helpers frères."""
    need(len(overlay['outputs']) == 26 and len(overlay['script_outputs']) == 17,
         'Préimage overlay26/17 différente')
    need(hashlib.sha256(diagnostic['helper_bytes']).hexdigest() == OBSERVABILITY_HELPER_SHA
         and len(diagnostic['helper_bytes']) == diagnostic['helper_ref']['bytes'],
         'Octets helper diagnostic différents du pin')
    payloads, outputs, scripts = overlay['payloads'], overlay['outputs'], overlay['script_outputs']
    original_transport = dict(overlay['transport_refs'])
    need(set(original_transport) == {'rpc_protocol.py', 'rpc_client.py'},
         'Deux dépendances overlay historiques requises')
    derivations = []
    for folder in ('runtime', 'complements/instruments'):
        for name in ('rpc_protocol.py', 'rpc_client.py'):
            relative = folder + '/' + name
            target = root / 'auxiliary-ports' / relative
            key = str(target)
            row = diagnostic['rows'][name]
            need(hashlib.sha256(row['preimage_bytes']).hexdigest() == row['preimage']['sha256']
                 and hashlib.sha256(row['candidate_bytes']).hexdigest() == row['candidate']['sha256'],
                 'Octets transport diagnostic différents du pin')
            need(payloads.get(key) == row['preimage_bytes']
                 and outputs.get(key) == {'path': key, 'sha256': hashlib.sha256(row['preimage_bytes']).hexdigest(),
                                          'bytes': len(row['preimage_bytes'])}
                 and scripts.get(relative) == outputs[key],
                 'Transport overlay ancien différent : ' + relative)
            raw = row['candidate_bytes']
            payloads[key] = raw
            outputs[key] = {'path': key, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
            scripts[relative] = outputs[key]
            derivations.append({'old_output': row['preimage'], 'new_output': outputs[key],
                                'candidate_source': row['candidate'], 'diff_ref': row['diff']})
        relative = folder + '/' + OBSERVABILITY_HELPER
        target = root / 'auxiliary-ports' / relative
        key = str(target)
        need(key not in payloads and key not in outputs and relative not in scripts,
             'Helper diagnostic déjà présent dans overlay')
        raw = diagnostic['helper_bytes']
        payloads[key] = raw
        outputs[key] = {'path': key, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
        scripts[relative] = outputs[key]
    overlay['original_transport_refs'] = original_transport
    overlay['transport_refs'] = {name: diagnostic['rows'][name]['candidate']
                                 for name in ('rpc_protocol.py', 'rpc_client.py')}
    overlay['diagnostic_derivations'] = derivations
    overlay['diagnostic_origin_index_ref'] = diagnostic['index_ref']
    need(len(payloads) == len(outputs) == 28 and len(scripts) == 19
         and len(derivations) == 4, 'Overlay diagnostic28/19 incomplet')
    return overlay


def join_sources79(base, witness, deltas, root):
    """Conserver les 76 chemins précédents et pinner les trois helpers actifs."""
    need(type(base) is list and len(base) == 66 and type(witness) is list and len(witness) == 7
         and type(deltas) is list and len(deltas) == 6, 'Table sources66+7+6 incomplète')
    result = base + witness + deltas
    helper_paths = {str(root / 'source' / OBSERVABILITY_HELPER),
                    str(root / 'auxiliary-ports/runtime' / OBSERVABILITY_HELPER),
                    str(root / 'auxiliary-ports/complements/instruments' / OBSERVABILITY_HELPER)}
    helper_rows = [ref for ref in result if ref.get('path') in helper_paths]
    need(len(helper_rows) == 3 and {ref['path'] for ref in helper_rows} == helper_paths
         and all(ref.get('sha256') == OBSERVABILITY_HELPER_SHA
                 and ref.get('bytes') == 6826 for ref in helper_rows),
         'Trois helpers de diagnostic physiques non épinglés')
    need(all(type(ref) is dict and set(ref) == {'path', 'sha256', 'bytes'}
             and type(ref['path']) is str and Path(ref['path']).is_absolute()
             and re.fullmatch('[a-f0-9]{64}', ref['sha256']) is not None
             and type(ref['bytes']) is int and ref['bytes'] >= 0 for ref in result)
         and len(result) == len({ref['path'] for ref in result}) == 79,
         'Table source refs79 divergente/doublonnée')
    return result


def construction_authority(root, authority_ref, web_ref, chrome_ref, physical_observations=None):
    body = json_checked(authority_ref)
    need(body.get('schema') == 'c17-root-fresh-wrapper-preparation-go-v1'
         and body.get('status') == 'go_prepare_only' and body.get('scope') == 'WRAPPER_CANARY'
         and body.get('root') == str(root) and body.get('actor') == '/root' and body.get('head') == HEAD
         and body.get('product_source_root') == str(QA) and body.get('web_profile_ref') == web_ref
         and body.get('chrome_profile_ref') == chrome_ref
         and body.get('runner_boundary_index_ref') == reference(WITNESS / 'INDEX.json')
         and body.get('origin_kind') == 'root_tool_call'
         and body.get('builder_ref') == reference(Path(__file__).resolve()), 'GO externe préparation non exact')
    registry = json_checked(body['identity_registry_ref'])
    need(registry.get('schema') == 'c17-wrapper-canary-live-identity-registry-v1'
         and registry.get('round_id') == root.name and registry.get('head') == HEAD
         and registry.get('chrome_profile_ref') == chrome_ref
         and registry.get('runner_boundary_index_ref') == body['runner_boundary_index_ref']
         and type(registry.get('actors')) is list and len(registry['actors']) == 1
         and registry['actors'][0].get('actor') == '/root'
         and isinstance(registry['actors'][0].get('observed_by'), str)
         and registry['actors'][0]['observed_by'] and registry['actors'][0].get('observed_at_utc'),
         'Registre réel neuf absent ; aucun ancien acteur relabellé')
    checked(body['gpu_observation_ref'])
    copy_proof = checked_chrome_qa_copy(body['chrome_qa_copy_ref'])
    if physical_observations is not None:
        physical_observations['before'] = copy_proof['fresh_physical_revalidation']
    return body


def build(root, *, web_profile_ref, chrome_profile_ref, authority_ref):
    root = future_root(root)
    need(web_profile_ref == WEB and checked(web_profile_ref), 'Seul successor metadata web exact admis')
    chrome_before, chrome_after = checked_chrome_successor(chrome_profile_ref)
    physical_observations = {}
    authority = construction_authority(root, authority_ref, web_profile_ref, chrome_profile_ref, physical_observations)
    pins, documents, historical_observations = validate_indexes()
    diagnostic = verify_observability()
    raw_manifest = regular_bytes(PROOFS / 'qa-source-files.json')
    need(hashlib.sha256(raw_manifest).hexdigest() == SOURCE_MANIFEST_SHA, 'Manifest frais autre checkout')
    source_manifest = json.loads(raw_manifest)
    need(source_manifest.get('head') == HEAD and source_manifest.get('status') == 'PASS'
         and source_manifest.get('product_source_root') == str(QA), 'Manifest source autre HEAD')
    deps = deps_check()
    # Imports uniquement des modules de préparation épinglés avant allocation.
    git = load_pure('git_snapshot', PREP / 'auxiliary/source/git_snapshot.py')
    static = json.loads(regular_bytes(PREP / 'auxiliary/STATIC-PLAN.json'))
    reader = git.GitSnapshot(static['git_definition_origin_ref'], QA)
    observed = reader.verify_worktree()
    need(reader.recheck() == HEAD and len(observed) == len(source_manifest['files']) == 3579,
         'HEAD/arbre3579 différents')
    for row in source_manifest['files']:
        relative = str(Path(row['path']).relative_to(QA))
        actual = observed.get(relative)
        need(actual and actual['git_blob'] == row['git_blob'] and actual['sha256'] == row['sha256']
             and actual['mode'] == source_manifest['modes'][row['path']], 'Blob/mode/snapshot source divergent')
    contract = load_pure('rpc_instrument_contract', PREP / 'successor/rpc_instrument_contract.py')
    successor = load_pure('c17_successor_constructor', PREP / 'successor/prepare-rpc-instruments.py')
    render_support = load_pure('render_support', PREP / 'support-v2/render_support.py')
    support = load_pure('c17_support_constructor', PREP / 'support-v2/prepare_support.py')
    renderer = load_pure('render_auxiliary', PREP / 'auxiliary/render_auxiliary.py')
    auxiliary = load_pure('c17_auxiliary_constructor', PREP / 'auxiliary/prepare_auxiliary.py')
    contract_before = regular_bytes(PREP / 'auxiliary/source/chrome_contract.py').decode()
    contract_qa = chrome_contract_qa_delta(contract_before)
    need(checked(CHROME_CONTRACT_QA_REF).decode() == contract_qa, 'Helper QA pinné divergent de la dérivation exacte')
    chrome_contract = load_pure('c17_chrome_contract', Path(CHROME_CONTRACT_QA_REF['path']))
    boundary = load_pure('c17_runner_boundary_definition', WITNESS / 'source/runner_boundary.py')
    base_g1 = regular_bytes(PREP / 'g1-26/runtime_session.py').decode()
    validate_closed_g1(base_g1)
    qa_g1 = g1_auxiliary_parent_delta(g1_chrome_executable_guard(g1_chrome_copy_delta(base_g1)))
    runtime = assignment_delta(qa_g1, 'WRAPPER_ADMISSION_TABLE', {}, wrapper_slot(root))
    runner_base = regular_bytes(PREP / 'coordinator/run_wrapper_canary.py').decode()
    runner_derived = runner_events_delta(runner_base)
    # Aucun root effectif avant la fin du préflight.
    os.mkdir(root, 0o700)
    emitter = Emitter(root)
    failed = True
    try:
        emitter.json('authorization/external-preparation-authority.json', authority)
        chrome_copy_before_ref = emitter.json('authorization/chrome-copy-fresh-before.json', physical_observations['before'])
        contract_delta_ref = emitter.write('proofs/derived-chrome-helper-qa.diff', ''.join(difflib.unified_diff(
            contract_before.splitlines(True), contract_qa.splitlines(True), fromfile='frozen_chrome_contract',
            tofile='fresh_root_QA_chrome_contract')).encode())
        emitter.write('authorization/source-files.json', raw_manifest)
        registry_ref = emitter.write('authorization/identity-registry.json', checked(authority['identity_registry_ref']))
        checkout_ref = emitter.json('authorization/source-checkout.json', {
            'schema': 'c17-wrapper-canary-source-checkout-v1', 'head': HEAD, 'git_head': HEAD,
            'product_source_root': str(QA), 'git_tree_verified': True, 'git_head_ref': reference(QA / '.git/HEAD'),
            'source_manifest_ref': reference(root / 'authorization/source-files.json'),
            'source_manifest_original_ref': reference(PROOFS / 'qa-source-files.json'),
            'tracked_files_verified': len(observed), 'symlinks_verified': sum(v['mode'] == '120000' for v in observed.values()),
            'metadata_only_not_runtime_qualification': True})
        common = {'scope': 'WRAPPER_CANARY', 'root': str(root), 'actor': '/root', 'round_id': root.name, 'head': HEAD}
        def origin(schema):
            return common | {'schema': schema, 'origin_kind': 'root_tool_call',
                'external_origin_ref': authority_ref, 'builder_ref': authority['builder_ref'],
                'preparation_only': True, 'runtime_GO_not_consumed': True}
        rpc_origin = emitter.json('authorization/root-origin.json', origin('c17-root-instrument-preparation-origin-v1'))
        rpc_renderer = load_pure('c17_rpc_renderer_read', PREP / 'source/render_rpc_ports.py')
        binding = common | {'schema': successor.BINDING_SCHEMA, 'product_source_root': str(QA),
            'qa_python': str(QA / '.venv-conforme/bin/python'), 'source_checkout_ref': checkout_ref,
            'root_authorization_origin': rpc_origin, 'constructor_ref': reference(PREP / 'successor/prepare-rpc-instruments.py'),
            'renderer_ref': reference(PREP / 'source/render_rpc_ports.py'),
            'helper_ref': reference(PREP / 'successor/nested_capture_helper.py'),
            'rpc_dependencies': {n: reference(PREP / 'source' / n) for n in contract.DEPENDENCIES},
            'definition_refs': {n: reference(Path(p)) for n, (p, _sha) in rpc_renderer.BASELINES.items()},
            'outputs': sorted(contract.OUTPUTS)}
        binding_ref = emitter.json('authorization/instruments-binding.json', binding)
        decision_ref = emitter.json('authorization/instruments-go.json', common | {'schema': successor.DECISION_SCHEMA,
            'status': 'go_prepare_rpc_instruments_only', 'supplied_by': '/root', 'decision_id': root.name,
            'binding_ref': binding_ref, 'root_authorization_origin': rpc_origin,
            'constructor_ref': binding['constructor_ref'], 'approved_outputs': binding['outputs']})
        base = successor.prepare(decision_ref, binding_ref)
        originals = dict(base['outputs'])
        need(len(originals) == 11, 'Sorties11 différentes')
        support_origin = emitter.json('authorization/support-origin.json', origin('c17-root-support-preparation-origin-v1'))
        support_binding = common | {'schema': support.SCHEMA_BINDING, 'preparation_manifest_ref': base['manifest_ref'],
            'source_manifest_ref': reference(root / 'authorization/source-files.json'), 'identity_registry_ref': registry_ref,
            'root_authorization_origin': support_origin, 'renderer_ref': reference(PREP / 'support-v2/render_support.py'),
            'constructor_ref': reference(PREP / 'support-v2/prepare_support.py'),
            'support_source_refs': {n: reference(p) for n, (p, _sha) in render_support.SOURCES.items()},
            'historical_contract_ref': reference(render_support.HISTORICAL_CONTRACT[0]),
            'historical_species_ref': reference(render_support.HISTORICAL_SPECIES[0]),
            'approved_outputs': sorted(render_support.ALL_OUTPUTS)}
        support_binding_ref = emitter.json('authorization/support-binding.json', support_binding)
        support_decision_ref = emitter.json('authorization/support-go.json', common | {'schema': support.SCHEMA_DECISION,
            'status': 'go_prepare_static_support_only', 'supplied_by': '/root', 'decision_id': root.name,
            'binding_ref': support_binding_ref, 'root_authorization_origin': support_origin,
            'constructor_ref': support_binding['constructor_ref'], 'approved_outputs': support_binding['approved_outputs']})
        supports = support.prepare(support_decision_ref, support_binding_ref)
        sql_ref = supports['outputs']['complements/contrats-normalises-proposes.json']
        blueprint_base = regular_bytes(PREP / 'coordinator/wrapper_blueprint.py').decode()
        blueprint_with_rootdir = boundary.derive_blueprint(blueprint_base)
        blueprint_derived = assignment_delta(blueprint_with_rootdir, 'SQL_CONTRACT_SHA', OLD_SQL_SHA, sql_ref['sha256'])
        # Copies nouvelles des définitions seulement, aucune sortie précédente lue.
        overlay = auxiliary.prepare_auxiliary(root=root, base_manifest_ref=base['manifest_ref'],
            definition_refs={n: ref for n, ref in static['input_refs'].items() if n not in renderer.BASE_RPC},
            helper_refs=static['helper_refs'], transport_refs=static['transport_refs'],
            git_definition_ref=static['git_definition_origin_ref'])
        witness_runner_path = str(root / 'auxiliary-ports/runtime/calibrate-test-runner.py')
        witness_runner_before = overlay['payloads'][witness_runner_path].decode()
        overlay = boundary.derive_overlay(overlay)
        witness_runner_after = overlay['payloads'][witness_runner_path].decode()
        overlay = derive_diagnostic_overlay(overlay, root, diagnostic)
        need(len(overlay['outputs']) == 28 and len(overlay['script_outputs']) == 19, 'Overlay28/19 différent')
        for target, raw in overlay['payloads'].items():
            emitter.write(str(Path(target).relative_to(root)), raw)
        overlay_ref = emitter.json('authorization/auxiliary-overlay.json', {k: v for k, v in overlay.items() if k != 'payloads'} |
            {'schema': 'c17-wrapper-auxiliary-physical-overlay-diagnostic-v1', 'emitted': True, 'emitted_by': '/root',
             'source_index_ref': reference(PREP / 'auxiliary/INDEX.json'), 'emitter_ref': authority['builder_ref'],
             'diagnostic_index_ref': diagnostic['index_ref'],
             'preparation_only': True, 'native_executed': False, 'OS_qualified': False, 'FULL': False, 'initial11unchanged': True})
        chrome_rows, chrome_files_ref, chrome_ref = chrome_prepare(emitter, chrome_contract,
            authority['gpu_observation_ref'], authority['chrome_qa_copy_ref'])
        core = []
        for name in CORE_G1:
            source = PREP / 'g1-26' / name
            raw = (runtime.encode() if name == 'runtime_session.py' else checked(web_profile_ref) if name == 'web.sb'
                   else checked(chrome_profile_ref) if name == 'chrome.sb' else regular_bytes(source))
            output = emitter.write('g1/' + name, raw)
            core.append({'input': reference(source), 'output': output,
                'derivation': 'WRAPPER_slot_two_exact_QA_Chrome_paths_and_executable_equality' if name == 'runtime_session.py' else 'pinned_web_metadata_successor' if name == 'web.sb' else
                              'pinned_chrome_ui_exact_successor' if name == 'chrome.sb' else 'byte_exact'})
        for name in CORE_TRANSPORT:
            source = PREP / 'transport-26/source' / name
            row = diagnostic['rows'].get(name)
            raw = row['candidate_bytes'] if row else regular_bytes(source)
            record = {'input': reference(source), 'output': emitter.write('source/' + name, raw),
                      'derivation': 'diagnostic_only_exact_delta' if row else 'byte_exact'}
            if row:
                record.update(candidate_source_ref=row['candidate'], diagnostic_diff_ref=row['diff'],
                              preimage_ref=row['preimage'])
            core.append(record)
        core.append({'input': diagnostic['helper_ref'],
                     'output': emitter.write('source/' + OBSERVABILITY_HELPER, diagnostic['helper_bytes']),
                     'derivation': 'diagnostic_helper_byte_exact'})
        for name in ('git_snapshot.py', 'chrome_contract.py'):
            source = PREP / 'auxiliary/source' / name
            raw = contract_qa.encode() if name == 'chrome_contract.py' else regular_bytes(source)
            row = {'input': reference(source), 'output': emitter.write('source/' + name, raw),
                   'derivation': 'CHROME_QA_exact_constant_only' if name == 'chrome_contract.py' else 'byte_exact'}
            if name == 'chrome_contract.py':
                row.update(derivation_source_ref=CHROME_CONTRACT_QA_REF, derivation_diff_ref=contract_delta_ref)
            core.append(row)
        need(len(core) == 18, 'Core18 différent')
        core_ref = emitter.json('authorization/core-preparation.json', {'schema': 'c17-wrapper-core-physical-preparation-diagnostic-v1',
            'copies': core, 'source_indexes': [reference(p) for p in INDEX_PINS],
            'diagnostic_origin_ref': diagnostic['origins_ref'],
            'web_profile_ref': web_profile_ref, 'chrome_profile_ref': chrome_profile_ref,
            'admission': False, 'native_executed': False, 'FULL': False})
        diagnostic_proofs = []
        for name in OBSERVABILITY_NAMES:
            row = diagnostic['rows'][name]
            for kind, origin, raw in (('preimage', row['preimage'], row['preimage_bytes']),
                                      ('diff', row['diff'], regular_bytes(Path(row['diff']['path'])))):
                relative = 'proofs/rpc-diagnostic-' + kind + '/' + name + ('.diff' if kind == 'diff' else '')
                diagnostic_proofs.append({'origin': origin, 'output': emitter.write(relative, raw)})
        emitter.write('proofs/preimages/runtime_session.py', base_g1.encode())
        emitter.write('proofs/preimages/wrapper_blueprint.py', blueprint_base.encode())
        emitter.write('proofs/preimages/run_wrapper_canary.py', runner_base.encode())
        deltas = []
        for name, before, after in (('root-wrapper-admission.diff', base_g1, runtime),
                                   ('derived-sql-pin.diff', blueprint_with_rootdir, blueprint_derived),
                                   ('derived-session-events-parent.diff', runner_base, runner_derived),
                                   ('derived-test-runner-boundary.diff', witness_runner_before, witness_runner_after),
                                   ('derived-pytest-rootdir-blueprint.diff', blueprint_base, blueprint_with_rootdir),
                                   ('derived-chrome-ui-exact.diff', chrome_before, chrome_after)):
            deltas.append(emitter.write('proofs/' + name, ''.join(difflib.unified_diff(
                before.splitlines(True), after.splitlines(True), fromfile='frozen_definition', tofile='fresh_root_copy')).encode()))
        coord = []
        for name in ('rpc_instrument_contract.py', 'wrapper_blueprint.py', 'run_wrapper_canary.py'):
            raw = (blueprint_derived.encode() if name == 'wrapper_blueprint.py' else
                   runner_derived.encode() if name == 'run_wrapper_canary.py' else
                   regular_bytes(PREP / 'coordinator' / name))
            coord.append(emitter.write('coordinator/' + name, raw))
        blueprint = load_pure('c17_fresh_wrapper_blueprint', root / 'coordinator/wrapper_blueprint.py')
        config = QA / 'src/frontend/vite.config.ts'
        config_row = next(row for row in source_manifest['files'] if row['path'] == str(config))
        need(reference(config) == {k: config_row[k] for k in ('path', 'sha256', 'bytes')}, 'Vite autre blob')
        vite = [emitter.write(str(Path(path).relative_to(root)), text.encode())
                for path, text in blueprint.render_vite_configs(root, regular_bytes(config).decode()).items()]
        auxiliary_ref = emitter.json('authorization/auxiliary-physical.json', {
            'schema': 'c17-wrapper-canary-auxiliary-physical-v1', 'root': str(root), 'head': HEAD,
            'git_snapshot_ref': overlay['git_snapshot_ref'], 'auxiliary_context_refs': overlay['auxiliary_context_refs'],
            'metadata_by_job': overlay['metadata_by_job'], 'auxiliary_descriptors': chrome_rows, 'chrome_files_ref': chrome_files_ref})
        need(blueprint.auxiliary_metadata(root, git_ref=overlay['git_snapshot_ref'],
             chrome_context_refs=overlay['auxiliary_context_refs']) == overlay['metadata_by_job'], 'Metadata/env divergents')
        witness_copies = [emitter.write('authorization/runner-boundary/' + name,
                                        regular_bytes(WITNESS / name)) for name in WITNESS_FILES]
        source_refs = coord + vite + list(overlay['outputs'].values()) + list(supports['outputs'].values())
        source_refs += [r['output'] for r in core] + [row['launch_defaults_ref'] for row in chrome_rows.values()]
        source_refs += [chrome_files_ref, reference(config)]
        source_refs = join_sources79(source_refs, witness_copies, deltas, root)
        refs_ref = emitter.json('authorization/source-refs.json', {
            'schema': 'c17-wrapper-canary-source-refs-v1', 'source_refs': source_refs, 'scope': 'WRAPPER_CANARY',
            'head': HEAD, 'root_admission_delta_ref': deltas[0], 'derived_sql_pin_ref': deltas[1],
            'derived_qa_parent_dirs_ref': deltas[2], 'derived_test_runner_ref': deltas[3],
            'derived_pytest_blueprint_ref': deltas[4], 'derived_chrome_ui_exact_ref': deltas[5],
            'runner_boundary_definition_refs': witness_copies,
            'rpc_diagnostic_origin_index_ref': diagnostic['index_ref'],
            'rpc_diagnostic_derivation_refs': diagnostic_proofs})
        chrome_copy_after = verify_chrome_qa_tree(json_checked(authority['chrome_qa_copy_ref']))
        need(all(chrome_copy_after[key] == physical_observations['before'][key]
                 for key in ('entries', 'types', 'source_snapshot_sha256', 'copy_snapshot_sha256')),
             'Arbre Chrome changé entre préflight et préparation finale')
        chrome_copy_after_ref = emitter.json('authorization/chrome-copy-fresh-after.json', chrome_copy_after)
        go_ref = emitter.json('authorization/root-go.json', {
            'schema': 'c17-wrapper-canary-root-go-v1', 'root': str(root), 'actor': '/root', 'head': HEAD,
            'scope': 'WRAPPER_CANARY', 'root_tool_authorization_verified': True,
            'source_checkout_ref': checkout_ref, 'source_refs_ref': refs_ref, 'auxiliary_ref': auxiliary_ref,
            'preparation_authority_ref': authority_ref, 'authority_is_external_tool_invocation_not_this_JSON': True,
            'chrome_profile_ref': reference(root / 'g1/chrome.sb'),
            'chrome_profile_origin_ref': chrome_profile_ref, 'chrome_qa_copy_ref': authority['chrome_qa_copy_ref'],
            'chrome_copy_fresh_before_ref': chrome_copy_before_ref, 'chrome_copy_fresh_after_ref': chrome_copy_after_ref,
            'chrome_contract_qa_ref': reference(root / 'source/chrome_contract.py'), 'chrome_contract_delta_ref': contract_delta_ref,
            'runner_boundary_index_ref': reference(root / 'authorization/runner-boundary/INDEX.json'),
            'native_exact_tool_GO_still_required': True, 'FULL': False, 'release': False})
        need(all(reference(Path(r['path'])) == r for r in originals.values()), 'Onze sorties originelles mutées')
        need(reference(Path(base['manifest_ref']['path'])) == base['manifest_ref'], 'Manifeste11 muté')
        need(all(reference(Path(r['path'])) == r for r in source_refs), 'Sources physiques générées mutées')
        need(all(reference(Path(r['path'])) == r for r in pins.values()), 'Gel d\'origine muté')
        need(reference(Path(__file__).resolve()) == authority['builder_ref'], 'Builder changé pendant construction')
        need(reader.recheck() == HEAD, 'HEAD changé pendant construction')
        need(not any((root / name).exists() for name in ('binding.json', 'decision.json', 'runtime/pile-reprise.json', 'wrapper-canary-result.json')),
             'État runtime créé par construction')
        result = {'schema': 'c17-fresh-wrapper-construction-receipt-v1', 'root': str(root), 'head': HEAD,
            'actor': '/root', 'status': 'prepared_only_native_tool_GO_required', 'builder_ref': authority['builder_ref'],
            'authority_ref': authority_ref, 'web_profile_ref': web_profile_ref,
            'chrome_profile_ref': chrome_profile_ref, 'chrome_qa_copy_ref': authority['chrome_qa_copy_ref'],
            'chrome_copy_fresh_before_ref': chrome_copy_before_ref, 'chrome_copy_fresh_after_ref': chrome_copy_after_ref,
            'chrome_contract_qa_ref': reference(root / 'source/chrome_contract.py'), 'chrome_contract_delta_ref': contract_delta_ref,
            'runner_boundary_definition_refs': witness_copies,
            'source_refs_count': len(source_refs), 'dependencies_observed': deps,
            'git_tree_files_verified': len(observed), 'source_indexes': [reference(p) for p in INDEX_PINS],
            'historical_ips_observations': historical_observations,
            'base11_ref': base['manifest_ref'], 'base11_unchanged': True, 'support8_ref': supports['manifest_ref'],
            'overlay28_ref': overlay_ref, 'chrome5_ref': chrome_ref, 'core18_ref': core_ref,
            'coordinator3_refs': coord, 'vite2_refs': vite, 'source_refs_ref': refs_ref, 'root_go_ref': go_ref,
            'rpc_diagnostic_origin_index_ref': diagnostic['index_ref'],
            'rpc_diagnostic_derivation_refs': diagnostic_proofs,
            'deltas': deltas, 'derived_qa_parent_dirs_ref': deltas[2],
            'derived_test_runner_ref': deltas[3], 'derived_pytest_blueprint_ref': deltas[4],
            'derived_chrome_ui_exact_ref': deltas[5],
            'sql_contract_ref': sql_ref, 'SQL_definition_review_required': True,
            'runtime_executed': False, 'G1_imported': False, 'FULL': False, 'release': False}
        receipt_ref = emitter.json('fresh-wrapper-construction.json', result)
        failed = False
        return {'status': result['status'], 'receipt_ref': receipt_ref, 'root_go_ref': go_ref, 'sql_contract_ref': sql_ref}
    finally:
        if failed:
            # Aucun rollback/destruction. Une racine partielle est gardée rouge et non relançable.
            try:
                emitter.json('construction-error.json', {'schema': 'c17-fresh-wrapper-construction-error-v1',
                    'root': str(root), 'at': datetime.now(UTC).isoformat(), 'partial_outputs': emitter.outputs,
                    'runtime_executed': False, 'replay_allowed': False, 'error': str(sys.exception())})
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--web-profile-ref', type=json.loads, required=True)
    parser.add_argument('--chrome-profile-ref', type=json.loads, required=True)
    parser.add_argument('--authority-ref', type=json.loads, required=True)
    parser.add_argument('--prepare', action='store_true')
    args = parser.parse_args()
    need(args.prepare, 'Aucune construction sans --prepare et GO externe précis')
    print(json.dumps(build(args.root, web_profile_ref=args.web_profile_ref,
                           chrome_profile_ref=args.chrome_profile_ref, authority_ref=args.authority_ref), sort_keys=True))


if __name__ == '__main__':
    main()
