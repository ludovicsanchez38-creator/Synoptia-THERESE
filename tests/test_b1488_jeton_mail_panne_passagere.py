"""B-1488 : une coupure réseau au renouvellement du jeton mail faisait
demander de reconnecter le compte.

Le client OAuth rendait toute erreur de transport en 500 « Token refresh
failed », et l'écran lit « Token » comme une session expirée (« Connexion
Gmail expirée - reconnecte-toi »). Le compte était sain : seul Google, ou
le réseau, ne répondait pas. Même défaut pour un 5xx de Google. Un refus
explicite (invalid_grant) reste une demande de reconnexion.
"""

import httpx
import pytest
from fastapi import HTTPException

MARQUEURS_DE_RECONNEXION = ("Token", "token", "expired", "revoked", "401", "reconnect")


class _ClientEnPanne:
    def __init__(self, reponse=None, erreur=None):
        self._reponse, self._erreur = reponse, erreur

    async def post(self, *args, **kwargs):
        if self._erreur:
            raise self._erreur
        return self._reponse


async def _renouveler(monkeypatch, client):
    from app.services import oauth

    async def faux_client():
        return client

    monkeypatch.setattr(oauth, "get_http_client", faux_client)
    from app.routers.email import get_gmail_oauth_config

    config = get_gmail_oauth_config("id", "secret")
    with pytest.raises(HTTPException) as erreur:
        await oauth.get_oauth_service().refresh_access_token("jeton-de-renouvellement", config)
    return erreur.value


@pytest.mark.asyncio
async def test_une_coupure_reseau_n_est_pas_une_session_expiree(monkeypatch):
    erreur = await _renouveler(monkeypatch, _ClientEnPanne(erreur=httpx.ConnectError("réseau coupé")))
    assert erreur.status_code == 503
    assert not any(m in erreur.detail for m in MARQUEURS_DE_RECONNEXION), erreur.detail


@pytest.mark.asyncio
async def test_une_panne_de_google_n_est_pas_une_session_expiree(monkeypatch):
    requete = httpx.Request("POST", "https://oauth2.googleapis.com/token")
    reponse = httpx.Response(503, json={"error": "backend_error"}, request=requete)
    erreur = await _renouveler(monkeypatch, _ClientEnPanne(reponse=reponse))
    assert erreur.status_code == 503
    assert not any(m in erreur.detail for m in MARQUEURS_DE_RECONNEXION), erreur.detail


@pytest.mark.asyncio
async def test_un_refus_explicite_demande_toujours_la_reconnexion(monkeypatch):
    requete = httpx.Request("POST", "https://oauth2.googleapis.com/token")
    reponse = httpx.Response(
        400, json={"error": "invalid_grant", "error_description": "Token has been expired or revoked."},
        request=requete,
    )
    erreur = await _renouveler(monkeypatch, _ClientEnPanne(reponse=reponse))
    assert erreur.status_code != 503
    assert "Token" in erreur.detail


@pytest.mark.asyncio
async def test_b1529_un_429_n_est_pas_une_session_expiree(monkeypatch):
    requete = httpx.Request("POST", "https://oauth2.googleapis.com/token")
    reponse = httpx.Response(429, json={"error": "rate_limit_exceeded"}, request=requete)
    erreur = await _renouveler(monkeypatch, _ClientEnPanne(reponse=reponse))
    assert erreur.status_code == 503
    assert not any(m in erreur.detail for m in MARQUEURS_DE_RECONNEXION), erreur.detail


@pytest.mark.asyncio
async def test_b1529_une_page_html_n_est_pas_une_session_expiree(monkeypatch):
    """Un portail captif (Wi-Fi d'hôtel) répond une page HTML en 200."""
    requete = httpx.Request("POST", "https://oauth2.googleapis.com/token")
    reponse = httpx.Response(200, text="<html><body>Connectez-vous au Wi-Fi</body></html>", request=requete)
    erreur = await _renouveler(monkeypatch, _ClientEnPanne(reponse=reponse))
    assert erreur.status_code == 503
    assert not any(m in erreur.detail for m in MARQUEURS_DE_RECONNEXION), erreur.detail
