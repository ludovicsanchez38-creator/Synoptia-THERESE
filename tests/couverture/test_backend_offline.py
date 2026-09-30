"""Témoins sans réseau du wrapper ASGI de couverture écran."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest


def _executer_script(script: str, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    """Exécute les gardes globales sans hériter des secrets ni du profil réel."""
    home_test = tmp_path / "home"
    home_test.mkdir(exist_ok=True)
    environnement = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "HOME": str(home_test),
        "USERPROFILE": str(home_test),
        "TMPDIR": str(tmp_path),
        "TEMP": str(tmp_path),
        "TMP": str(tmp_path),
        "PYTHONPATH": os.pathsep.join((
            str(Path(__file__).parent),
            str(Path(__file__).resolve().parents[2] / "src" / "backend"),
        )),
        "THERESE_DATA_DIR": str(tmp_path / "donnees"),
        "HTTP_PROXY": "http://127.0.0.1:9",
        "HTTPS_PROXY": "http://127.0.0.1:9",
        "ALL_PROXY": "http://127.0.0.1:9",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    if os.name == "nt":
        systemroot = os.environ.get("SYSTEMROOT") or os.environ.get("WINDIR")
        if not systemroot:
            pytest.skip("SYSTEMROOT ou WINDIR est requis pour le témoin Windows")
        environnement["SYSTEMROOT"] = systemroot
        environnement["WINDIR"] = environnement["SYSTEMROOT"]
    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env=environnement,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )


def test_garde_python_refuse_dns_et_sorties_mais_garde_le_loopback(tmp_path: Path) -> None:
    # Un processus fils évite que les monkeypatchs socket affectent pytest.
    # Les spies empêchent toute sortie réelle même en cas de régression.
    script = """
import asyncio
import builtins
import json
import os
import socket
import subprocess

# Sous Windows, la boucle Proactor construit son socketpair de réveil en TCP.
# Elle doit exister avant les spies qui simulent bind/connect sans créer de socket.
boucle = asyncio.new_event_loop()

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

# Reproduit aussi sur Unix l'absence de AF_UNIX du runner Windows.
af_unix_initial = getattr(socket, 'AF_UNIX', None)
if af_unix_initial is not None:
    del socket.AF_UNIX
try:
    assert backend_offline._destination_locale(
        socket.AF_INET, ('localhost', 17393)
    ) == ('127.0.0.1', 17393)
    doit_refuser(lambda: backend_offline._destination_locale(-1, '/socket-inconnue'))
finally:
    if af_unix_initial is not None:
        socket.AF_UNIX = af_unix_initial

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
boucle.run_until_complete(sous_processus_asynchrones_refuses())

assert socket.getaddrinfo('localhost', 80, family=socket.AF_INET, type=socket.SOCK_STREAM)
assert socket.getaddrinfo(
    '127.0.0.1', 17393, family=socket.AF_INET,
    type=socket.SOCK_STREAM, flags=socket.AI_PASSIVE,
)
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as local:
    local.bind(('localhost', 0))
    local.connect(('localhost', 17393))
    assert local.connect_ex(('127.0.0.1', 17393)) == 0
# Sans AF_UNIX, socketpair utilise des connexions TCP que les spies ci-dessus
# simulent sans les établir réellement.
if hasattr(socket, 'AF_UNIX'):
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

boucle.run_until_complete(verifier_attestation())
boucle.close()
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
    resultat = _executer_script(script, tmp_path)
    assert resultat.returncode == 0, resultat.stderr


@pytest.mark.parametrize("operation", ("connect", "connect_ex", "bind", "sendto", "sendmsg"))
@pytest.mark.parametrize("destination", ("/service-local.sock", b"\x00service-abstrait"))
def test_garde_refuse_toute_destination_unix_avant_appel_natif(
    tmp_path: Path, operation: str, destination: str | bytes,
) -> None:
    if not hasattr(socket, "AF_UNIX") or not hasattr(socket.socket, operation):
        pytest.skip("Cette plateforme ne fournit pas l'opération Unix testée")
    script = f"""
import asyncio
import socket
import backend_offline

def appel_natif_interdit(*args, **kwargs):
    raise AssertionError('la destination Unix atteint la socket native')

setattr(socket.socket, {operation!r}, appel_natif_interdit)
backend_offline.installer_garde_socket()
with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
    destination = {destination!r}
    try:
        if {operation!r} == 'sendto':
            sock.sendto(b'temoin', destination)
        elif {operation!r} == 'sendmsg':
            sock.sendmsg([b'temoin'], [], 0, destination)
        else:
            getattr(sock, {operation!r})(destination)
    except PermissionError:
        pass
    else:
        raise AssertionError('une destination Unix a été autorisée')

# La garde n'empêche pas la paire anonyme utilisée par le réveil asyncio.
gauche, droite = socket.socketpair()
try:
    gauche.sendall(b'paire')
    assert droite.recv(5) == b'paire'
finally:
    gauche.close()
    droite.close()
boucle = asyncio.new_event_loop()
boucle.run_until_complete(asyncio.sleep(0))
boucle.close()
"""
    resultat = _executer_script(script, tmp_path)
    assert resultat.returncode == 0, resultat.stderr


