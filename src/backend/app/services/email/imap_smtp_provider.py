"""
THERESE v2 - IMAP/SMTP Provider

Generic IMAP/SMTP implementation of EmailProvider.
Supports any standard IMAP/SMTP server (Gmail, Outlook, Fastmail, etc.)
"""

import asyncio
import logging
from datetime import UTC, datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
from app.services.email.base_provider import (
    EmailAttachmentDTO,
    EmailFolderDTO,
    EmailMessageDTO,
    EmailProvider,
    SendEmailRequest,
)
from imap_tools import AND, OR, MailBox, MailMessage

logger = logging.getLogger(__name__)


class ImapSmtpProvider(EmailProvider):
    """
    IMAP/SMTP implementation of EmailProvider.

    Supports any standard IMAP/SMTP server.
    """

    def __init__(
        self,
        email_address: str,
        password: str,
        imap_host: str,
        imap_port: int = 993,
        smtp_host: str = "",
        smtp_port: int = 587,
        use_ssl: bool = True,
        smtp_use_tls: bool = True,
    ):
        """
        Initialize IMAP/SMTP provider.

        Args:
            email_address: Email address for login
            password: Password or app-specific password
            imap_host: IMAP server hostname
            imap_port: IMAP server port (default 993 for SSL)
            smtp_host: SMTP server hostname (defaults to imap_host if empty)
            smtp_port: SMTP server port (default 587 for TLS)
            use_ssl: Use SSL for IMAP connection
            smtp_use_tls: Use STARTTLS for SMTP
        """
        self._email = email_address
        self._password = password
        self._imap_host = imap_host
        self._imap_port = imap_port
        self._smtp_host = smtp_host or imap_host
        self._smtp_port = smtp_port
        self._use_ssl = use_ssl
        self._smtp_use_tls = smtp_use_tls

    @property
    def provider_name(self) -> str:
        return "imap"

    @property
    def supports_labels(self) -> bool:
        return False  # IMAP uses folders, not labels

    @property
    def supports_threads(self) -> bool:
        return False  # Standard IMAP doesn't have thread grouping

    @property
    def supports_search(self) -> bool:
        return True

    # ============================================================
    # Message Operations
    # ============================================================

    async def list_messages(
        self,
        folder: str | None = None,
        max_results: int = 50,
        page_token: str | None = None,
        query: str | None = None,
        unread_only: bool = False,
    ) -> tuple[list[EmailMessageDTO], str | None]:
        """List messages from IMAP folder."""
        folder_name = folder or "INBOX"

        # Calculate offset from page token
        offset = int(page_token) if page_token else 0

        messages = []

        def _sync_fetch():
            with MailBox(self._imap_host, self._imap_port).login(
                self._email, self._password, initial_folder=folder_name
            ) as mailbox:
                # Build search criteria
                criteria = AND(seen=False) if unread_only else "ALL"

                if query:
                    # Simple text search in subject/body
                    criteria = AND(OR(subject=query, body=query))

                # Fetch messages (reversed for newest first)
                all_msgs = list(mailbox.fetch(criteria, reverse=True, limit=offset + max_results))

                # Apply pagination
                paginated = all_msgs[offset : offset + max_results]

                result = []
                for msg in paginated:
                    result.append(self._imap_to_dto(msg))

                # Calculate next page token
                next_token = None
                if len(all_msgs) > offset + max_results:
                    next_token = str(offset + max_results)

                return result, next_token

        loop = asyncio.get_event_loop()
        messages, next_token = await loop.run_in_executor(None, _sync_fetch)

        return messages, next_token

    async def get_message(
        self,
        message_id: str,
        include_body: bool = True,
        include_attachments: bool = False,
    ) -> EmailMessageDTO:
        """Get a single message from IMAP."""

        def _sync_fetch():
            with MailBox(self._imap_host, self._imap_port).login(
                self._email, self._password
            ) as mailbox:
                # Search by UID
                for msg in mailbox.fetch(AND(uid=message_id)):
                    return self._imap_to_dto(msg, include_attachments=include_attachments)
                raise ValueError(f"Message {message_id} not found")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync_fetch)

    async def send_message(self, request: SendEmailRequest) -> str:
        """Send an email via SMTP."""
        # Create message
        if request.is_html:
            msg = MIMEMultipart("alternative")
            msg.attach(MIMEText(request.body, "html", "utf-8"))
        else:
            msg = MIMEMultipart()
            msg.attach(MIMEText(request.body, "plain", "utf-8"))

        msg["From"] = self._email
        msg["To"] = ", ".join(request.to)
        msg["Subject"] = request.subject

        if request.cc:
            msg["Cc"] = ", ".join(request.cc)

        if request.in_reply_to:
            msg["In-Reply-To"] = request.in_reply_to
        if request.references:
            msg["References"] = request.references

        # Add attachments
        for filename, content, content_type in request.attachments:
            part = MIMEBase(*content_type.split("/", 1))
            part.set_payload(content)
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
            msg.attach(part)

        # Send via SMTP
        all_recipients = request.to + request.cc + request.bcc

        await aiosmtplib.send(
            msg,
            hostname=self._smtp_host,
            port=self._smtp_port,
            username=self._email,
            password=self._password,
            start_tls=self._smtp_use_tls,
            recipients=all_recipients,
        )

        # Return a generated ID (SMTP doesn't return one)
        return f"sent_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"

    async def create_draft(self, request: SendEmailRequest) -> str:
        """Create a draft in IMAP Drafts folder."""

        def _sync_create():
            # Create message
            if request.is_html:
                msg = MIMEMultipart("alternative")
                msg.attach(MIMEText(request.body, "html", "utf-8"))
            else:
                msg = MIMEMultipart()
                msg.attach(MIMEText(request.body, "plain", "utf-8"))

            msg["From"] = self._email
            msg["To"] = ", ".join(request.to)
            msg["Subject"] = request.subject

            if request.cc:
                msg["Cc"] = ", ".join(request.cc)

            with MailBox(self._imap_host, self._imap_port).login(
                self._email, self._password
            ) as mailbox:
                # Find Drafts folder
                drafts_folder = "Drafts"
                for folder in mailbox.folder.list():
                    if "draft" in folder.name.lower():
                        drafts_folder = folder.name
                        break

                # Append to Drafts
                mailbox.append(msg.as_bytes(), drafts_folder, dt=datetime.now())

            return f"draft_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync_create)

    async def modify_message(
        self,
        message_id: str,
        add_labels: list[str] | None = None,
        remove_labels: list[str] | None = None,
        mark_read: bool | None = None,
        mark_starred: bool | None = None,
    ) -> EmailMessageDTO:
        """Modify message flags in IMAP."""

        def _sync_modify():
            with MailBox(self._imap_host, self._imap_port).login(
                self._email, self._password
            ) as mailbox:
                if mark_read is True:
                    mailbox.flag([message_id], {r"\Seen"}, True)
                elif mark_read is False:
                    mailbox.flag([message_id], {r"\Seen"}, False)

                if mark_starred is True:
                    mailbox.flag([message_id], {r"\Flagged"}, True)
                elif mark_starred is False:
                    mailbox.flag([message_id], {r"\Flagged"}, False)

                # Fetch updated message
                for msg in mailbox.fetch(AND(uid=message_id)):
                    return self._imap_to_dto(msg)

                raise ValueError(f"Message {message_id} not found")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync_modify)

    async def delete_message(self, message_id: str, permanent: bool = False) -> None:
        """Delete a message from IMAP."""

        def _sync_delete():
            with MailBox(self._imap_host, self._imap_port).login(
                self._email, self._password
            ) as mailbox:
                if permanent:
                    mailbox.delete([message_id])
                else:
                    # Move to Trash
                    trash_folder = "Trash"
                    for folder in mailbox.folder.list():
                        if "trash" in folder.name.lower() or "deleted" in folder.name.lower():
                            trash_folder = folder.name
                            break
                    mailbox.move([message_id], trash_folder)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _sync_delete)

    async def move_message(self, message_id: str, destination_folder: str) -> EmailMessageDTO:
        """Move a message to another folder in IMAP."""

        def _sync_move():
            with MailBox(self._imap_host, self._imap_port).login(
                self._email, self._password
            ) as mailbox:
                mailbox.move([message_id], destination_folder)

                # Fetch from new location
                mailbox.folder.set(destination_folder)
                for msg in mailbox.fetch(AND(uid=message_id)):
                    return self._imap_to_dto(msg)

                raise ValueError(f"Message {message_id} not found after move")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync_move)

    # ============================================================
    # Folder Operations
    # ============================================================

    async def list_folders(self) -> list[EmailFolderDTO]:
        """List all IMAP folders."""

        def _sync_list():
            folders = []
            with MailBox(self._imap_host, self._imap_port).login(
                self._email, self._password
            ) as mailbox:
                for folder_info in mailbox.folder.list():
                    # Get folder status
                    try:
                        mailbox.folder.set(folder_info.name)
                        status = mailbox.folder.status(folder_info.name)

                        folders.append(EmailFolderDTO(
                            id=folder_info.name,
                            name=folder_info.name.split(folder_info.delim)[-1] if folder_info.delim else folder_info.name,
                            type="system" if folder_info.name.upper() in ["INBOX", "SENT", "DRAFTS", "TRASH", "SPAM", "JUNK"] else "user",
                            message_count=status.get("MESSAGES", 0),
                            unread_count=status.get("UNSEEN", 0),
                            path=folder_info.name,
                            delimiter=folder_info.delim,
                        ))
                    except Exception:
                        # Folder exists but can't be selected (e.g., parent folder)
                        folders.append(EmailFolderDTO(
                            id=folder_info.name,
                            name=folder_info.name.split(folder_info.delim)[-1] if folder_info.delim else folder_info.name,
                            type="user",
                            path=folder_info.name,
                            delimiter=folder_info.delim,
                        ))

            return folders

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync_list)

    async def create_folder(self, name: str, parent: str | None = None) -> EmailFolderDTO:
        """Create a new IMAP folder."""

        def _sync_create():
            with MailBox(self._imap_host, self._imap_port).login(
                self._email, self._password
            ) as mailbox:
                folder_name = f"{parent}/{name}" if parent else name
                mailbox.folder.create(folder_name)

                return EmailFolderDTO(
                    id=folder_name,
                    name=name,
                    type="user",
                    path=folder_name,
                )

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync_create)

    async def delete_folder(self, folder_id: str) -> None:
        """Delete an IMAP folder."""

        def _sync_delete():
            with MailBox(self._imap_host, self._imap_port).login(
                self._email, self._password
            ) as mailbox:
                mailbox.folder.delete(folder_id)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _sync_delete)

    # ============================================================
    # Attachment Operations
    # ============================================================

    async def get_attachment(
        self,
        message_id: str,
        attachment_id: str,
    ) -> EmailAttachmentDTO:
        """Get attachment content from IMAP message."""

        def _sync_fetch():
            with MailBox(self._imap_host, self._imap_port).login(
                self._email, self._password
            ) as mailbox:
                for msg in mailbox.fetch(AND(uid=message_id)):
                    for idx, att in enumerate(msg.attachments):
                        if str(idx) == attachment_id or att.filename == attachment_id:
                            return EmailAttachmentDTO(
                                filename=att.filename,
                                content_type=att.content_type,
                                size=len(att.payload),
                                content=att.payload,
                                attachment_id=str(idx),
                            )
                raise ValueError(f"Attachment {attachment_id} not found")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync_fetch)

    # ============================================================
    # Account Operations
    # ============================================================

    async def get_profile(self) -> dict:
        """Get account profile (email address)."""
        return {
            "email": self._email,
            "provider": "imap",
            "imap_host": self._imap_host,
            "smtp_host": self._smtp_host,
        }

    async def test_connection(self) -> bool:
        """Test IMAP connection."""

        def _sync_test():
            try:
                with MailBox(self._imap_host, self._imap_port).login(
                    self._email, self._password
                ):
                    return True
            except Exception as e:
                logger.error(f"IMAP connection test failed: {e}")
                return False

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync_test)

    # ============================================================
    # Private Helpers
    # ============================================================

    def _imap_to_dto(self, msg: MailMessage, include_attachments: bool = False) -> EmailMessageDTO:
        """Convert imap-tools MailMessage to EmailMessageDTO."""
        attachments = []
        if include_attachments:
            for idx, att in enumerate(msg.attachments):
                attachments.append(EmailAttachmentDTO(
                    filename=att.filename,
                    content_type=att.content_type,
                    size=len(att.payload),
                    content=att.payload,
                    attachment_id=str(idx),
                ))
        else:
            for idx, att in enumerate(msg.attachments):
                attachments.append(EmailAttachmentDTO(
                    filename=att.filename,
                    content_type=att.content_type,
                    size=len(att.payload),
                    attachment_id=str(idx),
                ))

        return EmailMessageDTO(
            id=msg.uid,
            subject=msg.subject,
            snippet=msg.text[:200] if msg.text else None,
            from_email=msg.from_,
            from_name=None,  # imap-tools combines name and email
            to_emails=list(msg.to),
            cc_emails=list(msg.cc),
            date=msg.date,
            is_read=r"\Seen" in msg.flags,
            is_starred=r"\Flagged" in msg.flags,
            body_plain=msg.text,
            body_html=msg.html,
            has_attachments=len(msg.attachments) > 0,
            attachment_count=len(msg.attachments),
            attachments=attachments,
            labels=[],  # IMAP uses folders, not labels
            size_bytes=0,  # Not easily available in imap-tools
        )
