"""Entrée ASGI jetable pour la couverture écran du cycle 14.

Lancer avec ``backend_offline:create_app --factory --loop asyncio``. La garde
est posée avant l'import de ``app.main`` ; elle bloque les sous-processus via
``subprocess``/``asyncio``, sans couvrir les appels natifs qui contournent Python.
"""

from __future__ import annotations

import asyncio
import ipaddress
import json
import os
import socket
import subprocess
import sys
from typing import Any

ATTESTATION = {"version": 1, "network_policy": "loopback-only", "offline": True}
_garde_installee = False


def _hote_local(hote: object) -> bool:
    if isinstance(hote, bytes):
        try:
            hote = hote.decode("ascii")
        except UnicodeDecodeError:
            return False
    if not isinstance(hote, str):
        return False
    if hote.lower().rstrip(".") == "localhost":
        return True
    try:
        return ipaddress.ip_address(hote).is_loopback
    except ValueError:
        return False


def _hote_numerique_local(hote: object, famille: int) -> str | None:
    if isinstance(hote, bytes):
        try:
            hote = hote.decode("ascii")
        except UnicodeDecodeError:
            return None
    if not isinstance(hote, str):
        return None
    if hote.lower().rstrip(".") == "localhost":
        return "::1" if famille == socket.AF_INET6 else "127.0.0.1"
    try:
        adresse_ip = ipaddress.ip_address(hote)
    except ValueError:
        return None
    if not adresse_ip.is_loopback:
        return None
    if famille == socket.AF_INET and adresse_ip.version != 4:
        return None
    if famille == socket.AF_INET6 and adresse_ip.version != 6:
        return None
    return str(adresse_ip)


def _destination_locale(famille: int, adresse: object) -> object:
    af_unix = getattr(socket, "AF_UNIX", None)
    if af_unix is not None and famille == af_unix:
        if isinstance(adresse, (str, bytes)):
            return adresse
        _refuser(adresse)
    if famille in (socket.AF_INET, socket.AF_INET6):
        if isinstance(adresse, tuple) and adresse:
            hote = _hote_numerique_local(adresse[0], famille)
            if hote:
                return (hote, *adresse[1:])
    _refuser(adresse)


def _refuser(adresse: object) -> None:
    raise PermissionError(f"Couverture hors ligne : destination refusée ({adresse!r})")


