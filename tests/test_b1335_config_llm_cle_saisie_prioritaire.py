"""B-1335 : POST /api/config/llm lisait la clé dans l'environnement sans la
garde de B-200 (version installée : jamais à l'insu de l'utilisateur) et la
faisait passer avant la clé saisie dans Paramètres, à l'inverse de B-530.
Lecteur ε, passe 8."""

import pytest

CLE_SAISIE = "AQ.abcdefghijklmnopqrstuvwxyz0123456789"


async def _poser_et_configurer(client):
    r = await client.post("/api/config/api-key", json={"provider": "gemini", "api_key": CLE_SAISIE})
    assert r.status_code == 200, r.text
    r = await client.post("/api/config/llm", json={"provider": "gemini", "model": "gemini-3-pro-preview"})
    assert r.status_code == 200, r.text
    from app.services import llm

    return llm._llm_service.config.api_key


@pytest.mark.asyncio
async def test_la_cle_saisie_passe_avant_l_environnement(client, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "cle-de-l-environnement")
    assert await _poser_et_configurer(client) == CLE_SAISIE


@pytest.mark.asyncio
async def test_la_version_installee_ne_lit_pas_l_environnement(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "therese_env", "production")
    monkeypatch.delenv("THERESE_LIRE_CLES_ENV", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "cle-de-l-environnement")
    r = await client.post("/api/config/llm", json={"provider": "gemini", "model": "gemini-3-pro-preview"})
    from app.services import llm

    assert r.status_code != 200 or llm._llm_service.config.api_key != "cle-de-l-environnement", r.text
