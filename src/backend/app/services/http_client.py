"""
THÉRÈSE v2 - Global HTTP Client Pool

Provides a shared httpx.AsyncClient for all services.
Sprint 2 - PERF-2.6: Reduces connection overhead.

Usage:
    from app.services.http_client import get_http_client, close_http_client

    async def my_function():
        client = await get_http_client()
        response = await client.get("https://api.example.com")

    # At app shutdown:
    await close_http_client()
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx

logger = logging.getLogger(__name__)

# Global client instance
_http_client: httpx.AsyncClient | None = None

# Default configuration
DEFAULT_TIMEOUT = 120.0  # 2 minutes for LLM calls
DEFAULT_LIMITS = httpx.Limits(
    max_keepalive_connections=20,
    max_connections=100,
    keepalive_expiry=30.0,
)


async def get_http_client(
    timeout: float | None = None,
) -> httpx.AsyncClient:
    """
    Get the global HTTP client instance.

    The client is lazily initialized on first call.
    Connection pooling is enabled by default.

    Args:
        timeout: Optional timeout override (default: 120s)

    Returns:
        Shared httpx.AsyncClient instance
    """
    global _http_client

    if _http_client is None:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(DEFAULT_TIMEOUT),
            limits=DEFAULT_LIMITS,
            follow_redirects=True,
        )
        logger.info("Global HTTP client initialized (pool: 20 keepalive, 100 max)")

    return _http_client


async def close_http_client() -> None:
    """
    Close the global HTTP client.

    Should be called at app shutdown to release connections.
    """
    global _http_client

    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None
        logger.info("Global HTTP client closed")


@asynccontextmanager
async def http_client_lifespan() -> AsyncGenerator[None, None]:
    """
    Context manager for app lifespan.

    Usage in FastAPI:
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            async with http_client_lifespan():
                yield
    """
    try:
        yield
    finally:
        await close_http_client()


async def get_short_timeout_client() -> httpx.AsyncClient:
    """
    Get a client reference with short timeout for quick checks.

    Note: This returns the same client but callers should use
    timeout parameter in their requests for short operations.
    """
    return await get_http_client()


# Convenience function for one-off requests that need custom timeout
@asynccontextmanager
async def http_request_context(
    timeout: float = DEFAULT_TIMEOUT,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    """
    Context manager for HTTP requests with custom timeout.

    This reuses the global client but allows timeout override per-request.

    Usage:
        async with http_request_context(timeout=5.0) as client:
            response = await client.get(url, timeout=5.0)
    """
    client = await get_http_client()
    yield client
