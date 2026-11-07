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
TAURI = 'src/frontend/src-tauri'
# tauri-bundler 2.8.1 (tauri-cli 2.10.1, crates/tauri-bundler/src/bundle.rs) écrit
# le type de paquet dans le binaire principal en remplaçant la PREMIÈRE occurrence
# de ce jeton, empaquette, puis restaure dans target/release la copie d'avant
# (« Restore unsigned and unpatched binary »). Le paquet contient donc le binaire
# patché, target/release l'original : relevé sur les paquets 0.82 publiés.
BUNDLE_TOKEN = b'__TAURI_BUNDLE_TYPE_VAR_UNK'
BUNDLE_TYPES = {'deb': b'__TAURI_BUNDLE_TYPE_VAR_DEB', 'appimage': b'__TAURI_BUNDLE_TYPE_VAR_APP',
                'msi': b'__TAURI_BUNDLE_TYPE_VAR_MSI', 'nsis': b'__TAURI_BUNDLE_TYPE_VAR_NSS'}
MAIN_NAMES = {'Linux': ('therese', 'THERESE'), 'Windows': ('therese.exe',)}


def engine_name(platform):
    """Nom du moteur dans l'installeur : Tauri retire le suffixe de cible des externalBin
    (settings.rs, copy_binaries ; msi et nsis idem) : backend-aarch64-apple-darwin
    devient Contents/MacOS/backend, backend-x86_64-pc-windows-msvc.exe devient backend.exe."""
    config = json.loads((ROOT / TAURI / 'tauri.conf.json').read_text(encoding='utf-8'))
    names = [Path(p).name for p in config['bundle']['externalBin']]
    if len(names) != 1:
        raise ValueError('Un unique moteur externalBin est attendu')
    return names[0] + ('.exe' if platform == 'Windows' else '')


def built_digests(root, platform, package):
    """Empreintes admises pour le binaire principal de CE build une fois empaqueté :
    l'original de target/release, ou le même avec le seul jeton de son paquet."""
    digests = set()
    for name in MAIN_NAMES[platform]:
        binary = root / TAURI / 'target/release' / name
        if not binary.is_file():
            continue
        raw = binary.read_bytes()
        digests.add(system.sha(raw))
        index = raw.find(BUNDLE_TOKEN)
        if index >= 0:
            digests.add(system.sha(raw[:index] + BUNDLE_TYPES[package] + raw[index + len(BUNDLE_TOKEN):]))
    return digests


def authenticode_signed(raw):
    """Vrai si l'en-tête PE déclare une table de certificats (répertoire de sécurité)."""
    if len(raw) < 0x40 or raw[:2] != b'MZ':
        raise ValueError('En-tête PE illisible')
    header = int.from_bytes(raw[0x3c:0x40], 'little')
    optional = header + 24
    if raw[header:header + 4] != b'PE\0\0' or len(raw) < optional + 2:
        raise ValueError('En-tête PE illisible')
    magic = int.from_bytes(raw[optional:optional + 2], 'little')
    if magic not in (0x10b, 0x20b):
        raise ValueError('En-tête PE illisible')
    security = optional + (112 if magic == 0x20b else 96) + 4 * 8
    if len(raw) < security + 8:
        raise ValueError('En-tête PE illisible')
    return int.from_bytes(raw[security + 4:security + 8], 'little') != 0


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


