"""
THÉRÈSE v2 - Email Router

REST API endpoints for email operations.
Supports Gmail (OAuth) and IMAP/SMTP (Local First).

Phase 1 - Core Native Email (Gmail)
Local First - IMAP/SMTP Provider
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_session
from app.models.entities import EmailAccount, EmailMessage, EmailLabel
from app.services.oauth import (
    get_oauth_service,
    OAuthConfig,
    GOOGLE_AUTH_URL,
    GOOGLE_TOKEN_URL,
    GOOGLE_ALL_SCOPES,
)
from app.services.gmail_service import GmailService, format_message_for_storage
from app.services.encryption import encrypt_value, decrypt_value, is_value_encrypted
from app.services.email.provider_factory import (
    get_email_provider,
    list_common_providers,
)

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    """UTC now as naive datetime (compatible SQLite)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


router = APIRouter()


# ============================================================
# Schemas
# ============================================================


class OAuthInitiateRequest(BaseModel):
    """OAuth flow initiation request (POST body).

    SEC-008: Les credentials OAuth sont transmis dans le body POST,
    pas en query parameters (visibles dans les logs serveur et l'historique navigateur).
    """
    client_id: str
    client_secret: str


class OAuthInitiateResponse(BaseModel):
    """OAuth flow initiation response."""
    auth_url: str
    state: str
    redirect_uri: str


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request."""
    state: str
    code: Optional[str] = None
    error: Optional[str] = None


class EmailAccountResponse(BaseModel):
    """Email account response."""
    id: str
    email: str
    provider: str
    scopes: list[str] = []
    created_at: datetime
    last_sync: Optional[datetime] = None


class ImapSetupRequest(BaseModel):
    """IMAP/SMTP account setup request."""
    email: str
    password: str  # App password
    imap_host: str
    imap_port: int = 993
    smtp_host: str
    smtp_port: int = 587
    smtp_use_tls: bool = True


class ImapTestRequest(BaseModel):
    """Test IMAP/SMTP connection request."""
    email: str
    password: str
    imap_host: str
    imap_port: int = 993
    smtp_host: str
    smtp_port: int = 587
    smtp_use_tls: bool = True


class MessageListRequest(BaseModel):
    """List messages request."""
    max_results: int = 50
    page_token: Optional[str] = None
    query: Optional[str] = None
    label_ids: Optional[list[str]] = None


class SendEmailRequest(BaseModel):
    """Send email request."""
    to: list[str]
    subject: str
    body: str
    cc: Optional[list[str]] = None
    bcc: Optional[list[str]] = None
    html: bool = False


class ModifyMessageRequest(BaseModel):
    """Modify message request."""
    add_label_ids: Optional[list[str]] = None
    remove_label_ids: Optional[list[str]] = None


class LabelCreateRequest(BaseModel):
    """Create label request."""
    name: str


# ============================================================
# Helper Functions
# ============================================================


def get_gmail_oauth_config(
    client_id: str,
    client_secret: str,
) -> OAuthConfig:
    """Get Google OAuth configuration (Gmail + Calendar scopes)."""
    return OAuthConfig(
        client_id=client_id,
        client_secret=client_secret,
        auth_url=GOOGLE_AUTH_URL,
        token_url=GOOGLE_TOKEN_URL,
        scopes=GOOGLE_ALL_SCOPES,
        redirect_uri="http://localhost:8000/api/email/auth/callback-redirect",
    )


async def ensure_valid_access_token(
    account: EmailAccount,
    session: AsyncSession,
) -> str:
    """
    Ensure the access token is valid, refreshing if expired.

    Used by both email and calendar routers.

    Returns:
        Valid (decrypted) access token.
    """
    access_token = decrypt_value(account.access_token)

    # Check if token expired
    if account.token_expiry and _utcnow() >= account.token_expiry:
        logger.info(f"Access token expired for {account.email}, refreshing...")
        refresh_token = decrypt_value(account.refresh_token)

        try:
            client_id = None
            client_secret = None

            # 1. Try stored credentials on the account
            if account.client_id and account.client_secret:
                client_id = decrypt_value(account.client_id)
                client_secret = decrypt_value(account.client_secret)
                logger.debug("Using stored OAuth credentials from account")

            # 2. Fallback: Try MCP Google Workspace server
            if not client_id or not client_secret:
                from app.services.mcp_service import get_mcp_service

                mcp_service = get_mcp_service()

                for server_id, server in mcp_service.servers.items():
                    if 'google' in server.name.lower() and 'workspace' in server.name.lower():
                        env = server.env or {}
                        cid = env.get('GOOGLE_OAUTH_CLIENT_ID', '')
                        csecret = env.get('GOOGLE_OAUTH_CLIENT_SECRET', '')

                        if is_value_encrypted(cid):
                            cid = decrypt_value(cid)
                        if is_value_encrypted(csecret):
                            csecret = decrypt_value(csecret)

                        if cid and csecret:
                            client_id = cid
                            client_secret = csecret
                            break

            if not client_id or not client_secret:
                raise HTTPException(
                    status_code=401,
                    detail="OAuth credentials not found. Please reconnect your account."
                )

            # Refresh token using OAuth service
            oauth_service = get_oauth_service()
            config = get_gmail_oauth_config(client_id, client_secret)

            new_tokens = await oauth_service.refresh_access_token(
                refresh_token,
                config,
            )

            # Update account with new tokens
            account.access_token = encrypt_value(new_tokens['access_token'])
            account.token_expiry = _utcnow() + timedelta(seconds=new_tokens['expires_in'])
            account.updated_at = _utcnow()
            session.add(account)
            await session.commit()

            logger.info(f"Access token refreshed for {account.email}")
            access_token = new_tokens['access_token']

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            raise HTTPException(
                status_code=401,
                detail="Access token expired. Please reconnect your account."
            )

    return access_token


async def get_gmail_service_for_account(
    account_id: str,
    session: AsyncSession,
) -> GmailService:
    """
    Get authenticated Gmail service for account.

    Handles token refresh if needed.
    """
    account = await session.get(EmailAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Email account not found")

    access_token = await ensure_valid_access_token(account, session)

    return GmailService(access_token)


# ============================================================
# OAuth Endpoints
# ============================================================


@router.post("/auth/initiate")
async def initiate_oauth(
    request: OAuthInitiateRequest,
) -> OAuthInitiateResponse:
    """
    Initiate Gmail OAuth flow.

    User should open the returned auth_url in browser.

    US-EMAIL-01: OAuth Gmail
    SEC-008: Credentials transmis dans le body POST (pas en query params).
    """
    oauth_service = get_oauth_service()
    config = get_gmail_oauth_config(request.client_id, request.client_secret)

    flow_data = oauth_service.initiate_flow('gmail', config)

    return OAuthInitiateResponse(**flow_data)


@router.post("/auth/callback")
async def handle_oauth_callback(
    request: OAuthCallbackRequest,
    session: AsyncSession = Depends(get_session),
) -> EmailAccountResponse:
    """
    Handle OAuth callback.

    Exchanges authorization code for tokens and creates/updates email account.

    US-EMAIL-01: OAuth Gmail
    """
    oauth_service = get_oauth_service()

    # Exchange code for tokens
    tokens = await oauth_service.handle_callback(
        request.state,
        request.code,
        request.error,
    )

    if not tokens.get('refresh_token'):
        raise HTTPException(
            status_code=400,
            detail="No refresh token received. Please revoke access and try again."
        )

    # Get user email via Gmail API
    gmail = GmailService(tokens['access_token'])
    profile = await gmail.get_profile()
    email_address = profile['emailAddress']

    # Check if account already exists
    statement = select(EmailAccount).where(EmailAccount.email == email_address)
    result = await session.execute(statement)
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing account
        existing.access_token = encrypt_value(tokens['access_token'])
        existing.refresh_token = encrypt_value(tokens['refresh_token'])
        existing.token_expiry = _utcnow() + timedelta(seconds=tokens['expires_in'])
        existing.scopes = json.dumps(tokens['scopes'])
        # Store OAuth credentials for token refresh
        if tokens.get('client_id'):
            existing.client_id = encrypt_value(tokens['client_id'])
        if tokens.get('client_secret'):
            existing.client_secret = encrypt_value(tokens['client_secret'])
        existing.updated_at = _utcnow()
        session.add(existing)
        await session.commit()
        await session.refresh(existing)
        account = existing
    else:
        # Create new account
        account = EmailAccount(
            email=email_address,
            access_token=encrypt_value(tokens['access_token']),
            refresh_token=encrypt_value(tokens['refresh_token']),
            token_expiry=_utcnow() + timedelta(seconds=tokens['expires_in']),
            scopes=json.dumps(tokens['scopes']),
            client_id=encrypt_value(tokens['client_id']) if tokens.get('client_id') else None,
            client_secret=encrypt_value(tokens['client_secret']) if tokens.get('client_secret') else None,
        )
        session.add(account)
        await session.commit()
        await session.refresh(account)

    logger.info(f"Email account {'updated' if existing else 'created'}: {email_address}")

    return EmailAccountResponse(
        id=account.id,
        email=account.email,
        provider=account.provider,
        scopes=json.loads(account.scopes),
        created_at=account.created_at,
        last_sync=account.last_sync,
    )


@router.get("/auth/callback-redirect", response_class=HTMLResponse)
async def handle_oauth_redirect(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """
    Handle Google's OAuth GET redirect.

    Google redirects here with ?code=xxx&state=xxx after user authorizes.
    Exchanges the code for tokens, creates/updates the account,
    then shows a success HTML page.
    """
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")

    if error:
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html><head><title>THERESE - Erreur OAuth</title>
        <style>body{{background:#0B1226;color:#E6EDF7;font-family:system-ui;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}}
        .card{{text-align:center;padding:2rem;border:1px solid #22D3EE33;border-radius:1rem;max-width:400px}}
        h1{{color:#E11D8D;font-size:1.5rem}}p{{color:#B6C7DA;margin:1rem 0}}</style></head>
        <body><div class="card"><h1>Erreur d'autorisation</h1><p>{error}</p><p>Tu peux fermer cette fenêtre et réessayer.</p></div></body></html>
        """, status_code=400)

    if not code or not state:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html><head><title>THERESE - Erreur</title>
        <style>body{background:#0B1226;color:#E6EDF7;font-family:system-ui;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}
        .card{text-align:center;padding:2rem;border:1px solid #22D3EE33;border-radius:1rem;max-width:400px}
        h1{color:#E11D8D;font-size:1.5rem}p{color:#B6C7DA}</style></head>
        <body><div class="card"><h1>Paramètres manquants</h1><p>Code ou state manquant dans la réponse Google.</p></div></body></html>
        """, status_code=400)

    try:
        oauth_service = get_oauth_service()
        tokens = await oauth_service.handle_callback(state, code, None)

        if not tokens.get('refresh_token'):
            return HTMLResponse(content="""
            <!DOCTYPE html>
            <html><head><title>THERESE - Erreur</title>
            <style>body{background:#0B1226;color:#E6EDF7;font-family:system-ui;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}
            .card{text-align:center;padding:2rem;border:1px solid #22D3EE33;border-radius:1rem;max-width:400px}
            h1{color:#E11D8D;font-size:1.5rem}p{color:#B6C7DA}</style></head>
            <body><div class="card"><h1>Pas de refresh token</h1><p>Révoque l'accès THÉRÈSE dans tes paramètres Google et réessaye.</p></div></body></html>
            """, status_code=400)

        # Get user email
        gmail = GmailService(tokens['access_token'])
        profile = await gmail.get_profile()
        email_address = profile['emailAddress']

        # Create or update account
        statement = select(EmailAccount).where(EmailAccount.email == email_address)
        result = await session.execute(statement)
        existing = result.scalar_one_or_none()

        if existing:
            existing.access_token = encrypt_value(tokens['access_token'])
            existing.refresh_token = encrypt_value(tokens['refresh_token'])
            existing.token_expiry = _utcnow() + timedelta(seconds=tokens['expires_in'])
            existing.scopes = json.dumps(tokens['scopes'])
            if tokens.get('client_id'):
                existing.client_id = encrypt_value(tokens['client_id'])
            if tokens.get('client_secret'):
                existing.client_secret = encrypt_value(tokens['client_secret'])
            existing.updated_at = _utcnow()
            session.add(existing)
            await session.commit()
            logger.info(f"Email account updated via redirect: {email_address}")
        else:
            account = EmailAccount(
                email=email_address,
                access_token=encrypt_value(tokens['access_token']),
                refresh_token=encrypt_value(tokens['refresh_token']),
                token_expiry=_utcnow() + timedelta(seconds=tokens['expires_in']),
                scopes=json.dumps(tokens['scopes']),
                client_id=encrypt_value(tokens['client_id']) if tokens.get('client_id') else None,
                client_secret=encrypt_value(tokens['client_secret']) if tokens.get('client_secret') else None,
            )
            session.add(account)
            await session.commit()
            logger.info(f"Email account created via redirect: {email_address}")

        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html><head><title>THERESE - Connexion réussie</title>
        <style>body{{background:#0B1226;color:#E6EDF7;font-family:system-ui;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}}
        .card{{text-align:center;padding:2rem;border:1px solid #22D3EE33;border-radius:1rem;max-width:400px}}
        h1{{color:#22D3EE;font-size:1.5rem}}p{{color:#B6C7DA;margin:1rem 0}}
        .email{{color:#22D3EE;font-weight:600}}</style></head>
        <body><div class="card"><h1>Connexion réussie !</h1><p>Le compte <span class="email">{email_address}</span> est connecté à THERESE.</p><p>Tu peux fermer cette fenêtre.</p></div></body></html>
        """)
    except Exception as e:
        logger.error(f"OAuth redirect callback failed: {e}")
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html><head><title>THERESE - Erreur</title>
        <style>body{{background:#0B1226;color:#E6EDF7;font-family:system-ui;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}}
        .card{{text-align:center;padding:2rem;border:1px solid #22D3EE33;border-radius:1rem;max-width:400px}}
        h1{{color:#E11D8D;font-size:1.5rem}}p{{color:#B6C7DA}}</style></head>
        <body><div class="card"><h1>Erreur</h1><p>{str(e)}</p><p>Tu peux fermer cette fenêtre et réessayer.</p></div></body></html>
        """, status_code=500)


@router.post("/auth/reauthorize/{account_id}")
async def reauthorize_account(
    account_id: str,
    session: AsyncSession = Depends(get_session),
) -> OAuthInitiateResponse:
    """
    Re-authorize an existing account with expired/revoked token.

    Uses stored client_id/client_secret to initiate a new OAuth flow.
    Falls back to MCP Google Workspace credentials if needed.
    """
    account = await session.get(EmailAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    client_id = None
    client_secret = None

    # 1. Try stored credentials on the account
    if account.client_id and account.client_secret:
        client_id = decrypt_value(account.client_id)
        client_secret = decrypt_value(account.client_secret)

    # 2. Fallback: MCP Google Workspace
    if not client_id or not client_secret:
        try:
            from app.services.mcp_service import get_mcp_service
            mcp_service = get_mcp_service()
            for server_id, server in mcp_service.servers.items():
                if 'google' in server.name.lower() and 'workspace' in server.name.lower():
                    env = server.env or {}
                    cid = env.get('GOOGLE_OAUTH_CLIENT_ID', '')
                    csecret = env.get('GOOGLE_OAUTH_CLIENT_SECRET', '')
                    if is_value_encrypted(cid):
                        cid = decrypt_value(cid)
                    if is_value_encrypted(csecret):
                        csecret = decrypt_value(csecret)
                    if cid and csecret:
                        client_id = cid
                        client_secret = csecret
                        break
        except Exception as e:
            logger.warning(f"Failed to get MCP credentials: {e}")

    if not client_id or not client_secret:
        raise HTTPException(
            status_code=400,
            detail="Aucun identifiant OAuth trouvé. Reconfigure le compte via le wizard."
        )

    oauth_service = get_oauth_service()
    config = get_gmail_oauth_config(client_id, client_secret)
    flow_data = oauth_service.initiate_flow('gmail', config)

    logger.info(f"Re-authorization initiated for {account.email}")

    return OAuthInitiateResponse(**flow_data)


@router.get("/auth/status")
async def get_auth_status(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Get OAuth connection status.

    US-EMAIL-01: OAuth Gmail
    """
    statement = select(EmailAccount)
    result = await session.execute(statement)
    accounts = result.scalars().all()

    return {
        'connected': len(accounts) > 0,
        'accounts': [
            {
                'id': acc.id,
                'email': acc.email,
                'provider': acc.provider,
                'last_sync': acc.last_sync.isoformat() if acc.last_sync else None,
            }
            for acc in accounts
        ],
    }


@router.post("/auth/update-credentials/{account_id}")
async def update_oauth_credentials(
    account_id: str,
    request: OAuthInitiateRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Update OAuth credentials for an existing account.

    Stores client_id and client_secret (encrypted) for token refresh.
    Then attempts to refresh the access token immediately.
    """
    account = await session.get(EmailAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Store credentials
    account.client_id = encrypt_value(request.client_id)
    account.client_secret = encrypt_value(request.client_secret)
    account.updated_at = _utcnow()
    session.add(account)
    await session.commit()

    # Try to refresh token immediately
    try:
        access_token = await ensure_valid_access_token(account, session)
        return {
            "status": "ok",
            "message": "Credentials updated and token refreshed",
            "email": account.email,
        }
    except HTTPException:
        return {
            "status": "credentials_saved",
            "message": "Credentials saved but token refresh failed. You may need to re-authorize.",
            "email": account.email,
        }


@router.delete("/auth/disconnect/{account_id}")
async def disconnect_account(
    account_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Disconnect email account.

    Deletes account and all synced messages.

    US-EMAIL-01: OAuth Gmail
    """
    account = await session.get(EmailAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # SEC-008: Revoquer le token OAuth Google avant suppression
    if account.provider == "gmail" and account.access_token:
        try:
            import httpx
            access_token = decrypt_value(account.access_token)
            async with httpx.AsyncClient(timeout=10.0) as client:
                revoke_response = await client.post(
                    "https://oauth2.googleapis.com/revoke",
                    params={"token": access_token},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                if revoke_response.status_code == 200:
                    logger.info(f"OAuth token revoked for {account.email}")
                else:
                    logger.warning(
                        f"OAuth revocation returned {revoke_response.status_code} for {account.email}. "
                        f"Continuing with account deletion."
                    )
        except Exception as e:
            # Ne pas bloquer la deconnexion si la revocation echoue
            logger.warning(f"Failed to revoke OAuth token for {account.email}: {e}. Continuing with deletion.")

    # Delete messages
    statement = select(EmailMessage).where(EmailMessage.account_id == account_id)
    result = await session.execute(statement)
    messages = result.scalars().all()
    for msg in messages:
        await session.delete(msg)

    # Delete account
    await session.delete(account)
    await session.commit()

    logger.info(f"Disconnected email account: {account.email}")

    return {"deleted": True, "account_id": account_id}


# ============================================================
# IMAP/SMTP Endpoints (Local First)
# ============================================================


@router.post("/auth/imap-setup")
async def setup_imap_account(
    request: ImapSetupRequest,
    session: AsyncSession = Depends(get_session),
) -> EmailAccountResponse:
    """
    Configure un compte IMAP/SMTP.

    Local First - pas besoin d'OAuth, juste les credentials IMAP.
    """
    # Check if account already exists
    statement = select(EmailAccount).where(EmailAccount.email == request.email)
    result = await session.execute(statement)
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing
        existing.provider = "imap"
        existing.imap_host = request.imap_host
        existing.imap_port = request.imap_port
        existing.imap_username = request.email
        existing.imap_password = encrypt_value(request.password)
        existing.smtp_host = request.smtp_host
        existing.smtp_port = request.smtp_port
        existing.smtp_use_tls = request.smtp_use_tls
        existing.updated_at = _utcnow()
        session.add(existing)
        await session.commit()
        await session.refresh(existing)
        account = existing
    else:
        account = EmailAccount(
            email=request.email,
            provider="imap",
            imap_host=request.imap_host,
            imap_port=request.imap_port,
            imap_username=request.email,
            imap_password=encrypt_value(request.password),
            smtp_host=request.smtp_host,
            smtp_port=request.smtp_port,
            smtp_use_tls=request.smtp_use_tls,
        )
        session.add(account)
        await session.commit()
        await session.refresh(account)

    logger.info(f"IMAP account {'updated' if existing else 'created'}: {request.email}")

    return EmailAccountResponse(
        id=account.id,
        email=account.email,
        provider=account.provider,
        scopes=[],
        created_at=account.created_at,
        last_sync=account.last_sync,
    )


@router.post("/auth/test-connection")
async def test_email_connection(
    request: ImapTestRequest,
) -> dict:
    """
    Teste la connexion IMAP/SMTP.

    Retourne le status de connexion sans sauvegarder.
    """
    try:
        provider = get_email_provider(
            provider_type="imap",
            email_address=request.email,
            password=request.password,
            imap_host=request.imap_host,
            imap_port=request.imap_port,
            smtp_host=request.smtp_host,
            smtp_port=request.smtp_port,
            smtp_use_tls=request.smtp_use_tls,
        )
        result = await provider.test_connection()
        return result
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return {
            "success": False,
            "message": f"Echec de connexion: {str(e)}",
        }


@router.get("/providers")
async def list_email_providers() -> list[dict]:
    """
    Liste les providers email preconfigures (IMAP/SMTP).

    Retourne les configurations pour les providers courants
    (Gmail IMAP, Outlook, Yahoo, Fastmail, etc.)
    """
    return list_common_providers()


# ============================================================
# Messages Endpoints
# ============================================================


@router.get("/messages")
async def list_messages(
    account_id: str = Query(...),
    max_results: int = Query(50, ge=1, le=500),
    page_token: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
    label_ids: Optional[str] = Query(None),  # Comma-separated
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    List messages from email account (Gmail or IMAP).

    US-EMAIL-02: Lire emails
    """
    account = await session.get(EmailAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Email account not found")

    # Route based on provider
    if account.provider == "imap":
        return await _list_messages_imap(account, max_results, query)
    else:
        return await _list_messages_gmail(account_id, session, max_results, page_token, query, label_ids)


async def _list_messages_gmail(
    account_id: str,
    session: AsyncSession,
    max_results: int,
    page_token: Optional[str],
    query: Optional[str],
    label_ids: Optional[str],
) -> dict:
    """List messages via Gmail API."""
    gmail = await get_gmail_service_for_account(account_id, session)

    label_ids_list = label_ids.split(',') if label_ids else None

    result = await gmail.list_messages(
        max_results=max_results,
        page_token=page_token,
        query=query,
        label_ids=label_ids_list,
    )

    # Enrich with metadata for each message
    enriched_messages = []
    for msg in result.get('messages', []):
        try:
            msg_detail = await gmail.get_message(msg['id'], format='metadata')
            headers = {h['name']: h['value'] for h in msg_detail.get('payload', {}).get('headers', [])}

            enriched_messages.append({
                'id': msg['id'],
                'threadId': msg.get('threadId'),
                'snippet': msg_detail.get('snippet', ''),
                'subject': headers.get('Subject', '(No subject)'),
                'from': headers.get('From', ''),
                'date': headers.get('Date', ''),
                'labelIds': msg_detail.get('labelIds', []),
            })
        except Exception as e:
            logger.error(f"Failed to get message {msg['id']}: {e}")
            enriched_messages.append({
                'id': msg['id'],
                'threadId': msg.get('threadId'),
                'error': str(e)
            })

    return {
        'messages': enriched_messages,
        'nextPageToken': result.get('nextPageToken'),
        'resultSizeEstimate': result.get('resultSizeEstimate'),
    }


async def _list_messages_imap(
    account: EmailAccount,
    max_results: int,
    query: Optional[str],
) -> dict:
    """List messages via IMAP provider."""
    provider = get_email_provider(
        provider_type="imap",
        email_address=account.email,
        password=decrypt_value(account.imap_password),
        imap_host=account.imap_host,
        imap_port=account.imap_port,
        smtp_host=account.smtp_host,
        smtp_port=account.smtp_port,
        smtp_use_tls=account.smtp_use_tls,
    )

    messages = await provider.list_messages(
        max_results=max_results,
        query=query,
    )

    # Convert DTOs to same format as Gmail endpoint
    enriched = []
    for msg in messages:
        enriched.append({
            'id': msg.id,
            'threadId': msg.thread_id or msg.id,
            'snippet': msg.snippet or '',
            'subject': msg.subject or '(Pas de sujet)',
            'from': f"{msg.from_name or ''} <{msg.from_email}>".strip(),
            'date': msg.date.isoformat() if msg.date else '',
            'labelIds': msg.labels or [],
        })

    return {
        'messages': enriched,
        'nextPageToken': None,
        'resultSizeEstimate': len(enriched),
    }


@router.get("/messages/stats")
async def get_email_stats(
    account_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Recupere les statistiques d'emails par priorite.

    US-EMAIL-12: Dashboard priorites

    NOTE: This route MUST be defined before /messages/{message_id}
    to avoid FastAPI matching 'stats' as a message_id parameter.
    """
    from sqlalchemy import func

    # High priority (unread)
    statement_high = select(func.count(EmailMessage.id)).where(
        EmailMessage.account_id == account_id,
        EmailMessage.priority == 'high',
        EmailMessage.is_read == False,
    )
    result_high = await session.execute(statement_high)
    high_count = result_high.scalar_one()

    # Medium priority (unread)
    statement_medium = select(func.count(EmailMessage.id)).where(
        EmailMessage.account_id == account_id,
        EmailMessage.priority == 'medium',
        EmailMessage.is_read == False,
    )
    result_medium = await session.execute(statement_medium)
    medium_count = result_medium.scalar_one()

    # Low priority (unread)
    statement_low = select(func.count(EmailMessage.id)).where(
        EmailMessage.account_id == account_id,
        EmailMessage.priority == 'low',
        EmailMessage.is_read == False,
    )
    result_low = await session.execute(statement_low)
    low_count = result_low.scalar_one()

    # Total unread
    total_unread = high_count + medium_count + low_count

    # Total messages
    statement_total = select(func.count(EmailMessage.id)).where(
        EmailMessage.account_id == account_id,
    )
    result_total = await session.execute(statement_total)
    total_count = result_total.scalar_one()

    return {
        'high': high_count,
        'medium': medium_count,
        'low': low_count,
        'total_unread': total_unread,
        'total': total_count,
    }


@router.get("/messages/{message_id}")
async def get_message(
    message_id: str,
    account_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Get message details.

    US-EMAIL-02: Lire emails
    """
    # Check local cache first
    cached = await session.get(EmailMessage, message_id)
    if cached and cached.account_id == account_id:
        return {
            'id': cached.id,
            'thread_id': cached.thread_id,
            'subject': cached.subject,
            'from_email': cached.from_email,
            'from_name': cached.from_name,
            'to_emails': json.loads(cached.to_emails),
            'date': cached.date.isoformat(),
            'labels': json.loads(cached.labels),
            'is_read': cached.is_read,
            'is_starred': cached.is_starred,
            'body_plain': cached.body_plain,
            'body_html': cached.body_html,
        }

    # Fetch from Gmail
    gmail = await get_gmail_service_for_account(account_id, session)
    message = await gmail.get_message(message_id)

    # Store in cache
    formatted = format_message_for_storage(message)
    formatted['account_id'] = account_id

    db_message = EmailMessage(**formatted)
    session.add(db_message)
    await session.commit()

    return message


@router.post("/messages")
async def send_email(
    request: SendEmailRequest,
    account_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Send an email (Gmail or IMAP/SMTP).

    US-EMAIL-03: Envoyer email
    """
    account = await session.get(EmailAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Email account not found")

    if account.provider == "imap":
        provider = get_email_provider(
            provider_type="imap",
            email_address=account.email,
            password=decrypt_value(account.imap_password),
            imap_host=account.imap_host,
            imap_port=account.imap_port,
            smtp_host=account.smtp_host,
            smtp_port=account.smtp_port,
            smtp_use_tls=account.smtp_use_tls,
        )
        from app.services.email.base_provider import SendEmailRequest as ProviderSendRequest
        send_req = ProviderSendRequest(
            to=request.to,
            subject=request.subject,
            body=request.body,
            cc=request.cc or [],
            bcc=request.bcc or [],
            is_html=request.html,
        )
        message_id = await provider.send_message(send_req)
        return {"id": message_id, "labelIds": ["SENT"]}
    else:
        gmail = await get_gmail_service_for_account(account_id, session)
        result = await gmail.send_message(
            to=request.to,
            subject=request.subject,
            body=request.body,
            cc=request.cc,
            bcc=request.bcc,
            html=request.html,
        )
        return result


@router.post("/messages/draft")
async def create_draft(
    request: SendEmailRequest,
    account_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Create a draft email.

    US-EMAIL-04: Brouillons
    """
    gmail = await get_gmail_service_for_account(account_id, session)

    result = await gmail.create_draft(
        to=request.to,
        subject=request.subject,
        body=request.body,
        cc=request.cc,
        bcc=request.bcc,
        html=request.html,
    )

    return result


@router.put("/messages/{message_id}")
async def modify_message(
    message_id: str,
    request: ModifyMessageRequest,
    account_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Modify message labels (mark read/unread, star, etc.).

    US-EMAIL-02: Lire emails
    """
    gmail = await get_gmail_service_for_account(account_id, session)

    result = await gmail.modify_message(
        message_id=message_id,
        add_label_ids=request.add_label_ids,
        remove_label_ids=request.remove_label_ids,
    )

    # Update cache
    cached = await session.get(EmailMessage, message_id)
    if cached:
        labels = json.loads(cached.labels)
        if request.add_label_ids:
            labels.extend(request.add_label_ids)
        if request.remove_label_ids:
            labels = [l for l in labels if l not in request.remove_label_ids]
        cached.labels = json.dumps(list(set(labels)))
        cached.is_read = 'UNREAD' not in labels
        cached.is_starred = 'STARRED' in labels
        session.add(cached)
        await session.commit()

    return result


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: str,
    account_id: str = Query(...),
    permanent: bool = Query(False),
    session: AsyncSession = Depends(get_session),
):
    """
    Delete message (trash or permanent).

    US-EMAIL-02: Lire emails
    """
    gmail = await get_gmail_service_for_account(account_id, session)

    if permanent:
        await gmail.delete_message(message_id)
    else:
        await gmail.trash_message(message_id)

    # Remove from cache
    cached = await session.get(EmailMessage, message_id)
    if cached:
        await session.delete(cached)
        await session.commit()

    return {"deleted": True, "message_id": message_id, "permanent": permanent}


# ============================================================
# Labels Endpoints
# ============================================================


@router.get("/labels")
async def list_labels(
    account_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    """
    List email labels/folders (Gmail labels or IMAP folders).

    US-EMAIL-05: Labels
    """
    account = await session.get(EmailAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Email account not found")

    if account.provider == "imap":
        provider = get_email_provider(
            provider_type="imap",
            email_address=account.email,
            password=decrypt_value(account.imap_password),
            imap_host=account.imap_host,
            imap_port=account.imap_port,
            smtp_host=account.smtp_host,
            smtp_port=account.smtp_port,
            smtp_use_tls=account.smtp_use_tls,
        )
        folders = await provider.list_folders()
        return [
            {
                "id": f.id,
                "name": f.name,
                "type": f.type,
                "messagesTotal": f.messages_total,
                "messagesUnread": f.messages_unread,
            }
            for f in folders
        ]
    else:
        gmail = await get_gmail_service_for_account(account_id, session)
        labels = await gmail.list_labels()
        return labels


@router.post("/labels")
async def create_label(
    request: LabelCreateRequest,
    account_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Create a new label.

    US-EMAIL-05: Labels
    """
    gmail = await get_gmail_service_for_account(account_id, session)
    label = await gmail.create_label(request.name)
    return label


@router.put("/labels/{label_id}")
async def update_label(
    label_id: str,
    request: LabelCreateRequest,
    account_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Update label name.

    US-EMAIL-05: Labels
    """
    gmail = await get_gmail_service_for_account(account_id, session)
    label = await gmail.update_label(label_id, request.name)
    return label


@router.delete("/labels/{label_id}")
async def delete_label(
    label_id: str,
    account_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a label.

    US-EMAIL-05: Labels
    """
    gmail = await get_gmail_service_for_account(account_id, session)
    await gmail.delete_label(label_id)
    return {"deleted": True, "label_id": label_id}


# ============================================================
# Smart Email Features Endpoints
# ============================================================


class ClassifyEmailRequest(BaseModel):
    """Classify email request."""
    force_reclassify: bool = False  # Force re-classification même si déjà classé


class GenerateResponseRequest(BaseModel):
    """Generate email response request."""
    tone: str = 'formal'  # formal | friendly | neutral
    length: str = 'medium'  # short | medium | detailed


class UpdatePriorityRequest(BaseModel):
    """Update email priority request."""
    priority: str  # 'high' | 'medium' | 'low'


@router.post("/messages/{message_id}/classify")
async def classify_email(
    message_id: str,
    request: ClassifyEmailRequest,
    account_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Classifie un email par priorité (Rouge/Orange/Vert).

    US-EMAIL-08: Priorisation visuelle
    US-EMAIL-10: Classement automatique
    """
    from app.services.email_classifier_v2 import EmailClassifierV2

    # Get message from DB or fetch from Gmail
    message = await session.get(EmailMessage, message_id)

    if not message:
        # Message not in DB, fetch from Gmail
        gmail = await get_gmail_service_for_account(account_id, session)
        gmail_msg = await gmail.get_message(message_id)

        # Store in cache
        formatted = format_message_for_storage(gmail_msg)
        formatted['account_id'] = account_id
        message = EmailMessage(**formatted)
        session.add(message)
        await session.commit()
        await session.refresh(message)

    if message.account_id != account_id:
        raise HTTPException(status_code=404, detail="Message not found")

    # Skip if already classified (unless force)
    if message.priority and not request.force_reclassify:
        return {
            'message_id': message_id,
            'priority': message.priority,
            'score': message.priority_score,
            'reason': message.priority_reason,
            'cached': True,
        }

    # Get CRM contact score if exists
    contact_score = None
    try:
        from app.services.qdrant import get_qdrant_service
        qdrant = get_qdrant_service()
        results = qdrant.search(
            query=f"{message.from_name} {message.from_email}",
            entity_type='contact',
            limit=1,
        )
        if results:
            # Assume score 0-100 is stored in metadata
            contact_score = results[0].payload.get('score', None)
    except Exception as e:
        logger.warning(f"Failed to get CRM score for {message.from_email}: {e}")

    # Classify
    labels_list = json.loads(message.labels) if message.labels else []
    result = EmailClassifierV2.classify(
        subject=message.subject or '',
        from_email=message.from_email,
        from_name=message.from_name or '',
        snippet=message.snippet or '',
        labels=labels_list,
        has_attachments=message.has_attachments,
        date=message.date,
        contact_score=contact_score,
    )

    # Update DB
    message.priority = result.priority
    message.priority_score = result.score
    message.priority_reason = result.reason
    message.category = result.category
    session.add(message)
    await session.commit()

    return {
        'message_id': message_id,
        'priority': result.priority,
        'category': result.category,
        'score': result.score,
        'reason': result.reason,
        'signals': result.signals,
        'cached': False,
    }


@router.post("/messages/{message_id}/generate-response")
async def generate_email_response(
    message_id: str,
    request: GenerateResponseRequest,
    account_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Génère une proposition de réponse intelligente via LLM.

    US-EMAIL-09: Génération de réponse IA
    """
    from app.services.email_response_generator import EmailResponseGenerator

    # Get message from DB
    message = await session.get(EmailMessage, message_id)
    if not message or message.account_id != account_id:
        raise HTTPException(status_code=404, detail="Message not found")

    # Get CRM contact context if exists
    contact_context = None
    try:
        from app.services.qdrant import get_qdrant_service
        qdrant = get_qdrant_service()
        results = qdrant.search(
            query=f"{message.from_name} {message.from_email}",
            entity_type='contact',
            limit=1,
        )
        if results:
            payload = results[0].payload
            contact_context = f"""Contact CRM :
- Nom : {payload.get('name', 'N/A')}
- Entreprise : {payload.get('company', 'N/A')}
- Email : {payload.get('email', 'N/A')}
- Téléphone : {payload.get('phone', 'N/A')}
- Score : {payload.get('score', 'N/A')}/100
- Tags : {payload.get('tags', 'N/A')}
- Notes : {payload.get('notes', 'N/A')}"""
    except Exception as e:
        logger.warning(f"Failed to get CRM context for {message.from_email}: {e}")

    # Get thread context (previous emails in thread)
    thread_context = None
    try:
        statement = select(EmailMessage).where(
            EmailMessage.thread_id == message.thread_id,
            EmailMessage.id != message_id,
        ).order_by(EmailMessage.date.desc()).limit(3)
        result = await session.execute(statement)
        thread_messages = result.scalars().all()

        if thread_messages:
            thread_lines = []
            for tm in thread_messages:
                thread_lines.append(f"[{tm.date.strftime('%Y-%m-%d %H:%M')}] De: {tm.from_name or tm.from_email}")
                thread_lines.append(f"Sujet: {tm.subject}")
                thread_lines.append(f"{tm.snippet or tm.body_plain[:200]}")
                thread_lines.append("---")
            thread_context = "\n".join(thread_lines)
    except Exception as e:
        logger.warning(f"Failed to get thread context for {message_id}: {e}")

    # Generate response
    response_text = await EmailResponseGenerator.generate_response(
        subject=message.subject or '',
        from_name=message.from_name or message.from_email,
        from_email=message.from_email,
        body=message.body_plain or message.snippet or '',
        tone=request.tone,
        length=request.length,
        contact_context=contact_context,
        thread_context=thread_context,
    )

    return {
        'message_id': message_id,
        'draft': response_text,
        'tone': request.tone,
        'length': request.length,
    }


@router.patch("/messages/{message_id}/priority")
async def update_message_priority(
    message_id: str,
    request: UpdatePriorityRequest,
    account_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Change manuellement la priorité d'un email.

    US-EMAIL-10: Classement automatique
    """
    # Validate priority
    if request.priority not in ['high', 'medium', 'low']:
        raise HTTPException(status_code=400, detail="Invalid priority. Must be 'high', 'medium', or 'low'.")

    # Get message from DB
    message = await session.get(EmailMessage, message_id)
    if not message or message.account_id != account_id:
        raise HTTPException(status_code=404, detail="Message not found")

    # Update priority
    message.priority = request.priority
    message.priority_reason = "Défini manuellement par l'utilisateur"
    # Keep score or set default
    if not message.priority_score:
        score_map = {'high': 75, 'medium': 40, 'low': 10}
        message.priority_score = score_map[request.priority]

    session.add(message)
    await session.commit()

    return {
        'message_id': message_id,
        'priority': message.priority,
        'score': message.priority_score,
        'reason': message.priority_reason,
    }



# NOTE: get_email_stats (GET /messages/stats) has been moved above
# get_message (GET /messages/{message_id}) to avoid FastAPI route shadowing.
