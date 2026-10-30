#!/usr/bin/env python3
"""Contrôler notices, provenance et octets de chaque installeur avant publication."""
import argparse
import hashlib
import json
import plistlib
import posixpath
import subprocess
import sys
import tarfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import system_libraries as system

ROOT = Path(__file__).resolve().parents[1]


def check_directory(directory, expected):
    notices = list(directory.rglob('THIRD_PARTY_LICENSES'))
    if not notices or any(p.read_bytes() != expected for p in notices):
        raise ValueError('Notice embarquée absente ou différente du fichier versionné')
    return len(notices)


def command(args):
    result = subprocess.run(args, capture_output=True)
    if result.returncode not in (0, 3010):
        raise RuntimeError(f'Inspection de l’installeur impossible : {args[0]} (code {result.returncode})')
    return result.stdout


def scan_tar(archive):
    """Lire le tar Debian sans extraire ni exécuter, résoudre tous les liens."""
    files, links, notices, inventories = {}, {}, [], []
    seen = set()
    for member in archive:
        name = posixpath.normpath(member.name).removeprefix('./')
        if name.startswith('/') or '..' in Path(name).parts or name in seen:
            raise ValueError('Chemin Debian invalide/dupliqué')
        seen.add(name)
        if member.isfile():
            stream = archive.extractfile(member)
            head = stream.read(4)
            digest = hashlib.sha256(head)
            text = bytearray(head) if Path(name).name in ('THIRD_PARTY_LICENSES', 'system-libraries.json') else None
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
                if text is not None:
                    text.extend(chunk)
            files[name] = (digest.hexdigest(), system.native(head))
            if Path(name).name == 'THIRD_PARTY_LICENSES':
                notices.append(bytes(text))
            if Path(name).name == 'system-libraries.json':
                inventories.append(bytes(text))
        elif member.issym() or member.islnk():
            target = member.linkname if member.islnk() else posixpath.join(posixpath.dirname(name), member.linkname)
            target = posixpath.normpath(target).removeprefix('./')
            if target.startswith('/') or '..' in Path(target).parts:
                raise ValueError('Lien Debian hors paquet')
            links[name] = target
    for name in links:
        target, visited = name, set()
        while target in links:
            if target in visited:
                raise ValueError('Cycle de liens Debian')
            visited.add(target)
            target = links[target]
        if target in files:
            files[name] = files[target]
        elif '/backend-libs/' in name or '.so' in Path(name).name:
            raise ValueError('Lien natif sans cible dans le paquet : ' + name)
    return {n: h for n, (h, is_native) in files.items() if is_native}, notices, inventories


def verify_linux_files(actual, manifest, root=ROOT):
    expected = manifest['files']
    embedded = {name.split('/backend-libs/', 1)[1]: digest for name, digest in actual.items()
                if '/backend-libs/' in name}
    # Plusieurs copies doivent toutes correspondre, sans écrasement silencieux.
    for name, digest in actual.items():
        if '/backend-libs/' in name:
            key = name.split('/backend-libs/', 1)[1]
            if key not in expected or digest != expected[key]['sha256']:
                raise ValueError('Bibliothèque absente de l’inventaire ou modifiée : ' + name)
    system.verify_files(embedded, expected)
    catalog = system.load_catalog(root)
    for record in expected.values():
        system.cpython_components.verify_record(record, 'Linux', catalog['cpython'])
    # Le seul binaire applicatif autorisé vient du compilateur de ce build.
    target = root / 'src/frontend/src-tauri/target/release'
    own = {system.file_sha(p) for p in (target / 'therese', target / 'THERESE') if p.is_file()}
    result = {}
    for name, digest in actual.items():
        if '/backend-libs/' in name:
            result[name] = expected[name.split('/backend-libs/', 1)[1]]
        elif digest in own and Path(name).name in ('therese', 'THERESE'):
            result[name] = {'sha256': digest, 'origin': 'THERESE/Cargo.lock', 'license': 'licence du dépôt'}
        else:
            row = next((r for r in catalog['libraries'] if r['sha256'] == digest), None)
            if row is None:
                raise ValueError('Bibliothèque ajoutée par l’empaqueteur hors inventaire : ' + name)
            path = Path('/') / row.get('binary_member', '')
            record = system.match_system(path, digest, catalog, 'Linux')
            result[name] = {'sha256': digest, **record}
    return result


def check_resources(notices, inventories, root=ROOT):
    expected = (root / 'THIRD_PARTY_LICENSES').read_bytes()
    if not notices or any(n != expected for n in notices):
        raise ValueError('Notice de l’installeur absente ou périmée')
    expected_inventory = (root / system.BUILD).read_bytes()
    if not inventories or any(n != expected_inventory for n in inventories):
        raise ValueError('Inventaire de l’installeur absent ou périmé')


def proof(artifact, records, root=ROOT):
    folder = root / '.work-release/installer-proofs'
    folder.mkdir(parents=True, exist_ok=True)
    data = {'schema': 1, 'artifact': artifact.name, 'artifact_sha256': system.file_sha(artifact),
            'build_inventory_sha256': system.file_sha(root / system.BUILD), 'files': records}
    (folder / (artifact.name + '.json')).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{artifact.name} : {len(records)} fichiers natifs rapprochés, notices et inventaire identiques.')


