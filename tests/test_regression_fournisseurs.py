"""Non-régression des fournisseurs LLM, vérifiée par le COMPORTEMENT (B-039, B-332).

Remplace les gardes textuelles de `test_regression.py` qui lisaient la source
(`read_text`) et y cherchaient des chaînes : BUG-025 (prompt système Ollama),
BUG-040/041 (erreurs Ollama lisibles), BUG-048 (num_predict/num_ctx), BUG-050
(délai de lecture), BUG-052/058/063/098 (préférences et repli), BUG-053 et
strftime Windows (date du jour), « réponses légères », registre OpenRouter,
réponses vides et codes 401/402 d'OpenRouter, lot 0.21.1 Ollama.

Chaque test exerce la fonction réelle avec un faux client HTTP et regarde ce
qu'elle produit ; un renommage interne ne le fait pas rougir, une régression
de comportement oui.
"""

from __future__ import annotations

import contextlib
import json
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import httpx
import pytest


class FausseReponse:
    def __init__(self, lignes: list[str], statut: int = 200, corps: bytes = b""):
        self.status_code = statut
        self._lignes = lignes
        self._corps = corps
        self.headers: dict[str, str] = {}

    async def aread(self):
        return self._corps

    async def aiter_lines(self):
        for ligne in self._lignes:
            yield ligne

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"{self.status_code}", request=MagicMock(), response=self
            )


class FauxClient:
    """Client httpx factice : mémorise l'appel et rend une réponse préparée."""

    def __init__(self, reponse: FausseReponse | None = None, exception: Exception | None = None):
        self.reponse = reponse
        self.exception = exception
        self.appels: list[dict] = []

    def stream(self, method, url, **kwargs):
        self.appels.append({"method": method, "url": url, **kwargs})
        if self.exception is not None:
            raise self.exception

        @contextlib.asynccontextmanager
        async def _cm():
            yield self.reponse

        return _cm()

    async def aclose(self):
        return None


def _config_ollama(**kw):
    from app.services.providers.base import LLMConfig, LLMProvider

    modele = kw.pop("model", "gemma-test")
    return LLMConfig(LLMProvider.OLLAMA, modele, **kw)


def _ollama(client: FauxClient, **kw):
    from app.services.providers.ollama import OllamaProvider

    return OllamaProvider(_config_ollama(**kw), client)


async def _evenements(provider, systeme="Tu es THÉRÈSE.", messages=None):
    messages = messages or [{"role": "user", "content": "Bonjour"}]
    sortie = []
    async for evenement in provider.stream(systeme, messages):
        sortie.append(evenement)
    return sortie


def _erreurs(evenements):
    return [e.content or "" for e in evenements if e.type == "error"]


# ---------------------------------------------------------------- Ollama


class TestOllamaCorpsDeRequete:
    def test_le_prompt_systeme_est_un_message_system_unique(self):
        provider = _ollama(FauxClient())
        corps = provider._build_request_body(
            "SYSTÈME", [{"role": "system", "content": "ancien"}, {"role": "user", "content": "Bonjour"}]
        )
        roles = [m["role"] for m in corps["messages"]]
        assert corps["messages"][0] == {"role": "system", "content": "SYSTÈME"}
        assert roles.count("system") == 1, "les messages system existants doivent être filtrés"
        assert "system" not in corps, "/api/chat n'accepte pas de champ system de premier niveau"

    @pytest.mark.parametrize(
        ("max_tokens", "context_window", "num_predict", "num_ctx"),
        [(6000, 200_000, 6000, 8192), (256, 512, 256, 2048), (4096, 4096, 4096, 4096)],
    )
    def test_les_options_suivent_la_configuration_bornee(self, max_tokens, context_window, num_predict, num_ctx):
        provider = _ollama(FauxClient(), max_tokens=max_tokens, context_window=context_window)
        options = provider._build_request_body(None, [{"role": "user", "content": "x"}])["options"]
        assert options["num_predict"] == num_predict
        assert options["num_ctx"] == num_ctx, "num_ctx est borné entre 2048 et 8192 (BUG-052)"

    @pytest.mark.asyncio
    async def test_l_url_de_base_perd_sa_barre_finale_et_la_connexion_est_bornee(self):
        client = FauxClient(FausseReponse([json.dumps({"message": {"content": "ok"}, "done": True})]))
        provider = _ollama(client, base_url="http://127.0.0.1:11434/")
        await _evenements(provider)
        appel = client.appels[0]
        assert appel["url"] == "http://127.0.0.1:11434/api/chat", appel["url"]
        delai = appel["timeout"]
        assert delai.connect == 5.0, "la connexion doit échouer vite si Ollama n'est pas lancé"
        assert delai.read is None, "pas de délai de lecture : un skill Office peut dépasser deux minutes (BUG-050)"