def verify_linux_files(actual, manifest, root=ROOT, package='deb'):
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
    # Le seul binaire applicatif autorisé vient du compilateur de ce build, à sa place.
    own = built_digests(root, 'Linux', package)
    result, refusals = {}, []
    for name, digest in actual.items():
        if '/backend-libs/' in name:
            result[name] = expected[name.split('/backend-libs/', 1)[1]]
        elif (digest in own and posixpath.dirname(name) == 'usr/bin'
              and posixpath.basename(name) in MAIN_NAMES['Linux']):
            result[name] = {'sha256': digest, 'origin': 'THERESE/Cargo.lock', 'license': 'licence du dépôt'}
        else:
            row = next((r for r in catalog['libraries'] if r['sha256'] == digest), None)
            if row is None:
                refusals.append('Bibliothèque ajoutée par l’empaqueteur hors inventaire : '
                                + name + ' (SHA-256 ' + digest + ')')
                continue
            path = Path('/') / row.get('binary_member', '')
            try:
                record = system.match_system(path, digest, catalog, 'Linux')
            except ValueError as exc:
                refusals.append(str(exc) + ' (' + name + ')')
                continue
            result[name] = {'sha256': digest, **record}
    # Tout relever avant d'échouer : un seul passage donne la liste complète.
    if refusals:
        raise ValueError('\n'.join(refusals))
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
    records = verify_linux_files(actual, manifest, root, 'deb')
    proof(artifact, records, root)


def is_engine(path, platform, name):
    """Le moteur est à la place où Tauri le dépose, sous son nom sans suffixe de cible."""
    if platform == 'macOS':
        parents = path.parents
        return (path.name == name and len(parents) >= 3 and parents[0].name == 'MacOS'
                and parents[1].name == 'Contents' and parents[2].suffix == '.app')
    # Windows : à côté de l'exécutable principal (racine du NSIS, dossier d'installation du MSI).
    return (path.name.lower() == name.lower()
            and any((path.parent / n).is_file() for n in MAIN_NAMES['Windows']))


def verify_directory(folder, manifest, platform, root=ROOT, package=None):
    check_resources([p.read_bytes() for p in folder.rglob('THIRD_PARTY_LICENSES')],
                    [p.read_bytes() for p in folder.rglob('system-libraries.json')], root)
    if platform == 'Linux':
        return verify_linux_files(system.scan_tree(folder), manifest, root, package or 'appimage')
    name = engine_name(platform)
    files = sorted(p for p in folder.rglob('*') if p.is_file())
    engines = [p for p in files if is_engine(p, platform, name)]
    if not engines:
        raise ValueError('Moteur onefile absent de l’installeur : ' + name)
    if len(engines) > 1:
        raise ValueError('Plusieurs moteurs onefile dans l’installeur : '
                         + ', '.join(p.relative_to(folder).as_posix() for p in engines))
    engine = engines[0]
    actual = system.onefile(engine)
    system.verify_files(actual, manifest['files'])
    records = {engine.relative_to(folder).as_posix() + '!' + n: r for n, r in manifest['files'].items()}
    own = built_digests(root, platform, package) if platform == 'Windows' else set()
    refusals = []
    # Les DLL/dylib en dehors du moteur sont également fermées par défaut.
    for path in files:
        if path == engine:
            continue
        relative = path.relative_to(folder).as_posix()
        with path.open('rb') as f:
            if not system.native(f.read(4)):
                continue
        # macOS : l'exécutable Tauri est re-signé par le bundler ; codesign --verify
        # --deep --strict le contrôle dans l'étape suivante du workflow.
        if platform == 'macOS' and relative.endswith(('/Contents/MacOS/therese', '/Contents/MacOS/THERESE')):
            continue
        if platform == 'Windows' and path.name.lower() in MAIN_NAMES['Windows']:
            raw = path.read_bytes()
            digest = system.sha(raw)
            if digest in own:
                records[relative] = {'sha256': digest, 'origin': 'THERESE/Cargo.lock', 'license': 'licence du dépôt'}
                continue
            # Signé Authenticode : relève de la garde de signature (verify_windows_signing.ps1).
            if authenticode_signed(raw):
                continue
            refusals.append('Exécutable principal non signé et différent de ce build : '
                            + relative + ' (SHA-256 ' + digest + ')')
            continue
        refusals.append('Binaire externe au moteur sans inventaire : ' + relative
                        + ' (SHA-256 ' + system.file_sha(path) + ')')
    # Tout relever avant d'échouer : un seul passage donne la liste complète.
    if refusals:
        raise ValueError('\n'.join(refusals))
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
            proof(artifact, verify_directory(folder, manifest, 'Linux', package='appimage'))
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
            proof(matches[0], verify_directory(folder, manifest, 'Windows', package=name))
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
