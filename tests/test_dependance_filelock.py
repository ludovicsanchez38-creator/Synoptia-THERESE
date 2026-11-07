"""filelock 4.x : avis du 28/10/2026 corrigés, usages des dépendances inchangés (correctifs 0.83).

filelock 3.20.3, tiré par huggingface-hub, torch et transformers, porte
CVE-2026-112909 (GHSA-69hj-f68j-2879, ``UnixFileLock`` tronque et rechmode un
fichier substitué sur le chemin du verrou) et CVE-2026-112910
(GHSA-8mx5-7m5m-r77g, ``WindowsFileLock`` ignore le mode), corrigées en 4.2.1.
La règle du dépôt est de monter, pas d'ignorer l'avis (B-256).

La 4.0 est une version majeure : elle ne rompt que le protocole disque de
``SoftReadWriteLock``, que personne n'utilise ici. Notre code n'importe pas
filelock ; ces gardes rejouent les usages réels des trois dépendances.
"""
import errno
import sys
import threading
import tomllib
import warnings
from pathlib import Path

import filelock
import pytest

RACINE = Path(__file__).resolve().parents[1]
AVIS = ('CVE-2026-112909', 'GHSA-69hj-f68j-2879', 'CVE-2026-112910', 'GHSA-8mx5-7m5m-r77g')


def _version(texte: str) -> tuple[int, ...]:
    return tuple(int(part) for part in texte.split('.')[:3])


def test_verrou_filelock_corrige_les_avis_du_28_10_sans_les_ignorer():
    verrou = tomllib.loads((RACINE / 'uv.lock').read_text(encoding='utf-8'))
    versions = [p['version'] for p in verrou['package'] if p['name'] == 'filelock']
    assert versions and all(_version(v) >= (4, 2, 1) for v in versions), versions
    ci = (RACINE / '.github/workflows/ci.yml').read_text(encoding='utf-8')
    assert not [avis for avis in AVIS if avis in ci]


def test_verrou_de_huggingface_hub_reste_exclusif(tmp_path):
    from huggingface_hub.utils import WeakFileLock

    resultat = []

    def second_preneur():
        try:
            with WeakFileLock(tmp_path / 'modele.lock', timeout=0.3):
                resultat.append('acquis')
        except filelock.Timeout:
            resultat.append('expiré')

    with WeakFileLock(tmp_path / 'modele.lock') as verrou:
        assert verrou.is_locked
        fil = threading.Thread(target=second_preneur)
        fil.start()
        fil.join(5)
    assert resultat == ['expiré']
    with WeakFileLock(tmp_path / 'modele.lock', timeout=1) as verrou:
        assert verrou.is_locked


# flock et fcntl n'existent que sous POSIX ; sous Windows, filelock verrouille
# avec msvcrt et ce repli n'a pas lieu d'être (Tests Windows, run 42355341794).
# Une marque de plateforme plutôt qu'importorskip : sous Linux et macOS, un
# fcntl absent ferait échouer le test au lieu de le sauter en silence.
@pytest.mark.skipif(sys.platform == 'win32', reason='flock et fcntl sont propres à POSIX')
def test_sans_flock_huggingface_hub_obtient_un_verrou_souple(tmp_path, monkeypatch):
    """Système de fichiers sans flock : la 3.x levait une erreur que
    huggingface-hub rattrapait ; la 4.x bascule d'elle-même vers SoftFileLock."""
    import fcntl

    from huggingface_hub.utils import WeakFileLock

    def flock_absent(*_args):
        raise OSError(errno.ENOSYS, 'Function not implemented')

    monkeypatch.setattr(fcntl, 'flock', flock_absent)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        with WeakFileLock(tmp_path / 'modele.lock', timeout=2) as verrou:
            assert isinstance(verrou, filelock.SoftFileLock)
            assert verrou.is_locked


def test_torch_et_transformers_acceptent_filelock_installe(tmp_path):
    from torch.utils._filelock import FileLock as VerrouTorch
    from transformers.utils.versions import require_version_core

    with VerrouTorch(str(tmp_path / 'noyau.lock'), timeout=1) as verrou:
        assert verrou.is_locked
    require_version_core('filelock')
    assert _version(filelock.__version__) >= (4, 2, 1)


@pytest.mark.parametrize('nom', ['BaseFileLock', 'FileLock', 'SoftFileLock', 'Timeout'])
def test_noms_importes_par_les_dependances_toujours_exportes(nom):
    assert nom in filelock.__all__
