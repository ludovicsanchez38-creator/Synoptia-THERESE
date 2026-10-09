"""Exécuteur MAIN fermé : archive documentaire seulement, jamais runtime."""
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys

BASE = Path('/private/tmp/therese-c17-lot74-final-qY7yoXIY')
REPO = Path('/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE-c15-codex')
DEST = REPO / '.app-loop/cycles/17/qualification/RPC-lot74-20261009'
INDEX_SHA = '9ead71cd06729ce41d0f484fbae990494ece954c06606e88307420ee183887a9'
SCRIPT_SHA = '4938b04f6c44f4dfacd6e1de9a9f54bb6cc88bf627ae2bcab324dd79aa7c461c'
PLAN_SHA = '2b43270ea021a5dec1d67cc2d45ecfd7396b7784aad7815660d6cd1cfac5ea99'
SELECTION_SHA = 'bcf84da4132f8d65202a911bfe9156441eb2f0cd97ce2ae9509fd063549ce5c4'


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def physical(path: Path) -> tuple[bytes, dict]:
    require(path.resolve(strict=True) == path, 'chemin non canonique')
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
            and before.st_nlink in (1, 2) and before.st_size <= 8_000_000,
            'type, UID, lien ou taille inattendu')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        opened = os.fstat(fd)
        keys = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns', 'st_nlink')
        require(all(getattr(before, k) == getattr(opened, k) for k in keys), 'inode ouverture')
        parts = []
        size = 0
        while part := os.read(fd, 1 << 20):
            size += len(part)
            require(size <= before.st_size, 'croissance lecture')
            parts.append(part)
        require(all(getattr(before, k) == getattr(os.fstat(fd), k) for k in keys),
                'mutation lecture')
    finally:
        os.close(fd)
    require(all(getattr(before, k) == getattr(path.lstat(), k) for k in keys), 'mutation chemin')
    raw = b''.join(parts)
    return raw, {'path': str(path), 'sha256': digest(raw), 'bytes': len(raw),
                 'dev': before.st_dev, 'ino': before.st_ino, 'nlink': before.st_nlink,
                 'mtime_ns': before.st_mtime_ns, 'ctime_ns': before.st_ctime_ns}


def exact(path: Path, sha: str, size: int) -> bytes:
    raw, observed = physical(path)
    require(observed['sha256'] == sha and observed['bytes'] == size, 'pin divergent : ' + str(path))
    return raw


