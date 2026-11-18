#!/usr/bin/env python3
"""Dernière étape : re-signer les octets finaux pour l'updater, puis les joindre au brouillon."""
import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import tarfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]


def artifacts(bundle, platform):
    patterns = {
        'macOS': ('dmg/*.dmg', 'macos/*.app.tar.gz'),
        'Windows': ('nsis/*.exe', 'msi/*.msi'),
        'Linux': ('deb/*.deb',),
    }[platform]
    paths = []
    for pattern in patterns:
        matches = list(bundle.glob(pattern))
        if len(matches) != 1:
            raise ValueError(f'Un unique artefact {pattern} est requis')
        paths.extend(matches)
    if platform == 'Linux':
        paths.extend(sorted(bundle.glob('appimage/*.AppImage')))
    return paths


def verified_proofs(paths, root=ROOT):
    """Les vérifications ne doivent pas être contournées en appelant publish seul."""
    inventory = root / '.work-release/system-libraries.json'
    inventory_hash = hashlib.sha256(inventory.read_bytes()).hexdigest()
    proofs = []
    for artifact in paths:
        path = root / '.work-release/installer-proofs' / (artifact.name + '.json')
        data = json.loads(path.read_text(encoding='utf-8'))
        with artifact.open('rb') as f:
            digest = hashlib.file_digest(f, 'sha256').hexdigest()
        if (data.get('artifact') != artifact.name or data.get('artifact_sha256') != digest or
                data.get('build_inventory_sha256') != inventory_hash or not data.get('files')):
            raise ValueError('Preuve de l’installeur absente ou périmée : ' + artifact.name)
        proofs.append(path)
    return proofs


def require_arm64(archive):
    """Lire le Mach-O de l'app dans l'archive, sans extraire ni modifier le bundle."""
    try:
        with tarfile.open(archive, 'r:gz') as tar:
            binaries = []
            for member in tar:
                parts = PurePosixPath(member.name).parts
                if (member.isfile() and len(parts) == 4 and parts[0].endswith('.app')
                        and parts[1:3] == ('Contents', 'MacOS')
                        and parts[3] in ('therese', 'THERESE')):
                    binaries.append(member)
            if len(binaries) != 1:
                raise ValueError('Un unique exécutable macOS est requis dans l’archive')
            member = binaries[0]
            stream = tar.extractfile(member)
            if stream is None:
                raise ValueError('Exécutable macOS illisible dans l’archive')
            header = stream.read(32)
            thin = {b'\xcf\xfa\xed\xfe': '<', b'\xfe\xed\xfa\xcf': '>'}
            fat = {b'\xca\xfe\xba\xbe': ('>', 20), b'\xbe\xba\xfe\xca': ('<', 20),
                   b'\xca\xfe\xba\xbf': ('>', 32), b'\xbf\xba\xfe\xca': ('<', 32)}
            magic = header[:4]
            if magic in thin and len(header) == 32:
                if struct.unpack_from(thin[magic] + 'I', header, 4)[0] == 0x0100000c:
                    return
            elif magic in fat and len(header) >= 8:
                endian, size = fat[magic]
                count = struct.unpack_from(endian + 'I', header, 4)[0]
                if 0 < count <= 64:
                    stream.seek(8)
                    entries = stream.read(count * size)
                    if len(entries) == count * size:
                        for i in range(count):
                            entry = entries[i * size:(i + 1) * size]
                            cpu = struct.unpack_from(endian + 'I', entry)[0]
                            kind = 'II' if size == 20 else 'QQ'
                            offset, length = struct.unpack_from(endian + kind, entry, 8)
                            if cpu == 0x0100000c and length >= 32 and offset + length <= member.size:
                                stream.seek(offset)
                                slice_header = stream.read(32)
                                order = thin.get(slice_header[:4])
                                if (order and len(slice_header) == 32 and
                                        struct.unpack_from(order + 'I', slice_header, 4)[0] == cpu):
                                    return
    except (OSError, EOFError, tarfile.TarError, struct.error) as exc:
        raise ValueError('Architecture de l’archive macOS illisible : ' + archive.name) from exc
    raise ValueError('Archive macOS incompatible : architecture aarch64 absente')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle', type=Path)
    parser.add_argument('--platform', required=True, choices=['macOS', 'Windows', 'Linux'])
    args = parser.parse_args()
    bundle = args.bundle.resolve()
    paths = artifacts(bundle, args.platform)
    proofs = verified_proofs(paths)
    signing_env = {**os.environ, 'TAURI_SIGNING_PRIVATE_KEY': os.environ['TAURI_SIGNING_PRIVATE_KEY'], 'TAURI_SIGNING_PRIVATE_KEY_PASSWORD': os.environ.get('TAURI_SIGNING_PRIVATE_KEY_PASSWORD', '')}
    command = [shutil.which('node'), str(ROOT / 'src/frontend/node_modules/@tauri-apps/cli/tauri.js'), 'signer', 'sign']
    uploads = list(proofs)
    for index, path in enumerate(paths):
        if path.name.endswith('.app.tar.gz'):
            require_arm64(path)
            if not path.name.endswith('_aarch64.app.tar.gz'):
                renamed = path.with_name(path.name.replace('.app.tar.gz', '_aarch64.app.tar.gz'))
                shutil.copyfile(path, renamed)
                proof = proofs[index]
                data = json.loads(proof.read_text(encoding='utf-8'))
                data['artifact'] = renamed.name
                alias_proof = proof.with_name(renamed.name + '.json')
                alias_proof.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
                uploads[index] = verified_proofs([renamed])[0]
                path = renamed
        if path.suffix != '.dmg':
            result = subprocess.run([*command, str(path)], cwd=ROOT / 'src/frontend', env=signing_env, capture_output=True)
            if result.returncode:
                raise RuntimeError('Échec de signature updater ; publication annulée')
            signature = Path(str(path) + '.sig')
            if not signature.is_file() or not signature.read_text().strip():
                raise RuntimeError('Signature updater absente')
            uploads.append(signature)
        uploads.append(path)
    tag = os.environ['RELEASE_TAG']
    # Les trois runners peuvent créer le même brouillon : un perdant vérifie
    # qu'il existe réellement, sans masquer une erreur d'authentification.
    result = subprocess.run(['gh', 'release', 'view', tag], capture_output=True)
    if result.returncode:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import release_notes
        notes = bundle / 'release-notes.md'
        notes.write_text(release_notes.body_from_env(), encoding='utf-8')
        result = subprocess.run(['gh', 'release', 'create', tag, '--draft', '--prerelease', '--title', 'THÉRÈSE ' + tag, '--notes-file', str(notes)], capture_output=True)
        if result.returncode:
            subprocess.run(['gh', 'release', 'view', tag], check=True, capture_output=True)
    result = subprocess.run(['gh', 'release', 'view', tag, '--json', 'isDraft'], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('Impossible de vérifier le statut brouillon : publication refusée')
    try:
        draft = json.loads(result.stdout).get('isDraft')
    except (ValueError, AttributeError) as exc:
        raise RuntimeError('Statut brouillon illisible : publication refusée') from exc
    if draft is not True:
        raise RuntimeError('La release doit être un brouillon : publication refusée')
    subprocess.run(['gh', 'release', 'upload', tag, '--clobber', *map(str, uploads)], check=True)
    print(f'{len(uploads)} fichiers finaux joints au brouillon après vérification.')


if __name__ == '__main__':
    main()
