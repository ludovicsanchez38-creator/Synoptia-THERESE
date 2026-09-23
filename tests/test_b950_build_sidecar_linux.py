"""B-950 (cycle 11, 23/09/2026) : `make build-sidecar` échouait sous Linux.

`backend.spec` produit sous Linux un dossier onedir (`dist/backend/`, BUG-044),
mais `scripts/build-sidecar.sh` attendait un binaire unique `dist/backend` :
« Binaire non trouvé » et sortie 1 après un build réussi. Le workflow de
release, lui, traitait déjà le onedir (wrapper shell + `backend-libs/`). Preuve :
`.app-loop/cycles/11/reproduce/b950-build-sidecar-onedir.log`.

Le script est exécuté dans un faux projet : PyInstaller et `uname` y sont
simulés, rien n'est construit pour de bon.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "build-sidecar.sh"

pytestmark = pytest.mark.skipif(
    sys.platform == "win32" or shutil.which("bash") is None, reason="script bash"
)


def _faux_projet(tmp_path: Path, systeme: str, machine: str, sortie_onedir: bool) -> tuple[Path, dict]:
    projet = tmp_path / "projet"
    (projet / "scripts").mkdir(parents=True)
    (projet / "src" / "backend").mkdir(parents=True)
    (projet / "src" / "frontend" / "src-tauri").mkdir(parents=True)
    shutil.copy(SCRIPT, projet / "scripts" / "build-sidecar.sh")
    venv_bin = projet / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    if sortie_onedir:
        corps = (
            "mkdir -p dist/backend/_internal\n"
            "printf 'lib' > dist/backend/_internal/libtemoin.so\n"
            "printf '#!/bin/sh\\n' > dist/backend/backend && chmod +x dist/backend/backend\n"
        )
    else:
        corps = "mkdir -p dist && printf '#!/bin/sh\\n' > dist/backend && chmod +x dist/backend\n"
    (venv_bin / "pyinstaller").write_text("#!/usr/bin/env bash\n" + corps, encoding="utf-8")
    (venv_bin / "pyinstaller").chmod(0o755)
    faux = tmp_path / "faux-bin"
    faux.mkdir()
    (faux / "uname").write_text(
        f'#!/usr/bin/env bash\ncase "$1" in -s) echo {systeme} ;; -m) echo {machine} ;; *) echo {systeme} ;; esac\n',
        encoding="utf-8",
    )
    (faux / "uname").chmod(0o755)
    env = {**os.environ, "PATH": f"{faux}{os.pathsep}{os.environ.get('PATH', '')}"}
    return projet, env


def _lancer(projet: Path, env: dict) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(projet / "scripts" / "build-sidecar.sh")],
        capture_output=True, text=True, env=env, timeout=60,
    )


def test_sous_linux_le_onedir_devient_un_wrapper_et_ses_bibliotheques(tmp_path: Path):
    projet, env = _faux_projet(tmp_path, "Linux", "x86_64", sortie_onedir=True)
    r = _lancer(projet, env)
    assert r.returncode == 0, r.stdout + r.stderr
    binaires = projet / "src" / "frontend" / "src-tauri" / "binaries"
    wrapper = binaires / "backend-x86_64-unknown-linux-gnu"
    assert wrapper.is_file() and os.access(wrapper, os.X_OK)
    assert "backend-libs" in wrapper.read_text(encoding="utf-8")
    assert (binaires / "backend-libs" / "backend").is_file()
    assert (binaires / "backend-libs" / "_internal" / "libtemoin.so").is_file()


def test_sous_macos_le_onefile_est_copie_comme_avant(tmp_path: Path):
    projet, env = _faux_projet(tmp_path, "Darwin", "arm64", sortie_onedir=False)
    r = _lancer(projet, env)
    assert r.returncode == 0, r.stdout + r.stderr
    binaire = projet / "src" / "frontend" / "src-tauri" / "binaries" / "backend-aarch64-apple-darwin"
    assert binaire.is_file() and os.access(binaire, os.X_OK)
    assert not (binaire.parent / "backend-libs").exists()
