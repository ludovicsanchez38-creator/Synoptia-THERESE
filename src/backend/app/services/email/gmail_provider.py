"""
THERESE v2 - Gmail Provider

Gmail OAuth implementation of EmailProvider.
Wraps the existing GmailService.
"""

import json
import logging
from datetime import datetime
from typing import Optional

from app.services.email.base_provider import (
    EmailProvider,
    EmailMessageDTO,
    EmailFolderDTO,
    EmailAttachmentDTO,
    SendEmailRequest,
)
from app.services.gmail_service import (
    GmailService,
    format_message_for_storage,
    parse_email_body,
)

logger = logging.getLogger(__name__)


class GmailProvider(EmailProvider):
    """
    Gmail implementation of EmailProvider.

    Uses OAuth2 access token for authentication.
    """

    def __init__(self, access_token: str):
        """
        Initialize Gmail provider.

        Args:
            access_token: Valid OAuth2 access token
        """
        self._service = GmailService(access_token)
        self._access_token = access_token

    @property
    def provider_name(self) -> str:
        return "gmail"

    @property
    def supports_labels(self) -> bool:
        return True  # Gmail uses labels instead of folders

    @property
    def supports_threads(self) -> bool:
        return True  # Gmail groups emails into threads

    @property
    def supports_search(self) -> bool:
        return True  # Gmail has powerful search

    # ============================================================
    # Message Operations
    # ============================================================

    async def list_messages(
        self,
        folder: Optional[str] = None,
        max_results: int = 50,
        page_token: Optional[str] = None,
        query: Optional[str] = None,
        unread_only: bool = False,
    ) -> tuple[list[EmailMessageDTO], Optional[str]]:
        """List messages from Gmail."""
        label_ids = None
        if folder:
            label_ids = [folder]

        search_query = query or ""
        if unread_only:
            search_query = f"{search_query} is:unread".strip()

        result = await self._service.list_messages(
            max_results=max_results,
            page_token=page_token,
            query=search_query if search_query else None,
            label_ids=label_ids,
        )

        messages = []
        for msg_stub in result.get("messages", []):
            # Fetch full message
            full_msg = await self._service.get_message(msg_stub["id"])
            dto = self._gmail_to_dto(full_msg)
            messages.append(dto)

        return messages, result.get("nextPageToken")

    async def get_message(
        self,
        message_id: str,
        include_body: bool = True,
        include_attachments: bool = False,
    ) -> EmailMessageDTO:
        """Get a single message from Gmail."""
        msg_format = "full" if include_body else "metadata"
        gmail_msg = await self._service.get_message(message_id, format=msg_format)
        dto = self._gmail_to_dto(gmail_msg)

        if include_attachments and dto.has_attachments:
            # Fetch attachment details (not content yet)
            payload = gmail_msg.get("payload", {})
            dto.attachments = self._extract_attachments(payload, message_id)

        return dto

    async def send_message(self, request: SendEmailRequest) -> str:
        """Send an email via Gmail."""
        result = await self._service.send_message(
            to=request.to,
            subject=request.subject,
            body=request.body,
            cc=request.cc if request.cc else None,
            bcc=request.bcc if request.bcc else None,
            html=request.is_html,
        )
        return result.get("id", "")

    async def create_draft(self, request: SendEmailRequest) -> str:
        """Create a draft in Gmail."""
        result = await self._service.create_draft(
            to=request.to,
            subject=request.subject,
            body=request.body,
            cc=request.cc if request.cc else None,
            bcc=request.bcc if request.bcc else None,
            html=request.is_html,
        )
        return result.get("id", "")

    async def modify_message(
        self,
        message_id: str,
        add_labels: Optional[list[str]] = None,
        remove_labels: Optional[list[str]] = None,
        mark_read: Optional[bool] = None,
        mark_starred: Optional[bool] = None,
    ) -> EmailMessageDTO:
        """Modify message labels/flags in Gmail."""
        add_label_ids = list(add_labels) if add_labels else []
        remove_label_ids = list(remove_labels) if remove_labels else []

        # Handle read/unread
        if mark_read is True:
            remove_label_ids.append("UNREAD")
        elif mark_read is False:
            add_label_ids.append("UNREAD")

        # Handle starred
        if mark_starred is True:
            add_label_ids.append("STARRED")
        elif mark_starred is False:
            remove_label_ids.append("STARRED")

        await self._service.modify_message(
            message_id,
            add_label_ids=add_label_ids if add_label_ids else None,
            remove_label_ids=remove_label_ids if remove_label_ids else None,
        )

        return await self.get_message(message_id)

    async def delete_message(self, message_id: str, permanent: bool = False) -> None:
        """Delete a message from Gmail."""
        if permanent:
            await self._service.delete_message(message_id)
        else:
            await self._service.trash_message(message_id)

    async def move_message(self, message_id: str, destination_folder: str) -> EmailMessageDTO:
        """Move a message to another label in Gmail."""
        # In Gmail, moving means adding new label and removing old ones
        # For simplicity, we add the destination label
        await self._service.modify_message(
            message_id,
            add_label_ids=[destination_folder],
        )
        return await self.get_message(message_id)

    # ============================================================
    # Folder/Label Operations
    # ============================================================

    async def list_folders(self) -> list[EmailFolderDTO]:
        """List all Gmail labels."""
        labels = await self._service.list_labels()
        return [self._label_to_dto(label) for label in labels]

    async def create_folder(self, name: str, parent: Optional[str] = None) -> EmailFolderDTO:
        """Create a new Gmail label."""
        label_name = f"{parent}/{name}" if parent else name
        result = await self._service.create_label(label_name)
        return self._label_to_dto(result)

    async def delete_folder(self, folder_id: str) -> None:
        """Delete a Gmail label."""
        await self._service.delete_label(folder_id)

    # ============================================================
    # Attachment Operations
    # ============================================================

    async def get_attachment(
        self,
        message_id: str,
        attachment_id: str,
    ) -> EmailAttachmentDTO:
        """Get attachment content from Gmail."""
        import base64
        import httpx

        url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}/attachments/{attachment_id}"
        headers = {"Authorization": f"Bearer {self._access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()

        content = base64.urlsafe_b64decode(data.get("data", ""))

        return EmailAttachmentDTO(
            filename="attachment",  # We don't have filename here
            content_type="application/octet-stream",
            size=len(content),
            content=content,
            attachment_id=attachment_id,
        )

    # ============================================================
    # Account Operations
    # ============================================================

    async def get_profile(self) -> dict:
        """Get Gmail account profile."""
        return await self._service.get_profile()

    # ============================================================
    # Private Helpers
    # ============================================================

    def _gmail_to_dto(self, gmail_msg: dict) -> EmailMessageDTO:
        """Convert Gmail API message to EmailMessageDTO."""
        formatted = format_message_for_storage(gmail_msg)

        # Parse JSON arrays
        to_emails = json.loads(formatted.get("to_emails", "[]"))
        cc_emails = json.loads(formatted.get("cc_emails", "[]")) if formatted.get("cc_emails") else []
        labels = json.loads(formatted.get("labels", "[]"))

        return EmailMessageDTO(
            id=formatted["id"],
            thread_id=formatted.get("thread_id"),
            subject=formatted.get("subject"),
            snippet=formatted.get("snippet"),
            from_email=formatted.get("from_email", ""),
            from_name=formatted.get("from_name"),
            to_emails=to_emails,
            cc_emails=cc_emails,
            date=formatted.get("date"),
            is_read=formatted.get("is_read", False),
            is_starred=formatted.get("is_starred", False),
            is_important=formatted.get("is_important", False),
            is_draft=formatted.get("is_draft", False),
            body_plain=formatted.get("body_plain"),
            body_html=formatted.get("body_html"),
            has_attachments=formatted.get("has_attachments", False),
            attachment_count=formatted.get("attachment_count", 0),
            labels=labels,
            size_bytes=formatted.get("size_bytes", 0),
        )

    def _label_to_dto(self, label: dict) -> EmailFolderDTO:
        """Convert Gmail label to EmailFolderDTO."""
        return EmailFolderDTO(
            id=label.get("id", ""),
            name=label.get("name", ""),
            type="system" if label.get("type") == "system" else "user",
            message_count=label.get("messagesTotal", 0),
            unread_count=label.get("messagesUnread", 0),
            color=label.get("color", {}).get("backgroundColor"),
        )

    def _extract_attachments(self, payload: dict, message_id: str) -> list[EmailAttachmentDTO]:
        """Extract attachment metadata from Gmail payload."""
        attachments = []

        def process_parts(parts: list[dict]):
            for part in parts:
                if "parts" in part:
                    process_parts(part["parts"])
                elif part.get("filename"):
                    attachments.append(EmailAttachmentDTO(
                        filename=part["filename"],
                        content_type=part.get("mimeType", "application/octet-stream"),
                        size=part.get("body", {}).get("size", 0),
                        attachment_id=part.get("body", {}).get("attachmentId"),
                    ))

        if "parts" in payload:
            process_parts(payload["parts"])

        return attachments
