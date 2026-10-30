#!/usr/bin/env python3
"""Installer exactement la roue CPU dont les notices ont été collectées."""
import json
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def wheel_url(rows, platform, version):
    suffix = {'linux': 'linux', 'win32': 'windows'}[platform]
    matches = [r for r in rows if r['id'] == f'python:torch@{version}/wheel-cpu-{suffix}']
    if len(matches) != 1:
        raise ValueError('Roue CPU absente ou périmée ; actualiser son verrou et les notices')
    row = matches[0]
    return row['artifact'] + '#' + row['integrity'].replace(':', '=', 1)


if __name__ == '__main__':
    if sys.version_info[:2] != (3, 13):
        raise ValueError('Les roues CPU verrouillées ciblent CPython 3.13')
    packages = tomllib.loads((ROOT / 'uv.lock').read_text())['package']
    version = next(p['version'] for p in packages if p['name'] == 'torch')
    rows = json.loads((ROOT / 'licenses/runtime-wheels.lock.json').read_text())
    subprocess.run(['uv', 'pip', 'install', '--reinstall', '--no-deps', wheel_url(rows, sys.platform, version)], check=True, cwd=ROOT)
