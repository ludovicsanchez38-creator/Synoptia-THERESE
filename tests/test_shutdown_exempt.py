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


# ============================================================
# B-164 : l'exemption d'auth ouvre /api/shutdown au CSRF
# ============================================================
#
# RB-007 : POST /api/shutdown sans aucun en-tête rend 200 et le backend
# s'arrête réellement. L'exemption est nécessaire (le TcpStream brut de
# lib.rs n'a pas le jeton), mais elle laisse n'importe quelle page web
# visitée par l'utilisateur éteindre l'application : un POST simple est
# envoyé sans préflight, et le navigateur y met un en-tête Origin.


@pytest.mark.asyncio
async def test_shutdown_refuse_une_origine_de_navigateur_non_autorisee(client, monkeypatch):
    """Une page web tierce ne doit pas pouvoir éteindre l'application."""
    tue = []
    monkeypatch.setattr(os, "kill", lambda *a, **k: tue.append(a))
    monkeypatch.setattr(app.state, "session_token", "tok-test", raising=False)

    resp = await client.post(
        "/api/shutdown", headers={"Origin": "http://evil.example"}
    )

    assert resp.status_code == 403, resp.text
    assert resp.json()["code"] == "ORIGINE_NON_AUTORISEE"
    assert tue == []


@pytest.mark.asyncio
async def test_shutdown_accepte_l_origine_de_la_fenetre_tauri(client, monkeypatch):
    """UpdateBanner appelle la route depuis la webview : elle doit passer."""
    monkeypatch.setattr(os, "kill", lambda *a, **k: None)
    monkeypatch.setattr(app.state, "session_token", "tok-test", raising=False)

    resp = await client.post(
        "/api/shutdown", headers={"Origin": "tauri://localhost"}
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "shutting_down"
