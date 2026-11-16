"""B-1905 : une pièce Gmail téléchargée garde ses métadonnées MIME."""
from unittest.mock import AsyncMock, Mock

from app.services.email.gmail_provider import GmailProvider


async def test_piece_jointe_gmail_retrouve_nom_et_type(monkeypatch):
    from app.services import http_client

    fournisseur = GmailProvider("fictif")
    fournisseur._service.get_message = AsyncMock(return_value={
        "payload": {"parts": [{"parts": [
            {"filename": "devis.pdf", "mimeType": "application/pdf", "body": {"attachmentId": "piece-42", "size": 5}}
        ]}]}
    })
    reponse = Mock()
    reponse.json.return_value = {"data": "aGVsbG8="}
    client = Mock()
    client.get = AsyncMock(return_value=reponse)
    monkeypatch.setattr(http_client, "get_http_client", AsyncMock(return_value=client))

    piece = await fournisseur.get_attachment("message-1", "piece-42")
    assert piece.filename == "devis.pdf"
    assert piece.content_type == "application/pdf"
    assert piece.content == b"hello"
    assert piece.size == 5
