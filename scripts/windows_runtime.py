#!/usr/bin/env python3
"""Runtime VC++ du moteur Windows : une source officielle, jamais le hasard du PATH.

Relevé à blanc du 06/11/2026 : PyInstaller résolvait msvcp140.dll dans le
dossier du JDK du runner (dont la version a changé d'une heure à l'autre) et
msvcp140_1.dll et vcomp140.dll dans celui d'ImageMagick. ctranslate2,
onnxruntime et scikit-learn en ont besoin : il faut les livrer, mais depuis le
dossier de redistribution de Visual Studio (« Distributable Code »), et
refuser le build si une autre source s'impose.
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path, PureWindowsPath

VC_RUNTIME = re.compile(r'(?:msvcp140(?:_\d+|_atomic_wait|_codecvt_ids)?|vcruntime140(?:_\d+)?|vcomp140|concrt140)\.dll',
                        re.I)
VSWHERE = Path(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)')) / 'Microsoft Visual Studio/Installer/vswhere.exe'


def _version(name):
    return tuple(int(part) for part in name.split('.'))


def redist_dirs(vswhere=VSWHERE, run=subprocess.run):
    """Dossiers CRT et OpenMP x64 de la dernière version MSVC installée."""
    if not Path(vswhere).is_file():
        raise ValueError('Visual Studio introuvable (vswhere) : runtime VC++ sans source officielle')
    found = run([str(vswhere), '-latest', '-products', '*', '-property', 'installationPath'],
                capture_output=True, text=True, check=True).stdout.strip()
    base = Path(found) / 'VC/Redist/MSVC'
    versions = sorted((p for p in base.iterdir() if p.is_dir() and re.fullmatch(r'\d+(?:\.\d+)+', p.name)),
                      key=lambda p: _version(p.name)) if base.is_dir() else []
    if not versions:
        raise ValueError('Redistribuable VC++ absent de Visual Studio : ' + str(base))
    x64 = versions[-1] / 'x64'
    dirs = sorted(x64.glob('Microsoft.VC14*.CRT')) + sorted(x64.glob('Microsoft.VC14*.OpenMP'))
    if not dirs:
        raise ValueError('Dossiers CRT/OpenMP absents : ' + str(x64))
    return dirs


def _within(path, root):
    parts = [p.lower() for p in PureWindowsPath(str(path).replace('/', '\\')).parts]
    base = [p.lower() for p in PureWindowsPath(str(root).replace('/', '\\')).parts]
    return parts[:len(base)] == base


def check_sources(binaries, allowed_roots):
    """Refuser un runtime VC++ de premier niveau venu d'ailleurs que des racines permises.

    Les copies rangées dans le dossier d'une roue (sklearn/.libs…) relèvent du
    RECORD de la roue et de son inventaire : elles ne sont pas visées ici.
    """
    refused = []
    for name, source, _kind in binaries:
        if '/' in name.replace('\\', '/') or not VC_RUNTIME.fullmatch(name):
            continue
        if not any(_within(source, root) for root in allowed_roots):
            refused.append(f'{name} ← {source}')
    if refused:
        raise ValueError('Runtime VC++ hors source officielle :\n' + '\n'.join(refused))
