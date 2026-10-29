"""Garde synchrone à la remise HTTP, propre à un envoi et à ses finalités."""
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any, TypeVar

T = TypeVar("T")


def appeler_avec_accord(verifier: Callable[[], None], appel: Callable[[], T]) -> T:
    """SDK synchrone : vérifier dans le thread, juste avant de lui remettre les données."""
    verifier()
    return appel()


class TransportAvecAccord:
    """Ne partage jamais la garde d'une conversation avec une autre."""

    def __init__(self, client: Any, verifier: Callable[[], None]):
        self._client = client
        self._verifier = verifier

    @asynccontextmanager
    async def stream(self, *args: Any, **kwargs: Any) -> AsyncIterator[Any]:
        self._verifier()
        async with self._client.stream(*args, **kwargs) as response:
            yield response

    async def post(self, *args: Any, **kwargs: Any) -> Any:
        self._verifier()
        return await self._client.post(*args, **kwargs)

    async def get(self, *args: Any, **kwargs: Any) -> Any:
        self._verifier()
        return await self._client.get(*args, **kwargs)
