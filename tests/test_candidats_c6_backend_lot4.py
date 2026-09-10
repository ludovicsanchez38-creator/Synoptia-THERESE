"""Cycle 6, lot 4 (10/09/2026) : candidats des secondes lectures, confirmés par Grok.

- IMAP : un identifiant de message porte son dossier ; lire, marquer, supprimer ou
  déplacer un message des Envoyés agit dans les Envoyés, jamais sur l'UID homonyme
  de la boîte de réception (P1) ;
- IMAP : « non lus » et « mot-clé » se combinent au lieu de s'écraser ;
- voix locale : une panne (RuntimeError) ne recopie pas un chemin local à l'écran,
  mais un message écrit pour l'utilisateur passe intact.
"""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest


def _message(uid: str, sujet: str):
    return SimpleNamespace(
        uid=uid, subject=sujet, text=f"corps de {sujet}", html="", from_="camille@example.com",
        to=["ludo@example.com"], cc=[], date=datetime(2026, 9, 10, 9, 0, tzinfo=UTC), flags=(), attachments=[],
    )


class FauxMailbox:
    def __init__(self, journal: list, dossier: str, boites: dict):
        self.journal = journal
        self.dossier = dossier
        self.boites = boites
        self.folder = SimpleNamespace(set=lambda nom: journal.append(("set", nom)), list=lambda: [])

    def fetch(self, criteria, **kwargs):
        self.journal.append(("fetch", self.dossier, str(criteria)))
        uid = getattr(criteria, "uid", None) if not isinstance(criteria, str) else None
        texte = str(criteria)
        for msg in self.boites.get(self.dossier, []):
            if uid is None and f'UID {msg.uid}' not in texte and 'UID' in texte:
                continue
            if 'UID' in texte and f'UID {msg.uid}' not in texte:
                continue
            yield msg

    def move(self, uids, destination):
        self.journal.append(("move", self.dossier, list(uids), destination))

    def delete(self, uids):
        self.journal.append(("delete", self.dossier, list(uids)))

    def flag(self, uids, flags, value):
        self.journal.append(("flag", self.dossier, list(uids), set(flags), value))


def _fournisseur(monkeypatch, boites: dict, journal: list):
    from app.services.email.imap_smtp_provider import ImapSmtpProvider

    provider = ImapSmtpProvider("ludo@example.com", "secret", "imap.example.com")

    @contextlib.contextmanager
    def _connexion(timeout=None, initial_folder="INBOX"):
        journal.append(("login", initial_folder))
        yield FauxMailbox(journal, initial_folder, boites)

    monkeypatch.setattr(provider, "_connect_mailbox", _connexion)
    monkeypatch.setattr(provider, "_dossier_corbeille", lambda mailbox: "Trash", raising=False)
    return provider


@pytest.mark.asyncio
async def test_un_message_des_envoyes_est_lu_marque_et_supprime_dans_les_envoyes(monkeypatch):
    journal: list = []
    boites = {"INBOX": [_message("12", "Facture reçue")], "Sent": [_message("12", "Devis envoyé")]}
    provider = _fournisseur(monkeypatch, boites, journal)

    messages, _suite = await provider.list_messages(folder="Sent", max_results=10)
    envoye = messages[0]
    assert envoye.subject == "Devis envoyé"
    assert envoye.id != "12", "l'identifiant d'un message hors INBOX doit porter son dossier"

    journal.clear()
    lu = await provider.get_message(envoye.id)
    assert lu.subject == "Devis envoyé", "get_message a lu l'UID homonyme de la boîte de réception"
    assert ("login", "Sent") in journal, journal

    journal.clear()
    await provider.delete_message(envoye.id)
    assert any(op[0] == "move" and op[1] == "Sent" and op[2] == ["12"] for op in journal), f"suppression hors des Envoyés : {journal}"

    journal.clear()
    await provider.modify_message(envoye.id, mark_read=True)
    assert any(op[0] == "flag" and op[1] == "Sent" for op in journal), journal


