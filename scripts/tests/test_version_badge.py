"""Le badge Shields conserve le canal publié quand on change le numéro."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

DEPOT = Path(__file__).resolve().parents[2]


class TestVersionBadge(unittest.TestCase):
    def test_controle_et_bump_du_badge_independants_du_suffixe(self):
        fichiers = (
            "scripts/bump-version.sh",
            "scripts/check-app-version-sync.py",
            "README.md",
            "pyproject.toml",
            "package.json",
            "src/frontend/package.json",
            "src/frontend/package-lock.json",
            "src/frontend/src-tauri/tauri.conf.json",
            "src/frontend/src-tauri/Cargo.toml",
            "src/frontend/src-tauri/Cargo.lock",
            "src/backend/app/config.py",
            "src/backend/app/__init__.py",
            "uv.lock",
        )
        for suffixe in ("", "--alpha", "--beta", "--beta.1", "--rc--test.2"):
            with self.subTest(suffixe=suffixe):
                copie = Path(tempfile.mkdtemp(prefix="badge-therese-"))
                for fichier in fichiers:
                    destination = copie / fichier
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(DEPOT / fichier, destination)
                readme = copie / "README.md"
                version = json.loads((copie / "package.json").read_text(encoding="utf-8"))["version"]
                readme.write_text(
                    f'<img src="https://img.shields.io/badge/version-{version}{suffixe}-orange" alt="Version" />\n',
                    encoding="utf-8",
                )

                verifier = subprocess.run(
                    [sys.executable, copie / "scripts/check-app-version-sync.py"],
                    cwd=copie, capture_output=True, text=True, check=False,
                )

                # Les lockfiles et l'index sont indépendants du badge. De petits
                # exécutables témoins évitent npm, Cargo et uv pendant ce test.
                binaires = copie / "bin"
                binaires.mkdir()
                (copie / "docs").mkdir()
                (copie / "scripts/index-des-noms.mjs").touch()
                for outil in ("npm", "cargo", "uv", "node"):
                    temoin = binaires / outil
                    temoin.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
                    temoin.chmod(0o700)
                bump = subprocess.run(
                    ["bash", copie / "scripts/bump-version.sh", "7.8.9"], cwd=copie,
                    env={**os.environ, "PATH": f"{binaires}{os.pathsep}{os.environ['PATH']}"},
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(verifier.returncode, 0, verifier.stdout + verifier.stderr)
                self.assertEqual(bump.returncode, 0, bump.stdout + bump.stderr)
                self.assertIn(f"badge/version-7.8.9{suffixe}-orange", readme.read_text(encoding="utf-8"))
                self.assertIn("OK  README.md (badge version)", bump.stdout)
