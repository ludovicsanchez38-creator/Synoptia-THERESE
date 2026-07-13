#!/usr/bin/env python3
"""Vérifie que toutes les sources de version THÉRÈSE sont synchronisées."""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_toml(relative_path: str) -> dict[str, object]:
    with (ROOT / relative_path).open("rb") as file_handle:
        return tomllib.load(file_handle)


def read_json(relative_path: str) -> dict[str, object]:
    with (ROOT / relative_path).open(encoding="utf-8") as file_handle:
        return json.load(file_handle)


def extract_python_version(relative_path: str, pattern: str) -> str:
    content = (ROOT / relative_path).read_text(encoding="utf-8")
    match = re.search(pattern, content)
    if not match:
        raise ValueError(f"version introuvable dans {relative_path}")
    return match.group(1)


def package_version(lock_data: dict[str, object], package_name: str) -> str:
    packages = lock_data.get("package", [])
    if not isinstance(packages, list):
        raise ValueError("liste de packages absente du lockfile")

    for package in packages:
        if isinstance(package, dict) and package.get("name") == package_name:
            version = package.get("version")
            if isinstance(version, str):
                return version

    raise ValueError(f"package {package_name!r} introuvable dans le lockfile")


def collect_versions() -> dict[str, str]:
    pyproject = read_toml("pyproject.toml")
    cargo_toml = read_toml("src/frontend/src-tauri/Cargo.toml")
    uv_lock = read_toml("uv.lock")
    cargo_lock = read_toml("src/frontend/src-tauri/Cargo.lock")
    root_package = read_json("package.json")
    frontend_package = read_json("src/frontend/package.json")
    frontend_lock = read_json("src/frontend/package-lock.json")
    tauri_config = read_json("src/frontend/src-tauri/tauri.conf.json")

    project = pyproject.get("project", {})
    cargo_package = cargo_toml.get("package", {})
    if not isinstance(project, dict) or not isinstance(cargo_package, dict):
        raise ValueError("métadonnées de projet TOML invalides")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    badge_match = re.search(r"badge/version-(\d+\.\d+\.\d+)(?:--alpha)?-", readme)
    if not badge_match:
        raise ValueError("badge de version introuvable dans README.md")

    return {
        "pyproject.toml": str(project.get("version", "")),
        "package.json": str(root_package.get("version", "")),
        "src/frontend/package.json": str(frontend_package.get("version", "")),
        "src/frontend/package-lock.json": str(frontend_lock.get("version", "")),
        "src/frontend/src-tauri/tauri.conf.json": str(tauri_config.get("version", "")),
        "src/frontend/src-tauri/Cargo.toml": str(cargo_package.get("version", "")),
        "src/frontend/src-tauri/Cargo.lock": package_version(cargo_lock, "therese"),
        "src/backend/app/config.py": extract_python_version(
            "src/backend/app/config.py",
            r'app_version\s*:\s*str\s*=\s*["\']([^"\']+)["\']',
        ),
        "src/backend/app/__init__.py": extract_python_version(
            "src/backend/app/__init__.py",
            r'__version__\s*=\s*["\']([^"\']+)["\']',
        ),
        "uv.lock": package_version(uv_lock, "therese-backend"),
        "README.md (badge)": badge_match.group(1),
    }


def main() -> int:
    try:
        versions = collect_versions()
    except (OSError, ValueError, json.JSONDecodeError, tomllib.TOMLDecodeError) as error:
        print(f"ERREUR : impossible de contrôler les versions : {error}", file=sys.stderr)
        return 2

    expected = versions["pyproject.toml"]
    mismatches = {
        source: version
        for source, version in versions.items()
        if not version or version != expected
    }

    print(f"Version de référence : {expected}")
    for source, version in versions.items():
        status = "OK" if source not in mismatches else "ECART"
        print(f"  {status:<5} {source}: {version or '<vide>'}")

    if mismatches:
        print("\nDes versions ne sont pas synchronisées.", file=sys.stderr)
        return 1

    print("\nToutes les sources de version sont synchronisées.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
