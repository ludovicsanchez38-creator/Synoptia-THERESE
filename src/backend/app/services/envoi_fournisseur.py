"""Garde synchrone à la remise HTTP, propre à un envoi et à ses finalités."""
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any, TypeVar

import httpx

T = TypeVar("T")


class TransportHTTPAvecAccord(httpx.BaseTransport):
    """Garde chaque tentative des SDK, y compris leurs reprises internes."""

    def __init__(self, verifier: Callable[[], None]):
        self._verifier = verifier
        # Aucune reprise sous la garde (ni redirection automatique).
        self._transport = httpx.HTTPTransport(retries=0)

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self._verifier()
        return self._transport.handle_request(request)

    def close(self) -> None:
        self._transport.close()


def client_http_avec_accord(verifier: Callable[[], None]) -> httpx.Client:
    return httpx.Client(transport=TransportHTTPAvecAccord(verifier), timeout=120.0)


def appeler_avec_accord(verifier: Callable[[], None], appel: Callable[[], T]) -> T:
    """SDK synchrone : vérifier dans le thread, juste avant de lui remettre les données."""
    verifier()
    return appel()


class TransportAvecAccord:
    """Garde propre à l'appel ; aucune redirection ne contourne sa destination."""

    def __init__(self, client: Any, verifier: Callable[[], None]):
        self._client = client
        self._verifier = verifier

    @asynccontextmanager
    async def stream(self, *args: Any, **kwargs: Any) -> AsyncIterator[Any]:
        self._verifier()
        kwargs['follow_redirects'] = False
        async with self._client.stream(*args, **kwargs) as response:
            self._refuser_redirection(response)
            yield response

    async def post(self, *args: Any, **kwargs: Any) -> Any:
        self._verifier()
        kwargs['follow_redirects'] = False
        response = await self._client.post(*args, **kwargs)
        self._refuser_redirection(response)
        return response

    async def get(self, *args: Any, **kwargs: Any) -> Any:
        self._verifier()
        kwargs['follow_redirects'] = False
        response = await self._client.get(*args, **kwargs)
        self._refuser_redirection(response)
        return response

    @staticmethod
    def _refuser_redirection(response: Any) -> None:
        code = response.status_code
        if isinstance(code, int) and 300 <= code < 400:
            from app.services.error_handler import ErreurPourEcran
            raise ErreurPourEcran(
                "Le fournisseur demande une redirection. Aucun nouvel envoi n’a été effectué. "
                "Vérifie la destination de ton modèle avant de réessayer."
            )
