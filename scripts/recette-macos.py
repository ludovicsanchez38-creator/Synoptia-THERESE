#!/usr/bin/env python3
"""Recette du sidecar final macOS, après signature du bundle Tauri.

Le contrôle statique du sceau ne charge pas le Python embarqué en onefile.
Cette recette démarre exactement Contents/MacOS/backend, sous HOME/profil/cache
neufs, sans secrets ni modèle téléchargé, et interroge seulement sa santé.
Le groupe de processus créé pour ce lancement est le seul groupe arrêté.
Les preuves sont conservées ; ce contrôle ne qualifie pas le premier lancement GUI.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import plistlib
import re
import signal
import socket
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import ProxyHandler, build_opener


def sha256(path: Path) -> str:
    """Empreinte en flux du sidecar, potentiellement volumineux."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def membres_groupe(pgid: int) -> list[int]:
    """Un groupe dans la session neuve contient seulement nos descendants."""
    result = subprocess.run(
        ["/bin/ps", "-axo", "pid=,pgid="],
        check=True, capture_output=True, text=True,
    )
    return [int(pid) for pid, group in (line.split() for line in result.stdout.splitlines())
            if int(group) == pgid]


def signature(path: Path, output: Path, name: str) -> dict:
    """Lire les protections effectivement signées, sans re-signer l'artefact."""
    flags = subprocess.run(["/usr/bin/codesign", "-d", "--verbose=4", str(path)],
                           capture_output=True, text=True)
    entitlement = subprocess.run(
        ["/usr/bin/codesign", "-d", "--entitlements", ":-", str(path)],
        capture_output=True,
    )
    flags_path = output / f"{name}-signature.log"
    flags_path.write_text(flags.stdout + flags.stderr)
    plist_path = output / f"{name}-entitlements.plist"
    plist_path.write_bytes(entitlement.stdout)
    errors = output / f"{name}-entitlements.stderr.log"
    errors.write_bytes(entitlement.stderr)
    try:
        entitlements = plistlib.loads(entitlement.stdout)
    except (ValueError, plistlib.InvalidFileException):
        entitlements = None
    return {
        "path": str(path), "display_exit_code": flags.returncode,
        "entitlements_exit_code": entitlement.returncode,
        "hardened_runtime": bool(re.search(r"flags=.*\(.*runtime.*\)", flags.stdout + flags.stderr)),
        "ad_hoc": "Signature=adhoc" in flags.stdout + flags.stderr,
        "entitlements": entitlements,
        "proofs": [{"path": str(p), "sha256": sha256(p)}
                   for p in (flags_path, plist_path, errors)],
    }


