"""
Tests pour le service OAuth 2.0 PKCE de THÉRÈSE v2.

Tests couvrant :
- Génération des paramètres PKCE (verifier, challenge)
- Initiation du flux OAuth
- Gestion des callbacks avec validation
- Refresh token
- Cleanup des flows expirés
- Configuration OAuth dataclass
- Singleton du service
"""

import base64
import hashlib
import logging
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.services.oauth import (
    GMAIL_SCOPES,
    GOOGLE_AUTH_URL,
    GOOGLE_TOKEN_URL,
    OAuthConfig,
    OAuthPKCEService,
    generate_code_challenge,
    generate_code_verifier,
    get_oauth_service,
)
from fastapi import HTTPException

logger = logging.getLogger(__name__)


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def oauth_config():
    """Configuration OAuth de test."""
    return OAuthConfig(
        client_id="test_client_id_12345",
        client_secret="test_client_secret_xyz",
        auth_url=GOOGLE_AUTH_URL,
        token_url=GOOGLE_TOKEN_URL,
        scopes=GMAIL_SCOPES,
        redirect_uri="http://localhost:8000/api/email/auth/callback-redirect",
    )


@pytest.fixture
def oauth_service():
    """Instance du service OAuth pour tester."""
    service = OAuthPKCEService()
    yield service
    # Cleanup
    service._pending_flows.clear()


# ============================================================
# Tests : Génération paramètres PKCE
# ============================================================


def test_generate_code_verifier():
    """
    Test 1 : generate_code_verifier() génère un verifier de longueur valide.

    RFC 7636 : verifier doit être entre 43-128 caractères.
    """
    verifier = generate_code_verifier()

    assert isinstance(verifier, str)
    assert 43 <= len(verifier) <= 128
    # Doit être URL-safe base64 (pas de padding =)
    assert '=' not in verifier
    # Doit contenir caractères alphanumériques + - et _
    assert all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_' for c in verifier)


def test_generate_code_challenge():
    """
    Test 2 : generate_code_challenge() dérive le challenge correctement du verifier.

    La formule est : BASE64URL(SHA256(ASCII(code_verifier)))
    """
    verifier = generate_code_verifier()
    challenge = generate_code_challenge(verifier)

    # Vérifier que le challenge est dérivé correctement
    expected_digest = hashlib.sha256(verifier.encode('utf-8')).digest()
    expected_challenge = base64.urlsafe_b64encode(expected_digest).decode('utf-8').rstrip('=')

    assert challenge == expected_challenge
    assert '=' not in challenge
    assert len(challenge) > 0


# ============================================================
# Tests : Initiation du flux OAuth
# ============================================================


def test_initiate_flow_returns_auth_url(oauth_service, oauth_config):
    """
    Test 3 : initiate_flow() retourne une URL d'autorisation valide.

    L'URL doit contenir les paramètres PKCE corrects.
    """
    result = oauth_service.initiate_flow("gmail", oauth_config)

    assert "auth_url" in result
    assert "state" in result
    assert "redirect_uri" in result

    auth_url = result["auth_url"]

    # Vérifier que l'URL est bien formée
    assert auth_url.startswith(GOOGLE_AUTH_URL)
    assert "client_id=" in auth_url
    assert "code_challenge=" in auth_url
    assert "code_challenge_method=S256" in auth_url
    assert "state=" in auth_url
    assert "redirect_uri=" in auth_url
    assert "response_type=code" in auth_url


def test_initiate_flow_stores_state(oauth_service, oauth_config):
    """
    Test 4 : initiate_flow() stocke le state dans _pending_flows.

    Les données du flow doivent être accessibles via le state.
    """
    result = oauth_service.initiate_flow("gmail", oauth_config)
    state = result["state"]

    # Vérifier que le flow est stocké
    assert state in oauth_service._pending_flows

    flow_data = oauth_service._pending_flows[state]
    assert flow_data["provider"] == "gmail"
    assert flow_data["code_verifier"]
    assert "timestamp" in flow_data
    assert isinstance(flow_data["config"], OAuthConfig)


# ============================================================
# Tests : Gestion des callbacks avec erreurs
# ============================================================


@pytest.mark.asyncio
async def test_handle_callback_with_error(oauth_service):
    """
    Test 5 : handle_callback() avec error parameter lève HTTPException.

    Si un error est retourné, le flux doit être rejeté.
    """
    with pytest.raises(HTTPException) as exc_info:
        await oauth_service.handle_callback(
            state="some_state",
            code=None,
            error="access_denied",
        )

    assert exc_info.value.status_code == 400
    assert "access_denied" in exc_info.value.detail


