"""
THERESE v2 - Error Handler Service

Gestion centralisee des erreurs avec messages clairs.

US-ERR-01: Messages d'erreur clairs si API down
US-ERR-02: Retry automatique en cas de timeout
US-ERR-03: Mode degrade si Qdrant indisponible
"""

import logging
import asyncio
from typing import Optional, Callable, TypeVar, Any
from functools import wraps
from enum import Enum

import httpx

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ErrorCode(str, Enum):
    """Codes d'erreur standardises."""

    # API/Network errors
    API_UNREACHABLE = "api_unreachable"
    API_TIMEOUT = "api_timeout"
    API_RATE_LIMITED = "api_rate_limited"
    API_AUTH_FAILED = "api_auth_failed"
    API_SERVER_ERROR = "api_server_error"

    # LLM errors
    LLM_PROVIDER_UNAVAILABLE = "llm_provider_unavailable"
    LLM_CONTEXT_TOO_LONG = "llm_context_too_long"
    LLM_GENERATION_FAILED = "llm_generation_failed"

    # Database errors
    DB_CONNECTION_FAILED = "db_connection_failed"
    DB_QUERY_FAILED = "db_query_failed"

    # Qdrant errors
    QDRANT_UNAVAILABLE = "qdrant_unavailable"
    QDRANT_SEARCH_FAILED = "qdrant_search_failed"

    # MCP errors
    MCP_SERVER_FAILED = "mcp_server_failed"
    MCP_TOOL_FAILED = "mcp_tool_failed"

    # File errors
    FILE_NOT_FOUND = "file_not_found"
    FILE_TOO_LARGE = "file_too_large"
    FILE_PARSE_FAILED = "file_parse_failed"

    # General
    VALIDATION_ERROR = "validation_error"
    UNKNOWN_ERROR = "unknown_error"


# Messages d'erreur en francais (US-ERR-01)
ERROR_MESSAGES = {
    ErrorCode.API_UNREACHABLE: "Le service {service} est temporairement indisponible. Verifiez votre connexion internet.",
    ErrorCode.API_TIMEOUT: "Le service {service} met trop de temps a repondre. Nouvelle tentative en cours...",
    ErrorCode.API_RATE_LIMITED: "Trop de requetes envoyees. Attendez quelques instants avant de reessayer.",
    ErrorCode.API_AUTH_FAILED: "Cle API {provider} invalide ou expiree. Verifiez vos parametres.",
    ErrorCode.API_SERVER_ERROR: "Erreur serveur chez {provider}. L'equipe technique est probablement au courant.",
    ErrorCode.LLM_PROVIDER_UNAVAILABLE: "Le modele {model} n'est pas disponible. Essayez un autre provider.",
    ErrorCode.LLM_CONTEXT_TOO_LONG: "Le message est trop long ({tokens} tokens). Raccourcissez-le ou commencez une nouvelle conversation.",
    ErrorCode.LLM_GENERATION_FAILED: "La generation de reponse a echoue. Reessayez dans quelques instants.",
    ErrorCode.DB_CONNECTION_FAILED: "Impossible de se connecter a la base de donnees locale.",
    ErrorCode.DB_QUERY_FAILED: "Erreur lors de l'acces aux donnees. Redemarrez l'application si le probleme persiste.",
    ErrorCode.QDRANT_UNAVAILABLE: "La recherche semantique est temporairement indisponible. Le chat fonctionne sans memoire.",
    ErrorCode.QDRANT_SEARCH_FAILED: "La recherche dans la memoire a echoue. Resultat partiel possible.",
    ErrorCode.MCP_SERVER_FAILED: "Le serveur MCP {server} n'a pas pu demarrer. Verifiez la configuration.",
    ErrorCode.MCP_TOOL_FAILED: "L'outil {tool} a rencontre une erreur: {error}",
    ErrorCode.FILE_NOT_FOUND: "Fichier introuvable: {path}",
    ErrorCode.FILE_TOO_LARGE: "Le fichier est trop volumineux ({size} Mo). Limite: {limit} Mo.",
    ErrorCode.FILE_PARSE_FAILED: "Impossible de lire le fichier {filename}. Format non supporte ou fichier corrompu.",
    ErrorCode.VALIDATION_ERROR: "Donnees invalides: {details}",
    ErrorCode.UNKNOWN_ERROR: "Une erreur inattendue s'est produite. Details techniques: {error}",
}


class TheresError(Exception):
    """Exception personnalisee THERESE avec message utilisateur."""

    def __init__(
        self,
        code: ErrorCode,
        technical_message: str,
        user_message: Optional[str] = None,
        context: Optional[dict] = None,
        recoverable: bool = True,
    ):
        self.code = code
        self.technical_message = technical_message
        self.context = context or {}
        self.recoverable = recoverable

        # Generate user-friendly message
        template = ERROR_MESSAGES.get(code, ERROR_MESSAGES[ErrorCode.UNKNOWN_ERROR])
        self.user_message = user_message or template.format(
            error=technical_message, **self.context
        )

        super().__init__(self.user_message)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "code": self.code.value,
            "message": self.user_message,
            "recoverable": self.recoverable,
            "details": self.context,
        }


# ============================================================
# Retry Logic (US-ERR-02)
# ============================================================


