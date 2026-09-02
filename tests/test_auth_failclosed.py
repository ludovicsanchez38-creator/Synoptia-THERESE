"""US-001 : l'API locale est fail-closed et le token ne transite plus en URL.

- Ancien comportement (fail-open) : quand `app.state.session_token` valait None,
  la garde `if expected and ...` sautait et TOUTES les requetes passaient sans
  auth. Desormais : pas de token pret -> 503 (sauf drapeau de test explicite).
- Le token n'est plus accepte en parametre `?token=` d'URL (fuite dans les logs
  et le DOM de la webview), seul l'en-tete X-Therese-Token est valide.
"""
import pytest
from app.main import app


@pytest.mark.asyncio
async def test_fail_closed_503_quand_token_absent(client, monkeypatch):
    """Production avant amorcage : auth active mais token pas encore genere -> 503."""
    monkeypatch.setattr(app.state, "auth_disabled", False, raising=False)
    monkeypatch.setattr(app.state, "session_token", None, raising=False)

    resp = await client.get("/api/notifications/count")

    assert resp.status_code == 503
    assert resp.json()["code"] == "AUTH_NOT_READY"


@pytest.mark.asyncio
async def test_401_sans_token_quand_auth_active(client, monkeypatch):
    """Client localhost sans le secret -> 401 sur une route protegee."""
    monkeypatch.setattr(app.state, "session_token", "tok-test", raising=False)

    resp = await client.get("/api/notifications/count")

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_200_avec_bon_token_en_header(client, monkeypatch):
    """Le bon token en en-tete X-Therese-Token passe."""
    monkeypatch.setattr(app.state, "session_token", "tok-test", raising=False)

    resp = await client.get(
        "/api/notifications/count", headers={"X-Therese-Token": "tok-test"}
    )

    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_token_en_query_param_refuse(client, monkeypatch):
    """US-001 : le token en ?token= n'est plus accepte (seul l'en-tete compte)."""
    monkeypatch.setattr(app.state, "session_token", "tok-test", raising=False)

    resp = await client.get("/api/notifications/count?token=tok-test")

    assert resp.status_code == 401


# ============================================================
# B-165 : GET /api/auth/token promet « seul Tauri » sans rien vérifier
# ============================================================
#
# RB-008 : la docstring de la route affirme « Protégé par CORS (seul Tauri
# peut lire la réponse) ». CORS ne refuse rien côté serveur : une requête
# portant Origin: http://evil.example recevait le jeton de session complet
# en 200, le seul effet de l'origine étrangère étant un avertissement dans
# le journal. La route doit refuser elle-même l'origine non autorisée.


@pytest.mark.asyncio
async def test_le_jeton_de_session_est_refuse_a_une_origine_non_autorisee(client, monkeypatch):
    monkeypatch.setattr(app.state, "session_token", "tok-secret", raising=False)

    resp = await client.get(
        "/api/auth/token", headers={"Origin": "http://evil.example"}
    )

    assert resp.status_code == 403, resp.text
    assert resp.json()["code"] == "ORIGINE_NON_AUTORISEE"
    assert "tok-secret" not in resp.text


@pytest.mark.asyncio
async def test_le_jeton_de_session_reste_lisible_par_la_fenetre_tauri(client, monkeypatch):
    monkeypatch.setattr(app.state, "session_token", "tok-secret", raising=False)

    resp = await client.get(
        "/api/auth/token", headers={"Origin": "tauri://localhost"}
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["token"] == "tok-secret"
