"""
THÉRÈSE v2 - Gmail Service

Client for Gmail API operations.
Handles email CRUD, labels, attachments, and sync.

Phase 1 - Core Native Email (Gmail)
"""

import base64
import logging
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException

logger = logging.getLogger(__name__)


# ============================================================
# Gmail API Constants
# ============================================================


GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"


# ============================================================
# Helper Functions
# ============================================================


def parse_email_body(payload: dict) -> tuple[Optional[str], Optional[str]]:
    """
    Extract plain and HTML body from Gmail message payload.

    Args:
        payload: Gmail message payload

    Returns:
        (body_plain, body_html) tuple
    """
    body_plain = None
    body_html = None

    def decode_part(data: str) -> str:
        """Decode base64url data."""
        return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')

    def extract_from_parts(parts: list[dict]):
        """Recursively extract body from parts."""
        nonlocal body_plain, body_html

        for part in parts:
            mime_type = part.get('mimeType', '')

            if 'parts' in part:
                # Multipart, recurse
                extract_from_parts(part['parts'])
            elif mime_type == 'text/plain' and 'data' in part.get('body', {}):
                body_plain = decode_part(part['body']['data'])
            elif mime_type == 'text/html' and 'data' in part.get('body', {}):
                body_html = decode_part(part['body']['data'])

    # Handle single part message
    if 'body' in payload and 'data' in payload['body']:
        mime_type = payload.get('mimeType', '')
        if mime_type == 'text/plain':
            body_plain = decode_part(payload['body']['data'])
        elif mime_type == 'text/html':
            body_html = decode_part(payload['body']['data'])

    # Handle multipart message
    if 'parts' in payload:
        extract_from_parts(payload['parts'])

    # Generate plain text from HTML if missing
    if body_html and not body_plain:
        soup = BeautifulSoup(body_html, 'html.parser')
        body_plain = soup.get_text(separator='\n').strip()

    return body_plain, body_html


def parse_email_address(header_value: str) -> tuple[str, Optional[str]]:
    """
    Parse email address from header value.

    Args:
        header_value: Header value (e.g., "John Doe <john@example.com>")

    Returns:
        (email, name) tuple
    """
    if '<' in header_value and '>' in header_value:
        # Format: "Name <email@example.com>"
        parts = header_value.split('<')
        name = parts[0].strip().strip('"')
        email = parts[1].strip('>').strip()
        return email, name if name else None
    else:
        # Format: "email@example.com"
        return header_value.strip(), None


# ============================================================
# Gmail Service
# ============================================================


class GmailService:
    """
    Gmail API client.

    Handles authentication, email operations, and sync.
    """

    def __init__(self, access_token: str):
        """
        Initialize Gmail service.

        Args:
            access_token: Valid OAuth access token
        """
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
    ) -> dict:
        """Make authenticated request to Gmail API."""
        url = f"{GMAIL_API_BASE}/{endpoint}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method,
                    url,
                    headers=self.headers,
                    params=params,
                    json=json_data,
                    timeout=30.0,
                )

                if response.status_code == 401:
                    raise HTTPException(status_code=401, detail="Access token expired or invalid")

                if response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    logger.error(f"Gmail API error: {response.status_code} {error_data}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=error_data.get('error', {}).get('message', 'Gmail API error')
                    )

                return response.json() if response.content else {}

            except httpx.HTTPError as e:
                logger.error(f"HTTP error: {e}")
                raise HTTPException(status_code=500, detail=f"Gmail API request failed: {str(e)}")

    # ============================================================
    # Messages
    # ============================================================

    async def list_messages(
        self,
        max_results: int = 50,
        page_token: Optional[str] = None,
        query: Optional[str] = None,
        label_ids: Optional[list[str]] = None,
    ) -> dict:
        """
        List messages.

        Args:
            max_results: Max messages to return (1-500)
            page_token: Page token for pagination
            query: Gmail search query
            label_ids: Filter by label IDs

        Returns:
            dict with messages and nextPageToken
        """
        params = {
            'maxResults': min(max_results, 500),
        }

        if page_token:
            params['pageToken'] = page_token
        if query:
            params['q'] = query
        if label_ids:
            params['labelIds'] = ','.join(label_ids)

        return await self._request('GET', 'users/me/messages', params=params)

    async def get_message(self, message_id: str, format: str = 'full') -> dict:
        """
        Get message details.

        Args:
            message_id: Gmail message ID
            format: Format (minimal, full, raw, metadata)

        Returns:
            Message object
        """
        return await self._request('GET', f'users/me/messages/{message_id}', params={'format': format})

    async def send_message(
        self,
        to: list[str],
        subject: str,
        body: str,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
        html: bool = False,
    ) -> dict:
        """
        Send an email.

        Args:
            to: List of recipient emails
            subject: Email subject
            body: Email body (plain or HTML)
            cc: CC recipients
            bcc: BCC recipients
            html: Whether body is HTML

        Returns:
            Sent message object
        """
        # Create message
        message = MIMEMultipart() if html else MIMEText(body)
        message['To'] = ', '.join(to)
        message['Subject'] = subject

        if cc:
            message['Cc'] = ', '.join(cc)
        if bcc:
            message['Bcc'] = ', '.join(bcc)

        if html:
            message.attach(MIMEText(body, 'html'))

        # Encode message
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

        return await self._request('POST', 'users/me/messages/send', json_data={'raw': raw})

    async def create_draft(
        self,
        to: list[str],
        subject: str,
        body: str,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
        html: bool = False,
    ) -> dict:
        """Create a draft email."""
        # Create message (same as send)
        message = MIMEMultipart() if html else MIMEText(body)
        message['To'] = ', '.join(to)
        message['Subject'] = subject

        if cc:
            message['Cc'] = ', '.join(cc)
        if bcc:
            message['Bcc'] = ', '.join(bcc)

        if html:
            message.attach(MIMEText(body, 'html'))

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

        return await self._request(
            'POST',
            'users/me/drafts',
            json_data={'message': {'raw': raw}}
        )

    async def modify_message(
        self,
        message_id: str,
        add_label_ids: Optional[list[str]] = None,
        remove_label_ids: Optional[list[str]] = None,
    ) -> dict:
        """
        Modify message labels.

        Args:
            message_id: Gmail message ID
            add_label_ids: Labels to add
            remove_label_ids: Labels to remove

        Returns:
            Updated message
        """
        data = {}
        if add_label_ids:
            data['addLabelIds'] = add_label_ids
        if remove_label_ids:
            data['removeLabelIds'] = remove_label_ids

        return await self._request('POST', f'users/me/messages/{message_id}/modify', json_data=data)

    async def trash_message(self, message_id: str) -> dict:
        """Move message to trash."""
        return await self._request('POST', f'users/me/messages/{message_id}/trash')

    async def delete_message(self, message_id: str):
        """Permanently delete message."""
        await self._request('DELETE', f'users/me/messages/{message_id}')

    # ============================================================
    # Labels
    # ============================================================

    async def list_labels(self) -> list[dict]:
        """List all labels."""
        result = await self._request('GET', 'users/me/labels')
        return result.get('labels', [])

    async def create_label(
        self,
        name: str,
        label_list_visibility: str = 'labelShow',
        message_list_visibility: str = 'show',
    ) -> dict:
        """Create a new label."""
        data = {
            'name': name,
            'labelListVisibility': label_list_visibility,
            'messageListVisibility': message_list_visibility,
        }
        return await self._request('POST', 'users/me/labels', json_data=data)

    async def update_label(self, label_id: str, name: str) -> dict:
        """Update label name."""
        return await self._request('PATCH', f'users/me/labels/{label_id}', json_data={'name': name})

    async def delete_label(self, label_id: str):
        """Delete a label."""
        await self._request('DELETE', f'users/me/labels/{label_id}')

    # ============================================================
    # Profile
    # ============================================================

    async def get_profile(self) -> dict:
        """Get user profile information."""
        return await self._request('GET', 'users/me/profile')

    # ============================================================
    # Batch Operations
    # ============================================================

    async def batch_modify_messages(
        self,
        message_ids: list[str],
        add_label_ids: Optional[list[str]] = None,
        remove_label_ids: Optional[list[str]] = None,
    ) -> dict:
        """Batch modify multiple messages."""
        data = {
            'ids': message_ids,
        }
        if add_label_ids:
            data['addLabelIds'] = add_label_ids
        if remove_label_ids:
            data['removeLabelIds'] = remove_label_ids

        return await self._request('POST', 'users/me/messages/batchModify', json_data=data)


