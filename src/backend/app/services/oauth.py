"""
THÉRÈSE v2 - OAuth 2.0 PKCE Service

Handles OAuth 2.0 PKCE flow for desktop applications.
Used for Gmail, Google Calendar, and other OAuth providers.

Phase 1 - Core Native Email (Gmail)
"""

import asyncio
import base64
import hashlib
import logging
import secrets
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlencode, parse_qs, urlparse

import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)


# ============================================================
# OAuth Configuration
# ============================================================


@dataclass
class OAuthConfig:
    """OAuth provider configuration."""
    client_id: str
    client_secret: str
    auth_url: str
    token_url: str
    scopes: list[str]
    redirect_uri: str = "http://localhost:8080/oauth/callback"


# Google OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


# Gmail scopes
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.labels",
]

# Google Calendar scopes
GCAL_SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
]

# Combined Google scopes (Gmail + Calendar)
GOOGLE_ALL_SCOPES = GMAIL_SCOPES + GCAL_SCOPES

# Google Sheets scopes (for CRM sync)
GSHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]


# ============================================================
# PKCE Helper Functions
# ============================================================


def generate_code_verifier() -> str:
    """
    Generate a cryptographically random code verifier.

    Per RFC 7636, verifier must be 43-128 chars.
    """
    return base64.urlsafe_b64encode(secrets.token_bytes(96)).decode('utf-8').rstrip('=')


def generate_code_challenge(verifier: str) -> str:
    """
    Generate code challenge from verifier using S256.

    challenge = BASE64URL(SHA256(ASCII(code_verifier)))
    """
    digest = hashlib.sha256(verifier.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')


# ============================================================
# OAuth PKCE Service
# ============================================================


class OAuthPKCEService:
    """
    OAuth 2.0 PKCE flow for desktop applications.

    PKCE (Proof Key for Code Exchange) is more secure than traditional
    OAuth flow for desktop/mobile apps as it doesn't require client secrets.
    """

    def __init__(self):
        """Initialize OAuth service."""
        self._pending_flows: dict[str, dict] = {}  # state -> flow data

    def initiate_flow(
        self,
        provider: str,
        config: OAuthConfig,
    ) -> dict:
        """
        Initiate OAuth PKCE flow.

        Returns authorization URL and state for frontend to open.

        Args:
            provider: Provider name (gmail, gcal, etc.)
            config: OAuth configuration

        Returns:
            dict with auth_url, state, code_verifier
        """
        # Generate PKCE parameters
        state = secrets.token_urlsafe(32)
        code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(code_verifier)

        # Build authorization URL
        params = {
            'client_id': config.client_id,
            'redirect_uri': config.redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(config.scopes),
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'access_type': 'offline',  # Request refresh token
            'prompt': 'consent',  # Force consent to get refresh token
        }

        auth_url = f"{config.auth_url}?{urlencode(params)}"

        # Store flow data
        self._pending_flows[state] = {
            'provider': provider,
            'config': config,
            'code_verifier': code_verifier,
            'timestamp': time.time(),
        }

        logger.info(f"Initiated OAuth flow for {provider} with state {state[:8]}...")

        return {
            'auth_url': auth_url,
            'state': state,
            'redirect_uri': config.redirect_uri,
        }

    async def handle_callback(
        self,
        state: str,
        code: Optional[str],
        error: Optional[str] = None,
    ) -> dict:
        """
        Handle OAuth callback with authorization code.

        Exchanges code for access/refresh tokens.

        Args:
            state: State parameter from callback
            code: Authorization code from callback
            error: Error from callback if any

        Returns:
            dict with access_token, refresh_token, expires_in, scopes

        Raises:
            HTTPException: If flow not found or exchange fails
        """
        if error:
            logger.error(f"OAuth error: {error}")
            raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

        if state not in self._pending_flows:
            logger.error(f"Unknown OAuth state: {state[:8]}...")
            raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

        flow_data = self._pending_flows.pop(state)
        config = flow_data['config']
        code_verifier = flow_data['code_verifier']

        # Check timeout (10 minutes)
        if time.time() - flow_data['timestamp'] > 600:
            logger.error(f"OAuth flow expired for state {state[:8]}...")
            raise HTTPException(status_code=400, detail="OAuth flow expired")

        if not code:
            raise HTTPException(status_code=400, detail="No authorization code received")

        # Exchange code for tokens
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    config.token_url,
                    data={
                        'client_id': config.client_id,
                        'client_secret': config.client_secret,
                        'code': code,
                        'code_verifier': code_verifier,
                        'grant_type': 'authorization_code',
                        'redirect_uri': config.redirect_uri,
                    },
                    timeout=30.0,
                )

                if response.status_code != 200:
                    error_data = response.json() if response.content else {}
                    logger.error(f"Token exchange failed: {response.status_code} {error_data}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Token exchange failed: {error_data.get('error_description', 'Unknown error')}"
                    )

                tokens = response.json()
                logger.info(f"OAuth flow completed for {flow_data['provider']}")

                return {
                    'access_token': tokens['access_token'],
                    'refresh_token': tokens.get('refresh_token'),
                    'expires_in': tokens.get('expires_in', 3600),
                    'scopes': tokens.get('scope', ' '.join(config.scopes)).split(),
                    'token_type': tokens.get('token_type', 'Bearer'),
                    'client_id': config.client_id,
                    'client_secret': config.client_secret,
                }

            except httpx.HTTPError as e:
                logger.error(f"HTTP error during token exchange: {e}")
                raise HTTPException(status_code=500, detail=f"Token exchange failed: {str(e)}")

    async def refresh_access_token(
        self,
        refresh_token: str,
        config: OAuthConfig,
    ) -> dict:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: The refresh token
            config: OAuth configuration

        Returns:
            dict with new access_token, expires_in

        Raises:
            HTTPException: If refresh fails
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    config.token_url,
                    data={
                        'client_id': config.client_id,
                        'client_secret': config.client_secret,
                        'refresh_token': refresh_token,
                        'grant_type': 'refresh_token',
                    },
                    timeout=30.0,
                )

                if response.status_code != 200:
                    error_data = response.json() if response.content else {}
                    logger.error(f"Token refresh failed: {response.status_code} {error_data}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Token refresh failed: {error_data.get('error_description', 'Unknown error')}"
                    )

                tokens = response.json()
                logger.info("Access token refreshed successfully")

                return {
                    'access_token': tokens['access_token'],
                    'expires_in': tokens.get('expires_in', 3600),
                    'token_type': tokens.get('token_type', 'Bearer'),
                }

            except httpx.HTTPError as e:
                logger.error(f"HTTP error during token refresh: {e}")
                raise HTTPException(status_code=500, detail=f"Token refresh failed: {str(e)}")

    def cleanup_expired_flows(self):
        """Clean up expired OAuth flows (older than 10 minutes)."""
        now = time.time()
        expired = [
            state for state, data in self._pending_flows.items()
            if now - data['timestamp'] > 600
        ]
        for state in expired:
            del self._pending_flows[state]
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired OAuth flows")


# ============================================================
# Global Instance
# ============================================================


_oauth_service: Optional[OAuthPKCEService] = None


def get_oauth_service() -> OAuthPKCEService:
    """Get global OAuth service instance."""
    global _oauth_service
    if _oauth_service is None:
        _oauth_service = OAuthPKCEService()
    return _oauth_service


# Background cleanup task
async def cleanup_expired_flows_periodically():
    """Periodic cleanup of expired OAuth flows."""
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        get_oauth_service().cleanup_expired_flows()