@pytest.mark.asyncio
async def test_handle_callback_unknown_state(oauth_service):
    """
    Test 6 : handle_callback() avec state inconnu lève HTTPException.

    Si le state n'existe pas dans _pending_flows, c'est une erreur.
    """
    with pytest.raises(HTTPException) as exc_info:
        await oauth_service.handle_callback(
            state="unknown_state_xyz",
            code="some_code",
            error=None,
        )

    assert exc_info.value.status_code == 400
    assert "Invalid or expired OAuth state" in exc_info.value.detail


@pytest.mark.asyncio
async def test_handle_callback_expired_flow(oauth_service, oauth_config):
    """
    Test 7 : handle_callback() après 10 minutes lève HTTPException.

    Le flow doit expirer après 600 secondes.
    """
    # Créer un flow expiré
    state = "expired_state_123"
    oauth_service._pending_flows[state] = {
        "provider": "gmail",
        "config": oauth_config,
        "code_verifier": generate_code_verifier(),
        "timestamp": time.time() - 601,  # 601 secondes dans le passé
    }

    with pytest.raises(HTTPException) as exc_info:
        await oauth_service.handle_callback(
            state=state,
            code="some_code",
            error=None,
        )

    assert exc_info.value.status_code == 400
    assert "OAuth flow expired" in exc_info.value.detail
    # Le flow doit être supprimé après vérification d'expiration
    assert state not in oauth_service._pending_flows


@pytest.mark.asyncio
async def test_handle_callback_no_code(oauth_service, oauth_config):
    """
    Test 8 : handle_callback() sans code lève HTTPException.

    Le code est obligatoire pour l'échange de token.
    """
    # Créer un flow valide
    state = "valid_state_456"
    oauth_service._pending_flows[state] = {
        "provider": "gmail",
        "config": oauth_config,
        "code_verifier": generate_code_verifier(),
        "timestamp": time.time(),
    }

    with pytest.raises(HTTPException) as exc_info:
        await oauth_service.handle_callback(
            state=state,
            code=None,
            error=None,
        )

    assert exc_info.value.status_code == 400
    assert "No authorization code received" in exc_info.value.detail


# ============================================================
# Tests : Callback réussi (mocké)
# ============================================================


@pytest.mark.asyncio
async def test_handle_callback_success(oauth_service, oauth_config):
    """
    Test 9 : handle_callback() avec code valide retourne les tokens.

    Mocke httpx.AsyncClient pour simuler la réponse du serveur OAuth.
    """
    # Créer un flow valide
    state = "success_state_789"
    verifier = generate_code_verifier()
    oauth_service._pending_flows[state] = {
        "provider": "gmail",
        "config": oauth_config,
        "code_verifier": verifier,
        "timestamp": time.time(),
    }

    # Mock la réponse du serveur token
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "ya29.a0AfH6SMBx...",
        "refresh_token": "1//0gF...",
        "expires_in": 3600,
        "scope": " ".join(GMAIL_SCOPES),
        "token_type": "Bearer",
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        result = await oauth_service.handle_callback(
            state=state,
            code="4/0AX4XfWh...",
            error=None,
        )

    assert "access_token" in result
    assert result["access_token"] == "ya29.a0AfH6SMBx..."
    assert "refresh_token" in result
    assert result["expires_in"] == 3600
    assert result["token_type"] == "Bearer"
    # Le flow doit être supprimé après utilisation
    assert state not in oauth_service._pending_flows


# ============================================================
# Tests : Refresh token
# ============================================================


@pytest.mark.asyncio
async def test_refresh_access_token_success(oauth_config):
    """
    Test 10 : refresh_access_token() retourne un nouveau token.

    Mocke httpx.AsyncClient pour simuler la réponse du serveur token.
    """
    service = OAuthPKCEService()
    refresh_token = "1//0gF5g6r..."

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "ya29.a0AfH6SMBx_new...",
        "expires_in": 3600,
        "token_type": "Bearer",
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        result = await service.refresh_access_token(refresh_token, oauth_config)

    assert "access_token" in result
    assert result["access_token"] == "ya29.a0AfH6SMBx_new..."
    assert result["expires_in"] == 3600
    assert result["token_type"] == "Bearer"


