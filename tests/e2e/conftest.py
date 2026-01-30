"""
THÉRÈSE v2 - E2E Test Configuration

Fixtures pour tests end-to-end avec Playwright.
"""

import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Generator

import pytest
from playwright.sync_api import Browser, Page, sync_playwright


# Configuration
FRONTEND_URL = "http://localhost:1420"
BACKEND_URL = "http://localhost:8000"
SANDBOX_DIR = Path.home() / ".therese-test-sandbox"
BACKEND_DIR = Path(__file__).parent.parent.parent / "src" / "backend"


@pytest.fixture(scope="session")
def sandbox_env():
    """Environnement de test isolé."""
    # Créer dossier sandbox
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["THERESE_DATA_DIR"] = str(SANDBOX_DIR)

    yield env

    # Cleanup après tous les tests
    if SANDBOX_DIR.exists():
        shutil.rmtree(SANDBOX_DIR)


@pytest.fixture(scope="session")
def backend_server(sandbox_env):
    """Lance le backend FastAPI en mode test."""
    process = subprocess.Popen(
        ["uv", "run", "uvicorn", "app.main:app", "--port", "8000"],
        cwd=BACKEND_DIR,
        env=sandbox_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Attendre que le serveur démarre
    time.sleep(3)

    # Vérifier que le serveur est up
    import httpx
    for _ in range(10):
        try:
            response = httpx.get(f"{BACKEND_URL}/health", timeout=2)
            if response.status_code == 200:
                break
        except Exception:
            time.sleep(1)

    yield process

    # Arrêter le serveur
    process.terminate()
    process.wait(timeout=5)


@pytest.fixture(scope="function")
def reset_db():
    """Reset la base de données entre chaque test."""
    db_path = SANDBOX_DIR / "therese.db"
    if db_path.exists():
        db_path.unlink()

    # Reset Qdrant
    qdrant_path = SANDBOX_DIR / "qdrant"
    if qdrant_path.exists():
        shutil.rmtree(qdrant_path)

    yield

    # Cleanup après le test
    if db_path.exists():
        db_path.unlink()


@pytest.fixture(scope="function")
def browser_context(backend_server, reset_db) -> Generator[Browser, None, None]:
    """Context navigateur Playwright."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page(browser_context: Browser) -> Generator[Page, None, None]:
    """Page Playwright pour les tests."""
    context = browser_context.new_context(
        viewport={"width": 1280, "height": 800},
        locale="fr-FR",
    )
    page = context.new_page()

    # Navigation vers l'app
    page.goto(FRONTEND_URL)

    # Attendre que l'app soit chargée
    page.wait_for_load_state("networkidle")

    yield page

    page.close()
    context.close()


@pytest.fixture
def skip_onboarding(page: Page):
    """Skip onboarding pour les tests qui n'en ont pas besoin."""
    # Marquer l'onboarding comme complété directement dans la DB
    import sqlite3

    db_path = SANDBOX_DIR / "therese.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Créer la table preferences si elle n'existe pas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS preferences (
            id TEXT PRIMARY KEY,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insérer onboarding_complete
    import uuid
    cursor.execute(
        "INSERT OR REPLACE INTO preferences (id, key, value) VALUES (?, ?, ?)",
        (str(uuid.uuid4()), "onboarding_complete", "true")
    )

    conn.commit()
    conn.close()

    # Reload la page
    page.reload()
    page.wait_for_load_state("networkidle")


def take_screenshot(page: Page, name: str):
    """Helper pour capturer des screenshots."""
    screenshots_dir = Path(__file__).parent / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)

    path = screenshots_dir / f"{name}.png"
    page.screenshot(path=str(path))
    print(f"📸 Screenshot: {path}")
