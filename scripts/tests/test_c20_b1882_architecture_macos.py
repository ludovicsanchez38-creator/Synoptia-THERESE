"""B-1882 : une archive contenant un Mach-O x86 ne doit pas devenir aarch64."""

import builtins
import importlib.util
import io
import struct
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_archive_x64_refusee_avant_renommage_et_publication(monkeypatch):
    spec = importlib.util.spec_from_file_location("publication_arch_c20", ROOT / "scripts/publish_release_artifacts.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    archive = Path("THERESE.app.tar.gz")
    preuve = Path("THERESE.app.tar.gz.json")
    # En-tête Mach-O 64 bits, CPU_TYPE_X86_64, rangé dans un tar.gz en mémoire.
    macho = struct.pack("<IiiIIIII", 0xFEEDFACF, 0x01000007, 3, 2, 0, 0, 0, 0)
    flux = io.BytesIO()
    with tarfile.open(fileobj=flux, mode="w:gz") as tar:
        entree = tarfile.TarInfo("THERESE.app/Contents/MacOS/therese")
        entree.size = len(macho)
        tar.addfile(entree, io.BytesIO(macho))
    fichiers = {archive: flux.getvalue()}
    monkeypatch.setattr(sys, "argv", ["publish_release_artifacts.py", "bundle-factice", "--platform", "macOS"])
    monkeypatch.setenv("RELEASE_TAG", "v0.83.0-alpha")
    monkeypatch.setenv("TAURI_SIGNING_PRIVATE_KEY", "cle-factice")
    monkeypatch.setattr(module, "artifacts", lambda *_: [archive])
    monkeypatch.setattr(module, "verified_proofs", lambda paths: [preuve] if paths == [archive] else [])
    monkeypatch.setattr(module.shutil, "which", lambda _: "/virtuel/node")
    copies = []
    def copier(src, dst):
        copies.append((src, dst))
        fichiers[dst] = fichiers[src]
    monkeypatch.setattr(module.shutil, "copyfile", copier)
    ancien_is_file = Path.is_file
    ancien_read_text = Path.read_text
    ancien_read_bytes = Path.read_bytes
    ancien_open = builtins.open
    monkeypatch.setattr(Path, "is_file", lambda p: True if p in fichiers or p.name.endswith(".sig") else ancien_is_file(p))
    monkeypatch.setattr(Path, "read_text", lambda p, *a, **kw: "signature-factice" if p.name.endswith(".sig") else ancien_read_text(p, *a, **kw))
    monkeypatch.setattr(Path, "read_bytes", lambda p: fichiers[p] if p in fichiers else ancien_read_bytes(p))
    monkeypatch.setattr(builtins, "open", lambda p, *a, **kw: io.BytesIO(fichiers[Path(p)]) if isinstance(p, (str, Path)) and Path(p) in fichiers else ancien_open(p, *a, **kw))
    appels = []

    def fausse_commande(commande, **_options):
        appels.append(commande)
        return subprocess.CompletedProcess(commande, 0, stdout='{"isDraft": true}')

    monkeypatch.setattr(module.subprocess, "run", fausse_commande)
    try:
        module.main()
    except (RuntimeError, ValueError, subprocess.CalledProcessError, SystemExit):
        pass
    uploads = [c for c in appels if c[:3] == ["gh", "release", "upload"]]
    assert not uploads, f"archive x86_64 publiée sous aarch64 : {uploads}"