def installer_garde_socket() -> None:
    """Refuse DNS, sockets hors loopback et sous-processus dans l'ASGI."""
    global _garde_installee
    if _garde_installee:
        return

    # Un proxy sur loopback pourrait relayer une demande cloud malgré la garde
    # socket. On retire les proxies d'environnement avant tout import backend.
    for cle in tuple(os.environ):
        if cle.upper().endswith("_PROXY"):
            os.environ.pop(cle, None)
    os.environ["NO_PROXY"] = "*"
    os.environ["no_proxy"] = "*"

    getaddrinfo = socket.getaddrinfo
    getnameinfo = socket.getnameinfo
    connect = socket.socket.connect
    connect_ex = socket.socket.connect_ex
    bind = socket.socket.bind
    sendto = socket.socket.sendto
    sendmsg = getattr(socket.socket, "sendmsg", None)
    popen = subprocess.Popen

    def garder_hote(hote: object) -> None:
        if not _hote_local(hote):
            _refuser(hote)

    def getaddrinfo_local(
        host: Any, port: Any, family: int = 0, type: int = 0,
        proto: int = 0, flags: int = 0,
    ) -> Any:
        garder_hote(host)
        numerique = _hote_numerique_local(host, family)
        if numerique is None:
            _refuser(host)
        # AI_NUMERICHOST interdit au résolveur de questionner le DNS, même
        # pour « localhost » (qui est transformé en adresse littérale).
        return getaddrinfo(numerique, port, family, type, proto, flags | socket.AI_NUMERICHOST)

    def gethostbyname_local(hote: str) -> str:
        garder_hote(hote)
        numerique = _hote_numerique_local(hote, socket.AF_INET)
        if numerique is None:
            _refuser(hote)
        return numerique

    def gethostbyname_ex_local(hote: str) -> tuple[str, list[str], list[str]]:
        garder_hote(hote)
        numerique = _hote_numerique_local(hote, socket.AF_INET)
        if numerique is None:
            _refuser(hote)
        return ("localhost", [], [numerique])

    def gethostbyaddr_local(hote: str) -> tuple[str, list[str], list[str]]:
        garder_hote(hote)
        numerique = _hote_numerique_local(hote, 0)
        if numerique is None:
            _refuser(hote)
        return ("localhost", [], [numerique])

    def getnameinfo_local(adresse: tuple[Any, ...], flags: int) -> tuple[str, str]:
        if not adresse or not _hote_local(adresse[0]):
            _refuser(adresse)
        numerique = _hote_numerique_local(adresse[0], 0)
        if numerique is None:
            _refuser(adresse)
        return getnameinfo((numerique, *adresse[1:]), flags | socket.NI_NUMERICHOST | socket.NI_NUMERICSERV)

    def verifier_socket(sock: socket.socket, adresse: object) -> object:
        return _destination_locale(sock.family, adresse)

    def connect_local(sock: socket.socket, adresse: object) -> None:
        return connect(sock, verifier_socket(sock, adresse))

    def connect_ex_local(sock: socket.socket, adresse: object) -> int:
        return connect_ex(sock, verifier_socket(sock, adresse))

    def bind_local(sock: socket.socket, adresse: object) -> None:
        return bind(sock, verifier_socket(sock, adresse))

    def sendto_local(sock: socket.socket, donnees: bytes, *args: Any) -> int:
        if args:
            args = (*args[:-1], verifier_socket(sock, args[-1]))
        return sendto(sock, donnees, *args)

    def sendmsg_local(sock: socket.socket, *args: Any, **kwargs: Any) -> int:
        destination = kwargs.get("address")
        if destination is None and len(args) >= 4:
            destination = args[3]
        if destination is not None:
            destination = verifier_socket(sock, destination)
            if "address" in kwargs:
                kwargs["address"] = destination
            else:
                args = (*args[:3], destination, *args[4:])
        assert sendmsg is not None
        return sendmsg(sock, *args, **kwargs)

    class PopenInterdit(popen):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            _refuser("sous-processus")

    async def processus_asynchrone_interdit(*args: Any, **kwargs: Any) -> None:
        _refuser("sous-processus asynchrone")

    socket.getaddrinfo = getaddrinfo_local
    socket.gethostbyname = gethostbyname_local
    socket.gethostbyname_ex = gethostbyname_ex_local
    socket.gethostbyaddr = gethostbyaddr_local
    socket.getnameinfo = getnameinfo_local
    socket.socket.connect = connect_local
    socket.socket.connect_ex = connect_ex_local
    socket.socket.bind = bind_local
    socket.socket.sendto = sendto_local
    if sendmsg is not None:
        socket.socket.sendmsg = sendmsg_local
    subprocess.Popen = PopenInterdit
    asyncio.create_subprocess_exec = processus_asynchrone_interdit
    asyncio.create_subprocess_shell = processus_asynchrone_interdit
    _garde_installee = True


class BackendOffline:
    """Attestation servie avant les middlewares et routes du backend produit."""

    def __init__(self, produit: Any) -> None:
        self.produit = produit

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] == "http" and scope.get("path") == "/__couverture/offline":
            methode = scope.get("method")
            if methode != "GET":
                await send({"type": "http.response.start", "status": 405, "headers": []})
                await send({"type": "http.response.body", "body": b""})
                return
            boucle = asyncio.get_running_loop()
            if (
                not _garde_installee
                or os.environ.get("THERESE_SKIP_SERVICES") != "1"
                or not type(boucle).__module__.startswith("asyncio.")
            ):
                await send({"type": "http.response.start", "status": 503, "headers": []})
                await send({"type": "http.response.body", "body": b""})
                return
            corps = json.dumps(ATTESTATION, separators=(",", ":")).encode("ascii")
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"cache-control", b"no-store"),
                ],
            })
            await send({"type": "http.response.body", "body": corps})
            return
        await self.produit(scope, receive, send)


def create_app() -> BackendOffline:
    """Installe la garde puis construit l'application produit inchangée."""
    if os.environ.get("THERESE_SKIP_SERVICES") != "1":
        raise RuntimeError("THERESE_SKIP_SERVICES=1 est requis pour la couverture hors ligne")
    if "app.main" in sys.modules:
        raise RuntimeError("app.main a été importé avant la garde hors ligne")
    installer_garde_socket()
    from app.main import app

    return BackendOffline(app)
