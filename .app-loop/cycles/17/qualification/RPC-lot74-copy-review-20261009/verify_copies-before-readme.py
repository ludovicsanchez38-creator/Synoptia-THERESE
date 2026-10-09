"""Read existing LOT74 copies only; no extraction, writing, OS calls or imports of QA code."""
from __future__ import annotations

import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import tarfile

ROOT = Path('/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE-c15-codex/.app-loop/cycles/17/qualification/RPC-lot74-20261009')
MANIFEST_SHA = '70dfab4954a1f562c58b9b35cf9d59eedbfb3867ca02153f58f67ebcc43d6116'
SELECTION_SHA = 'bcf84da4132f8d65202a911bfe9156441eb2f0cd97ce2ae9509fd063549ce5c4'


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


observed = {}


def read(name: str, digest: str | None = None, size: int | None = None) -> bytes:
    need(Path(name).name == name, 'Read not a direct archive copy')
    path = ROOT / name
    before = path.lstat()
    need(path.resolve() == path and stat.S_ISREG(before.st_mode) and before.st_uid == 501
         and stat.S_IMODE(before.st_mode) == 0o600 and before.st_nlink == 1,
         'Archive copy type/mode/owner/link')
    need(before.st_size <= 8_000_000, 'Copy above closed bound')
    raw = path.read_bytes()
    after = path.lstat()
    # Ordinary reads may update atime; it is not evidence of changed bytes.
    keys = ('st_dev', 'st_ino', 'st_mode', 'st_uid', 'st_gid', 'st_nlink',
            'st_size', 'st_mtime_ns', 'st_ctime_ns')
    need(all(getattr(before, key) == getattr(after, key) for key in keys)
         and len(raw) == before.st_size, 'Copy changed during read')
    if digest is not None:
        need(sha(raw) == digest and len(raw) == size, 'Copy pinned bytes differ: ' + name)
    observed[name] = (sha(raw), len(raw))
    return raw


def unpack(raw: bytes, expected: list[dict], bound: int) -> dict[str, bytes]:
    need(len(expected) <= 4096, 'Too many archive members')
    data = bytearray()
    with gzip.GzipFile(fileobj=io.BytesIO(raw), mode='rb') as source:
        while part := source.read(1 << 20):
            data.extend(part)
            need(len(data) <= bound, 'Decompressed archive above bound')
    bodies = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:') as archive:
        members = archive.getmembers()
        need(len(members) == len(expected), 'Extra or absent member')
        for entry, spec in zip(members, expected):
            pure = PurePosixPath(entry.name)
            need(entry.name == spec['name'] and not pure.is_absolute() and '..' not in pure.parts
                 and str(pure) == entry.name and entry.name not in bodies, 'Member name/order')
            need(entry.type == tarfile.REGTYPE and entry.mode == 0o600
                 and entry.uid == entry.gid == entry.mtime == 0
                 and entry.uname == entry.gname == entry.linkname == ''
                 and not entry.pax_headers and data[entry.offset + 257:entry.offset + 263] == b'ustar\x00',
                 'Member not regular closed USTAR metadata')
            need(entry.size == spec['bytes'], 'Member size')
            stream = archive.extractfile(entry)
            need(stream is not None, 'Unreadable member')
            with stream:
                body = stream.read(entry.size + 1)
            need(len(body) == spec['bytes'] and sha(body) == spec['sha256'], 'Member digest')
            bodies[entry.name] = body
    return bodies


need(ROOT.resolve() == ROOT and ROOT.is_dir(), 'Other canonical root')
manifest = json.loads(read('MANIFEST.json', MANIFEST_SHA, 250732))
receipt = json.loads(read('receipt.json', '9337258fd47d1471ee4cc4c195bc82354a4d7212266388265186bda5dfc38ba4', 740))
need(manifest['schema'] == 'c17-lot74-reviewed-documentary-archive-v1'
     and manifest['native15_result'] == 'RED_exit86' and manifest['selection_sha256'] == SELECTION_SHA
     and manifest['sources_before_after_equal'] is True and manifest['private_full_system_log_excluded'] is True
     and manifest['copies_are_live_identity_or_ownership'] is False
     and all(manifest[key] is False for key in ('A_B_admitted', 'FULL', 'release', 'native_executed_by_archiver')),
     'Archived documentary scope/RED changed')
need(receipt['status'] == 'archive_created_and_verified' and receipt['sources_unchanged'] is True
     and all(receipt[key] is False for key in ('native', 'FULL', 'release'))
     and receipt['manifest']['sha256'] == MANIFEST_SHA and receipt['manifest']['bytes'] == 250732,
     'MAIN receipt mismatch')
need(len(manifest['archives']) == manifest['archive_count'] == receipt['archives'] == 30
     and len(manifest['source_files']) == receipt['members'] == 310
     and manifest['control_files'] == 13 and manifest['selected_files'] == 297
     and manifest['selected_bytes'] == 14568266, 'Counts changed')
