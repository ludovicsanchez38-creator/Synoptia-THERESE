import pytest
from app.services.modeles_catalogue import libelle_modele


@pytest.mark.parametrize(('identifiant', 'libelle'), [
    ('grok-4.20-0309-reasoning', 'Grok 4.20 Reasoning'),
    ('grok-4.20-0309-non-reasoning', 'Grok 4.20 Non Reasoning'),
    ('google/gemini-3.1-pro', 'Gemini 3.1 Pro'),
    ('meta-llama/llama-4-maverick', 'Llama 4 Maverick'),
    ('deepseek-v4-pro', 'DeepSeek V4 Pro'),
    ('ministral-8b-2512', 'Ministral 8B'),
])
def test_libelles(identifiant, libelle):
    assert libelle_modele(identifiant) == libelle

# Dix identifiants inventés après le correctif, sans appel de fournisseur.
@pytest.mark.parametrize(('identifiant', 'libelle'), [
    ('grok-4.21-0412-reasoning', 'Grok 4.21 Reasoning'),
    ('grok-4.21-0412-non-reasoning', 'Grok 4.21 Non Reasoning'),
    ('google/gemini-4.2-flash', 'Gemini 4.2 Flash'),
    ('meta-llama/llama-5-scout', 'Llama 5 Scout'),
    ('deepseek-v5-chat', 'DeepSeek V5 Chat'),
    ('ministral-12b-2610', 'Ministral 12B'),
    ('claude-sonnet-5-7-20261022', 'Claude Sonnet 5.7'),
    ('openai/gpt-7-mini', 'GPT-7 Mini'),
    ('qwen-4-3b', 'Qwen 4 3B'),
    ('minimax-m3', 'MiniMax M3'),
])
def test_rejeu_apres_correctif(identifiant, libelle):
    assert libelle_modele(identifiant) == libelle
