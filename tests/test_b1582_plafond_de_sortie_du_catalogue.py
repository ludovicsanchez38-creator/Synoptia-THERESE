"""B-1582 : le chat envoyait max_tokens 4096 à Opus 5.5, dont le plafond de
sortie couvre la réflexion ET le texte : après une longue réflexion, la
réponse était coupée sans le dire. Seul le Board appliquait le plafond
recommandé du catalogue. Il s'applique désormais à la construction de la
configuration ; un plafond explicite l'emporte.
"""


def _config(modele: str, **kwargs):
    from app.services.llm import LLMConfig, LLMProvider

    return LLMConfig(provider=LLMProvider.ANTHROPIC, model=modele, api_key="sk-test", **kwargs)


def test_opus_55_recoit_le_plafond_recommande():
    from app.services.modeles_catalogue import max_tokens_recommande

    assert _config("claude-opus-5-5").max_tokens == max_tokens_recommande("claude-opus-5-5") == 64000


def test_un_modele_sans_recommandation_garde_4096():
    assert _config("claude-haiku-4-5-20251001").max_tokens == 4096


def test_un_plafond_explicite_l_emporte():
    assert _config("claude-opus-5-5", max_tokens=8000).max_tokens == 8000
