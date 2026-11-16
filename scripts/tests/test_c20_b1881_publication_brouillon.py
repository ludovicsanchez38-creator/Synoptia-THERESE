"""B-1881 : exécuter le script avec une release publique et des appels fictifs."""

import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_une_release_publique_ne_recoit_aucun_upload(monkeypatch):
    spec = importlib.util.spec_from_file_location("publication_c20", ROOT / "scripts/publish_release_artifacts.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(sys, "argv", ["publish_release_artifacts.py", "bundle-factice", "--platform", "macOS"])
    monkeypatch.setenv("RELEASE_TAG", "v0.83.0-alpha")
    monkeypatch.setenv("TAURI_SIGNING_PRIVATE_KEY", "cle-factice")
    monkeypatch.setattr(module, "artifacts", lambda *_: [Path("factice.dmg")])
    monkeypatch.setattr(module, "verified_proofs", lambda *_: [Path("preuve-factice.json")])
    monkeypatch.setattr(module.shutil, "which", lambda _: "/virtuel/node")
    appels = []

    def fausse_commande(commande, **_options):
        appels.append(commande)
        if commande[:3] == ["gh", "release", "view"]:
            return subprocess.CompletedProcess(commande, 0, stdout='{"isDraft": false}')
        if commande[:3] == ["gh", "release", "upload"]:
            return subprocess.CompletedProcess(commande, 0)
        raise AssertionError(f"Commande inattendue, non exécutée : {commande}")

    monkeypatch.setattr(module.subprocess, "run", fausse_commande)
    try:
        module.main()
    except (RuntimeError, ValueError, subprocess.CalledProcessError, SystemExit):
        pass  # Refuser la release est le comportement attendu.
    assert any(c[:3] == ["gh", "release", "view"] for c in appels)
    uploads = [c for c in appels if c[:3] == ["gh", "release", "upload"]]
    assert not uploads, f"release publique : upload effectué malgré isDraft=false : {uploads}"
