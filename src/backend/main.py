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

import argparse
import os

# PyInstaller : ajuster les chemins pour trouver alembic/ et les data files
if getattr(sys, "_MEIPASS", None):
    os.environ.setdefault("THERESE_FROZEN", "1")
    # Alembic et autres data files sont dans le bundle PyInstaller
    os.chdir(sys._MEIPASS)

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
