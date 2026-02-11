"""
THÉRÈSE v2 - Backend Entry Point

This module re-exports the FastAPI app from the app package.
Use 'uvicorn app.main:app' to run the server.

En mode sidecar (PyInstaller), accepte --host et --port en arguments.
"""

import multiprocessing
import sys

# CRITIQUE : freeze_support() AVANT tout import lourd (BUG-008)
# Sans cela, les sous-processus (resource_tracker de torch/sentence_transformers)
# re-exécutent main.py au lieu du code multiprocessing, causant :
# - "unrecognized arguments" dans argparse (confirmé dans les logs)
# - Potentiel double lancement du serveur sur Windows
# Réf : https://pyinstaller.org/en/stable/common-issues-and-pitfalls.html
if __name__ == "__main__":
    multiprocessing.freeze_support()

# Patch resource_tracker PyInstaller (BUG-008 complément)
# Le freeze_support() de PyInstaller (runtime hook pyi_rth_multiprocessing) tente
# de capturer le resource_tracker, mais sa condition échoue quand les sys.flags
# de l'interpréteur frozen ne correspondent pas aux flags -B -S -I.
# On intercepte manuellement AVANT argparse.
# Réf : https://github.com/pyinstaller/pyinstaller/issues/7920
if getattr(sys, "frozen", False) and len(sys.argv) >= 3:
    if sys.argv[-2] == "-c" and sys.argv[-1].startswith(
        (
            "from multiprocessing.resource_tracker import main",
            "from multiprocessing.forkserver import main",
        )
    ):
        exec(sys.argv[-1])  # noqa: S102 - Code généré par CPython, sûr
        sys.exit(0)

import argparse
import os

# PyInstaller : ajuster les chemins pour trouver alembic/ et les data files
if getattr(sys, "_MEIPASS", None):
    os.environ.setdefault("THERESE_FROZEN", "1")
    # Alembic et autres data files sont dans le bundle PyInstaller
    os.chdir(sys._MEIPASS)


def _kill_zombie_backends():
    """Tuer les anciens process backend THÉRÈSE et nettoyer le lock Qdrant.

    Scénario : mise à jour v0.1.4 → v0.1.5+, l'ancien process n'a pas été
    arrêté proprement et tient encore le verrou Qdrant + ~1.45 Go de RAM.
    """
    import signal
    import subprocess
    from pathlib import Path

    current_pid = os.getpid()

    if sys.platform == "win32":
        try:
            result = subprocess.run(
                [
                    "wmic", "process", "where",
                    "name='backend.exe' and commandline like '%--host%127.0.0.1%'",
                    "get", "processid", "/format:list",
                ],
                capture_output=True, text=True, timeout=5,
            )
            for line in result.stdout.splitlines():
                if line.startswith("ProcessId="):
                    pid = int(line.split("=")[1].strip())
                    if pid != current_pid:
                        subprocess.run(
                            ["taskkill", "/T", "/F", "/PID", str(pid)],
                            capture_output=True, timeout=5,
                        )
        except Exception:
            pass
    else:
        try:
            result = subprocess.run(
                ["pgrep", "-f", r"backend.*--host.*127\.0\.0\.1"],
                capture_output=True, text=True, timeout=5,
            )
            pids = []
            for line in result.stdout.splitlines():
                try:
                    pid = int(line.strip())
                    if pid != current_pid:
                        pids.append(pid)
                except ValueError:
                    continue

            for pid in pids:
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass

            if pids:
                import time
                time.sleep(2)
                for pid in pids:
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
        except Exception:
            pass

    # Nettoyer le fichier .lock Qdrant
    lock_file = Path.home() / ".therese" / "qdrant" / ".lock"
    if lock_file.exists():
        try:
            lock_file.unlink()
        except OSError:
            pass


# En mode frozen (sidecar), nettoyer les zombies avant tout
if getattr(sys, "frozen", False) and __name__ == "__main__":
    _kill_zombie_backends()

from app.main import app

__all__ = ["app"]

if __name__ == "__main__":
    import atexit
    import uvicorn

    # Nettoyage des processus enfants à la fermeture (BUG-007)
    def _cleanup_children():
        """Tuer les processus enfants restants (resource_tracker, workers, etc.)."""
        for child in multiprocessing.active_children():
            child.terminate()
        import time
        time.sleep(0.5)
        for child in multiprocessing.active_children():
            child.kill()

    atexit.register(_cleanup_children)

    parser = argparse.ArgumentParser(description="THÉRÈSE backend")
    parser.add_argument("--host", default="127.0.0.1", help="Adresse d'écoute")
    parser.add_argument("--port", type=int, default=8000, help="Port d'écoute")
    args = parser.parse_args()

    # En mode frozen (PyInstaller), pas de reload
    is_frozen = getattr(sys, "frozen", False)

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=not is_frozen,
        log_level="info",
    )