@pytest.mark.asyncio
async def test_un_identifiant_nu_reste_un_message_de_la_boite_de_reception(monkeypatch):
    journal: list = []
    provider = _fournisseur(monkeypatch, {"INBOX": [_message("7", "Bonjour")]}, journal)
    lu = await provider.get_message("7")
    assert lu.subject == "Bonjour" and ("login", "INBOX") in journal


@pytest.mark.asyncio
async def test_non_lus_et_mot_cle_se_combinent(monkeypatch):
    journal: list = []
    provider = _fournisseur(monkeypatch, {"INBOX": []}, journal)
    await provider.list_messages(unread_only=True, query="devis", max_results=10)
    criteres = [op[2] for op in journal if op[0] == "fetch"][0]
    assert "UNSEEN" in criteres and "devis" in criteres, f"critères : {criteres}"
    journal.clear()
    await provider.list_messages(unread_only=True, flagged_only=True, max_results=10)
    criteres = [op[2] for op in journal if op[0] == "fetch"][0]
    assert "UNSEEN" in criteres and "FLAGGED" in criteres, f"critères : {criteres}"


@pytest.mark.asyncio
async def test_une_panne_de_voix_locale_ne_recopie_pas_un_chemin_a_l_ecran(client, monkeypatch):
    from app.services import voice_local
    from app.services.error_handler import ErreurPourEcran

    monkeypatch.setattr(voice_local, "active_whisper_model", lambda: "small", raising=False)
    monkeypatch.setattr(voice_local, "stt_available", lambda: True, raising=False)

    def _panne(*_a, **_k):
        raise RuntimeError("Modèle absent : /Users/ludo/.therese/whisper/small.bin")

    monkeypatch.setattr(voice_local, "transcribe_local", _panne)
    reponse = await client.post("/api/voice/local/transcribe", files={"audio": ("rec.webm", b"RIFF....", "audio/webm")})
    assert reponse.status_code in (500, 503), reponse.text
    assert "/Users/ludo" not in reponse.text, reponse.text

    def _message_utilisateur(*_a, **_k):
        raise ErreurPourEcran("STT local indisponible : faster-whisper non installé.")

    monkeypatch.setattr(voice_local, "transcribe_local", _message_utilisateur)
    reponse = await client.post("/api/voice/local/transcribe", files={"audio": ("rec.webm", b"RIFF....", "audio/webm")})
    assert reponse.status_code == 503, reponse.text
    assert "faster-whisper non installé" in reponse.text, reponse.text


# --- revue Grok du diff 0.70.0, finding 1 : l'identifiant après déplacement ----

class FauxMailboxCopyUid(FauxMailbox):
    """Un serveur IMAP répond COPYUID au déplacement : l'UID change dans la destination."""

    def move(self, uids, destination):
        super().move(uids, destination)
        return (("OK", [b"[COPYUID 1694 5 42] Move completed"]), ("OK", [b"Expunge completed"]))


@pytest.mark.asyncio
async def test_un_message_deplace_porte_l_uid_de_sa_destination(monkeypatch):
    """Revue Grok 0.70.0 (P2) : `move_message` renvoyait `Dest::ancienUid` ; un UID
    homonyme dans la destination faisait agir lecture, drapeau ou suppression sur
    un autre message. Le serveur dit le nouvel UID (COPYUID) : c'est lui qui compte."""
    from app.services.email.imap_smtp_provider import ImapSmtpProvider

    journal: list = []
    boites = {"INBOX": [_message("5", "À archiver")], "Archive": [_message("5", "Un autre message, UID homonyme")]}
    provider = ImapSmtpProvider("ludo@example.com", "secret", "imap.example.com")

    @contextlib.contextmanager
    def _connexion(timeout=None, initial_folder="INBOX"):
        journal.append(("login", initial_folder))
        yield FauxMailboxCopyUid(journal, initial_folder, boites)

    monkeypatch.setattr(provider, "_connect_mailbox", _connexion)
    deplace = await provider.move_message("5", "Archive")
    assert deplace.id == "Archive::42", deplace.id
    assert deplace.subject == "À archiver"
