"""GPT-5 refuse toute température autre que la sienne.

Signalé par Ludo le 28/08 : « gpt ne marche pas », API error 400 sur chaque
message. Reproduit contre l'API réelle, qui répond mot pour mot :

    Unsupported value: 'temperature' does not support 0.7 with this model.
    Only the default (1) value is supported.

C'est le même motif que Gemini 3 en 0.48.2 : un modèle de raisonnement refuse
les réglages d'échantillonnage. Le provider envoyait `temperature` à tous les
modèles sans distinction, et toute la famille gpt-5 était donc inutilisable.
"""
from app.services.llm import LLMConfig, LLMProvider
from app.services.providers.openai import OpenAIProvider


def _corps(modele: str) -> dict:
    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        model=modele,
        api_key="test",
        temperature=0.7,
        max_tokens=4096,
    )
    import httpx
    provider = OpenAIProvider(config, httpx.AsyncClient())
    return provider._build_request_body([{"role": "user", "content": "test"}], None)


class TestLesModelesDeRaisonnementNAcceptentPasLaTemperature:
    def test_gpt_5_6_ne_recoit_pas_de_temperature(self):
        assert "temperature" not in _corps("gpt-5.6-luna")

    def test_toute_la_famille_gpt_5_est_couverte(self):
        for modele in ("gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.5", "gpt-5.5-pro", "gpt-5.4-mini"):
            assert "temperature" not in _corps(modele), modele

    def test_la_serie_o_aussi(self):
        for modele in ("o1", "o3-mini", "o4-preview"):
            assert "temperature" not in _corps(modele), modele

    def test_un_modele_classique_garde_sa_temperature(self):
        """Le réglage reste utile là où il est accepté : on ne le retire pas partout."""
        corps = _corps("gpt-4o")
        assert corps["temperature"] == 0.7

    def test_le_reste_du_corps_est_intact(self):
        corps = _corps("gpt-5.6-luna")
        assert corps["model"] == "gpt-5.6-luna"
        assert corps["max_completion_tokens"] == 4096
        assert corps["stream"] is True


class TestUneErreurDeLApiSeLitDansLesLogs:
    """« API error: 400 » ne dit pas ce qui a été refusé.

    Le message d'OpenAI portait la réponse exacte — « temperature does not
    support 0.7 with this model » — et le log la jetait. Diagnostiquer a
    demandé de reproduire l'appel à la main. Le détail appartient aux logs,
    pas à l'écran : la frontière d'erreurs de la 0.48 reste tenue.
    """

    def test_le_detail_de_l_api_part_dans_le_log(self):
        import inspect

        from app.services.providers import openai as module

        source = inspect.getsource(module)
        # Le corps de la réponse d'erreur doit être lu, pas seulement son code.
        assert "e.response.text" in source or "e.response.json()" in source, (
            "le message d'erreur de l'API est perdu : diagnostiquer un 400 "
            "oblige à reproduire l'appel à la main"
        )
