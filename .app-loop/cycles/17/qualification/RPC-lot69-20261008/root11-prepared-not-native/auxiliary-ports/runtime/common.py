"""Chemins durables et environnement explicite de la recette jetable C17."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from git_snapshot import from_environment
from datetime import UTC, datetime
from pathlib import Path

OUT = Path(__file__).resolve().parent
REPO = Path('/private/tmp/therese-c17-wrapper-source-kGvU1hdx/source')
FRONT_SOURCE = REPO / "src/frontend"
FRONT = REPO / "src/frontend"
PYTHON = Path('/private/tmp/therese-c17-wrapper-source-kGvU1hdx/source/.venv-conforme/bin/python')
NODE = Path("/Users/synoptia/.nvm/versions/node/v22.19.0/bin/node")
MANIFEST = Path('/private/tmp/therese-c17-wrapper-canary-eff7b4e4f24649dd8628503bc7bfc8b3/runtime/pile-reprise.json')
BASE = "http://127.0.0.1:5173/?port=17593"
BACK = "http://127.0.0.1:17593"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def head() -> str:
    return from_environment(REPO).recheck()


def save(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def manifest() -> dict:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data["repo"] != str(REPO):
        raise RuntimeError("Manifeste appartenant à un autre checkout")
    for key in ("home", "data_dir"):
        if not Path(data[key]).resolve().is_relative_to(Path("/private/tmp")):
            raise RuntimeError(f"{key} sort de /private/tmp")
    return data


def environment(data_dir: Path | str | None = None) -> dict[str, str]:
    data = manifest()
    chosen_data = Path(data_dir or data["data_dir"])
    return {
        "PATH": f"{NODE.parent}:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin",
        "HOME": data["home"], "CFFIXED_USER_HOME": data["home"], "TMPDIR": data["temporary_root"],
        "LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8",
        "PYTHONPATH": f"{OUT}:{REPO}:{REPO / 'src/backend'}",
        "PYTHONUNBUFFERED": "1", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1",
        "THERESE_DATA_DIR": str(chosen_data), "DATA_DIR": str(chosen_data),
        "DB_PATH": str(chosen_data / "therese.db"), "QDRANT_PATH": str(chosen_data / "qdrant"),
        "PORT": "17593", "HOST": "127.0.0.1",
        "PYTHON_KEYRING_BACKEND": "keyring.backends.null.Keyring", "THERESE_DB_PLAINTEXT": "1", "THERESE_SKIP_SERVICES": "1",
        "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
        "THERESE_SONDE_CATALOGUE": "off", "OLLAMA_BASE_URL": "http://127.0.0.1:9",
        "VITE_THERESE_BACKEND_PORT": "17593",
        "PLAYWRIGHT_BROWSERS_PATH": '/private/tmp/therese-c17-wrapper-canary-eff7b4e4f24649dd8628503bc7bfc8b3/auxiliary/playwright-unused',
    }


def new_run(prefix: str) -> Path:
    if prefix != "logs" or os.environ.get("C17_AUX_LOGS_RUN") != '/private/tmp/therese-c17-wrapper-canary-eff7b4e4f24649dd8628503bc7bfc8b3/runtime/calibration/logs-rpc':
        raise RuntimeError("Allocation logs root exacte requise, aucun dossier dynamique")
    path = Path(os.environ["C17_AUX_LOGS_RUN"])
    if path.exists() or path.is_symlink():
        raise RuntimeError("Allocation logs déjà utilisée")
    path.mkdir()
    return path


def immutable_snapshot() -> dict[str, str]:
    return {(str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)): sha(path) for path in (
        REPO / "src/frontend/index.html", Path('/private/tmp/therese-c17-wrapper-canary-eff7b4e4f24649dd8628503bc7bfc8b3/campaign-sentinel.txt'),
        REPO / "tests/couverture/couverture-ecran.mjs",
    ) if path.exists()}


def assert_unchanged(snapshot: dict[str, str]) -> None:
    for name, expected in snapshot.items():
        if not (REPO / name).exists() or sha(REPO / name) != expected:
            raise RuntimeError(f"Source ou verrou modifié pendant la recette : {name}")