def write_new(path: Path, raw: bytes) -> None:
    require(path.parent == DEST and path.name not in ('', '.', '..'), 'destination non fermée')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def encoded(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review-index', required=True)
    parser.add_argument('--review-sha256', required=True)
    parser.add_argument('--review-bytes', required=True, type=int)
    parser.add_argument('--execute-reviewed-archive', action='store_true')
    args = parser.parse_args()
    require(args.execute_reviewed_archive, 'aucune émission sans appel explicite MAIN')
    review_path = Path(args.review_index)
    require(str(review_path).startswith('/private/tmp/therese-c17-lot74-review-')
            and review_path.name == 'INDEX.json', 'racine revue non fermée')
    review = json.loads(exact(review_path, args.review_sha256, args.review_bytes))
    require(review.get('actor') == '/root/cycle17_gate_review'
            and review.get('status') == 'archive_preparation_reviewed_only'
            and review.get('subject_index_sha256') == INDEX_SHA
            and review.get('executor_sha256') == digest(Path(__file__).read_bytes())
            and review.get('native_executed') is False
            and review.get('FULL') is False and review.get('release') is False,
            'revue indépendante ne joint pas ces octets')
    index_raw = exact(BASE / 'INDEX.json', INDEX_SHA, 3911)
    index = json.loads(index_raw)
    exact(BASE / 'archive_lot74.py', SCRIPT_SHA, 22710)
    plan_raw = exact(BASE / 'PLAN.json', PLAN_SHA, 12619)
    plan = json.loads(plan_raw)
    require(plan['prepared_selection_sha256'] == SELECTION_SHA
            and len(plan['rows']) == 28 and plan['archive_execution_authorized'] is False
            and plan['FULL'] is False and plan['release'] is False,
            'plan historique modifié ou qualification fabriquée')
    spec = importlib.util.spec_from_file_location('closed_lot74_archive_module', BASE / 'archive_lot74.py')
    require(spec is not None and spec.loader is not None, 'module absent')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    rows = [(row['id'], module.select(row)) for row in plan['rows']]
    docs = module.select_external(plan)
    rows.append(('29-external-documents', docs))
    material = [{'row': key, 'name': item.name, 'sha256': item.digest, 'bytes': len(item.data)}
                for key, items in rows for item in items]
    selection = digest(json.dumps(material, sort_keys=True, separators=(',', ':')).encode())
    require(selection == SELECTION_SHA and len(material) == 297
            and sum(item['bytes'] for item in material) == 14_568_266, 'sélection différente')
    controls = [module.read_item(BASE, BASE / 'INDEX.json')]
    controls += [module.read_item(BASE, Path(ref['path']), expected=ref) for ref in index['local_refs']]
    rows.append(('30-preparation-controls', controls))
    execution_sources = [Path(__file__).resolve(), review_path]
    execution_raw = [(path, *physical(path)) for path in execution_sources]
    sources_before = {str(item.path): physical(item.path)[1] for _, items in rows for item in items}
    sources_before.update({str(path): observed for path, _, observed in execution_raw})
    forbidden = Path('/private/tmp/therese-c17-root15-chrome14738-log-QS4RpE/stdout.json')
    require(str(forbidden) not in sources_before, 'log système privé sélectionné')
    require(REPO.resolve(strict=True) == REPO and DEST.parent.resolve(strict=True) == DEST.parent,
            'racine Git/destination divergente')
    for parent in DEST.parents:
        if parent == REPO.parent:
            break
        require(not parent.is_symlink(), 'parent destination symlink')
    require((REPO / '.git/HEAD').read_text() == 'ref: refs/heads/codex/cycle-17\n', 'autre branche')
    require(not DEST.exists() and not DEST.is_symlink(), 'lot déjà présent, aucun overwrite')
    started = datetime.now(UTC).isoformat()
    DEST.mkdir(mode=0o700)
    archives = []
    source_files = []
    for key, items in rows:
        archive = module.tar_archive(DEST / (key + '.tar.gz'), items, key,
                                     archive_limit=8_000_000 if key == '01-source-qa-archive' else 3_000_000)
        archives.append(archive)
        for item in items:
            source_files.append({'archive': Path(archive['path']).name,
                                 'member': key + '/' + item.name,
                                 'source': item.ref(), 'physical_origin': sources_before[str(item.path)]})
    require(sum(ref['bytes'] for ref in archives) <= 24_000_000, 'archives >24MB')
    for path, raw, _ in execution_raw:
        write_new(DEST / ('archive-reviewed-executor.py' if path == Path(__file__).resolve()
                          else 'INDEPENDENT-PREPARATION-REVIEW.json'), raw)
    sources_after = {path: physical(Path(path))[1] for path in sources_before}
    require(sources_before == sources_after, 'source modifiée pendant archive')
    manifest = {'schema': 'c17-lot74-reviewed-documentary-archive-v1', 'actor': '/root',
                'started_at': started, 'completed_at': datetime.now(UTC).isoformat(),
                'selection_sha256': selection, 'selected_files': 297,
                'selected_bytes': 14_568_266, 'control_files': len(controls),
                'archive_count': len(archives), 'archives': archives,
                'source_files': source_files, 'sources_before_after_equal': True,
                'private_full_system_log_excluded': True,
                'source_qa_head_historical': plan['source_qa_head_historical'],
                'native15_result': 'RED_exit86', 'native_executed_by_archiver': False,
                'copies_are_live_identity_or_ownership': False,
                'A_B_admitted': False, 'FULL': False, 'release': False,
                'independent_preparation_review_ref': {'path': str(review_path),
                    'sha256': args.review_sha256, 'bytes': args.review_bytes},
                'executor_ref': {'path': str(Path(__file__).resolve()),
                    'sha256': digest(Path(__file__).read_bytes()),
                    'bytes': Path(__file__).stat().st_size}}
    write_new(DEST / 'MANIFEST.json', encoded(manifest))
    receipt = {'schema': 'c17-lot74-MAIN-archive-receipt-v1', 'status': 'archive_created_and_verified',
               'manifest': physical(DEST / 'MANIFEST.json')[1],
               'archives': len(archives), 'members': len(source_files),
               'compressed_bytes': sum(ref['bytes'] for ref in archives),
               'selection_sha256': selection, 'sources_unchanged': True,
               'native': False, 'FULL': False, 'release': False}
    write_new(DEST / 'receipt.json', encoded(receipt))
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
