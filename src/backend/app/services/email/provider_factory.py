"""
THERESE v2 - Email Provider Factory

Factory pattern for creating email providers based on configuration.
Part of the "Local First" architecture.
"""

import logging
from typing import Literal, Optional

from app.services.email.base_provider import EmailProvider
from app.services.email.gmail_provider import GmailProvider
from app.services.email.imap_smtp_provider import ImapSmtpProvider

logger = logging.getLogger(__name__)


EmailProviderType = Literal["gmail", "imap"]


def get_email_provider(
    provider_type: EmailProviderType,
    # Gmail OAuth
    access_token: Optional[str] = None,
    # IMAP/SMTP config
    email_address: Optional[str] = None,
    password: Optional[str] = None,
    imap_host: Optional[str] = None,
    imap_port: int = 993,
    smtp_host: Optional[str] = None,
    smtp_port: int = 587,
    use_ssl: bool = True,
    smtp_use_tls: bool = True,
) -> EmailProvider:
    """
    Create an email provider based on configuration.

    Args:
        provider_type: Type of provider ('gmail' or 'imap')

        For Gmail:
            access_token: OAuth2 access token

        For IMAP/SMTP:
            email_address: Login email
            password: Password or app password
            imap_host: IMAP server hostname
            imap_port: IMAP port (default 993)
            smtp_host: SMTP server hostname
            smtp_port: SMTP port (default 587)
            use_ssl: Use SSL for IMAP
            smtp_use_tls: Use STARTTLS for SMTP

    Returns:
        EmailProvider instance

    Raises:
        ValueError: If required parameters are missing
    """
    if provider_type == "gmail":
        if not access_token:
            raise ValueError("Gmail provider requires access_token")
        return GmailProvider(access_token=access_token)

    elif provider_type == "imap":
        if not email_address or not password or not imap_host:
            raise ValueError("IMAP provider requires email_address, password, and imap_host")

        return ImapSmtpProvider(
            email_address=email_address,
            password=password,
            imap_host=imap_host,
            imap_port=imap_port,
            smtp_host=smtp_host or imap_host,
            smtp_port=smtp_port,
            use_ssl=use_ssl,
            smtp_use_tls=smtp_use_tls,
        )

    else:
        raise ValueError(f"Unknown provider type: {provider_type}")


# Common IMAP/SMTP server configurations
COMMON_PROVIDERS = {
    "gmail": {
        "imap_host": "imap.gmail.com",
        "imap_port": 993,
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "use_ssl": True,
        "smtp_use_tls": True,
        "note": "Requires App Password with 2FA enabled",
    },
    "outlook": {
        "imap_host": "outlook.office365.com",
        "imap_port": 993,
        "smtp_host": "smtp.office365.com",
        "smtp_port": 587,
        "use_ssl": True,
        "smtp_use_tls": True,
        "note": "Works with Microsoft 365 accounts",
    },
    "yahoo": {
        "imap_host": "imap.mail.yahoo.com",
        "imap_port": 993,
        "smtp_host": "smtp.mail.yahoo.com",
        "smtp_port": 587,
        "use_ssl": True,
        "smtp_use_tls": True,
        "note": "Requires App Password",
    },
    "fastmail": {
        "imap_host": "imap.fastmail.com",
        "imap_port": 993,
        "smtp_host": "smtp.fastmail.com",
        "smtp_port": 587,
        "use_ssl": True,
        "smtp_use_tls": True,
        "note": "Requires App Password",
    },
    "protonmail": {
        "imap_host": "127.0.0.1",  # ProtonMail Bridge
        "imap_port": 1143,
        "smtp_host": "127.0.0.1",
        "smtp_port": 1025,
        "use_ssl": False,
        "smtp_use_tls": False,
        "note": "Requires ProtonMail Bridge application",
    },
    "icloud": {
        "imap_host": "imap.mail.me.com",
        "imap_port": 993,
        "smtp_host": "smtp.mail.me.com",
        "smtp_port": 587,
        "use_ssl": True,
        "smtp_use_tls": True,
        "note": "Requires App-Specific Password",
    },
    "zoho": {
        "imap_host": "imap.zoho.com",
        "imap_port": 993,
        "smtp_host": "smtp.zoho.com",
        "smtp_port": 587,
        "use_ssl": True,
        "smtp_use_tls": True,
    },
    "ovh": {
        "imap_host": "ssl0.ovh.net",
        "imap_port": 993,
        "smtp_host": "ssl0.ovh.net",
        "smtp_port": 587,
        "use_ssl": True,
        "smtp_use_tls": True,
    },
    "infomaniak": {
        "imap_host": "mail.infomaniak.com",
        "imap_port": 993,
        "smtp_host": "mail.infomaniak.com",
        "smtp_port": 587,
        "use_ssl": True,
        "smtp_use_tls": True,
    },
}


def get_provider_config(provider_name: str) -> dict:
    """
    Get pre-configured settings for common email providers.

    Args:
        provider_name: Name of the provider (gmail, outlook, yahoo, etc.)

    Returns:
        Dict with IMAP/SMTP configuration

    Raises:
        KeyError: If provider is not in the list
    """
    return COMMON_PROVIDERS[provider_name.lower()]


def list_common_providers() -> list[dict]:
    """
    List all pre-configured email providers.

    Returns:
        List of provider configs with names
    """
    return [
        {"name": name, **config}
        for name, config in COMMON_PROVIDERS.items()
    ]
