"""
Tests GmailService - format_message_for_storage.

Défense en profondeur (dette 09/06/2026) : le body_html d'un mail Gmail
n'était jamais sanitisé côté backend au moment du cache, contrairement aux
signatures (nh3). Sûr tant que le seul point de rendu est le sanitizer front
(sanitizeEmailHtml), fragile si un futur écran affiche le corps sans repasser
par lui.
"""

import base64

from app.services.gmail_service import format_message_for_storage


def _b64(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode("utf-8")).decode("ascii")


def _gmail_message(html: str | None, plain: str | None = "Corps texte") -> dict:
    parts = []
    if plain is not None:
        parts.append({"mimeType": "text/plain", "body": {"data": _b64(plain)}})
    if html is not None:
        parts.append({"mimeType": "text/html", "body": {"data": _b64(html)}})

    return {
        "id": "msg-1",
        "threadId": "thread-1",
        "internalDate": "1717500000000",
        "labelIds": [],
        "sizeEstimate": 100,
        "snippet": "Bonjour",
        "payload": {
            "headers": [
                {"name": "From", "value": "expediteur@exemple.fr"},
                {"name": "To", "value": "dest@exemple.fr"},
                {"name": "Subject", "value": "Sujet"},
            ],
            "parts": parts,
        },
    }


class TestFormatMessageForStorageSanitizesHtml:
    def test_retire_le_script_du_body_html(self):
        message = _gmail_message(html="<p>Bonjour</p><script>alert(1)</script>")

        formatted = format_message_for_storage(message)

        assert "<script>" not in formatted["body_html"]
        assert "Bonjour" in formatted["body_html"]

    def test_laisse_le_body_html_absent_intact(self):
        message = _gmail_message(html=None)

        formatted = format_message_for_storage(message)

        assert formatted["body_html"] is None
