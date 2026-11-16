"""Cas limites des gardes de publication, avec commandes externes fictives."""

import hashlib
import importlib.util
import io
import json
import struct
import subprocess
import sys
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


def workflow():
    return yaml.safe_load((ROOT / '.github/workflows/release.yml').read_text(encoding='utf-8'))


def publication():
    spec = importlib.util.spec_from_file_location('publication_gardes', ROOT / 'scripts/publish_release_artifacts.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_shell(script):
    return subprocess.run(['bash', '-e', '-c', script], capture_output=True, text=True, check=False)


@pytest.mark.parametrize(('commit', 'status', 'accepted'), [('abc123', 0, True), ('def456', 0, False), ('', 1, False)])
def test_comparaison_du_tag_avec_le_commit_de_la_ci(commit, status, accepted):
    steps = workflow()['jobs']['preflight']['steps']
    checkout = next(step for step in steps if step.get('uses', '').startswith('actions/checkout@'))
    guard = next(step for step in steps if 'git rev-parse' in step.get('run', ''))
    assert checkout['with']['fetch-depth'] == 0
    assert 'dry_run != true' in checkout['if'] and 'dry_run != true' in guard['if']
    mock = (f"git() {{ [ \"$4\" = 'refs/tags/v-test^{{commit}}' ] || return 3; "
            f"printf '%s' '{commit}'; return {status}; }}\n")
    result = run_shell(mock + "TAG_A_VERIFIER=v-test\nGITHUB_SHA=abc123\n" + guard['run'])
    assert (result.returncode == 0) is accepted
    if not accepted:
        assert '::error::' in result.stdout


@pytest.mark.parametrize(('draft', 'status', 'accepted'), [('true', 0, True), ('false', 0, False), ('true', 1, False)])
def test_sources_refusent_brouillon_public_ou_lecture_echouee(draft, status, accepted):
    steps = workflow()['jobs']['sources-copyleft']['steps']
    step = next(step for step in steps if 'gh release upload' in step.get('run', ''))
    script = step['run']
    guard = script[script.index('if ! statut_brouillon='):script.index('gh release upload')]
    mock = f"gh() {{ printf '%s' '{draft}'; return {status}; }}\n"
    result = run_shell(mock + guard)
    assert (result.returncode == 0) is accepted
    if not accepted:
        assert '::error::' in result.stdout


@pytest.mark.parametrize(('final_status', 'draft', 'accepted'), [(0, True, True), (0, False, False), (1, True, False)])
def test_course_creation_relit_le_brouillon_juste_avant_upload(monkeypatch, tmp_path, final_status, draft, accepted):
    module = publication()
    monkeypatch.setattr(sys, 'argv', ['publish_release_artifacts.py', str(tmp_path), '--platform', 'macOS'])
    monkeypatch.setattr(sys, 'path', sys.path.copy())
    monkeypatch.setitem(sys.modules, 'release_notes', SimpleNamespace(body_from_env=lambda: 'Notes fictives'))
    monkeypatch.setenv('RELEASE_TAG', 'v-test')
    monkeypatch.setenv('TAURI_SIGNING_PRIVATE_KEY', 'cle-fictive')
    monkeypatch.setattr(module, 'artifacts', lambda *_: [Path('factice.dmg')])
    monkeypatch.setattr(module, 'verified_proofs', lambda *_: [Path('preuve-fictive.json')])
    monkeypatch.setattr(module.shutil, 'which', lambda _: '/virtuel/node')
    calls = []
    views = 0

    def fake_run(command, **_kwargs):
        nonlocal views
        calls.append(command)
        if command[:3] == ['gh', 'release', 'view']:
            views += 1
            if '--json' in command:
                return subprocess.CompletedProcess(command, final_status, stdout=json.dumps({'isDraft': draft}))
            return subprocess.CompletedProcess(command, 1 if views == 1 else 0, stdout='')
        if command[:3] == ['gh', 'release', 'create']:
            return subprocess.CompletedProcess(command, 1)
        if command[:3] == ['gh', 'release', 'upload']:
            return subprocess.CompletedProcess(command, 0)
        raise AssertionError('Commande fictive inattendue')

    monkeypatch.setattr(module.subprocess, 'run', fake_run)
    if accepted:
        module.main()
    else:
        with pytest.raises(RuntimeError, match='brouillon'):
            module.main()
    uploads = [call for call in calls if call[:3] == ['gh', 'release', 'upload']]
    assert bool(uploads) is accepted
    assert views == 3


def write_archive(path, executable):
    with tarfile.open(path, 'w:gz') as archive:
        info = tarfile.TarInfo('THERESE.app/Contents/MacOS/therese')
        info.size = len(executable)
        archive.addfile(info, io.BytesIO(executable))


def macho(cpu):
    return struct.pack('<IiiIIIII', 0xFEEDFACF, cpu, 0, 2, 0, 0, 0, 0)


def test_macos_universel_controle_aussi_la_tranche_arm64(tmp_path):
    module = publication()
    arm = macho(0x0100000c)
    x86 = macho(0x01000007)
    header = struct.pack('>II', 0xcafebabe, 2)
    entries = struct.pack('>IIIII', 0x01000007, 0, 48, 32, 0)
    entries += struct.pack('>IIIII', 0x0100000c, 0, 80, 32, 0)
    archive = tmp_path / 'THERESE.app.tar.gz'
    write_archive(archive, header + entries + x86 + arm)
    module.require_arm64(archive)
    write_archive(archive, header + entries + x86 + x86)
    with pytest.raises(ValueError, match='aarch64'):
        module.require_arm64(archive)


def test_alias_macos_garde_les_octets_et_une_preuve_au_nom_publie(monkeypatch, tmp_path):
    module = publication()
    archive = tmp_path / 'THERESE.app.tar.gz'
    write_archive(archive, macho(0x0100000c))
    original = archive.read_bytes()
    inventory = tmp_path / '.work-release/system-libraries.json'
    inventory.parent.mkdir()
    inventory.write_bytes(b'inventaire fictif')
    proof_dir = tmp_path / '.work-release/installer-proofs'
    proof_dir.mkdir()
    proof = {'artifact': archive.name, 'artifact_sha256': hashlib.sha256(original).hexdigest(),
             'build_inventory_sha256': hashlib.sha256(inventory.read_bytes()).hexdigest(), 'files': {'fictif': {}}}
    (proof_dir / (archive.name + '.json')).write_text(json.dumps(proof), encoding='utf-8')
    verified = module.verified_proofs
    monkeypatch.setattr(module, 'artifacts', lambda *_: [archive])
    monkeypatch.setattr(module, 'verified_proofs', lambda paths: verified(paths, tmp_path))
    monkeypatch.setattr(sys, 'argv', ['publish_release_artifacts.py', str(tmp_path), '--platform', 'macOS'])
    monkeypatch.setenv('RELEASE_TAG', 'v-test')
    monkeypatch.setenv('TAURI_SIGNING_PRIVATE_KEY', 'cle-fictive')
    monkeypatch.setattr(module.shutil, 'which', lambda _: '/virtuel/node')
    calls = []

    def fake_run(command, **_kwargs):
        calls.append(command)
        if 'signer' in command:
            Path(str(command[-1]) + '.sig').write_text('signature fictive', encoding='utf-8')
        return subprocess.CompletedProcess(command, 0, stdout='{"isDraft": true}')

    monkeypatch.setattr(module.subprocess, 'run', fake_run)
    module.main()
    alias = tmp_path / 'THERESE_aarch64.app.tar.gz'
    alias_proof = proof_dir / (alias.name + '.json')
    data = json.loads(alias_proof.read_text(encoding='utf-8'))
    assert archive.read_bytes() == alias.read_bytes() == original
    assert data['artifact'] == alias.name and data['artifact_sha256'] == hashlib.sha256(original).hexdigest()
    upload = next(call for call in calls if call[:3] == ['gh', 'release', 'upload'])
    assert str(alias) in upload and str(alias_proof) in upload
    assert str(proof_dir / (archive.name + '.json')) not in upload
