"""B-440 (05/09/2026) : le test de connexion CalDAV répondait en anglais et
recopiait l'exception brute (« Connection failed: <urllib3…> »)."""

from __future__ import annotations

import pytest

from app.services.calendar import provider_factory


@pytest.mark.asyncio
async def test_le_succes_est_dit_en_francais(monkeypatch):
    class Cal:
        def __init__(self, i):
            self.id, self.name = i, f"Agenda {i}"

    class Provider:
        def __init__(self, **kwargs):
            pass

        async def list_calendars(self):
            return [Cal("a"), Cal("b")]

    monkeypatch.setattr(provider_factory, "CalDAVProvider", Provider)
    resultat = await provider_factory.test_caldav_connection("https://cal.test", "marie", "x")
    assert resultat["success"] is True
    assert "Connected successfully" not in resultat["message"]
    assert "2 calendriers" in resultat["message"]


@pytest.mark.asyncio
async def test_l_echec_ne_recopie_pas_l_exception_brute(monkeypatch):
    class Provider:
        def __init__(self, **kwargs):
            raise RuntimeError("HTTPSConnectionPool(host='cal.test') sk-secret /Users/ludo")

    monkeypatch.setattr(provider_factory, "CalDAVProvider", Provider)
    resultat = await provider_factory.test_caldav_connection("https://cal.test", "marie", "x")
    assert resultat["success"] is False
    assert "Connection failed" not in resultat["message"]
    assert "sk-secret" not in resultat["message"] and "/Users/ludo" not in resultat["message"]
    assert len(resultat["message"]) > 20