@pytest.mark.parametrize("operation", ("connect", "connect_ex", "sendto", "sendmsg"))
def test_garde_refuse_un_proxy_reintroduit_avant_connexion_locale(
    tmp_path: Path, operation: str,
) -> None:
    if not hasattr(socket.socket, operation):
        pytest.skip("Cette plateforme ne fournit pas l'opération socket testée")
    script = f"""
import os
import socket
import backend_offline

def appel_natif_interdit(*args, **kwargs):
    raise AssertionError('le proxy réintroduit atteint la socket native')

setattr(socket.socket, {operation!r}, appel_natif_interdit)
backend_offline.installer_garde_socket()
os.environ['https_proxy'] = 'http://127.0.0.1:9'
os.environ['NO_PROXY'] = ''
os.environ['no_proxy'] = ''
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    try:
        if {operation!r} == 'sendto':
            sock.sendto(b'temoin', ('127.0.0.1', 9))
        elif {operation!r} == 'sendmsg':
            sock.sendmsg([b'temoin'], [], 0, ('127.0.0.1', 9))
        else:
            getattr(sock, {operation!r})(('127.0.0.1', 9))
    except PermissionError:
        pass
    else:
        raise AssertionError('le proxy réintroduit a été autorisé')
"""
    resultat = _executer_script(script, tmp_path)
    assert resultat.returncode == 0, resultat.stderr


def test_reinstaller_la_garde_neutralise_les_proxies_reintroduits(tmp_path: Path) -> None:
    resultat = _executer_script("""
import os
import backend_offline
backend_offline.installer_garde_socket()
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:9'
os.environ['NO_PROXY'] = ''
backend_offline.installer_garde_socket()
assert 'HTTPS_PROXY' not in os.environ
assert os.environ['NO_PROXY'] == '*'
assert os.environ['no_proxy'] == '*'
""", tmp_path)
    assert resultat.returncode == 0, resultat.stderr


def test_factory_exige_un_dossier_explicite_avant_import_produit(tmp_path: Path) -> None:
    resultat = _executer_script("""
import builtins
import os
import backend_offline
os.environ['THERESE_SKIP_SERVICES'] = '1'
os.environ.pop('THERESE_DATA_DIR')
import_initial = builtins.__import__
def import_interdit(name, *args, **kwargs):
    if name == 'app.main':
        raise AssertionError('le produit est importé sans dossier jetable')
    return import_initial(name, *args, **kwargs)
builtins.__import__ = import_interdit
try:
    backend_offline.create_app()
except RuntimeError as erreur:
    assert 'THERESE_DATA_DIR' in str(erreur)
else:
    raise AssertionError('le dossier de données implicite est autorisé')
""", tmp_path)
    assert resultat.returncode == 0, resultat.stderr


def test_configuration_avec_override_ne_cree_pas_le_profil_par_defaut(tmp_path: Path) -> None:
    resultat = _executer_script("""
import os
from pathlib import Path
from app.config import settings
assert settings.data_dir == Path(os.environ['THERESE_DATA_DIR'])
assert settings.data_dir.is_dir()
assert not (Path.home() / '.therese').exists()
""", tmp_path)
    assert resultat.returncode == 0, resultat.stderr


def test_factory_refuse_configuration_chargee_avant_la_garde(tmp_path: Path) -> None:
    resultat = _executer_script("""
import builtins
import os
import sys
from types import ModuleType
import backend_offline
os.environ['THERESE_SKIP_SERVICES'] = '1'
# Le cache de config pourrait déjà porter un autre dossier que l'override.
# Le faux module évite de charger une configuration ou un profil réels.
sys.modules['app.config'] = ModuleType('app.config')
import_initial = builtins.__import__
def import_interdit(name, *args, **kwargs):
    if name == 'app.main':
        raise AssertionError('le produit est importé avec une configuration antérieure')
    return import_initial(name, *args, **kwargs)
builtins.__import__ = import_interdit
try:
    backend_offline.create_app()
except RuntimeError as erreur:
    assert 'app.config' in str(erreur)
else:
    raise AssertionError('la configuration antérieure est autorisée')
""", tmp_path)
    assert resultat.returncode == 0, resultat.stderr
