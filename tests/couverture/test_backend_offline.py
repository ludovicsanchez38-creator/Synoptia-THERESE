"""Témoins sans réseau du wrapper ASGI de couverture écran."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_garde_python_refuse_dns_et_sorties_mais_garde_le_loopback() -> None:
    # Un processus fils évite que les monkeypatchs socket affectent pytest.
    # Les spies empêchent toute sortie réelle même en cas de régression.
    script = """
import asyncio
import builtins
import json
import os
import socket
import subprocess

getaddrinfo_initial = socket.getaddrinfo

def dns_spy(host, *args, **kwargs):
    assert host in ('127.0.0.1', '::1'), f'DNS hors loopback atteint : {host}'
    return getaddrinfo_initial(host, *args, **kwargs)

def connect_spy(sock, address):
    assert address[0] in ('127.0.0.1', '::1'), f'connect hors loopback atteint : {address}'
    return None

def connect_ex_spy(sock, address):
    assert address[0] in ('127.0.0.1', '::1'), f'connect_ex hors loopback atteint : {address}'
    return 0

def bind_spy(sock, address):
    assert address[0] in ('127.0.0.1', '::1'), f'bind hors loopback atteint : {address}'
    return None

def sendto_spy(sock, data, *args):
    assert args[-1][0] in ('127.0.0.1', '::1'), f'sendto hors loopback atteint : {args[-1]}'
    return len(data)

class PopenSpy(subprocess.Popen):
    def __init__(self, *args, **kwargs):
        raise AssertionError('un sous-processus aurait été lancé')

async def async_process_spy(*args, **kwargs):
    raise AssertionError('un sous-processus asynchrone aurait été lancé')

socket.getaddrinfo = dns_spy
socket.socket.connect = connect_spy
socket.socket.connect_ex = connect_ex_spy
socket.socket.bind = bind_spy
socket.socket.sendto = sendto_spy
subprocess.Popen = PopenSpy
asyncio.create_subprocess_exec = async_process_spy
asyncio.create_subprocess_shell = async_process_spy

import backend_offline
backend_offline.installer_garde_socket()
os.environ['THERESE_SKIP_SERVICES'] = '1'
assert backend_offline.ATTESTATION == {
    'version': 1, 'network_policy': 'loopback-only', 'offline': True,
}
assert os.environ['NO_PROXY'] == '*'
assert os.environ['no_proxy'] == '*'
assert 'HTTP_PROXY' not in os.environ
assert 'HTTPS_PROXY' not in os.environ
assert 'ALL_PROXY' not in os.environ

def doit_refuser(operation):
    try:
        operation()
    except PermissionError:
        return
    raise AssertionError('une destination non locale a été autorisée')

doit_refuser(lambda: socket.getaddrinfo('openrouter.ai', 443))
doit_refuser(lambda: socket.gethostbyname('openrouter.ai'))
doit_refuser(lambda: socket.gethostbyaddr('8.8.8.8'))
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as externe:
    doit_refuser(lambda: externe.connect(('203.0.113.1', 443)))
    doit_refuser(lambda: externe.connect_ex(('203.0.113.1', 443)))
    doit_refuser(lambda: externe.connect(('proxy.exemple.invalid', 8080)))
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
    doit_refuser(lambda: udp.sendto(b'test', ('203.0.113.1', 53)))
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as non_local:
    doit_refuser(lambda: non_local.bind(('0.0.0.0', 0)))
doit_refuser(lambda: subprocess.Popen(('interdit',)))
async def sous_processus_asynchrones_refuses():
    for appel in (asyncio.create_subprocess_exec, asyncio.create_subprocess_shell):
        try:
            await appel('interdit')
        except PermissionError:
            continue
        raise AssertionError('un sous-processus asynchrone a été autorisé')
asyncio.run(sous_processus_asynchrones_refuses())

assert socket.getaddrinfo('localhost', 80, family=socket.AF_INET, type=socket.SOCK_STREAM)
assert socket.getaddrinfo(
    '127.0.0.1', 17393, family=socket.AF_INET,
    type=socket.SOCK_STREAM, flags=socket.AI_PASSIVE,
)
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as local:
    local.bind(('localhost', 0))
    local.connect(('localhost', 17393))
    assert local.connect_ex(('127.0.0.1', 17393)) == 0
gauche, droite = socket.socketpair()
try:
    gauche.sendall(b'local')
    assert droite.recv(5) == b'local'
finally:
    gauche.close()
    droite.close()

# Le catch-all produit simulé ne doit jamais voir l'attestation.
appels_produit = []
async def produit(scope, receive, send):
    appels_produit.append(scope['path'])
    await send({'type': 'http.response.start', 'status': 404, 'headers': []})
    await send({'type': 'http.response.body', 'body': b''})

async def verifier_attestation():
    app = backend_offline.BackendOffline(produit)
    messages = []
    async def receive():
        return {'type': 'http.request', 'body': b'', 'more_body': False}
    async def send(message):
        messages.append(message)
    await app({'type': 'http', 'path': '/__couverture/offline', 'method': 'GET'}, receive, send)
    assert messages[0]['status'] == 200
    assert json.loads(messages[1]['body']) == backend_offline.ATTESTATION
    assert appels_produit == []
    os.environ['THERESE_SKIP_SERVICES'] = '0'
    messages.clear()
    await app({'type': 'http', 'path': '/__couverture/offline', 'method': 'GET'}, receive, send)
    assert messages[0]['status'] == 503
    os.environ['THERESE_SKIP_SERVICES'] = '1'
    messages.clear()
    await app({'type': 'http', 'path': '/autre', 'method': 'GET'}, receive, send)
    assert messages[0]['status'] == 404
    assert appels_produit == ['/autre']

asyncio.run(verifier_attestation())
os.environ['THERESE_SKIP_SERVICES'] = '0'
import_initial = builtins.__import__
def import_spy(name, *args, **kwargs):
    if name == 'app.main':
        raise AssertionError('import produit atteint avec services actifs')
    return import_initial(name, *args, **kwargs)
builtins.__import__ = import_spy
try:
    try:
        backend_offline.create_app()
    except RuntimeError as erreur:
        assert 'THERESE_SKIP_SERVICES=1' in str(erreur)
    else:
        raise AssertionError('factory autorisée avec services actifs')
finally:
    builtins.__import__ = import_initial
"""
    environnement = os.environ.copy()
    environnement.update(
        {
            "HTTP_PROXY": "http://127.0.0.1:9",
            "HTTPS_PROXY": "http://127.0.0.1:9",
            "ALL_PROXY": "http://127.0.0.1:9",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    resultat = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).parent,
        env=environnement,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert resultat.returncode == 0, resultat.stderr
