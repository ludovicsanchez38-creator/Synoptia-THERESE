#!/usr/bin/env python3
"""Relever, sans rien publier, les octets natifs qu'un runner embarque.

Lit la provenance enregistrée par le spec PyInstaller (avant strip et
signature) et copie dans un dossier d'artefact chaque fichier natif qu'aucune
roue Python installée ne revendique dans son RECORD : ce sont eux, CPython et
bibliothèques du système, que les catalogues doivent recenser à l'octet. Les
fichiers des roues ne sont que listés (leur attribution passe par
`licenses/inventory.json`). Rien n'est interprété ici : la revue se fait hors
du runner, sur les octets copiés.
"""
from __future__ import annotations

import argparse
import json
import platform
import shutil
import sys
import sysconfig
from pathlib import Path

import system_libraries

ROOT = Path(__file__).resolve().parents[1]
DRAFTS = ['pyinstaller-origins.json', 'system-libraries-unreviewed.json', 'system-libraries.json']


def _relative_to_python(path: Path) -> str | None:
    for base in {Path(sys.base_prefix).resolve(), Path(sysconfig.get_path('stdlib')).resolve().parent}:
        if path.is_relative_to(base):
            return path.relative_to(base).as_posix()
    return None


def survey(origins: dict, installed: dict, output: Path) -> dict:
    """Copier les natifs hors RECORD ; lister les autres. Rend le relevé."""
    files = output / 'fichiers'
    rows = []
    for name, source in sorted(origins.items()):
        path = Path(source['path'])
        row = {'name': name, 'path': str(path), 'sha256': source['sha256'],
               'size': path.stat().st_size, 'python_relative': _relative_to_python(path.resolve())}
        owner = installed.get(path.resolve())
        if owner:
            row['record'] = {'distribution': owner[0], 'version': owner[1], 'sha256': owner[2]}
        else:
            if system_libraries.file_sha(path) != source['sha256']:
                raise ValueError('Origine modifiée depuis Analysis : ' + name)
            target = files / source['sha256'] / path.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            row['copie'] = target.relative_to(output).as_posix()
        rows.append(row)
    return {'files': rows, 'hors_record': sum('copie' in r for r in rows)}


def python_notices(output: Path) -> list[str]:
    """Copier les textes de licence livrés avec la distribution Python du runner."""
    base = Path(sys.base_prefix).resolve()
    found = []
    candidates = [*base.glob('LICENSE*'), *base.glob('lib/python3.*/LICENSE*'),
                  *base.glob('Lib/LICENSE*'), *base.glob('share/doc/**/LICENSE*')]
    for path in sorted(set(candidates)):
        if path.is_file():
            target = output / 'notices-python' / path.relative_to(base)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            found.append(path.relative_to(base).as_posix())
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    work = ROOT / '.work-release'
    for name in DRAFTS:
        if (work / name).is_file():
            shutil.copy2(work / name, output / name)
    origins = json.loads((work / 'pyinstaller-origins.json').read_text(encoding='utf-8'))
    report = survey(origins, system_libraries.distribution_files(), output)
    report['environnement'] = {
        'python': sys.version, 'implementation': platform.python_implementation(),
        'version': platform.python_version(), 'base_prefix': str(Path(sys.base_prefix).resolve()),
        'executable': sys.executable, 'platform': platform.platform(), 'machine': platform.machine(),
        'sysconfig_platform': sysconfig.get_platform(),
    }
    report['notices_python'] = python_notices(output)
    (output / 'releve.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n',
                                        encoding='utf-8')
    print(f'{len(report["files"])} natifs relevés ; {report["hors_record"]} copiés hors RECORD ; '
          f'{len(report["notices_python"])} notices Python')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