@pytest.mark.asyncio
async def test_refresh_access_token_failure(oauth_config):
    """
    Test 11 : refresh_access_token() avec erreur lève HTTPException.

    Si le serveur retourne une erreur, elle doit être signalée.
    """
    service = OAuthPKCEService()
    refresh_token = "invalid_refresh_token"

    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.content = b'{"error": "invalid_grant", "error_description": "Token has been revoked"}'
    mock_response.json.return_value = {
        "error": "invalid_grant",
        "error_description": "Token has been revoked",
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        with pytest.raises(HTTPException) as exc_info:
            await service.refresh_access_token(refresh_token, oauth_config)

    assert exc_info.value.status_code == 400
    assert "Token refresh failed" in exc_info.value.detail


# ============================================================
# Tests : Cleanup flows expirés
# ============================================================


def test_cleanup_expired_flows(oauth_service, oauth_config):
    """
    Test 12 : cleanup_expired_flows() supprime les flows expirés.

    Les flows de plus de 10 minutes doivent être supprimés.
    """
    # Créer 3 flows : 1 valide, 2 expirés
    now = time.time()

    # Flow valide (créé à l'instant)
    state_valid = "state_valid"
    oauth_service._pending_flows[state_valid] = {
        "provider": "gmail",
        "config": oauth_config,
        "code_verifier": generate_code_verifier(),
        "timestamp": now,
    }

    # Flow expiré depuis 11 minutes
    state_expired_old = "state_expired_1"
    oauth_service._pending_flows[state_expired_old] = {
        "provider": "gmail",
        "config": oauth_config,
        "code_verifier": generate_code_verifier(),
        "timestamp": now - 661,  # 661 secondes dans le passé
    }

    # Flow expiré depuis 20 minutes
    state_expired_older = "state_expired_2"
    oauth_service._pending_flows[state_expired_older] = {
        "provider": "gmail",
        "config": oauth_config,
        "code_verifier": generate_code_verifier(),
        "timestamp": now - 1201,  # 1201 secondes dans le passé
    }

    # Cleanup
    oauth_service.cleanup_expired_flows()

    # Vérifier les résultats
    assert state_valid in oauth_service._pending_flows  # Toujours là
    assert state_expired_old not in oauth_service._pending_flows  # Supprimé
    assert state_expired_older not in oauth_service._pending_flows  # Supprimé


# ============================================================
# Tests : Dataclass et configuration
# ============================================================


def test_oauth_config_dataclass():
    """
    Test 13 : OAuthConfig dataclass a tous les champs requis.

    Les champs sont correctement typés et le redirect_uri a une valeur par défaut.
    """
    config = OAuthConfig(
        client_id="id123",
        client_secret="secret456",
        auth_url="https://example.com/auth",
        token_url="https://example.com/token",
        scopes=["scope1", "scope2"],
    )

    assert config.client_id == "id123"
    assert config.client_secret == "secret456"
    assert config.auth_url == "https://example.com/auth"
    assert config.token_url == "https://example.com/token"
    assert config.scopes == ["scope1", "scope2"]
    assert config.redirect_uri == "http://localhost:8080/oauth/callback"

    # Vérifier que on peut aussi spécifier un redirect_uri custom
    config_custom = OAuthConfig(
        client_id="id123",
        client_secret="secret456",
        auth_url="https://example.com/auth",
        token_url="https://example.com/token",
        scopes=["scope1"],
        redirect_uri="http://custom:9000/callback",
    )
    assert config_custom.redirect_uri == "http://custom:9000/callback"


def test_gmail_scopes_defined():
    """
    Test 14 : GMAIL_SCOPES contient les bons scopes.

    Doit inclure readonly, send, modify, et labels.
    """
    assert isinstance(GMAIL_SCOPES, list)
    assert len(GMAIL_SCOPES) == 4

    scopes_str = " ".join(GMAIL_SCOPES)
    assert "gmail.readonly" in scopes_str
    assert "gmail.send" in scopes_str
    assert "gmail.modify" in scopes_str
    assert "gmail.labels" in scopes_str


# ============================================================
# Tests : Singleton
# ============================================================


def test_get_oauth_service_singleton():
    """
    Test 15 : get_oauth_service() retourne un singleton.

    Chaque appel doit retourner la même instance.
    """
    # Reinitialiser le singleton global
    import app.services.oauth as oauth_module
    oauth_module._oauth_service = None

    service1 = get_oauth_service()
    service2 = get_oauth_service()

    assert service1 is service2
    assert isinstance(service1, OAuthPKCEService)
    assert isinstance(service2, OAuthPKCEService)
