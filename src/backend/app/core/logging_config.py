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

# Patterns de secrets a masquer dans les logs
_SECRET_PATTERNS = re.compile(
    r"("
    r"(?:api[_-]?key|token|password|secret|auth|credential|private[_-]?key|access[_-]?key)"
    r"\s*[:=]\s*"
    r")"
    r"(['\"]?[A-Za-z0-9+/=_\-]{8,}['\"]?)",
    re.IGNORECASE,
)

# Patterns supplementaires pour les cles API brutes (Bearer tokens, sk-xxx, gAAAAA, etc.)
_BARE_SECRET_PATTERNS = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|gAAAAA[A-Za-z0-9+/=_\-]{20,}|Bearer\s+[A-Za-z0-9+/=_\-]{20,})",
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

        # Ajouter l'exception si presente
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False, default=str)


class ReadableFormatter(logging.Formatter):
    """Formateur lisible pour la console (developpement)."""

    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


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
    log_dir = Path.home() / ".therese" / "logs"
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
