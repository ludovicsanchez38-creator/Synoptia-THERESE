"""
THERESE v2 - Configuration du logging structure

Logs JSON en fichier (rotation 10 Mo, 5 fichiers) + console lisible pour le dev.
Masquage automatique des secrets dans les messages de log.
"""

import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

# Patterns de secrets a masquer dans les logs.
#
# Le separateur accepte aussi l'ESPACE : les fournisseurs ecrivent souvent
# « invalid api key sk-... » dans leurs messages d'erreur, sans deux-points.
_SECRET_PATTERNS = re.compile(
    r"("
    r"(?:api[_-]?key|token|password|secret|auth|credential|private[_-]?key|access[_-]?key)"
    r"\s*[:=]\s*"
    r")"
    r"(['\"]?[A-Za-z0-9+/=_\-]{8,}['\"]?)",
    re.IGNORECASE,
)

# Cles d'API brutes.
#
# CORRECTIF du 24/08/2026 : l'ancien motif exigeait `sk-` suivi de caracteres
# ALPHANUMERIQUES uniquement. Or les cles OpenAI modernes portent un prefixe a
# tiret - `sk-proj-...`, `sk-svcacct-...`, `sk-admin-...` - et n'etaient donc
# JAMAIS masquees. Verifie : `_mask_secrets("sk-proj-SECRET42")` rendait la
# chaine intacte.
#
# Les prefixes des autres fournisseurs sont ajoutes au passage : une cle qui
# fuit dans un rapport de bug colle sur Discord est compromise, quel que soit
# son emetteur.
_BARE_SECRET_PATTERNS = re.compile(
    r"(?<![A-Za-z0-9])("
    # Seuil bas assume : tres peu de texte francais ou anglais commence par
    # « sk- », alors qu'une cle tronquee dans un message d'erreur reste une cle.
    r"sk-[A-Za-z0-9_\-]{8,}"           # OpenAI, y compris sk-proj- et sk-ant-
    r"|xai-[A-Za-z0-9_\-]{16,}"        # xAI
    r"|AIza[A-Za-z0-9_\-]{20,}"        # Google
    r"|gsk_[A-Za-z0-9_\-]{16,}"        # Groq
    r"|glpat-[A-Za-z0-9_\-]{16,}"      # GitLab
    r"|gh[pousr]_[A-Za-z0-9]{16,}"      # GitHub
    r"|gAAAAA[A-Za-z0-9+/=_\-]{20,}"   # Fernet (nos propres secrets chiffres)
    r"|Bearer\s+[A-Za-z0-9+/=_\-\.]{20,}"
    r")",
    re.IGNORECASE,
)


def _mask_secrets(message: str) -> str:
    """Masque les secrets detectes dans un message de log."""
    if not isinstance(message, str):
        return message
    # Masquer les patterns cle=valeur
    result = _SECRET_PATTERNS.sub(r"\1***MASKED***", message)
    # Masquer les tokens bruts
    result = _BARE_SECRET_PATTERNS.sub("***MASKED***", result)
    return result


class SecretMaskingFilter(logging.Filter):
    """Filtre qui masque les secrets dans les messages de log."""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.msg and isinstance(record.msg, str):
            record.msg = _mask_secrets(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: _mask_secrets(str(v)) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    _mask_secrets(str(a)) if isinstance(a, str) else a
                    for a in record.args
                )
        return True