class TestOllamaErreursLisibles:
    @pytest.mark.asyncio
    async def test_connexion_impossible_suggere_ollama_serve(self):
        provider = _ollama(FauxClient(exception=httpx.ConnectError("refusée")))
        messages = _erreurs(await _evenements(provider))
        assert messages and "ollama serve" in messages[0], messages

    @pytest.mark.asyncio
    async def test_modele_absent_suggere_ollama_pull(self):
        corps = json.dumps({"error": "model 'gemma-test' not found"}).encode()
        provider = _ollama(FauxClient(FausseReponse([], statut=404, corps=corps)))
        messages = _erreurs(await _evenements(provider))
        assert messages and "ollama pull" in messages[0], messages

    @pytest.mark.asyncio
    async def test_erreur_interne_500_est_nommee(self):
        provider = _ollama(FauxClient(FausseReponse([], statut=500, corps=b'{"error":"boom"}')))
        messages = _erreurs(await _evenements(provider))
        assert messages and "500" in messages[0], messages

    @pytest.mark.asyncio
    async def test_une_erreur_dans_le_flux_devient_un_evenement_d_erreur(self):
        provider = _ollama(FauxClient(FausseReponse([json.dumps({"error": "out of memory"})])))
        messages = _erreurs(await _evenements(provider))
        assert messages, "le champ error d'un événement du flux doit remonter"
        assert "erreur" in messages[0].lower()

    @pytest.mark.asyncio
    async def test_une_reponse_vide_ne_reste_pas_silencieuse(self):
        provider = _ollama(FauxClient(FausseReponse([json.dumps({"message": {"content": ""}, "done": True})])))
        messages = _erreurs(await _evenements(provider))
        assert messages and "aucun contenu" in messages[0].lower(), messages


# ---------------------------------------------------------------- prompt système


class TestPromptSystemeDuJour:
    def _prompt(self, profil=None):
        from app.services.llm import LLMService

        with patch("app.services.user_profile.get_cached_profile", return_value=profil):
            service = LLMService.__new__(LLMService)
            return service._get_system_prompt_with_identity()

    def test_la_date_du_jour_est_substituee_en_francais_sans_zero_initial(self):
        maintenant = datetime.now(UTC)
        mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
                "septembre", "octobre", "novembre", "décembre"][maintenant.month - 1]
        prompt = self._prompt()
        assert "{current_date}" not in prompt
        assert f"{maintenant.day} {mois} {maintenant.year}" in prompt, (
            "la date doit être écrite jour mois année, sans %-d (absent sous Windows)"
        )

    def test_avec_un_profil_la_date_exemple_est_aussi_substituee(self):
        from app.services.user_profile import UserProfile

        prompt = self._prompt(UserProfile(name="Jérôme"))
        assert "Jérôme" in prompt
        assert "{current_date_example}" not in prompt and "{current_date}" not in prompt

    def test_les_regles_de_reponse_legere_sont_dans_le_prompt(self):
        prompt = self._prompt().lower()
        assert "tableau" in prompt, "le prompt doit décourager les tableaux markdown (réponses légères)"
        assert "puces" in prompt or "listes" in prompt
        assert "chat uniquement" in prompt, "la règle de récapitulatif ne vaut que pour le chat (BUG-053)"


# ---------------------------------------------------------------- préférences et repli


async def _poser_preferences(db_session, **valeurs):
    from app.models.entities import Preference

    for cle, valeur in valeurs.items():
        db_session.add(Preference(key=cle, value=valeur))
    await db_session.commit()


