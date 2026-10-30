"""Avis du 29/10/2026 sur pyasn1 et pypdf, corrigés par montée (correctifs 0.83, règle B-256).

Ils sont apparus dans pip-audit, porte de release, après le passage de
l'intégration du 30/10 à 23 h 26 :
- pyasn1 0.6.4 (tiré par rsa et pyasn1-modules) : quatre décodages BER/DER
  en temps quadratique, corrigés en 0.6.5 (GHSA-fm9c-5rcf-2q5p,
  GHSA-9m75-vc3g-4x39, GHSA-2qm8-x737-gmw5, GHSA-mm57-4v3p-rchx) ;
- pypdf 6.21.2 (lecture et marquage des PDF) : temps et mémoire excessifs
  sur des PDF piégés, corrigés en 6.21.3 (GHSA-42gh-23hr-vphw,
  GHSA-4vqv-7265-gm2w, GHSA-62m5-6wh8-28x7, GHSA-x3rh-gjgm-fmqc).
"""
import tomllib
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
MINIMA = {
    'pyasn1': ((0, 6, 5), ('CVE-2026-119194', 'CVE-2026-119195', 'CVE-2026-119196', 'CVE-2026-119197')),
}


@pytest.mark.parametrize('paquet', sorted(MINIMA))
def test_verrou_corrige_les_avis_sans_les_ignorer(paquet):
    minimum, avis = MINIMA[paquet]
    verrou = tomllib.loads((RACINE / 'uv.lock').read_text(encoding='utf-8'))
    versions = [p['version'] for p in verrou['package'] if p['name'] == paquet]
    assert versions and all(tuple(int(x) for x in v.split('.')[:3]) >= minimum for v in versions), versions
    ci = (RACINE / '.github/workflows/ci.yml').read_text(encoding='utf-8')
    assert not [a for a in avis if a in ci]
