"""US-005 : /api/shutdown doit être exempté de l'auth middleware.

En production, le token de session est défini. Sans exemption, l'appel de
Tauri (TcpStream à la fermeture) et d'UpdateBanner, qui n'envoient pas le
token, repart en 401 : le shutdown graceful n'a jamais lieu (force-kill, et
verrou backend.exe pendant l'auto-update Windows, BUG-099).

NB : le lifespan de test ne génère pas de session_token, donc l'auth est
inopérante par défaut en test. On force un token pour activer le middleware.
"""
import os

import pytest
from app.main import app


@pytest.mark.asyncio
async def test_shutdown_exempte_du_token_de_session(client, monkeypatch):
    # Le handler programme un os.kill différé : on le neutralise pour le test.
    monkeypatch.setattr(os, "kill", lambda *a, **k: None)
    # Activer l'auth middleware (absent en test) avec un token de session.
    monkeypatch.setattr(app.state, "session_token", "tok-test", raising=False)

    # Aucun header X-Therese-Token : doit passer (exempté), pas 401.
    resp = await client.post("/api/shutdown")

    assert resp.status_code == 200
    assert resp.json()["status"] == "shutting_down"


@pytest.mark.asyncio
async def test_endpoint_protege_reste_401_sans_token(client, monkeypatch):
    """Garde-fou : l'exemption du shutdown ne désactive pas l'auth globale."""
    monkeypatch.setattr(app.state, "session_token", "tok-test", raising=False)

    resp = await client.get("/api/notifications/count")

    assert resp.status_code == 401
