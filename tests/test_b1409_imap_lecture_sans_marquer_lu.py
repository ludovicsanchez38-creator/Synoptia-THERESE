"""B-1409 (relevé à la lecture du code par la RFC P-105, reproduit ici) :
toutes les lectures IMAP appelaient `mailbox.fetch` sans `mark_seen`, qui vaut
`True` par défaut dans imap_tools (lecture `BODY[]` au lieu de `BODY.PEEK[]`).

- Ouvrir la vue Courrier marquait lus, chez le fournisseur, jusqu'à 51
  messages que l'utilisateur n'avait pas ouverts.
- « Marquer non lu » ôtait le drapeau `\\Seen`, puis relisait le message pour
  le rendre : la relecture le remettait aussitôt en lu.

L'interface marque « lu » explicitement à l'ouverture (`EmailDetail`,
`markAsRead`) : aucune lecture ne doit le faire à sa place.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from app.services.email.imap_smtp_provider import ImapSmtpProvider


def _fournisseur() -> ImapSmtpProvider:
    return ImapSmtpProvider(
        email_address="moi@example.org", password="x",
        imap_host="imap.example.org", imap_port=993,
        smtp_host="smtp.example.org", smtp_port=465, smtp_use_tls=True,
    )


def _boite():
    boite = MagicMock()
    message = MagicMock()
    message.attachments = []
    boite.fetch.return_value = [message]
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=boite)
    cm.__exit__ = MagicMock(return_value=False)
    return boite, cm


async def _appeler(operation: str):
    fournisseur = _fournisseur()
    boite, cm = _boite()
    with (
        patch.object(fournisseur, "_connect_mailbox", return_value=cm),
        patch.object(fournisseur, "_imap_to_dto", return_value=MagicMock()),
    ):
        if operation == "lister":
            await fournisseur.list_messages()
        elif operation == "ouvrir":
            await fournisseur.get_message("42")
        elif operation == "marquer_non_lu":
            await fournisseur.modify_message("42", mark_read=False)
        elif operation == "deplacer":
            await fournisseur.move_message("42", "Archives")
        elif operation == "piece_jointe":
            with pytest.raises(ValueError, match="not found"):
                await fournisseur.get_attachment("42", "0")
    return boite


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["lister", "ouvrir", "marquer_non_lu", "deplacer", "piece_jointe"])
async def test_aucune_lecture_imap_ne_marque_le_message_comme_lu(operation):
    boite = await _appeler(operation)

    assert boite.fetch.called, "l'opération doit relire le message"
    for appel in boite.fetch.call_args_list:
        assert appel.kwargs.get("mark_seen") is False, (
            f"{operation} : fetch appelé sans mark_seen=False ({appel})"
        )


@pytest.mark.asyncio
async def test_marquer_non_lu_ne_repose_pas_le_drapeau_lu():
    boite = await _appeler("marquer_non_lu")

    boite.flag.assert_called_once_with(["42"], {r"\Seen"}, False)
    assert all(a.kwargs.get("mark_seen") is False for a in boite.fetch.call_args_list)
