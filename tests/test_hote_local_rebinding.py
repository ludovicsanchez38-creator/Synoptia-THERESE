"""B-1336 : le moteur local doit refuser un en-tête Host étranger (DNS rebinding).

Audit bêta du 27/10/2026 (A5) : une page web piégée fait pointer son propre nom
de domaine vers 127.0.0.1. Ses requêtes arrivent alors au moteur avec
`Host: rebind.attaquant.example:17293` et, pour un GET même-origine, sans en-tête
Origin : `_origine_refusee` les laisse passer, `/api/auth/token` rend le jeton,
et toutes les routes à jeton s'ouvrent ensuite.

Le moteur n'écoute que sur la boucle locale ; ses seuls appelants légitimes
s'adressent à lui par `127.0.0.1` (webview, `lib.rs`) ou `localhost` (retour
OAuth). Tout autre nom d'hôte est un signe de rebinding et se refuse avant
tout traitement.
"""
import pytest
from app.main import app

HOTES_ETRANGERS = [
    "rebind.attaquant.example:17293",
    "attaquant.example",
    "127.0.0.1.attaquant.example:17293",
    "localhost.attaquant.example:17293",
    "evil.com:17293",
    "tauri.localhost:17293",
    "0.0.0.0:17293",
    "192.168.1.20:17293",
]


@pytest.mark.parametrize("hote", HOTES_ETRANGERS)
@pytest.mark.asyncio
async def test_jeton_refuse_a_un_hote_etranger(client, monkeypatch, hote):
    monkeypatch.setattr(app.state, "session_token", "tok-secret", raising=False)

    resp = await client.get("/api/auth/token", headers={"Host": hote})

    assert resp.status_code == 400
    assert "tok-secret" not in resp.text
    assert resp.json()["code"] == "HOTE_NON_AUTORISE"


@pytest.mark.asyncio
async def test_route_a_jeton_refusee_a_un_hote_etranger_meme_avec_le_bon_jeton(client, monkeypatch):
    monkeypatch.setattr(app.state, "session_token", "tok-secret", raising=False)

    resp = await client.get(
        "/api/notifications/count",
        headers={"Host": "rebind.attaquant.example:17293", "X-Therese-Token": "tok-secret"},
    )

    assert resp.status_code == 400


def test_preflight_refuse_a_un_hote_etranger(sync_client):
    resp = sync_client.options(
        "/api/auth/token",
        headers={
            "Host": "rebind.attaquant.example:17293",
            "Origin": "http://rebind.attaquant.example:17293",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert resp.status_code == 400


@pytest.mark.parametrize(
    "hote",
    ["127.0.0.1:17293", "127.0.0.1", "localhost:17293", "localhost", "LOCALHOST:17293", "[::1]:17293"],
)
@pytest.mark.asyncio
async def test_hotes_de_boucle_locale_acceptes(client, monkeypatch, hote):
    monkeypatch.setattr(app.state, "session_token", "tok-secret", raising=False)

    resp = await client.get("/api/auth/token", headers={"Host": hote})

    assert resp.status_code == 200
    assert resp.json()["token"] == "tok-secret"


@pytest.mark.asyncio
async def test_hote_local_accepte_sur_une_route_a_jeton(client, monkeypatch):
    monkeypatch.setattr(app.state, "session_token", "tok-secret", raising=False)

    resp = await client.get(
        "/api/notifications/count",
        headers={"Host": "127.0.0.1:17293", "X-Therese-Token": "tok-secret"},
    )

    assert resp.status_code == 200
