"""
THERESE v2 - IMAP/SMTP Provider

Generic IMAP/SMTP implementation of EmailProvider.
Supports any standard IMAP/SMTP server (Gmail, Outlook, Fastmail, etc.)

BUG-095: Robust timeout and error handling matching test_connection's approach.
"""

import asyncio
import logging
import ssl
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
from app.services.html_sanitizer import sanitize_html
from imap_tools import AND, OR, MailBox, MailMessage

logger = logging.getLogger(__name__)

# Timeout for IMAP operations (seconds).
# test_connection uses 15s; data operations get more time because
# fetching many messages legitimately takes longer than a handshake.
IMAP_CONNECT_TIMEOUT = 15
IMAP_OPERATION_TIMEOUT = 30


def _smtp_security_hint(port: int, use_starttls: bool) -> str | None:
    """Détecte une combinaison port/mode de sécurité incohérente.

    Les deux conventions dominantes : 465 = SSL/TLS direct (implicite),
    587 = STARTTLS. Une inversion ne produit AUCUNE erreur explicite côté
    serveur (chacun attend l'autre) - juste un timeout muet, illisible pour
    un non-technicien (retour Dr_logic-3D, 05/07/2026).
    """
    if port == 465 and use_starttls:
        return (
            "Le port 465 attend une connexion SSL/TLS directe : "
            "décoche « Utiliser TLS/STARTTLS » (ou passe au port 587 en gardant STARTTLS)."
        )
    if port == 587 and not use_starttls:
        return (
            "Le port 587 attend du STARTTLS : "
            "coche « Utiliser TLS/STARTTLS » (ou passe au port 465 en SSL direct)."
        )
    return None


def _humanize_smtp_error(e: Exception, port: int, use_starttls: bool) -> str:
    """Traduit une erreur SMTP brute en message français actionnable."""
    text = str(e)
    lower = text.lower()
    if isinstance(e, aiosmtplib.SMTPAuthenticationError) or "535" in text or "authentication" in lower:
        return (
            "SMTP : identifiants refusés par le serveur. Vérifie l'adresse email et le "
            "mot de passe - pour Gmail, Outlook ou Yahoo, il faut un « mot de passe "
            "d'application », pas le mot de passe du compte."
        )
    if isinstance(e, (ConnectionRefusedError, aiosmtplib.SMTPConnectError)) or "refused" in lower:
        hint = _smtp_security_hint(port, use_starttls)
        return f"SMTP : connexion refusée par le serveur (port {port}). " + (
            hint or "Vérifie l'adresse du serveur et le port."
        )
    if "getaddrinfo" in lower or "name or service" in lower or "nodename" in lower:
        return "SMTP : serveur introuvable. Vérifie l'adresse du serveur SMTP (ex. smtp.monfournisseur.fr)."
    if isinstance(e, ssl.SSLError) or "ssl" in lower or "tls" in lower:
        hint = _smtp_security_hint(port, use_starttls)
        return "SMTP : échec de la négociation SSL/TLS. " + (
            hint or "Vérifie le mode de sécurité choisi et le port."
        )
    return f"SMTP : {text}"


def _humanize_imap_error(e: Exception) -> str:
    """Traduit une erreur IMAP brute en message français actionnable."""
    text = str(e)
    lower = text.lower()
    if "authenticationfailed" in lower.replace(" ", "") or "login failed" in lower or "invalid credentials" in lower:
        return (
            "IMAP : identifiants refusés par le serveur. Vérifie l'adresse email et le "
            "mot de passe - pour Gmail, Outlook ou Yahoo, il faut un « mot de passe "
            "d'application », pas le mot de passe du compte."
        )
    if "getaddrinfo" in lower or "name or service" in lower or "nodename" in lower:
        return "IMAP : serveur introuvable. Vérifie l'adresse du serveur IMAP (ex. imap.monfournisseur.fr)."
    if isinstance(e, ConnectionRefusedError) or "refused" in lower:
        return "IMAP : connexion refusée par le serveur. Vérifie l'adresse du serveur et le port (993 en SSL)."
    if isinstance(e, ssl.SSLError) or "ssl" in lower:
        return "IMAP : échec de la négociation SSL. Vérifie le port (993 = SSL, 143 = sans SSL) et l'option SSL."
    return f"IMAP : {text}"