# ============================================================
# Helper Functions
# ============================================================


def format_message_for_storage(gmail_message: dict) -> dict:
    """
    Format Gmail API message for storage in database.

    Args:
        gmail_message: Raw Gmail API message

    Returns:
        Formatted dict for EmailMessage model
    """
    headers = {h['name'].lower(): h['value'] for h in gmail_message.get('payload', {}).get('headers', [])}

    # Parse from address
    from_email, from_name = parse_email_address(headers.get('from', ''))

    # Parse to/cc/bcc addresses
    to_emails = [parse_email_address(addr)[0] for addr in headers.get('to', '').split(',') if addr.strip()]
    cc_emails = [parse_email_address(addr)[0] for addr in headers.get('cc', '').split(',') if addr.strip()] if headers.get('cc') else None
    bcc_emails = [parse_email_address(addr)[0] for addr in headers.get('bcc', '').split(',') if addr.strip()] if headers.get('bcc') else None

    # Extract body
    body_plain, body_html = parse_email_body(gmail_message.get('payload', {}))

    # Parse date
    internal_date = datetime.fromtimestamp(int(gmail_message['internalDate']) / 1000)
    date_str = headers.get('date')
    # Simplified date parsing (production would use email.utils.parsedate_to_datetime)
    date = internal_date  # Fallback to internal date

    import json

    return {
        'id': gmail_message['id'],
        'thread_id': gmail_message['threadId'],
        'subject': headers.get('subject'),
        'snippet': gmail_message.get('snippet'),
        'from_email': from_email,
        'from_name': from_name,
        'to_emails': json.dumps(to_emails),
        'cc_emails': json.dumps(cc_emails) if cc_emails else None,
        'bcc_emails': json.dumps(bcc_emails) if bcc_emails else None,
        'date': date,
        'internal_date': internal_date,
        'labels': json.dumps(gmail_message.get('labelIds', [])),
        'is_read': 'UNREAD' not in gmail_message.get('labelIds', []),
        'is_starred': 'STARRED' in gmail_message.get('labelIds', []),
        'is_important': 'IMPORTANT' in gmail_message.get('labelIds', []),
        'is_draft': 'DRAFT' in gmail_message.get('labelIds', []),
        'has_attachments': 'parts' in gmail_message.get('payload', {}) and any(
            p.get('filename') for p in gmail_message['payload'].get('parts', [])
        ),
        'attachment_count': sum(1 for p in gmail_message.get('payload', {}).get('parts', []) if p.get('filename')),
        'body_plain': body_plain,
        'body_html': body_html,
        'size_bytes': gmail_message.get('sizeEstimate', 0),
        'synced_at': datetime.utcnow(),
    }
