"""R1-9 : le repli hors ligne est généré depuis le catalogue du moteur."""
import json
from pathlib import Path

from app.services.modeles_catalogue import CATALOGUE, fenetre_de_contexte
from app.services.token_tracker import get_token_tracker


def test_argon_sans_caracteristiques_inventees():
    assert 'gemini-4-argon' in CATALOGUE['gemini'].modeles
    assert fenetre_de_contexte('gemini', 'gemini-4-argon') == 32000
    assert not get_token_tracker().tarif_connu('gemini-4-argon')


def test_snapshot_frontend_et_defauts_identiques():
    contenu = json.loads((Path(__file__).resolve().parents[1] / 'src/frontend/src/lib/modelesCatalogue.generated.json').read_text(encoding="utf-8"))
    for nom, fiche in CATALOGUE.items():
        if nom == 'ollama':
            continue
        assert [m['id'] for m in contenu[nom]] == list(fiche.modeles)
    assert contenu['anthropic'][0]['id'] == 'claude-opus-5-5'