def _make_ssl_context() -> ssl.SSLContext:
    """
    Create a permissive SSL context for private/self-signed IMAP servers.

    Some corporate or small-provider IMAP servers use certificates that
    fail strict verification (self-signed, expired intermediate, wrong CN).
    We try the system default first; the caller falls back to this only
    when the default context raises an SSL error.
    """
    ctx = ssl.create_default_context()
    # Private providers may have certificate issues - be lenient
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


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
    # Connection Helpers
    # ============================================================

    def _create_mailbox(self, timeout: int = IMAP_CONNECT_TIMEOUT) -> MailBox:
        """
        Create a MailBox instance with socket-level timeout.

        Uses the system SSL context first; falls back to a permissive
        context for private providers with certificate issues.
        """
        return MailBox(
            self._imap_host,
            self._imap_port,
            timeout=timeout,
        )

    def _create_mailbox_permissive(self, timeout: int = IMAP_CONNECT_TIMEOUT) -> MailBox:
        """
        Create a MailBox with permissive SSL for servers with cert issues.
        """
        return MailBox(
            self._imap_host,
            self._imap_port,
            timeout=timeout,
            ssl_context=_make_ssl_context(),
        )

    def _connect_mailbox(
        self,
        initial_folder: str = "INBOX",
        timeout: int = IMAP_CONNECT_TIMEOUT,
    ) -> MailBox:
        """
        Connect and login to IMAP, with automatic SSL fallback.

        Tries standard SSL first, then falls back to permissive SSL
        if the server has certificate issues.

        Returns a logged-in MailBox context manager (use with `with`).
        """
        try:
            mb = self._create_mailbox(timeout=timeout)
            return mb.login(self._email, self._password, initial_folder=initial_folder)
        except ssl.SSLError as e:
            logger.warning(
                f"IMAP SSL error for {self._imap_host}, retrying with permissive SSL: {e}"
            )
            mb = self._create_mailbox_permissive(timeout=timeout)
            return mb.login(self._email, self._password, initial_folder=initial_folder)

    async def _run_imap_operation(
        self,
        sync_fn,
        timeout: float = IMAP_OPERATION_TIMEOUT,
        operation_name: str = "IMAP",
    ):
        """
        Run a synchronous IMAP function in an executor with async timeout.

        This is the central pattern used by all IMAP operations to ensure
        consistent timeout handling matching test_connection's approach.

        Args:
            sync_fn: Synchronous callable to execute
            timeout: Maximum seconds to wait
            operation_name: Name for error messages

        Raises:
            TimeoutError: If operation exceeds timeout
            Exception: Re-raised from the sync function
        """
        loop = asyncio.get_running_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(None, sync_fn),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.error(
                f"{operation_name} timeout ({timeout}s) for {self._imap_host}"
            )
            raise TimeoutError(
                f"{operation_name} : delai depasse ({timeout}s) "
                f"pour {self._imap_host}"
            )

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
        """List messages from IMAP folder with timeout and error handling."""
        folder_name = folder or "INBOX"

        # Calculate offset from page token
        offset = int(page_token) if page_token else 0

        def _sync_fetch():
            with self._connect_mailbox(
                initial_folder=folder_name,
                timeout=IMAP_CONNECT_TIMEOUT,
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

        return await self._run_imap_operation(
            _sync_fetch,
            timeout=IMAP_OPERATION_TIMEOUT,
            operation_name="IMAP list_messages",
        )

    # BUG-122 : correspondance label Gmail-style -> dossier IMAP réel.
    # (flag special-use RFC 6154, puis heuristique de nom multi-langue).
    _SPECIAL_FOLDER_MATCH: dict[str, tuple[str, tuple[str, ...]]] = {
        "SENT": ("\\Sent", ("sent", "envoy", "gesendet", "enviad")),
        "DRAFTS": ("\\Drafts", ("draft", "brouillon")),
        "DRAFT": ("\\Drafts", ("draft", "brouillon")),
        "TRASH": ("\\Trash", ("trash", "deleted", "corbeille")),
        "SPAM": ("\\Junk", ("junk", "spam", "pourriel", "indésirable")),
    }

    async def resolve_folder_for_label(self, label: str) -> str | None:
        """Nom réel du dossier IMAP pour un label Gmail-style (SENT, DRAFTS...).

        Priorité aux flags special-use RFC 6154 (\\Sent, \\Drafts...), repli sur
        une heuristique de nom (multi-langue). None pour INBOX/label inconnu :
        l'appelant garde alors l'INBOX. Corrige BUG-122 (onglet Envoyé montrait
        l'INBOX car label_ids était ignoré côté IMAP)."""
        match = self._SPECIAL_FOLDER_MATCH.get((label or "").upper())
        if match is None:
            return None
        wanted_flag, name_hints = match

        def _sync() -> str | None:
            with self._connect_mailbox(timeout=IMAP_CONNECT_TIMEOUT) as mailbox:
                infos = list(mailbox.folder.list())
                # 1. Flag special-use (fiable, indépendant de la langue).
                for fi in infos:
                    if any(f.lower() == wanted_flag.lower() for f in (fi.flags or ())):
                        return fi.name
                # 2. Heuristique de nom sur la feuille du chemin.
                for fi in infos:
                    leaf = fi.name.split(fi.delim)[-1] if fi.delim else fi.name
                    if any(h in leaf.lower() for h in name_hints):
                        return fi.name
            return None

        folder_name: str | None = await self._run_imap_operation(
            _sync,
            timeout=IMAP_OPERATION_TIMEOUT,
            operation_name="IMAP resolve_folder",
        )
        return folder_name

    async def get_message(
        self,
        message_id: str,
        include_body: bool = True,
        include_attachments: bool = False,
    ) -> EmailMessageDTO:
        """Get a single message from IMAP with timeout."""

        def _sync_fetch():
            with self._connect_mailbox(timeout=IMAP_CONNECT_TIMEOUT) as mailbox:
                # Search by UID
                for msg in mailbox.fetch(AND(uid=message_id)):
                    return self._imap_to_dto(msg, include_attachments=include_attachments)
                raise ValueError(f"Message {message_id} not found")

        return await self._run_imap_operation(
            _sync_fetch,
            timeout=IMAP_OPERATION_TIMEOUT,
            operation_name="IMAP get_message",
        )

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

        # Mêmes options de sécurité que test_connection : sans `use_tls`
        # explicite, un compte configuré en SSL direct (port 465, STARTTLS
        # décoché) passait le TEST mais l'ENVOI partait en clair et expirait
        # (retour Dr_logic-3D, 05/07/2026).
        try:
            await aiosmtplib.send(
                msg,
                hostname=self._smtp_host,
                port=self._smtp_port,
                username=self._email,
                password=self._password,
                use_tls=not self._smtp_use_tls,
                start_tls=self._smtp_use_tls,
                timeout=IMAP_OPERATION_TIMEOUT,
                recipients=all_recipients,
            )
        except asyncio.TimeoutError:
            hint = _smtp_security_hint(self._smtp_port, self._smtp_use_tls)
            raise RuntimeError(
                f"SMTP : délai dépassé ({IMAP_OPERATION_TIMEOUT}s) pendant l'envoi. "
                + (hint or "Vérifie la connexion et la configuration du serveur SMTP.")
            ) from None
        except aiosmtplib.errors.SMTPException as e:
            raise RuntimeError(
                _humanize_smtp_error(e, self._smtp_port, self._smtp_use_tls)
            ) from e

        # Return a generated ID (SMTP doesn't return one)
        return f"sent_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"

    async def create_draft(self, request: SendEmailRequest) -> str:
        """Create a draft in IMAP Drafts folder with timeout."""

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

            with self._connect_mailbox(timeout=IMAP_CONNECT_TIMEOUT) as mailbox:
                # Find Drafts folder
                drafts_folder = "Drafts"
                for folder in mailbox.folder.list():
                    if "draft" in folder.name.lower():
                        drafts_folder = folder.name
                        break

                # Append to Drafts
                mailbox.append(msg.as_bytes(), drafts_folder, dt=datetime.now())

            return f"draft_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"

        return await self._run_imap_operation(
            _sync_create,
            timeout=IMAP_OPERATION_TIMEOUT,
            operation_name="IMAP create_draft",
        )

    async def modify_message(
        self,
        message_id: str,
        add_labels: list[str] | None = None,
        remove_labels: list[str] | None = None,
        mark_read: bool | None = None,
        mark_starred: bool | None = None,
    ) -> EmailMessageDTO:
        """Modify message flags in IMAP with timeout."""

        def _sync_modify():
            with self._connect_mailbox(timeout=IMAP_CONNECT_TIMEOUT) as mailbox:
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

        return await self._run_imap_operation(
            _sync_modify,
            timeout=IMAP_OPERATION_TIMEOUT,
            operation_name="IMAP modify_message",
        )

    async def delete_message(self, message_id: str, permanent: bool = False) -> None:
        """Delete a message from IMAP with timeout."""

        def _sync_delete():
            with self._connect_mailbox(timeout=IMAP_CONNECT_TIMEOUT) as mailbox:
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

        await self._run_imap_operation(
            _sync_delete,
            timeout=IMAP_OPERATION_TIMEOUT,
            operation_name="IMAP delete_message",
        )

    async def move_message(self, message_id: str, destination_folder: str) -> EmailMessageDTO:
        """Move a message to another folder in IMAP with timeout."""

        def _sync_move():
            with self._connect_mailbox(timeout=IMAP_CONNECT_TIMEOUT) as mailbox:
                mailbox.move([message_id], destination_folder)

                # Fetch from new location
                mailbox.folder.set(destination_folder)
                for msg in mailbox.fetch(AND(uid=message_id)):
                    return self._imap_to_dto(msg)

                raise ValueError(f"Message {message_id} not found after move")

        return await self._run_imap_operation(
            _sync_move,
            timeout=IMAP_OPERATION_TIMEOUT,
            operation_name="IMAP move_message",
        )

    # ============================================================
    # Folder Operations
    # ============================================================

    async def list_folders(self) -> list[EmailFolderDTO]:
        """List all IMAP folders with timeout."""

        def _sync_list():
            folders = []
            with self._connect_mailbox(timeout=IMAP_CONNECT_TIMEOUT) as mailbox:
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
                    except Exception as e:
                        logger.debug("Dossier IMAP non selectionnable, fallback: %s", e)
                        # Folder exists but can't be selected (e.g., parent folder)
                        folders.append(EmailFolderDTO(
                            id=folder_info.name,
                            name=folder_info.name.split(folder_info.delim)[-1] if folder_info.delim else folder_info.name,
                            type="user",
                            path=folder_info.name,
                            delimiter=folder_info.delim,
                        ))

            return folders

        return await self._run_imap_operation(
            _sync_list,
            timeout=IMAP_OPERATION_TIMEOUT,
            operation_name="IMAP list_folders",
        )

    async def create_folder(self, name: str, parent: str | None = None) -> EmailFolderDTO:
        """Create a new IMAP folder with timeout."""

        def _sync_create():
            with self._connect_mailbox(timeout=IMAP_CONNECT_TIMEOUT) as mailbox:
                folder_name = f"{parent}/{name}" if parent else name
                mailbox.folder.create(folder_name)

                return EmailFolderDTO(
                    id=folder_name,
                    name=name,
                    type="user",
                    path=folder_name,
                )

        return await self._run_imap_operation(
            _sync_create,
            timeout=IMAP_OPERATION_TIMEOUT,
            operation_name="IMAP create_folder",
        )

    async def delete_folder(self, folder_id: str) -> None:
        """Delete an IMAP folder with timeout."""

        def _sync_delete():
            with self._connect_mailbox(timeout=IMAP_CONNECT_TIMEOUT) as mailbox:
                mailbox.folder.delete(folder_id)

        await self._run_imap_operation(
            _sync_delete,
            timeout=IMAP_OPERATION_TIMEOUT,
            operation_name="IMAP delete_folder",
        )

    # ============================================================
    # Attachment Operations
    # ============================================================

    async def get_attachment(
        self,
        message_id: str,
        attachment_id: str,
    ) -> EmailAttachmentDTO:
        """Get attachment content from IMAP message with timeout."""

        def _sync_fetch():
            with self._connect_mailbox(timeout=IMAP_CONNECT_TIMEOUT) as mailbox:
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

        return await self._run_imap_operation(
            _sync_fetch,
            timeout=IMAP_OPERATION_TIMEOUT,
            operation_name="IMAP get_attachment",
        )

    # ============================================================
    # Account Operations
    # ============================================================

    async def get_profile(self) -> dict[str, str]:
        """Get account profile (email address)."""
        return {
            "email": self._email,
            "provider": "imap",
            "imap_host": self._imap_host,
            "smtp_host": self._smtp_host,
        }

    async def test_connection(self) -> dict:
        """Test IMAP and SMTP connections with timeout."""

        # Test IMAP - uses the same _connect_mailbox as all other operations
        def _sync_test_imap():
            try:
                with self._connect_mailbox(timeout=IMAP_CONNECT_TIMEOUT) as _mailbox:
                    return {"ok": True, "message": "IMAP OK"}
            except Exception as e:
                logger.error(f"IMAP connection test failed: {e}")
                return {"ok": False, "message": _humanize_imap_error(e)}

        loop = asyncio.get_running_loop()
        try:
            imap_result = await asyncio.wait_for(
                loop.run_in_executor(None, _sync_test_imap),
                timeout=IMAP_CONNECT_TIMEOUT + 5,
            )
        except asyncio.TimeoutError:
            imap_result = {
                "ok": False,
                "message": f"IMAP : delai de connexion depasse ({IMAP_CONNECT_TIMEOUT}s)",
            }

        # Test SMTP
        try:
            smtp = aiosmtplib.SMTP(
                hostname=self._smtp_host,
                port=self._smtp_port,
                use_tls=not self._smtp_use_tls,
                start_tls=self._smtp_use_tls,
                timeout=IMAP_CONNECT_TIMEOUT,
            )
            await asyncio.wait_for(smtp.connect(), timeout=IMAP_CONNECT_TIMEOUT)
            await smtp.login(self._email, self._password)
            await smtp.quit()
            smtp_result = {"ok": True, "message": "SMTP OK"}
        except asyncio.TimeoutError:
            # Un timeout muet cache le plus souvent une inversion port/mode
            # de sécurité (465 = SSL direct, 587 = STARTTLS) : le dire.
            hint = _smtp_security_hint(self._smtp_port, self._smtp_use_tls)
            smtp_result = {
                "ok": False,
                "message": (
                    f"SMTP : délai de connexion dépassé ({IMAP_CONNECT_TIMEOUT}s). "
                    + (hint or "Vérifie l'adresse du serveur, le port et le mode de sécurité.")
                ),
            }
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            smtp_result = {
                "ok": False,
                "message": _humanize_smtp_error(e, self._smtp_port, self._smtp_use_tls),
            }

        success = imap_result["ok"] and smtp_result["ok"]
        if success:
            message = "Connexion IMAP et SMTP reussie"
        else:
            parts = []
            if not imap_result["ok"]:
                parts.append(imap_result["message"])
            if not smtp_result["ok"]:
                parts.append(smtp_result["message"])
            message = " | ".join(parts)

        return {
            "success": success,
            "imap_ok": imap_result["ok"],
            "smtp_ok": smtp_result["ok"],
            "message": message,
        }

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
            # Défense en profondeur : sanitisé aussi ici (cf gmail_service.py
            # format_message_for_storage, même politique nh3).
            body_html=sanitize_html(msg.html) if msg.html else msg.html,
            has_attachments=len(msg.attachments) > 0,
            attachment_count=len(msg.attachments),
            attachments=attachments,
            labels=[],  # IMAP uses folders, not labels
            size_bytes=0,  # Not easily available in imap-tools
        )
