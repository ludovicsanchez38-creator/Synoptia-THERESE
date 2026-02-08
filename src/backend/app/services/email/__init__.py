"""
THERESE v2 - Email Services Package

Multi-provider email support (Gmail OAuth, IMAP/SMTP).
Part of the "Local First" architecture.
"""

from app.services.email.base_provider import (
    EmailAttachmentDTO,
    EmailFolderDTO,
    EmailMessageDTO,
    EmailProvider,
    SendEmailRequest,
)
from app.services.email.provider_factory import EmailProviderType, get_email_provider

__all__ = [
    "EmailProvider",
    "EmailMessageDTO",
    "EmailFolderDTO",
    "EmailAttachmentDTO",
    "SendEmailRequest",
    "get_email_provider",
    "EmailProviderType",
]
