"""oauthlib 4.0.1 : avis CVE-2026-49272 corrigé sans l'ignorer (0.83).

oauthlib 4.0.0, tiré par requests-oauthlib puis google-auth-oauthlib, accepte au
point de jeton un ``device_code`` inventé pour tout client du flux appareil
(GHSA-3jp2-3mrg-2vxc, CVE-2026-49272), corrigé en 4.0.1. THÉRÈSE n'emploie
oauthlib qu'en client, jamais comme serveur de jetons ; la règle du dépôt reste
de monter, pas d'ignorer l'avis (B-256).
"""
import tomllib
from importlib.metadata import version
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
AVIS = ('CVE-2026-49272', 'GHSA-3jp2-3mrg-2vxc')


def _version(texte: str) -> tuple[int, ...]:
    return tuple(int(part) for part in texte.split('.')[:3])


def test_verrou_oauthlib_corrige_l_avis_sans_l_ignorer():
    verrou = tomllib.loads((RACINE / 'uv.lock').read_text(encoding='utf-8'))
    versions = [p['version'] for p in verrou['package'] if p['name'] == 'oauthlib']
    assert versions and all(_version(v) >= (4, 0, 1) for v in versions), versions
    for workflow in ('ci.yml', 'release.yml'):
        texte = (RACINE / '.github/workflows' / workflow).read_text(encoding='utf-8')
        assert not [avis for avis in AVIS if avis in texte], workflow


def test_client_oauth2_de_requests_oauthlib_reste_utilisable():
    from requests_oauthlib import OAuth2Session

    assert _version(version('oauthlib')) >= (4, 0, 1)
    session = OAuth2Session('client-test', redirect_uri='http://127.0.0.1:9/rappel',
                            scope=['openid'])
    url, etat = session.authorization_url('https://accounts.example.test/o/oauth2/auth')
    assert url.startswith('https://accounts.example.test/o/oauth2/auth?')
    assert 'client_id=client-test' in url and f'state={etat}' in url
