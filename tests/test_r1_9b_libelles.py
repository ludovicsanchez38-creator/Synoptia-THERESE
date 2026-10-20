"""R1-9b : les identifiants OpenRouter connus gardent le nom du modèle natif."""
import json
from pathlib import Path

import pytest
from app.services.modeles_catalogue import catalogue_pour_interface, libelle_modele


@pytest.mark.parametrize('modele', [
    'anthropic/claude-sonnet-4-6',
    'anthropic/claude-opus-4-8',
    'openai/gpt-5.5',
    'google/gemini-3.5-flash',
])
def test_modele_openrouter_connu_reprend_le_libelle_natif(modele):
    assert libelle_modele(modele) == libelle_modele(modele.split('/', 1)[1])


@pytest.mark.parametrize(('modele', 'attendu'), [
    ('meta-llama/llama-4-maverick', 'Meta Llama/llama 4 Maverick'),
    ('inconnu/modele-1-2', 'Inconnu/modele 1.2'),
])
def test_modele_inconnu_garde_son_libelle_actuel(modele, attendu):
    assert libelle_modele(modele) == attendu


def test_snapshot_complet_regenere_depuis_le_catalogue():
    chemin = Path(__file__).resolve().parents[1] / 'src/frontend/src/lib/modelesCatalogue.generated.json'
    assert json.loads(chemin.read_text(encoding='utf-8')) == catalogue_pour_interface()
