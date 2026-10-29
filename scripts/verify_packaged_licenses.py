#!/usr/bin/env python3
"""Vérifier le texte réellement embarqué, octet pour octet, avant publication."""
import argparse
import subprocess
import tarfile
from pathlib import Path

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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform', required=True, choices=['macOS', 'Windows', 'Linux'])
    args = parser.parse_args()
    expected = (ROOT / 'THIRD_PARTY_LICENSES').read_bytes()
    bundle = ROOT / 'src/frontend/src-tauri/target/release/bundle'
    if args.platform == 'macOS':
        count = check_directory(bundle / 'macos', expected)
        print(f'{count} notice(s) vérifiée(s) dans le bundle macOS.')
    elif args.platform == 'Windows':
        destination = ROOT / '.work-release/installer-inspection'
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
            count = check_directory(folder, expected)
            print(f'{count} notice(s) vérifiée(s) dans {name}.')
    else:
        packages = list(bundle.glob('deb/*.deb'))
        if len(packages) != 1:
            raise ValueError('Un unique paquet Debian est requis')
        process = subprocess.Popen(['dpkg-deb', '--fsys-tarfile', str(packages[0])], stdout=subprocess.PIPE)
        count = 0
        with tarfile.open(fileobj=process.stdout, mode='r|*') as archive:
            for member in archive:
                if Path(member.name).name == 'THIRD_PARTY_LICENSES' and member.isfile():
                    if archive.extractfile(member).read() != expected:
                        raise ValueError('Notice Debian périmée')
                    count += 1
        if process.wait() or not count:
            raise ValueError('Notice Debian absente ou extraction en échec')
        print(f'{count} notice(s) vérifiée(s) dans le paquet Debian.')


if __name__ == '__main__':
    main()
