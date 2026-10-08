"""Observation peer Unix Darwin liée au ledger, jamais à un PID du payload.

Ne crée aucun socket ni processus. Le serveur root doit fournir le socket
accepté et garder l'observation hors du JSON ; les tests présents sont purs.
Deux observations ne constituent pas une primitive atomique contre PID reuse.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import socket
import sys
from typing import Any

SOL_LOCAL = 0
LOCAL_PEERPID = 2


class PeerObservationError(RuntimeError):
    pass


def check(condition: bool, message: str) -> None:
    if not condition:
        raise PeerObservationError(message)


def _peer_pid(connection: Any) -> int:
    check(sys.platform == 'darwin', 'Darwin peer observation only')
    check(connection.family == socket.AF_UNIX
          and connection.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE) == socket.SOCK_STREAM,
          'Connected Unix stream required')
    pid = connection.getsockopt(SOL_LOCAL, LOCAL_PEERPID)
    check(type(pid) is int and pid > 0, 'Invalid kernel peer PID')
    return pid


def _live(ledger: Any, canonical: dict[str, Any]) -> dict[str, Any]:
    row = ledger.info(canonical['pid'])
    check(row is not None and ledger.unchanged(canonical, row)
          and row.get('status') != 5 and row.get('ppid') == canonical['ppid'],
          'Requester birth/UID/PGID/PPID changed or no longer alive')
    return row


@dataclass(frozen=True)
class PeerSnapshot:
    _canonical: dict[str, Any]
    _owner: dict[str, Any]
    _ledger_id: int
    _fd: int

    @property
    def identity(self) -> dict[str, Any]:
        return deepcopy(self._canonical)

    def revalidate(self, connection: Any, ledger: Any) -> dict[str, Any]:
        check(id(ledger) == self._ledger_id and connection.fileno() == self._fd,
              'Observation ledger/socket changed')
        check(_peer_pid(connection) == self._canonical['pid'], 'Kernel peer changed')
        canonical = ledger.records.get(ledger.key(self._canonical))
        check(canonical == self._canonical, 'Canonical requester registry changed')
        check(ledger.owner == self._owner, 'Canonical owner identity changed')
        _live(ledger, self._owner)
        _live(ledger, self._canonical)
        return self.identity


def capture_peer(connection: Any, ledger: Any, allowed_roles: set[str]) -> PeerSnapshot:
    check(bool(allowed_roles) and all(isinstance(role, str) and role.startswith('stage-')
                                    for role in allowed_roles),
          'Only explicit stage requester roles allowed')
    pid = _peer_pid(connection)
    candidates = [row for row in ledger.records.values()
                  if row.get('pid') == pid and row.get('role') in allowed_roles]
    check(len(candidates) == 1, 'Kernel peer is not one enrolled requester')
    canonical = deepcopy(candidates[0])
    check(canonical['uid'] == ledger.owner['uid'], 'Requester UID differs from owner')
    _live(ledger, ledger.owner)
    _live(ledger, canonical)
    fd = connection.fileno()
    check(type(fd) is int and fd >= 0, 'Closed/noncanonical peer socket')
    observation = PeerSnapshot(canonical, deepcopy(ledger.owner), id(ledger), fd)
    observation.revalidate(connection, ledger)
    return observation
