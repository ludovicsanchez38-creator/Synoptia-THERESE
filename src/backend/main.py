"""
THÉRÈSE v2 - Backend Entry Point

This module re-exports the FastAPI app from the app package.
Use 'uvicorn app.main:app' to run the server.

En mode sidecar (PyInstaller), accepte --host et --port en arguments.
"""

import os
import sys


def _is_stream_valid(stream, *, readable: bool) -> bool:
    """Vérifie qu'un flux stdio est utilisable (pas seulement non-None)."""
    if stream is None:
        return False
    try:
        if getattr(stream, "closed", False):
            return False
        fileno = stream.fileno()
        if fileno < 0:
            return False
        os.fstat(fileno)
        if readable:
            return not hasattr(stream, "readable") or stream.readable()
        return not hasattr(stream, "writable") or stream.writable()
    except Exception:
        return False


# ── BUG-009 : Protection stdio pour Windows sidecar ──────────────────
# Quand Tauri (app GUI, windows_subsystem="windows") lance le sidecar,
# les handles stdin/stdout/stderr peuvent être None ou invalides.
# Cela crashe uvicorn, torch, ou tout code appelant sys.stdout.write().
# On redirige vers devnull AVANT tout autre import.
# Réf : https://github.com/pyinstaller/pyinstaller/issues/3692
if getattr(sys, "frozen", False) and sys.platform == "win32":
    if not _is_stream_valid(sys.stdout, readable=False):
        sys.stdout = open(os.devnull, "w")  # noqa: SIM115
    if not _is_stream_valid(sys.stderr, readable=False):
        sys.stderr = open(os.devnull, "w")  # noqa: SIM115
    if not _is_stream_valid(sys.stdin, readable=True):
        sys.stdin = open(os.devnull, "r")  # noqa: SIM115

# ── BUG-009 : Diagnostic de démarrage sidecar ────────────────────────
# Écrit dans un fichier AVANT tout import lourd pour savoir si Python démarre.
# Supprimable une fois le bug confirmé corrigé.
if getattr(sys, "frozen", False):
    try:
        _diag_dir = os.path.join(os.path.expanduser("~"), ".therese", "logs")
        os.makedirs(_diag_dir, exist_ok=True)
        with open(os.path.join(_diag_dir, "diag-startup.txt"), "w") as _df:
            _df.write(f"pid={os.getpid()}\n")
            _df.write(f"ppid={os.getppid()}\n")
            _df.write(f"argv={sys.argv}\n")
            _df.write(f"platform={sys.platform}\n")
            _df.write(f"stdout={sys.stdout}\n")
            _df.write(f"stderr={sys.stderr}\n")
            _df.write(f"stdin={sys.stdin}\n")
            _df.write(f"stdout_valid={_is_stream_valid(sys.stdout, readable=False)}\n")
            _df.write(f"stderr_valid={_is_stream_valid(sys.stderr, readable=False)}\n")
            _df.write(f"stdin_valid={_is_stream_valid(sys.stdin, readable=True)}\n")
            _df.write(f"frozen={getattr(sys, 'frozen', False)}\n")
            _df.write(f"_MEIPASS={getattr(sys, '_MEIPASS', None)}\n")
    except Exception:
        pass

import multiprocessing  # noqa: E402

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

import argparse  # noqa: E402

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
    # BUG-009 : Sur Windows, PyInstaller --onefile crée 2 process
    # (bootloader parent + Python child). os.getpid() retourne le child PID,
    # mais wmic trouve le parent PID (aussi nommé backend.exe).
    # Sans exclure le parent, taskkill /T tue le parent ET ses enfants = self-kill.
    parent_pid = os.getppid()

    if sys.platform == "win32":
        import time

        killed_any = False
        zombie_pids: list[int] = []

        # Détecter les zombies backend.exe.
        # wmic est supprimé sur Windows 11 25H2+ (oct 2025), donc on utilise
        # tasklist en fallback. tasklist ne filtre pas par ligne de commande,
        # mais backend.exe est spécifique à THÉRÈSE donc c'est acceptable.
        try:
            result = subprocess.run(
                [
                    "wmic", "process", "where",
                    "name='backend.exe' and commandline like '%--host%127.0.0.1%'",
                    "get", "processid", "/format:list",
                ],
                capture_output=True, text=True, timeout=5,
                stdin=subprocess.DEVNULL,
            )
            for line in result.stdout.splitlines():
                if line.startswith("ProcessId="):
                    pid = int(line.split("=")[1].strip())
                    if pid != current_pid and pid != parent_pid:
                        zombie_pids.append(pid)
        except FileNotFoundError:
            # wmic absent (Windows 11 25H2+) → fallback tasklist
            try:
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq backend.exe", "/FO", "CSV", "/NH"],
                    capture_output=True, text=True, timeout=5,
                    stdin=subprocess.DEVNULL,
                )
                for line in result.stdout.splitlines():
                    parts = line.strip().strip('"').split('","')
                    if len(parts) >= 2:
                        try:
                            pid = int(parts[1].strip('"'))
                            if pid != current_pid and pid != parent_pid:
                                zombie_pids.append(pid)
                        except (ValueError, IndexError):
                            continue
            except Exception:
                pass
        except Exception:
            pass

        # Tuer les zombies détectés
        for pid in zombie_pids:
            try:
                subprocess.run(
                    ["taskkill", "/T", "/F", "/PID", str(pid)],
                    capture_output=True, timeout=5,
                    stdin=subprocess.DEVNULL,
                )
                killed_any = True
            except Exception:
                pass

        # BUG-009 : Attendre que Windows libère les handles fichier des zombies tués.
        # Sans ce délai, le .lock Qdrant reste verrouillé et Path.unlink() échoue
        # avec PermissionError [WinError 32].
        if killed_any:
            time.sleep(3)
    else:
        try:
            result = subprocess.run(
                ["pgrep", "-f", r"backend.*--host.*127\.0\.0\.1"],
                capture_output=True, text=True, timeout=5,
                stdin=subprocess.DEVNULL,
            )
            pids = []
            for line in result.stdout.splitlines():
                try:
                    pid = int(line.strip())
                    if pid != current_pid and pid != parent_pid:
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

from app.main import app  # noqa: E402

__all__ = ["app"]

if __name__ == "__main__":
    import atexit  # noqa: I001
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
    parser.add_argument("--port", type=int, default=17293, help="Port d'écoute")
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