def main() -> int:
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app", type=Path)
    parser.add_argument("version")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    if sys.platform != "darwin":
        parser.error("cette recette exige macOS")
    if not 1 <= args.timeout <= 300:
        parser.error("timeout attendu entre 1 et 300 secondes")

    app = args.app.resolve(strict=True)
    backend = app / "Contents/MacOS/backend"
    with (app / "Contents/Info.plist").open("rb") as stream:
        gui = app / "Contents/MacOS" / plistlib.load(stream)["CFBundleExecutable"]
    seal = app / "Contents/_CodeSignature/CodeResources"
    if not backend.is_file() or not os.access(backend, os.X_OK) or not seal.is_file():
        parser.error("bundle signé et sidecar exécutable requis")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    profile = Path(tempfile.mkdtemp(prefix="therese-recette-macos-", dir="/private/tmp"))
    for name in ("home", "data", "tmp", "hf", "cache", "torch"):
        (profile / name).mkdir()
    env = {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": str(profile / "home"),
        "THERESE_DATA_DIR": str(profile / "data"),
        "TMPDIR": str(profile / "tmp"),
        "TEMP": str(profile / "tmp"),
        "TMP": str(profile / "tmp"),
        "LANG": "en_US.UTF-8",
        "PYTHON_KEYRING_BACKEND": "keyring.backends.null.Keyring",
        # Clé synthétique propre au profil jetable, aucun accès au trousseau.
        "THERESE_DB_KEY": "a" * 64,
        "HF_HOME": str(profile / "hf"),
        "HF_HUB_CACHE": str(profile / "hf/hub"),
        "HF_MODULES_CACHE": str(profile / "hf/modules"),
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "XDG_CACHE_HOME": str(profile / "cache"),
        "TORCH_HOME": str(profile / "torch"),
        "OLLAMA_BASE_URL": "http://127.0.0.1:9",
        "THERESE_ENV": "production",
    }
    # Ne jamais joindre l'API usuelle 17293 ni emprunter un listener existant.
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    if port in (17293, 17393, 1420):
        raise RuntimeError("port réservé choisi par le système")

    # Confinement du lancement de contrôle, sans altérer les signatures ni le GUI.
    # Le nettoyeur de zombies du produit ne peut pas signaler un autre processus.
    sandbox = output / "profil.sb"
    sandbox.write_text(f'''(version 1)
(allow default)
(deny network*)
(allow network-bind (local ip "localhost:{port}"))
(allow network-inbound (local ip "localhost:{port}"))
(allow network-outbound (remote ip "localhost:{port}"))
(deny signal)
(allow signal (target self))
(allow signal (target children))
(deny appleevent-send)
(deny job-creation)
''')
    command = ["/usr/bin/sandbox-exec", "-f", str(sandbox), str(backend),
               "--host", "127.0.0.1", "--port", str(port)]
    receipt = {
        "status": "failed", "started_at": datetime.now(timezone.utc).isoformat(),
        "app": str(app), "expected_version": args.version,
        "command": command, "environment": env, "profile": str(profile),
        "services_skipped": False, "embedding_cache_initially_empty": True,
        "backend_sha256_before": sha256(backend), "seal_sha256_before": sha256(seal),
        "gui_sha256_before": sha256(gui),
        "script_sha256_before": sha256(Path(__file__)),
        "signatures": [signature(backend, output, "backend"), signature(gui, output, "gui")],
        "checks": [], "http": [], "listener_observations": [], "limits": [
            "Pas de lancement GUI, de notarisation ni de qualification updater.",
            "Modèles absents et hors ligne : embedding dégradé admis ; DB et Qdrant requis.",
        ],
    }
    proc = None
    opener = build_opener(ProxyHandler({}))
    log = output / "backend.log"
    log.touch()
    try:
        other = subprocess.run(
            ["/usr/bin/pgrep", "-f", r"backend.*--host.*127\.0\.0\.1"],
            capture_output=True, text=True,
        )
        receipt["backend_preflight"] = {"exit_code": other.returncode, "matching_pids": other.stdout.split()}
        if other.returncode != 1:
            raise RuntimeError("autre backend présent, ou préflight pgrep impossible")
        with log.open("wb") as stream:
            proc = subprocess.Popen(command, cwd=profile, env=env, stdout=stream,
                                    stderr=subprocess.STDOUT, start_new_session=True)
            receipt["owned_process_group"] = proc.pid
            deadline = time.monotonic() + args.timeout
            health = None
            while time.monotonic() < deadline:
                if proc.poll() is not None:
                    raise RuntimeError(f"sidecar terminé avant /health, exit {proc.returncode}")
                # Attribuer le listener AVANT de contacter le port éphémère.
                listeners = subprocess.run(
                    ["/usr/sbin/lsof", "-nP", "-a", f"-iTCP@127.0.0.1:{port}", "-sTCP:LISTEN", "-Fp"],
                    capture_output=True, text=True,
                )
                pids = {int(line[1:]) for line in listeners.stdout.splitlines() if line.startswith("p")}
                owned = set(membres_groupe(proc.pid))
                receipt["listener_observations"].append({
                    "exit_code": listeners.returncode, "listener_pids": sorted(pids),
                    "owned_group_members": sorted(owned),
                })
                if listeners.returncode not in (0, 1) or (pids and not pids <= owned):
                    raise RuntimeError("listener inconnu ou attribution impossible, aucun HTTP autorisé")
                if not pids:
                    time.sleep(0.5)
                    continue
                try:
                    with opener.open(f"http://127.0.0.1:{port}/health", timeout=2) as response:
                        health = json.load(response)
                    break
                except (OSError, ValueError):
                    time.sleep(0.5)
            if health is None:
                raise TimeoutError("aucune réponse /health avant le délai")
            receipt["listener_pids"] = sorted(pids)
            receipt["http"].append({"path": "/health", "response": health})
            if health.get("version") != args.version:
                raise RuntimeError(f"version inattendue : {health.get('version')}")
            if health.get("status") not in ("healthy", "degraded"):
                raise RuntimeError("état de santé invalide")
            with opener.open(f"http://127.0.0.1:{port}/health/services", timeout=5) as response:
                services = json.load(response)
            receipt["http"].append({"path": "/health/services", "response": services})
            for name in ("database", "qdrant"):
                if services.get("services", {}).get(name, {}).get("available") is not True:
                    raise RuntimeError(f"service {name} indisponible")
            for metadata in receipt["signatures"]:
                if (metadata["display_exit_code"] != 0 or metadata["entitlements_exit_code"] != 0
                        or not metadata["hardened_runtime"] or not metadata["ad_hoc"]
                        or metadata["entitlements"] != {"com.apple.security.cs.disable-library-validation": True}):
                    raise RuntimeError(f"signature effective hors contrat : {metadata['path']}")
            receipt["checks"] = ["listener possédé", "version exacte", "DB disponible", "Qdrant disponible",
                                 "hardened runtime sidecar et GUI", "unique exception library-validation"]
            receipt["status"] = "passed"
    except Exception as exc:
        receipt["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        if proc is not None:
            receipt["exit_before_cleanup"] = proc.poll()
            receipt["cleanup_members_before"] = membres_groupe(proc.pid)
            # Nouveau groupe créé par setsid(), différent de celui du contrôleur.
            if receipt["cleanup_members_before"]:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(proc.pid, signal.SIGTERM)
            limit = time.monotonic() + 10
            while time.monotonic() < limit and membres_groupe(proc.pid):
                proc.poll()
                time.sleep(0.1)
            if membres_groupe(proc.pid):
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(proc.pid, signal.SIGKILL)
            proc.wait(timeout=10)
            receipt["cleanup_members_after"] = membres_groupe(proc.pid)
            if receipt["cleanup_members_after"]:
                receipt["status"] = "failed"
                receipt["cleanup_error"] = "descendants encore présents"
        receipt["backend_sha256_after"] = sha256(backend)
        receipt["seal_sha256_after"] = sha256(seal)
        receipt["gui_sha256_after"] = sha256(gui)
        receipt["script_sha256_after"] = sha256(Path(__file__))
        receipt["artifact_unchanged"] = (
            receipt["backend_sha256_before"] == receipt["backend_sha256_after"]
            and receipt["seal_sha256_before"] == receipt["seal_sha256_after"]
            and receipt["gui_sha256_before"] == receipt["gui_sha256_after"]
            and receipt["script_sha256_before"] == receipt["script_sha256_after"]
        )
        if not receipt["artifact_unchanged"]:
            receipt["status"] = "failed"
        receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
        receipt["backend_log"] = {"path": str(log), "sha256": sha256(log)}
        receipt["sandbox_profile"] = {"path": str(sandbox), "sha256": sha256(sandbox)}
        receipt_path = output / "receipt.json"
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"status": receipt["status"], "receipt": str(receipt_path),
                          "sha256": sha256(receipt_path)}, ensure_ascii=False))
    return 0 if receipt["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
