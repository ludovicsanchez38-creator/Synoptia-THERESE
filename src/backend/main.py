"""
THÉRÈSE v2 - Backend Entry Point

This module re-exports the FastAPI app from the app package.
Use 'uvicorn app.main:app' to run the server.

En mode sidecar (PyInstaller), accepte --host et --port en arguments.
"""

import argparse
import os
import sys

# PyInstaller : ajuster les chemins pour trouver alembic/ et les data files
if getattr(sys, "_MEIPASS", None):
    os.environ.setdefault("THERESE_FROZEN", "1")
    # Alembic et autres data files sont dans le bundle PyInstaller
    os.chdir(sys._MEIPASS)

from app.main import app

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn

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
