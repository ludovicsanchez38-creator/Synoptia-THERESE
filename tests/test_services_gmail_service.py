"""
Tests GmailService - format_message_for_storage.

Défense en profondeur (dette 09/06/2026) : le body_html d'un mail Gmail
n'était jamais sanitisé côté backend au moment du cache, contrairement aux
signatures (nh3). Sûr tant que le seul point de rendu est le sanitizer front
(sanitizeEmailHtml), fragile si un futur écran affiche le corps sans repasser
par lui.
"""

import base64
from unittest.mock import AsyncMock

import pytest
from app.services.gmail_service import GmailService, format_message_for_storage


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


@pytest.mark.asyncio
async def test_modify_message_sans_etiquette_est_un_noop():
    """B-310 : ne jamais appeler Gmail avec un corps modify vide."""
    service = GmailService("token")
    service._request = AsyncMock()

    result = await service.modify_message("msg-1", add_label_ids=[], remove_label_ids=[])

    assert result == {"id": "msg-1"}
    service._request.assert_not_awaited()


class TestB478LesPiecesJointesImbriqueesSontComptees:
    """B-478 (05/09/2026) : format_message_for_storage ne regardait que les
    `parts` de premier niveau. Un transfert (multipart/mixed > message/rfc822
    > multipart/mixed > devis.pdf) donnait has_attachments False et
    attachment_count 0, alors que _extract_attachments récurse et trouve le
    fichier : la liste disait « sans pièce jointe », le détail en montrait une.
    """

    def _message_transfere(self) -> dict:
        return {
            "id": "m1",
            "threadId": "t1",
            "labelIds": ["INBOX"],
            "sizeEstimate": 1000,
            "internalDate": "1757000000000",
            "payload": {
                "mimeType": "multipart/mixed",
                "headers": [
                    {"name": "From", "value": "Paul Durand <paul@durand.test>"},
                    {"name": "To", "value": "marie@atelier.test"},
                    {"name": "Subject", "value": "Fwd: devis"},
                    {"name": "Date", "value": "Fri, 05 Sep 2026 10:00:00 +0200"},
                ],
                "parts": [
                    {"mimeType": "text/plain", "body": {"data": ""}},
                    {
                        "mimeType": "message/rfc822",
                        "parts": [
                            {
                                "mimeType": "multipart/mixed",
                                "parts": [
                                    {"mimeType": "text/plain", "body": {"data": ""}},
                                    {
                                        "mimeType": "application/pdf",
                                        "filename": "devis.pdf",
                                        "body": {"size": 4321, "attachmentId": "att-1"},
                                    },
                                ],
                            }
                        ],
                    },
                ],
            },
        }

    def test_un_fichier_imbrique_compte(self):
        stocke = format_message_for_storage(self._message_transfere())

        assert stocke["has_attachments"] is True
        assert stocke["attachment_count"] == 1