class JSONFormatter(logging.Formatter):
    """Formateur JSON structure pour les fichiers de log."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }

        # Ajouter les extras pertinents (pas les champs internes de logging)
        _internal_keys = {
            "name", "msg", "args", "created", "relativeCreated",
            "thread", "threadName", "msecs", "filename", "funcName",
            "levelno", "lineno", "module", "exc_info", "exc_text",
            "stack_info", "levelname", "pathname", "processName",
            "process", "message", "taskName",
        }
        extras = {
            k: v for k, v in record.__dict__.items()
            if k not in _internal_keys and not k.startswith("_")
        }
        if extras:
            log_entry["extra"] = extras

        # Ajouter l'exception si presente.
        # Le filtre de secrets ne voit que `record.msg` et `record.args` : la
        # trace, elle, est formatee ici et lui echappait. Or un message d'erreur
        # de fournisseur contient parfois la requete, donc l'en-tete
        # d'autorisation, donc la cle. Ces journaux sont lus, copies et colles
        # dans des rapports de bug - c'est meme ce que font nos testeurs.
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = _mask_secrets(self.formatException(record.exc_info))

        return json.dumps(log_entry, ensure_ascii=False, default=str)


class ReadableFormatter(logging.Formatter):
    """Formateur lisible pour la console (developpement)."""

    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def formatException(self, ei: Any) -> str:  # noqa: N802 (nom stdlib)
        """Masque les secrets dans la trace, comme pour le format JSON.

        C'est cette sortie-la que les testeurs copient : le sidecar ecrit sur la
        console, et un rapport de bug contient souvent ces lignes telles quelles.
        """
        return _mask_secrets(super().formatException(ei))


def dossier_des_journaux() -> Path:
    """Le dossier des journaux, DANS le dossier de donnees.

    Il valait `~/.therese/logs` en dur. La campagne dix personas l'a demontre
    en conditions reelles : chaque persona tournait sur une installation
    jetable via `THERESE_DATA_DIR`, et les journaux - qui portent les arguments
    COMPLETS des outils, donc des noms de contacts, des objets de mails, des
    montants - atterrissaient dans l'installation reelle.

    Le lot A de la 0.54 a corrige ce que l'ecran AFFIRMAIT sur l'isolation.
    Celui-ci corrige ce que l'application FAIT.
    """
    from app.config import settings

    base = settings.data_dir or (Path.home() / ".therese")
    return Path(base) / "logs"


def setup_logging() -> None:
    """Configure le logging structure pour THERESE.

    - Console : format lisible (pas JSON)
    - Fichier : JSON structure avec rotation (10 Mo, 5 fichiers)
    - Masquage automatique des secrets
    - Niveau configurable via THERESE_LOG_LEVEL (defaut: INFO)
    """
    # Niveau de log configurable
    log_level_name = os.environ.get("THERESE_LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    # Chemin des logs
    log_dir = dossier_des_journaux()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "therese.log"

    # Filtre de masquage des secrets (partage)
    secret_filter = SecretMaskingFilter()

    # --- Root logger ---
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Supprimer les handlers existants (eviter les doublons si appele 2 fois)
    root_logger.handlers.clear()

    # --- Console handler (lisible) ---
    # Le handler fichier force utf-8 (plus bas) ; la console, elle, héritait de
    # l'encodage du terminal. Sur une console Windows en cp1252, « Jérôme »
    # s'écrivait « J?r?me » dans les journaux du sidecar. Un diagnostic sur un
    # nom français en devenait illisible, précisément quand on en a besoin.
    _flux = sys.stdout
    if hasattr(_flux, "reconfigure"):
        try:
            _flux.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            # Flux non reconfigurable (redirigé, capturé par les tests) : on
            # garde le comportement d'origine plutôt que d'empêcher le
            # démarrage pour une question de journalisation.
            pass
    console_handler = logging.StreamHandler(_flux)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(ReadableFormatter())
    console_handler.addFilter(secret_filter)
    root_logger.addHandler(console_handler)

    # --- File handler (JSON structure avec rotation) ---
    file_handler = RotatingFileHandler(
        filename=str(log_file),
        maxBytes=10 * 1024 * 1024,  # 10 Mo
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(JSONFormatter())
    file_handler.addFilter(secret_filter)
    root_logger.addHandler(file_handler)

    # Reduire la verbosite des bibliotheques tierces
    for noisy_logger in [
        "httpx", "httpcore", "uvicorn.access", "watchfiles",
        "hpack", "h2", "h11",
    ]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        "Logging configure : console (lisible) + fichier JSON (%s), niveau=%s",
        log_file,
        log_level_name,
    )
