"""
Tests ImapSmtpProvider - erreurs causales et alignement test/envoi.

Retours Dr_logic-3D (05/07/2026, v0.26.1 Windows 10) :
- cocher STARTTLS avec le port 465 renvoyait un faux « délai de connexion
  dépassé (15s) » au lieu d'expliquer l'inversion port/mode de sécurité ;
- le TEST de connexion passait mais l'ENVOI réel expirait : send() ne
  passait pas `use_tls` à aiosmtplib (SSL direct jamais activé à l'envoi) ;
- les erreurs IMAP/SMTP brutes en anglais ([AUTHENTICATIONFAILED],
  535 5.7.8...) sont inexploitables pour un non-technicien.
"""

import asyncio
import ssl
from unittest.mock import AsyncMock, patch

import aiosmtplib
import pytest
from app.services.email.base_provider import SendEmailRequest
from app.services.email.imap_smtp_provider import (
    ImapSmtpProvider,
    _humanize_imap_error,
    _humanize_smtp_error,
    _smtp_security_hint,
)


def make_provider(**overrides) -> ImapSmtpProvider:
    params = {
        "email_address": "test@exemple.fr",
        "password": "secret",
        "imap_host": "imap.exemple.fr",
        "smtp_host": "smtp.exemple.fr",
        "smtp_port": 465,
        "smtp_use_tls": False,  # SSL direct
    }
    params.update(overrides)
    return ImapSmtpProvider(**params)


class TestSmtpSecurityHint:
    def test_port_465_avec_starttls_est_signale(self):
        hint = _smtp_security_hint(465, use_starttls=True)
        assert hint is not None
        assert "465" in hint
        assert "SSL/TLS directe" in hint

    def test_port_587_sans_starttls_est_signale(self):
        hint = _smtp_security_hint(587, use_starttls=False)
        assert hint is not None
        assert "587" in hint
        assert "STARTTLS" in hint

    def test_combinaisons_coherentes_sans_hint(self):
        assert _smtp_security_hint(465, use_starttls=False) is None
        assert _smtp_security_hint(587, use_starttls=True) is None
        assert _smtp_security_hint(25, use_starttls=True) is None


class TestHumanizeErrors:
    def test_smtp_auth_refusee_mentionne_mot_de_passe_application(self):
        e = aiosmtplib.SMTPAuthenticationError(535, "5.7.8 authentication failed")
        msg = _humanize_smtp_error(e, 587, True)
        assert "identifiants refusés" in msg
        assert "mot de passe" in msg
        assert "authentication failed" not in msg  # plus d'anglais brut

    def test_smtp_serveur_introuvable(self):
        e = OSError("[Errno 8] nodename nor servname provided, or not known")
        msg = _humanize_smtp_error(e, 587, True)
        assert "serveur introuvable" in msg.lower()

    def test_smtp_erreur_ssl_donne_le_hint_port_mode(self):
        e = ssl.SSLError("wrong version number")
        msg = _humanize_smtp_error(e, 465, True)
        assert "SSL/TLS" in msg
        assert "465" in msg  # le hint port/mode est inclus

    def test_smtp_erreur_inconnue_reste_visible(self):
        e = RuntimeError("erreur exotique 42")
        msg = _humanize_smtp_error(e, 587, True)
        assert "erreur exotique 42" in msg

    def test_imap_authenticationfailed_traduit(self):
        e = Exception("b'[AUTHENTICATIONFAILED] Invalid credentials (Failure)'")
        msg = _humanize_imap_error(e)
        assert "identifiants refusés" in msg
        assert "mot de passe" in msg

    def test_imap_serveur_introuvable(self):
        e = OSError("[Errno -2] Name or service not known")
        msg = _humanize_imap_error(e)
        assert "serveur introuvable" in msg.lower()


class TestSendUsesSameSecurityAsTest:
    """Régression : send() doit passer les MÊMES options TLS que test_connection."""

    @pytest.mark.asyncio
    async def test_send_ssl_direct_passe_use_tls(self):
        provider = make_provider(smtp_port=465, smtp_use_tls=False)
        request = SendEmailRequest(to=["dest@exemple.fr"], subject="Test", body="Corps")

        with patch("app.services.email.imap_smtp_provider.aiosmtplib.send", new=AsyncMock()) as mock_send:
            await provider.send_message(request)

        kwargs = mock_send.call_args.kwargs
        assert kwargs["use_tls"] is True  # SSL direct activé à l'envoi
        assert kwargs["start_tls"] is False
        assert kwargs["timeout"] is not None

    @pytest.mark.asyncio
    async def test_send_starttls_passe_start_tls(self):
        provider = make_provider(smtp_port=587, smtp_use_tls=True)
        request = SendEmailRequest(to=["dest@exemple.fr"], subject="Test", body="Corps")

        with patch("app.services.email.imap_smtp_provider.aiosmtplib.send", new=AsyncMock()) as mock_send:
            await provider.send_message(request)

        kwargs = mock_send.call_args.kwargs
        assert kwargs["use_tls"] is False
        assert kwargs["start_tls"] is True

    @pytest.mark.asyncio
    async def test_send_timeout_donne_message_causal(self):
        provider = make_provider(smtp_port=465, smtp_use_tls=True)  # combinaison incohérente
        request = SendEmailRequest(to=["dest@exemple.fr"], subject="Test", body="Corps")

        with patch(
            "app.services.email.imap_smtp_provider.aiosmtplib.send",
            new=AsyncMock(side_effect=asyncio.TimeoutError()),
        ), pytest.raises(RuntimeError) as exc:
            await provider.send_message(request)

        assert "465" in str(exc.value)
        assert "SSL/TLS directe" in str(exc.value)


class TestConnectionTimeoutMessage:
    @pytest.mark.asyncio
    async def test_timeout_smtp_465_starttls_message_causal(self):
        provider = make_provider(smtp_port=465, smtp_use_tls=True)

        # IMAP OK (mocké), SMTP timeout : le message doit expliquer
        # l'inversion port/mode, pas juste « délai dépassé ».
        with patch.object(provider, "_connect_mailbox"), patch(
            "app.services.email.imap_smtp_provider.aiosmtplib.SMTP"
        ) as mock_smtp_cls:
            mock_smtp_cls.return_value.connect = AsyncMock(side_effect=asyncio.TimeoutError())
            result = await provider.test_connection()

        assert result["smtp_ok"] is False
        assert "465" in result["message"]
        assert "SSL/TLS directe" in result["message"]


class TestImapToDtoSanitizesHtml:
    """Défense en profondeur (dette 09/06/2026) : le body_html d'un mail IMAP
    n'était jamais sanitisé côté backend, contrairement aux signatures (nh3).
    Sûr tant que le seul point de rendu est le sanitizer front, fragile sinon.
    """

    def _fake_msg(self, html: str | None):
        from types import SimpleNamespace

        return SimpleNamespace(
            uid="42",
            subject="Sujet",
            text="Corps texte",
            html=html,
            from_="expediteur@exemple.fr",
            to=("dest@exemple.fr",),
            cc=(),
            date=None,
            flags=(),
            attachments=[],
        )

    def test_retire_le_script_du_body_html(self):
        provider = make_provider()
        msg = self._fake_msg("<p>Bonjour</p><script>alert(1)</script>")

        dto = provider._imap_to_dto(msg)

        assert "<script>" not in dto.body_html
        assert "Bonjour" in dto.body_html

    def test_laisse_le_body_html_absent_intact(self):
        provider = make_provider()
        msg = self._fake_msg(None)

        dto = provider._imap_to_dto(msg)

        assert dto.body_html is None
