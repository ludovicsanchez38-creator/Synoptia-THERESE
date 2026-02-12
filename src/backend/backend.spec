# -*- mode: python ; coding: utf-8 -*-
"""
THÉRÈSE v2 - PyInstaller Spec
Produit un exécutable unique pour le sidecar Tauri.
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Répertoire du backend
backend_dir = os.path.dirname(os.path.abspath(SPEC))

# Hidden imports nécessaires au runtime
hidden_imports = [
    # Serveur ASGI
    "uvicorn",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    # FastAPI / Pydantic / SQLModel
    "pydantic",
    "pydantic_settings",
    "sqlmodel",
    "sqlalchemy",
    "sqlalchemy.dialects.sqlite",
    "aiosqlite",
    # HTTP / API clients
    "httpx",
    "anthropic",
    "openai",
    # Qdrant
    "qdrant_client",
    # Embeddings (sentence-transformers + torch + sklearn/scipy)
    "sentence_transformers",
    "torch",
    "numpy",
    "einops",
    "sklearn",
    "scipy",
    # Sécurité
    "cryptography",
    "keyring",
    "keyring.backends",
    "keyring.backends.macOS",
    # Rate limiting
    "slowapi",
    # Multipart
    "multipart",
    "python_multipart",
    # Office
    "docx",
    "pptx",
    "openpyxl",
    # Images & PDF
    "PIL",
    "reportlab",
    "pypdf",
    # Web scraping
    "bs4",
    # Async
    "greenlet",
    # Google APIs
    "google.auth",
    "google.oauth2",
    "google_auth_oauthlib",
    "googleapiclient",
    # Email / Calendar
    "imap_tools",
    "aiosmtplib",
    "caldav",
    "icalendar",
    # YAML
    "yaml",
    # Alembic
    "alembic",
    "alembic.config",
    "alembic.command",
    # App modules
    *collect_submodules("app"),
]

# Data files à inclure dans le bundle
datas = [
    (os.path.join(backend_dir, "alembic"), "alembic"),
    (os.path.join(backend_dir, "alembic.ini"), "."),
]

# Collecter les data files des bibliothèques qui en ont besoin
datas += collect_data_files("sentence_transformers")
datas += collect_data_files("qdrant_client")
datas += collect_data_files("certifi")

a = Analysis(
    [os.path.join(backend_dir, "main.py")],
    pathex=[backend_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "IPython",
        "jupyter",
        "notebook",
        "pytest",
        "mypy",
        "ruff",
        # NOTE : NE PAS exclure les sous-modules torch (torch.cuda, torch.distributed, etc.)
        # torch les importe à l'init et PyInstaller crash si ils manquent
        "triton",
        "caffe2",
    ],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=sys.platform != "win32",  # strip corrompt les DLL Windows
    upx=False,                      # UPX corrompt python3xx.dll et vcruntime140.dll sur Windows
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