async def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    retryable_exceptions: tuple = (httpx.TimeoutException, httpx.ConnectError),
) -> T:
    """
    Execute une fonction avec retry et backoff exponentiel.

    Args:
        func: Fonction async a executer
        max_retries: Nombre max de tentatives
        base_delay: Delai initial en secondes
        max_delay: Delai max en secondes
        exponential_base: Base pour le backoff exponentiel
        retryable_exceptions: Types d'exceptions a retenter

    Returns:
        Resultat de la fonction

    Raises:
        TheresError: Si toutes les tentatives echouent
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func()
        except retryable_exceptions as e:
            last_exception = e
            if attempt < max_retries:
                delay = min(base_delay * (exponential_base ** attempt), max_delay)
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)
            else:
                logger.error(f"All {max_retries + 1} attempts failed: {e}")
        except Exception as e:
            # Non-retryable exception
            raise e

    # All retries exhausted
    raise TheresError(
        code=ErrorCode.API_TIMEOUT,
        technical_message=str(last_exception),
        context={"attempts": max_retries + 1, "service": "API"},
        recoverable=True,
    )


def with_retry(
    max_retries: int = 3,
    retryable_exceptions: tuple = (httpx.TimeoutException, httpx.ConnectError),
):
    """Decorator pour ajouter du retry a une fonction async."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_with_backoff(
                lambda: func(*args, **kwargs),
                max_retries=max_retries,
                retryable_exceptions=retryable_exceptions,
            )

        return wrapper

    return decorator


# ============================================================
# Graceful Degradation (US-ERR-03)
# ============================================================


class ServiceStatus:
    """Tracker du statut des services externes."""

    _instance = None
    _statuses: dict[str, bool] = {}
    _last_check: dict[str, float] = {}
    _check_interval: float = 60.0  # Seconds between checks

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._statuses = {}
            cls._last_check = {}
        return cls._instance

    def set_available(self, service: str, available: bool) -> None:
        """Met a jour le statut d'un service."""
        self._statuses[service] = available
        import time

        self._last_check[service] = time.time()

    def is_available(self, service: str, default: bool = True) -> bool:
        """Verifie si un service est disponible."""
        return self._statuses.get(service, default)

    def should_check(self, service: str) -> bool:
        """Verifie si on doit retester le service."""
        import time

        last = self._last_check.get(service, 0)
        return time.time() - last > self._check_interval

    def get_all_statuses(self) -> dict[str, bool]:
        """Retourne tous les statuts."""
        return dict(self._statuses)


def get_service_status() -> ServiceStatus:
    """Get singleton instance."""
    return ServiceStatus()


async def with_graceful_degradation(
    primary_func: Callable[..., T],
    fallback_func: Optional[Callable[..., T]] = None,
    service_name: str = "unknown",
    default_value: Any = None,
) -> T:
    """
    Execute une fonction avec fallback gracieux.

    Si la fonction principale echoue, execute le fallback ou retourne default_value.
    """
    status = get_service_status()

    try:
        result = await primary_func()
        status.set_available(service_name, True)
        return result
    except Exception as e:
        logger.warning(f"Service {service_name} failed: {e}")
        status.set_available(service_name, False)

        if fallback_func:
            try:
                return await fallback_func()
            except Exception as fallback_error:
                logger.error(f"Fallback for {service_name} also failed: {fallback_error}")

        if default_value is not None:
            return default_value

        raise TheresError(
            code=ErrorCode.QDRANT_UNAVAILABLE if "qdrant" in service_name.lower() else ErrorCode.UNKNOWN_ERROR,
            technical_message=str(e),
            context={"service": service_name},
            recoverable=True,
        )


# ============================================================
# Error Classification
# ============================================================


def classify_http_error(status_code: int, provider: str = "API") -> TheresError:
    """Classifie une erreur HTTP en TheresError."""
    if status_code == 401:
        return TheresError(
            code=ErrorCode.API_AUTH_FAILED,
            technical_message=f"HTTP 401 from {provider}",
            context={"provider": provider},
        )
    elif status_code == 429:
        return TheresError(
            code=ErrorCode.API_RATE_LIMITED,
            technical_message=f"HTTP 429 from {provider}",
            context={"provider": provider},
        )
    elif status_code >= 500:
        return TheresError(
            code=ErrorCode.API_SERVER_ERROR,
            technical_message=f"HTTP {status_code} from {provider}",
            context={"provider": provider},
        )
    else:
        return TheresError(
            code=ErrorCode.UNKNOWN_ERROR,
            technical_message=f"HTTP {status_code} from {provider}",
            context={"provider": provider, "status_code": status_code},
        )


def classify_llm_error(error: Exception, provider: str) -> TheresError:
    """Classifie une erreur LLM."""
    error_str = str(error).lower()

    if ("context" in error_str and ("long" in error_str or "exceeded" in error_str or "length" in error_str)):
        return TheresError(
            code=ErrorCode.LLM_CONTEXT_TOO_LONG,
            technical_message=str(error),
            context={"provider": provider, "tokens": "?"},
        )
    elif "rate" in error_str or "limit" in error_str:
        return TheresError(
            code=ErrorCode.API_RATE_LIMITED,
            technical_message=str(error),
            context={"provider": provider},
        )
    elif "auth" in error_str or "key" in error_str or "401" in error_str:
        return TheresError(
            code=ErrorCode.API_AUTH_FAILED,
            technical_message=str(error),
            context={"provider": provider},
        )
    else:
        return TheresError(
            code=ErrorCode.LLM_GENERATION_FAILED,
            technical_message=str(error),
            context={"provider": provider},
        )
