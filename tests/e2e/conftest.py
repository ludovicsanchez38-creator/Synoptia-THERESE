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
    env["THERESE_ENV"] = "test"

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
    headless = os.environ.get("PLAYWRIGHT_HEADLESS", "false").lower() == "true"
    slow_mo = 0 if headless else 500

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=slow_mo)
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
    print(f"Screenshot: {path}")


# ============================================================
# Panel page factory (pour fenetres independantes ?panel=xxx)
# ============================================================


VALID_PANELS = {"email", "calendar", "tasks", "invoices", "crm"}


@pytest.fixture
def panel_page(browser_context, skip_onboarding):
    """
    Factory fixture pour ouvrir un panel dans une page standalone.

    Usage:
        def test_tasks(panel_page):
            page, context = panel_page("tasks")
            # ... assertions
    """
    pages = []
    contexts = []

    def _make(panel_name: str):
        assert panel_name in VALID_PANELS, f"Panel invalide: {panel_name}"

        context = browser_context.new_context(
            viewport={"width": 1200, "height": 800},
            locale="fr-FR",
        )
        page = context.new_page()
        page.goto(f"{FRONTEND_URL}/?panel={panel_name}")
        page.wait_for_load_state("networkidle")

        pages.append(page)
        contexts.append(context)

        return page, context

    yield _make

    for p in pages:
        try:
            p.close()
        except Exception:
            pass
    for c in contexts:
        try:
            c.close()
        except Exception:
            pass


# ============================================================
# API client fixture (httpx avec auth token)
# ============================================================


@pytest.fixture
def api_client(backend_server, sandbox_env):
    """
    Client httpx synchrone avec auth token pour seeding via API.

    Usage:
        def test_with_seeded_data(api_client):
            resp = api_client.get("/api/tasks")
            assert resp.status_code == 200
    """
    import httpx

    # Recuperer le token auth
    try:
        resp = httpx.get(f"{BACKEND_URL}/api/auth/token", timeout=5)
        token = resp.json().get("token", "")
    except Exception:
        token = ""

    client = httpx.Client(
        base_url=BACKEND_URL,
        headers={"X-Therese-Token": token} if token else {},
        timeout=10,
    )

    yield client

    client.close()


# ============================================================
# Seeding fixtures - donnees de test via API
# ============================================================


@pytest.fixture
def seeded_contacts(api_client):
    """
    5 contacts CRM a differents stages du pipeline.

    Returns:
        list[dict] - Les contacts crees (avec id)
    """
    contacts = [
        {
            "first_name": "Sophie",
            "last_name": "Martin",
            "company": "Coach Zen",
            "email": "sophie@coachzen.fr",
            "phone": "+33612345678",
            "tags": ["coaching", "client"],
        },
        {
            "first_name": "Marc",
            "last_name": "Dubois",
            "company": "Plomberie Express",
            "email": "marc@plomberie-express.fr",
            "phone": "+33698765432",
            "tags": ["artisan", "prospect"],
        },
        {
            "first_name": "Claire",
            "last_name": "Leroy",
            "company": "RH Conseil",
            "email": "claire@rhconseil.fr",
            "phone": "+33645678901",
            "tags": ["consultante", "lead"],
        },
        {
            "first_name": "Thomas",
            "last_name": "Bernard",
            "company": "Photo Pro",
            "email": "thomas@photopro.fr",
            "tags": ["photographe"],
        },
        {
            "first_name": "Nadia",
            "last_name": "Hamidi",
            "company": "Naturo Sante",
            "email": "nadia@naturosante.fr",
            "tags": ["naturopathe", "rgpd"],
        },
    ]

    created = []
    for contact_data in contacts:
        resp = api_client.post("/api/memory/contacts", json=contact_data)
        if resp.status_code == 200:
            created.append(resp.json())

    return created


@pytest.fixture
def seeded_tasks(api_client):
    """
    4 taches avec statuts et priorites varies.

    Returns:
        list[dict] - Les taches creees (avec id)
    """
    tasks = [
        {
            "title": "Envoyer devis Dupont",
            "description": "Devis coaching 3 seances",
            "priority": "high",
            "status": "todo",
        },
        {
            "title": "Relancer prospect Martin",
            "description": "Appel tel prevu",
            "priority": "medium",
            "status": "in_progress",
        },
        {
            "title": "Mettre a jour site web",
            "description": "Ajouter page temoignages",
            "priority": "low",
            "status": "todo",
        },
        {
            "title": "Facture janvier envoyee",
            "description": "Facture FACT-2026-001",
            "priority": "medium",
            "status": "done",
        },
    ]

    created = []
    for task_data in tasks:
        resp = api_client.post("/api/tasks", json=task_data)
        if resp.status_code == 200:
            created.append(resp.json())

    return created


@pytest.fixture
def seeded_invoice(api_client, seeded_contacts):
    """
    Facture brouillon avec 2 lignes.

    Returns:
        dict - La facture creee (avec id, invoice_number, lines)
    """
    if not seeded_contacts:
        pytest.skip("Pas de contacts seeded")

    contact_id = seeded_contacts[0]["id"]

    invoice_data = {
        "contact_id": contact_id,
        "lines": [
            {
                "description": "Coaching individuel - 3h",
                "quantity": 3,
                "unit_price_ht": 150.0,
                "tva_rate": 20.0,
            },
            {
                "description": "Support documentaire",
                "quantity": 1,
                "unit_price_ht": 50.0,
                "tva_rate": 20.0,
            },
        ],
        "notes": "Facture test E2E",
    }

    resp = api_client.post("/api/invoices", json=invoice_data)
    if resp.status_code == 200:
        return resp.json()

    pytest.skip(f"Impossible de creer la facture: {resp.status_code}")


@pytest.fixture
def seeded_calendar(api_client):
    """
    Calendrier local avec 2 evenements.

    Returns:
        dict with keys 'calendar' and 'events'
    """
    from datetime import UTC, datetime, timedelta

    # Creer un calendrier local
    cal_data = {
        "summary": "Calendrier Test E2E",
        "description": "Calendrier de test automatise",
        "timezone": "Europe/Paris",
        "provider": "local",
    }

    cal_resp = api_client.post("/api/calendar/calendars", json=cal_data)
    if cal_resp.status_code != 200:
        pytest.skip(f"Impossible de creer le calendrier: {cal_resp.status_code}")

    calendar = cal_resp.json()
    calendar_id = calendar["id"]

    # Creer 2 evenements
    now = datetime.now(UTC)
    events_data = [
        {
            "calendar_id": calendar_id,
            "summary": "RDV Client Sophie",
            "description": "Session coaching initiale",
            "start_datetime": (now + timedelta(days=1, hours=14)).isoformat(),
            "end_datetime": (now + timedelta(days=1, hours=15)).isoformat(),
            "location": "Manosque",
        },
        {
            "calendar_id": calendar_id,
            "summary": "Formation IA",
            "description": "Webinaire outils IA solopreneurs",
            "start_datetime": (now + timedelta(days=3, hours=10)).isoformat(),
            "end_datetime": (now + timedelta(days=3, hours=12)).isoformat(),
        },
    ]

    events = []
    for event_data in events_data:
        resp = api_client.post("/api/calendar/events", json=event_data)
        if resp.status_code == 200:
            events.append(resp.json())

    return {"calendar": calendar, "events": events}
