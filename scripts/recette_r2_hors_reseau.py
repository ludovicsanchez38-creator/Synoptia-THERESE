"""Portes R1 hors réseau sous Linux, dans un profil privé du worktree.

Usage : python3 scripts/recette_r1_hors_reseau.py .venv/bin/python -m pytest tests/ --ignore=tests/e2e
--baseline utilise la copie locale f61f28a3 dans recette-r1-base.
Aucune clé ni variable personnelle n'est héritée par la commande.
"""
import ctypes
import errno
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
box = root / '.recette-r2'
for dossier in (box, box / 'home', box / 'tmp', box / 'logs'):
    dossier.mkdir(parents=True, exist_ok=True)
code_root = root
if sys.argv[1:2] == ['--baseline']:
    code_root = root / '.recette-r2/base'
    sys.argv.pop(1)
# Pas d'héritage de clés, de proxy ni du profil personnel.
clean = {
    'PATH': f'{root}/.venv/bin:/usr/bin:/bin',
    'HOME': str(box / 'home'), 'TMPDIR': str(box / 'tmp'),
    'XDG_CACHE_HOME': str(box / 'home/cache'),
    'XDG_CONFIG_HOME': str(box / 'home/config'),
    'THERESE_DATA_DIR': tempfile.mkdtemp(prefix='data-', dir=box), 'THERESE_ENV': 'test',
    'THERESE_SKIP_SERVICES': '1', 'THERESE_SONDE_CATALOGUE': 'off',
    'OLLAMA_BASE_URL': 'http://127.0.0.1:1',
    'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1',
    'PYTHONPATH': str(code_root / 'src/backend'),
    'GIT_CEILING_DIRECTORIES': str(box / 'tmp'),
    'LANG': 'C.UTF-8', 'TZ': 'Europe/Paris',
}

def offline():
    lib = ctypes.CDLL('libseccomp.so.2', use_errno=True)
    lib.seccomp_init.restype = ctypes.c_void_p
    lib.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
    lib.seccomp_load.argtypes = [ctypes.c_void_p]
    ctx = lib.seccomp_init(0x7fff0000)
    for name in (b'connect', b'sendmsg', b'sendmmsg'):
        nr = lib.seccomp_syscall_resolve_name(name)
        assert lib.seccomp_rule_add(ctx, 0x50000 | errno.EPERM, nr, 0) == 0
    class Comparaison(ctypes.Structure):
        _fields_ = [('arg', ctypes.c_uint), ('op', ctypes.c_int), ('a', ctypes.c_uint64), ('b', ctypes.c_uint64)]
    # send()/socketpair() passe par sendto(..., NULL, 0) sous Linux.
    # Les datagrammes adressés restent interdits.
    assert lib.seccomp_rule_add(ctx, 0x50000 | errno.EPERM,
        lib.seccomp_syscall_resolve_name(b'sendto'), 1, Comparaison(4, 1, 0, 0)) == 0
    assert lib.seccomp_load(ctx) == 0

clean['PATH'] = f'{code_root}/.venv/bin:/usr/bin:/bin'
raise SystemExit(subprocess.call(sys.argv[1:], cwd=code_root, env=clean, preexec_fn=offline))