copies = {}
material = []
for ref in manifest['archives']:
    path = Path(ref['path'])
    need(path.parent == ROOT, 'Archive path outside output')
    rows = [row for row in manifest['source_files'] if row['archive'] == path.name]
    need(rows and len({row['member'] for row in rows}) == len(rows), 'Archive table empty/duplicate')
    for row in rows:
        source, origin = row['source'], row['physical_origin']
        need(all(origin[key] == source[key] for key in ('path', 'sha256', 'bytes'))
             and origin['nlink'] in (1, 2), 'Origin snapshot vs bytes mismatch')
        need(source['path'] != '/private/tmp/therese-c17-root15-chrome14738-log-QS4RpE/stdout.json',
             'Private full system log payload included')
        if not path.name.startswith('30-'):
            row_name, member_name = row['member'].split('/', 1)
            material.append({'row': row_name, 'name': member_name,
                'sha256': source['sha256'], 'bytes': source['bytes']})
    raw = read(path.name, ref['sha256'], ref['bytes'])
    need(len(raw) <= (8_000_000 if path.name.startswith('01-') else 3_000_000), 'Compressed row bound')
    copies.update(unpack(raw, [{'name': row['member'], 'sha256': row['source']['sha256'],
        'bytes': row['source']['bytes']} for row in rows], 20_000_000))
need(len(material) == 297 and sum(row['bytes'] for row in material) == 14568266
     and sha(json.dumps(material, sort_keys=True, separators=(',', ':')).encode()) == SELECTION_SHA,
     'Archived selection digest changed')
need(sum(ref['bytes'] for ref in manifest['archives']) == receipt['compressed_bytes'] == 8153159
     and receipt['compressed_bytes'] <= 24_000_000, 'Total compressed bound')

review = json.loads(read('INDEPENDENT-PREPARATION-REVIEW.json',
    'feb8ee35904667f13635934494c9738f613b8f6fe0b26d2f05e6f60e2f391c81', 3376))
need(review['actor'] == '/root/cycle17_gate_review' and review['status'] == 'archive_preparation_reviewed_only', 'Review scope')
for ref in review['refs']:
    path = Path(ref['path'])
    if path.parent == Path(manifest['independent_preparation_review_ref']['path']).parent:
        need(path.name in ('REVIEW.md', 'observations.json'), 'Other local review copy')
        read('INDEPENDENT-PREPARATION-' + path.name, ref['sha256'], ref['bytes'])
read('archive-reviewed-executor.py', 'f20c1a846a6435344b50e1b4dd421484f11d60320a7410d068d3fea2adef5673', 11634)
read('archive-executor-first-red-preimage.py', 'b4aa19d2c95d3f9563559e0ed6ed8cd2cffb6095a04963e50f588e2283da3eb0', 9869)
read('ARCHIVE-EXECUTOR-FIRST-REFUSAL.md', 'eb860e2311ba1ae94be6485d90b225bce977ef6dd41fce24e4984d8d439536fd', 1159)
for name, digest, size in (
    ('INDEX.json', 'c4edf25be8f52de9cbd9b03e3249165cb828dd9a5a78218be069b4d014ca6fae', 2510),
    ('REVIEW.md', 'de4b6d24642f6c7d7947b242b07b47fef6ba483c2cb5bba494f4732b613827fd', 4556),
    ('observations.json', '2e4a0bc1f627046ac73a5b2904c37799ea3bbac9190f0875342fa41dab3187e7', 1420)):
    read('FIRST-EXECUTOR-REVIEW-' + name, digest, size)
need(set(path.name for path in ROOT.iterdir()) == set(observed) and len(observed) == 41, 'Extra file or missing copy')

root15 = json.loads(copies['24-root15-native-red/wrapper-canary-result.json'])
need(root15['passed'] is False and root15['runner_exit'] == 86
     and root15['owned_shutdown_proved'] is False and root15['rpc_audit']['observed'] == 7
     and root15['rpc_audit']['expected'] == 15 and root15['FULL'] is False, 'Native RED changed in archive')
old_preflight = json.loads(copies['21-checker-preflight-red/receipt.json'])
need(old_preflight['passed'] is False and old_preflight['exit_code'] == 1, 'First checker RED changed')
gate = json.loads(copies['28-gate-independent-native-closure/INDEX.json'])
need(gate['first_analytical_chronology_red_preserved'] is True
     and gate['kernel_birth_chronology_proved'] is False and gate['campaign_qualification'] is False,
     'Analytical RED changed')

selection = json.loads(copies['01-source-qa-archive/SELECTION.json'])
source_raw = copies['01-source-qa-archive/source-qa-evidence.tar.gz']
need(sha(source_raw) == 'bab6b66a868bb7d361e32f3d8a389bbaf588ae0edee1f153ffb7cd5d3a174a68'
     and len(source_raw) == 6963011 and len(selection['members']) == selection['member_count'] == 95,
     'Only special source archive differs')
unpack(source_raw, [{'name': row['name'], 'sha256': row['origin_ref']['sha256'],
    'bytes': row['origin_ref']['bytes']} for row in selection['members']], 40_000_000)
for name, expected in observed.items():
    need((sha((ROOT / name).read_bytes()), (ROOT / name).stat().st_size) == expected,
         'Archived copy changed during review')
print(json.dumps({'status': 'documentary_copies_verified_readonly', 'root': str(ROOT),
    'manifest_sha256': MANIFEST_SHA, 'archives': 30, 'members': 310, 'metadata_copies': 9,
    'compressed_bytes': 8153159, 'selected_files': 297, 'selection_sha256': SELECTION_SHA,
    'inner_source_members': 95, 'private_raw_system_stdout_excluded': True,
    'native15_RED_preserved': True, 'first_checker_RED_preserved': True,
    'first_analytical_RED_preserved': True, 'original_paths_followed': False,
    'archive_or_receipt_written': False, 'G1_imported': False, 'native_executed': False,
    'FULL': False, 'release': False}, ensure_ascii=False))
