import re
from pathlib import Path


def test_les_cinq_pages_oauth_sont_en_francais():
    source = Path('src/backend/app/routers/email.py').read_text(encoding='utf-8')
    balises = re.findall(r'<html[^>]*>', source)
    assert len(balises) == 5
    assert all('lang="fr"' in balise for balise in balises)
    assert '<title>THERESE' not in source
