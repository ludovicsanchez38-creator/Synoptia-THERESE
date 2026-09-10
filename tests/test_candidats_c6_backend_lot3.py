"""Cycle 6, lot 3 (10/09/2026) : la frontière de l'écran (RULES section 13, lot C 0.48).

Un échec inattendu ne recopie jamais `str(e)` dans le `detail` HTTP : le texte
technique (chemins, jetons, messages de pilote) reste aux journaux, l'écran reçoit
un message français générique ou localisé (`message_pour_ecran`).
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

SECRET = "sk-secret-000 /Users/ludo/prive.db"


@pytest.mark.asyncio
async def test_une_panne_de_synchronisation_crm_ne_recopie_pas_l_exception_a_l_ecran(client: AsyncClient, monkeypatch):
    from app.services import crm_sync, sheets_service

    async def _jeton(session):
        return "jeton"

    class FauxSheets:
        def __init__(self, access_token=None, api_key=None):
            pass

        async def get_all_data_as_dicts(self, spreadsheet_id, sheet):
            return []

    def _bilan_en_panne(*_a, **_k):
        raise RuntimeError(SECRET)

    monkeypatch.setattr(crm_sync, "ensure_valid_crm_token", _jeton)
    monkeypatch.setattr(sheets_service, "GoogleSheetsService", FauxSheets)
    monkeypatch.setattr(crm_sync, "build_sync_message", _bilan_en_panne)
    config = await client.post("/api/crm/sync/config", json={"spreadsheet_id": "feuille-de-test"})
    assert config.status_code in (200, 201), config.text
    reponse = await client.post("/api/crm/sync")
    assert reponse.status_code == 500, reponse.text
    assert "sk-secret" not in reponse.text and "/Users/ludo" not in reponse.text, reponse.text


@pytest.mark.asyncio
async def test_une_panne_de_generation_de_trame_ne_recopie_pas_l_exception_a_l_ecran(client: AsyncClient, monkeypatch):
    from app.routers import documents as routeur

    def _panne():
        raise RuntimeError(SECRET)

    monkeypatch.setattr(routeur, "get_llm_service", _panne)
    document = await client.post("/api/documents", json={"title": "Proposition", "brief": "Test"})
    assert document.status_code == 200, document.text
    reponse = await client.post(f"/api/documents/{document.json()['id']}/outline")
    assert reponse.status_code == 500, reponse.text
    assert "sk-secret" not in reponse.text and "/Users/ludo" not in reponse.text, reponse.text


@pytest.mark.asyncio
async def test_une_sauvegarde_impossible_ne_recopie_pas_l_exception_a_l_ecran(client: AsyncClient, monkeypatch):
    from app.routers import data as routeur

    def _panne(_chemin):
        raise RuntimeError(SECRET)

    monkeypatch.setattr(routeur, "_create_archive", _panne)
    reponse = await client.post("/api/data/backup", json={"password": "motdepasse-de-test-1234"})
    assert reponse.status_code in (500, 503), reponse.text
    assert "sk-secret" not in reponse.text and "/Users/ludo" not in reponse.text, reponse.text
