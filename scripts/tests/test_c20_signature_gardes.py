"""Cas limites des gardes de publication, avec commandes externes fictives."""

import hashlib
import importlib.util
import io
import json
import os
import struct
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

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


def write_archive(path, executable):
    with tarfile.open(path, 'w:gz') as archive:
        info = tarfile.TarInfo('THERESE.app/Contents/MacOS/therese')
        info.size = len(executable)
        archive.addfile(info, io.BytesIO(executable))


def macho(cpu):
    return struct.pack('<IiiIIIII', 0xFEEDFACF, cpu, 0, 2, 0, 0, 0, 0)


class SignatureGardesTests(unittest.TestCase):
    def test_comparaison_du_tag_avec_le_commit_de_la_ci(self):
        for commit, status, accepted in [('abc123', 0, True), ('def456', 0, False), ('', 1, False)]:
            with self.subTest(commit=commit, status=status, accepted=accepted):
                steps = workflow()['jobs']['preflight']['steps']
                checkout = next(step for step in steps if step.get('uses', '').startswith('actions/checkout@'))
                guard = next(step for step in steps if 'git rev-parse' in step.get('run', ''))
                self.assertEqual(checkout['with']['fetch-depth'], 0)
                self.assertTrue('dry_run != true' in checkout['if'] and 'dry_run != true' in guard['if'])
                mock = (f"git() {{ [ \"$4\" = 'refs/tags/v-test^{{commit}}' ] || return 3; "
                        f"printf '%s' '{commit}'; return {status}; }}\n")
                result = run_shell(mock + "TAG_A_VERIFIER=v-test\nGITHUB_SHA=abc123\n" + guard['run'])
                self.assertIs(result.returncode == 0, accepted)
                if not accepted:
                    self.assertIn('::error::', result.stdout)

    def test_sources_refusent_brouillon_public_ou_lecture_echouee(self):
        for draft, status, accepted in [('true', 0, True), ('false', 0, False), ('true', 1, False)]:
            with self.subTest(draft=draft, status=status, accepted=accepted):
                steps = workflow()['jobs']['sources-copyleft']['steps']
                step = next(step for step in steps if 'gh release upload' in step.get('run', ''))
                script = step['run']
                guard = script[script.index('if ! statut_brouillon='):script.index('gh release upload')]
                mock = f"gh() {{ printf '%s' '{draft}'; return {status}; }}\n"
                result = run_shell(mock + guard)
                self.assertIs(result.returncode == 0, accepted)
                if not accepted:
                    self.assertIn('::error::', result.stdout)

    def test_course_creation_relit_le_brouillon_juste_avant_upload(self):
        for final_status, draft, accepted in [(0, True, True), (0, False, False), (1, True, False)]:
            with self.subTest(final_status=final_status, draft=draft, accepted=accepted), tempfile.TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                module = publication()
                calls = []
                views = 0

                def fake_run(command, calls=calls, final_status=final_status, draft=draft, **_kwargs):
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

                with (
                    patch.object(sys, 'argv', ['publish_release_artifacts.py', str(tmp_path), '--platform', 'macOS']),
                    patch.object(sys, 'path', sys.path.copy()),
                    patch.dict(sys.modules, {'release_notes': SimpleNamespace(body_from_env=lambda: 'Notes fictives')}),
                    patch.dict(os.environ, {'RELEASE_TAG': 'v-test', 'TAURI_SIGNING_PRIVATE_KEY': 'cle-fictive'}),
                    patch.object(module, 'artifacts', lambda *_: [Path('factice.dmg')]),
                    patch.object(module, 'verified_proofs', lambda *_: [Path('preuve-fictive.json')]),
                    patch.object(module.shutil, 'which', lambda _: '/virtuel/node'),
                    patch.object(module.subprocess, 'run', fake_run),
                ):
                    if accepted:
                        module.main()
                    else:
                        with self.assertRaisesRegex(RuntimeError, 'brouillon'):
                            module.main()
                uploads = [call for call in calls if call[:3] == ['gh', 'release', 'upload']]
                self.assertIs(bool(uploads), accepted)
                self.assertEqual(views, 3)

    def test_macos_universel_controle_aussi_la_tranche_arm64(self):
        tmp_path = Path(self.enterContext(tempfile.TemporaryDirectory()))
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
        with self.assertRaisesRegex(ValueError, 'aarch64'):
            module.require_arm64(archive)

    def test_alias_macos_garde_les_octets_et_une_preuve_au_nom_publie(self):
        tmp_path = Path(self.enterContext(tempfile.TemporaryDirectory()))
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
        self.enterContext(patch.object(module, 'artifacts', lambda *_: [archive]))
        self.enterContext(patch.object(module, 'verified_proofs', lambda paths: verified(paths, tmp_path)))
        self.enterContext(patch.object(sys, 'argv', ['publish_release_artifacts.py', str(tmp_path), '--platform', 'macOS']))
        self.enterContext(patch.dict(os.environ, {'RELEASE_TAG': 'v-test', 'TAURI_SIGNING_PRIVATE_KEY': 'cle-fictive'}))
        self.enterContext(patch.object(module.shutil, 'which', lambda _: '/virtuel/node'))
        calls = []

        def fake_run(command, **_kwargs):
            calls.append(command)
            if 'signer' in command:
                Path(str(command[-1]) + '.sig').write_text('signature fictive', encoding='utf-8')
            return subprocess.CompletedProcess(command, 0, stdout='{"isDraft": true}')

        self.enterContext(patch.object(module.subprocess, 'run', fake_run))
        module.main()
        alias = tmp_path / 'THERESE_aarch64.app.tar.gz'
        alias_proof = proof_dir / (alias.name + '.json')
        data = json.loads(alias_proof.read_text(encoding='utf-8'))
        self.assertTrue(archive.read_bytes() == alias.read_bytes() == original)
        self.assertTrue(data['artifact'] == alias.name and data['artifact_sha256'] == hashlib.sha256(original).hexdigest())
        upload = next(call for call in calls if call[:3] == ['gh', 'release', 'upload'])
        self.assertTrue(str(alias) in upload and str(alias_proof) in upload)
        self.assertNotIn(str(proof_dir / (archive.name + '.json')), upload)


if __name__ == '__main__':
    unittest.main()
