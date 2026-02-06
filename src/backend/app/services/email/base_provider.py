"""
THERESE v2 - Email Provider Abstract Interface

Defines the contract for email providers (Gmail, IMAP/SMTP).
Part of the "Local First" architecture.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


@dataclass
class EmailAttachmentDTO:
    """Data Transfer Object for email attachments."""
    filename: str
    content_type: str
    size: int
    content: bytes | None = None  # Only populated when explicitly requested
    attachment_id: str | None = None  # Provider-specific ID


@dataclass
class EmailMessageDTO:
    """Data Transfer Object for email messages."""
    id: str
    thread_id: str | None = None
    subject: str | None = None
    snippet: str | None = None

    # Sender
    from_email: str = ""
    from_name: str | None = None

    # Recipients
    to_emails: list[str] = field(default_factory=list)
    cc_emails: list[str] = field(default_factory=list)
    bcc_emails: list[str] = field(default_factory=list)

    # Timestamps
    date: datetime | None = None

    # Flags
    is_read: bool = False
    is_starred: bool = False
    is_important: bool = False
    is_draft: bool = False

    # Content
    body_plain: str | None = None
    body_html: str | None = None

    # Attachments
    has_attachments: bool = False
    attachment_count: int = 0
    attachments: list[EmailAttachmentDTO] = field(default_factory=list)

    # Labels/Folders
    labels: list[str] = field(default_factory=list)  # Gmail labels or IMAP folders

    # Size
    size_bytes: int = 0


@dataclass
class EmailFolderDTO:
    """Data Transfer Object for email folders/labels."""
    id: str
    name: str
    type: Literal["system", "user"] = "user"
    message_count: int = 0
    unread_count: int = 0
    color: str | None = None

    # IMAP-specific
    path: str | None = None  # Full IMAP folder path
    delimiter: str | None = None  # IMAP hierarchy delimiter


@dataclass
class SendEmailRequest:
    """Request to send an email."""
    to: list[str]
    subject: str
    body: str
    cc: list[str] = field(default_factory=list)
    bcc: list[str] = field(default_factory=list)
    is_html: bool = False
    attachments: list[tuple[str, bytes, str]] = field(default_factory=list)  # (filename, content, content_type)
    reply_to_message_id: str | None = None
    in_reply_to: str | None = None
    references: str | None = None


class EmailProvider(ABC):
    """
    Abstract base class for email providers.

    Defines the contract that all email providers (Gmail, IMAP/SMTP) must implement.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'gmail', 'imap')."""
        pass

    @property
    def supports_labels(self) -> bool:
        """Whether the provider supports labels (Gmail-style) vs folders (IMAP)."""
        return False

    @property
    def supports_threads(self) -> bool:
        """Whether the provider supports email threading."""
        return False

    @property
    def supports_search(self) -> bool:
        """Whether the provider supports server-side search."""
        return True

    # ============================================================
    # Message Operations
    # ============================================================

    @abstractmethod
    async def list_messages(
        self,
        folder: str | None = None,
        max_results: int = 50,
        page_token: str | None = None,
        query: str | None = None,
        unread_only: bool = False,
    ) -> tuple[list[EmailMessageDTO], str | None]:
        """
        List messages from a folder.

        Args:
            folder: Folder/label to list from (None for inbox)
            max_results: Maximum number of messages to return
            page_token: Pagination token
            query: Search query (provider-specific syntax)
            unread_only: Only return unread messages

        Returns:
            Tuple of (messages, next_page_token)
        """
        pass

    @abstractmethod
    async def get_message(
        self,
        message_id: str,
        include_body: bool = True,
        include_attachments: bool = False,
    ) -> EmailMessageDTO:
        """
        Get a single message by ID.

        Args:
            message_id: Provider-specific message ID
            include_body: Whether to include the message body
            include_attachments: Whether to include attachment content

        Returns:
            EmailMessageDTO with message details
        """
        pass

    @abstractmethod
    async def send_message(self, request: SendEmailRequest) -> str:
        """
        Send an email.

        Args:
            request: SendEmailRequest with message details

        Returns:
            Sent message ID
        """
        pass

    @abstractmethod
    async def create_draft(self, request: SendEmailRequest) -> str:
        """
        Create a draft email.

        Args:
            request: SendEmailRequest with message details

        Returns:
            Draft message ID
        """
        pass

    @abstractmethod
    async def modify_message(
        self,
        message_id: str,
        add_labels: list[str] | None = None,
        remove_labels: list[str] | None = None,
        mark_read: bool | None = None,
        mark_starred: bool | None = None,
    ) -> EmailMessageDTO:
        """
        Modify message labels/flags.

        Args:
            message_id: Message ID
            add_labels: Labels to add
            remove_labels: Labels to remove
            mark_read: Set read status
            mark_starred: Set starred status

        Returns:
            Updated EmailMessageDTO
        """
        pass

    @abstractmethod
    async def delete_message(self, message_id: str, permanent: bool = False) -> None:
        """
        Delete a message.

        Args:
            message_id: Message ID
            permanent: If True, permanently delete; otherwise move to trash
        """
        pass

    @abstractmethod
    async def move_message(self, message_id: str, destination_folder: str) -> EmailMessageDTO:
        """
        Move a message to another folder.

        Args:
            message_id: Message ID
            destination_folder: Target folder/label

        Returns:
            Updated EmailMessageDTO
        """
        pass

    # ============================================================
    # Folder/Label Operations
    # ============================================================

    @abstractmethod
    async def list_folders(self) -> list[EmailFolderDTO]:
        """
        List all folders/labels.

        Returns:
            List of EmailFolderDTO
        """
        pass

    async def create_folder(self, name: str, parent: str | None = None) -> EmailFolderDTO:
        """
        Create a new folder/label.

        Args:
            name: Folder name
            parent: Parent folder (for nested folders)

        Returns:
            Created EmailFolderDTO
        """
        raise NotImplementedError("Folder creation not supported by this provider")

    async def delete_folder(self, folder_id: str) -> None:
        """
        Delete a folder/label.

        Args:
            folder_id: Folder ID
        """
        raise NotImplementedError("Folder deletion not supported by this provider")

    # ============================================================
    # Attachment Operations
    # ============================================================

    async def get_attachment(
        self,
        message_id: str,
        attachment_id: str,
    ) -> EmailAttachmentDTO:
        """
        Get attachment content.

        Args:
            message_id: Message ID
            attachment_id: Attachment ID

        Returns:
            EmailAttachmentDTO with content
        """
        raise NotImplementedError("Attachment download not supported by this provider")

    # ============================================================
    # Account Operations
    # ============================================================

    @abstractmethod
    async def get_profile(self) -> dict:
        """
        Get account profile information.

        Returns:
            Dict with email, name, etc.
        """
        pass

    async def test_connection(self) -> bool:
        """
        Test the connection to the email server.

        Returns:
            True if connection successful
        """
        try:
            await self.get_profile()
            return True
        except Exception:
            return False
