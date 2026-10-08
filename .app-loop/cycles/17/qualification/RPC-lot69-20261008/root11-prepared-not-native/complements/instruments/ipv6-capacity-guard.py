"""Garde privée : seul le probe urllib3 vérifié reçoit EAFNOSUPPORT une fois.

La socket de ce probe est fermée avant de lever l'erreur attendue, sans bind.
Tout autre bind/connect/listen/envoi IP est refusé avant l'appel natif.
"""
from __future__ import annotations
import hashlib
import errno
import marshal
from pathlib import Path
import socket
import sys
import traceback
from types import CodeType
from typing import Any


def install_guard(source: Path, expected_sha: str, blocked: list, probes: list) -> None:
    source = source.resolve()
    payload = source.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == expected_sha
    compiled = compile(payload, str(source), 'exec', dont_inherit=True)
    candidates = [c for c in compiled.co_consts if isinstance(c, CodeType) and c.co_name == '_has_ipv6']
    assert len(candidates) == 1
    expected_code = candidates[0]
    code_sha = hashlib.sha256(marshal.dumps(expected_code)).hexdigest()
    raw_bind = socket.socket.bind
    raw = {name: getattr(socket.socket, name) for name in
           ['connect', 'connect_ex', 'listen', 'send', 'sendall', 'sendto', 'sendmsg']
           if hasattr(socket.socket, name)}
    probe_used = False

    def reject(operation: str, sock: socket.socket, address: Any = None) -> None:
        blocked.append({'operation': operation, 'family': int(sock.family),
                        'address': list(address) if isinstance(address, tuple) else address,
                        'stack': traceback.format_stack(limit=20), 'native_operation_called': False})
        raise RuntimeError('Harness offline : opération IP refusée : ' + operation)

    def guarded_bind(sock: socket.socket, address: Any) -> Any:
        nonlocal probe_used
        if sock.family not in (socket.AF_INET, socket.AF_INET6):
            return raw_bind(sock, address)
        caller = sys._getframe(1)
        exact = (not probe_used and sock.family == socket.AF_INET6
                 and sock.type == socket.SOCK_STREAM and sock.proto == 0
                 and address == ('::1', 0)
                 and caller.f_globals.get('__name__') == 'urllib3.util.connection'
                 and Path(caller.f_code.co_filename).resolve() == source
                 and caller.f_code.replace(co_filename=str(source)) == expected_code
                 and caller.f_locals.get('sock') is sock
                 and hashlib.sha256(source.read_bytes()).hexdigest() == expected_sha)
        if not exact:
            reject('bind', sock, address)
        probe_used = True
        row = {'operation': 'bind', 'kind': 'urllib3_exact_ipv6_capacity_probe',
               'family': int(sock.family), 'type': int(sock.type), 'proto': sock.proto,
               'address': list(address), 'source': str(source), 'source_sha256': expected_sha,
               'function': '_has_ipv6', 'code_sha256': code_sha, 'recognized_once': True,
               'native_bind_called': False, 'listen_called': False, 'connect_called': False,
               'packet_sent': False, 'policy': 'IPv6 unavailable in offline harness'}
        try:
            raise OSError(errno.EAFNOSUPPORT, 'IPv6 unavailable in offline harness')
        except BaseException as error:
            row['bind_succeeded'] = False
            row['error'] = type(error).__name__ + ': ' + str(error)
            raise
        finally:
            sock.close()
            row['closed_before_return'] = sock.fileno() == -1
            probes.append(row)

    def make_guard(operation: str):
        def guarded(sock: socket.socket, *args: Any, **kwargs: Any) -> Any:
            if sock.family in (socket.AF_INET, socket.AF_INET6):
                reject(operation, sock, args[0] if operation in ('connect', 'connect_ex') and args else None)
            return raw[operation](sock, *args, **kwargs)
        return guarded

    socket.socket.bind = guarded_bind
    for name in raw:
        setattr(socket.socket, name, make_guard(name))