def verify_deb(artifact, manifest, root=ROOT):
    process = subprocess.Popen(['dpkg-deb', '--fsys-tarfile', str(artifact)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        with tarfile.open(fileobj=process.stdout, mode='r|*') as archive:
            actual, notices, inventories = scan_tar(archive)
    except Exception:
        process.kill()
        process.wait()
        raise
    finally:
        process.stdout.close()
    if process.wait():
        raise ValueError('Extraction Debian en échec')
    check_resources(notices, inventories, root)
    records = verify_linux_files(actual, manifest, root)
    proof(artifact, records, root)


def verify_directory(folder, manifest, platform, root=ROOT):
    check_resources([p.read_bytes() for p in folder.rglob('THIRD_PARTY_LICENSES')],
                    [p.read_bytes() for p in folder.rglob('system-libraries.json')], root)
    if platform == 'Linux':
        return verify_linux_files(system.scan_tree(folder), manifest, root)
    engines = [p for p in folder.rglob('backend-*') if p.is_file() and p.suffix != '.sig']
    if not engines:
        raise ValueError('Moteur onefile absent de l’installeur')
    records = {}
    for engine in engines:
        actual = system.onefile(engine)
        system.verify_files(actual, manifest['files'])
        for name, record in manifest['files'].items():
            records[engine.relative_to(folder).as_posix() + '!' + name] = record
    # Les DLL/dylib en dehors du moteur sont également fermées par défaut.
    for path in folder.rglob('*'):
        if not path.is_file() or path in engines:
            continue
        # L'exécutable Tauri est contrôlé par la garde de signature de plateforme.
        relative = path.relative_to(folder).as_posix()
        if ((platform == 'macOS' and relative.endswith(('/Contents/MacOS/therese', '/Contents/MacOS/THERESE')))
                or (platform == 'Windows' and path.name.lower() == 'therese.exe')):
            continue
        with path.open('rb') as f:
            if system.native(f.read(4)):
                raise ValueError('Binaire externe au moteur sans inventaire : ' + relative)
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform', required=True, choices=['macOS', 'Windows', 'Linux'])
    args = parser.parse_args()
    manifest = system.load_build(ROOT)
    if manifest['platform'] != args.platform:
        raise ValueError('Plateforme de l’inventaire incorrecte')
    bundle = ROOT / 'src/frontend/src-tauri/target/release/bundle'
    destination = ROOT / '.work-release/installer-inspection'
    destination.mkdir(parents=True, exist_ok=True)
    if args.platform == 'Linux':
        packages = list(bundle.glob('deb/*.deb'))
        if len(packages) != 1:
            raise ValueError('Un unique paquet Debian est requis')
        verify_deb(packages[0], manifest)
        images = sorted(bundle.glob('appimage/*.AppImage'))
        for index, artifact in enumerate(images):
            offset = command([str(artifact), '--appimage-offset']).decode().strip()
            if not offset.isdigit():
                raise ValueError('Offset AppImage invalide')
            folder = destination / f'appimage-{index}'
            command(['unsquashfs', '-o', offset, '-d', str(folder), str(artifact)])
            proof(artifact, verify_directory(folder, manifest, 'Linux'))
        print(f'AppImage : {len(images)} produite(s) et contrôlée(s).')
    elif args.platform == 'Windows':
        for pattern, name in [('msi/*.msi', 'msi'), ('nsis/*.exe', 'nsis')]:
            matches = list(bundle.glob(pattern))
            if len(matches) != 1:
                raise ValueError('Un unique installeur est requis : ' + pattern)
            folder = destination / name
            folder.mkdir(parents=True, exist_ok=False)
            if name == 'msi':
                command(['msiexec', '/a', str(matches[0]), '/qn', 'TARGETDIR=' + str(folder)])
            else:
                command(['7z', 'x', '-y', str(matches[0]), '-o' + str(folder)])
            proof(matches[0], verify_directory(folder, manifest, 'Windows'))
    else:
        archives, images = list(bundle.glob('macos/*.app.tar.gz')), list(bundle.glob('dmg/*.dmg'))
        if len(archives) != 1 or len(images) != 1:
            raise ValueError('Un unique DMG et une archive updater sont requis')
        folder = destination / 'updater-macos'
        with tarfile.open(archives[0]) as archive:
            archive.extractall(folder, filter='data')
        proof(archives[0], verify_directory(folder, manifest, 'macOS'))
        mounted = plistlib.loads(command(['hdiutil', 'attach', '-readonly', '-nobrowse', '-plist', str(images[0])]))
        mounts = [Path(e['mount-point']) for e in mounted['system-entities'] if 'mount-point' in e]
        try:
            if len(mounts) != 1:
                raise ValueError('Montage DMG ambigu')
            proof(images[0], verify_directory(mounts[0], manifest, 'macOS'))
        finally:
            for mount in mounts:
                command(['hdiutil', 'detach', str(mount)])


if __name__ == '__main__':
    main()