class TestPreferencesDeModele:
    @pytest.mark.asyncio
    async def test_la_configuration_par_defaut_lit_le_fournisseur_et_le_modele_choisis(self, client, db_session):
        from app.services.llm import LLMProvider, LLMService

        await _poser_preferences(db_session, llm_provider="ollama", llm_model="qwen-choisi:8b")
        config = LLMService.__new__(LLMService)._default_config()
        assert config.provider == LLMProvider.OLLAMA
        assert config.model == "qwen-choisi:8b", "le modèle choisi l'emporte sur la détection (BUG-052)"

    @pytest.mark.asyncio
    async def test_le_modele_choisi_ne_s_applique_qu_a_son_fournisseur(self, client, db_session, monkeypatch):
        from app.services import llm as module

        await _poser_preferences(db_session, llm_provider="anthropic", llm_model="claude-choisi")
        monkeypatch.setattr(module, "_get_api_key_from_db", lambda nom: "cle-de-test")
        service_openai = module.get_llm_service_for_provider("openai")
        assert service_openai is not None
        assert service_openai.config.model != "claude-choisi", (
            "le modèle d'Anthropic ne doit pas être imposé à OpenAI (BUG-058)"
        )
        service_anthropic = module.get_llm_service_for_provider("anthropic")
        assert service_anthropic is not None and service_anthropic.config.model == "claude-choisi"

    @pytest.mark.asyncio
    async def test_sans_preference_le_repli_utilise_la_detection_ollama(self, client, monkeypatch):
        from app.services import llm as module

        monkeypatch.setattr(module, "_get_api_key_from_db", lambda nom: None)
        monkeypatch.setattr(module, "_cle_depuis_environnement", lambda nom: None)
        monkeypatch.setattr(module, "detect_default_ollama_model", lambda *a, **k: "modele-detecte:latest")
        config = module.LLMService.__new__(module.LLMService)._default_config()
        assert config.provider == module.LLMProvider.OLLAMA
        assert config.model == "modele-detecte:latest", "le repli ne doit pas coder un modèle en dur (BUG-098)"

    @pytest.mark.asyncio
    async def test_sur_la_version_installee_le_repli_ignore_les_cles_de_l_environnement(self, client, monkeypatch):
        from app.config import settings
        from app.services import llm as module

        monkeypatch.setattr(module, "_get_api_key_from_db", lambda nom: None)
        monkeypatch.setattr(module, "detect_default_ollama_model", lambda *a, **k: "local:latest")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-inconnue")
        monkeypatch.delenv("THERESE_LIRE_CLES_ENV", raising=False)

        monkeypatch.setattr(settings, "therese_env", "production")
        assert module.LLMService.__new__(module.LLMService)._default_config().provider == module.LLMProvider.OLLAMA

        monkeypatch.setattr(settings, "therese_env", "development")
        assert module.LLMService.__new__(module.LLMService)._default_config().provider == module.LLMProvider.ANTHROPIC


# ---------------------------------------------------------------- OpenRouter


def _openrouter(client: FauxClient):
    from app.services.providers.base import LLMConfig, LLMProvider
    from app.services.providers.openrouter import OpenRouterProvider

    return OpenRouterProvider(LLMConfig(LLMProvider.OPENROUTER, "anthropic/claude-sonnet-4-6", api_key="k"), client)


def _sse(*deltas, finish: str | None = "stop"):
    lignes = [
        "data: " + json.dumps({"choices": [{"delta": {"content": d}, "finish_reason": None}]})
        for d in deltas
    ]
    lignes.append("data: " + json.dumps({"choices": [{"delta": {}, "finish_reason": finish}]}))
    lignes.append("data: [DONE]")
    return lignes


class TestOpenRouter:
    @pytest.mark.asyncio
    async def test_le_registre_construit_bien_un_fournisseur_openrouter(self):
        from app.services.llm import LLMConfig, LLMProvider, LLMService

        service = LLMService(LLMConfig(LLMProvider.OPENROUTER, "openai/gpt-5.6", api_key="k"))
        await service._ensure_provider()
        assert type(service._provider).__name__ == "OpenRouterProvider"

    @pytest.mark.asyncio
    async def test_la_requete_part_vers_l_api_openrouter(self):
        client = FauxClient(FausseReponse(_sse("Bonjour")))
        await _evenements(_openrouter(client))
        assert client.appels[0]["url"].startswith("https://openrouter.ai/api/v1/")

    @pytest.mark.asyncio
    async def test_une_reponse_vide_est_annoncee(self):
        messages = _erreurs(await _evenements(_openrouter(FauxClient(FausseReponse(_sse())))))
        assert messages and "aucune réponse" in messages[0].lower(), messages

    @pytest.mark.asyncio
    async def test_budget_epuise_sans_texte_est_explique(self):
        messages = _erreurs(await _evenements(_openrouter(FauxClient(FausseReponse(_sse(finish="length"))))))
        assert messages and "budget" in messages[0].lower(), messages

    @pytest.mark.asyncio
    async def test_le_filtre_de_contenu_est_explique(self):
        messages = _erreurs(await _evenements(_openrouter(FauxClient(FausseReponse(_sse(finish="content_filter"))))))
        assert messages and "filtr" in messages[0].lower(), messages

    @pytest.mark.asyncio
    async def test_une_erreur_dans_le_flux_sse_remonte(self):
        lignes = ["data: " + json.dumps({"error": {"message": "Provider returned error", "code": 502}}), "data: [DONE]"]
        messages = _erreurs(await _evenements(_openrouter(FauxClient(FausseReponse(lignes)))))
        assert messages, "une erreur SSE doit produire un événement d'erreur"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(("statut", "attendu"), [(401, "invalide"), (402, "insuffisant")])
    async def test_les_codes_401_et_402_ont_un_message_clair(self, statut, attendu):
        reponse = MagicMock()
        reponse.status_code = statut
        reponse.text = ""
        erreur = httpx.HTTPStatusError(str(statut), request=MagicMock(), response=reponse)
        messages = _erreurs(await _evenements(_openrouter(FauxClient(exception=erreur))))
        assert messages and attendu in messages[0].lower(), messages
