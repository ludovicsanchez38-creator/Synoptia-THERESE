"""Cycle 6, lot 2 (10/09/2026) : candidats des lecteurs contredits par Grok, côté moteur.

- tableau de bord : les sources de clé LLM suivent la table du routeur de configuration ;
- disjoncteur : un échec est porté au fournisseur réellement appelé (repli compris) ;
- recherche web : une préférence illisible coupe la recherche et le dit, au lieu du défaut « autorisé » ;
- agenda depuis le chat : plusieurs agendas sans sélection ne se présentent pas comme « aucun calendrier » ;
- synchronisation CRM : l'onglet Deliverables annoncé est lu ;
- plafonds de jetons : un échec de lecture est retenté au contrôle suivant.
"""

from __future__ import annotations

import logging
import os

import pytest

# --- tableau de bord ------------------------------------------------------

def test_le_tableau_de_bord_connait_tous_les_fournisseurs_du_routeur_config():
    from app.routers.config import CLES_API_PAR_FOURNISSEUR
    from app.routers.dashboard import _LLM_KEY_SOURCES

    attendues = {pref for _env, pref in CLES_API_PAR_FOURNISSEUR.values()}
    connues = {pref for _envs, pref in _LLM_KEY_SOURCES}
    assert attendues <= connues, f"fournisseurs ignorés par la checklist : {sorted(attendues - connues)}"


@pytest.mark.asyncio
@pytest.mark.parametrize("variable", ["DEEPSEEK_API_KEY", "GLM_API_KEY", "KIMI_API_KEY", "QWEN_API_KEY", "MINIMAX_API_KEY", "PERPLEXITY_API_KEY", "INFOMANIAK_API_KEY"])
async def test_une_cle_d_un_fournisseur_recent_suffit_a_la_checklist(db_session, monkeypatch, variable):
    from app.routers.dashboard import _has_any_llm_key

    for nom in list(os.environ):
        if nom.endswith("_API_KEY"):
            monkeypatch.delenv(nom, raising=False)
    monkeypatch.setenv(variable, "cle-de-test")
    assert await _has_any_llm_key(db_session) is True, f"{variable} n'est pas reconnue comme une clé IA"


# --- disjoncteur ------------------------------------------------------------

@pytest.mark.asyncio
async def test_le_disjoncteur_porte_l_echec_au_fournisseur_de_repli(monkeypatch):
    from app.services import llm as module
    from app.services.llm import LLMConfig, LLMProvider, LLMService

    service = LLMService(LLMConfig(LLMProvider.ANTHROPIC, "claude-sonnet-4-6", api_key="k", max_tokens=4096))
    repli = LLMConfig(LLMProvider.OLLAMA, "repli-local", max_tokens=4096)
    monkeypatch.setattr(service, "_resolve_with_circuit_breaker", lambda: repli)
    echecs: list[str] = []

    class FauxDisjoncteur:
        def record_failure(self, provider, message):
            echecs.append(provider)

        def record_success(self, provider):
            pass

    monkeypatch.setattr(module, "get_circuit_breaker", lambda: FauxDisjoncteur())

    async def flux_en_panne(context, tools=None, enable_grounding=True, config=None):
        raise RuntimeError("repli en panne")
        yield  # pragma: no cover

    monkeypatch.setattr(service, "stream_response_with_tools", flux_en_panne)
    with pytest.raises(RuntimeError):
        await service.generate_content("Rédige")
    assert echecs == ["ollama"], f"l'échec est porté à {echecs}, alors que l'appel est parti sur le repli"


# --- recherche web ------------------------------------------------------------

@pytest.mark.asyncio
async def test_une_preference_de_recherche_web_illisible_coupe_la_recherche_et_le_dit(monkeypatch, caplog):
    from app.services import web_search

    monkeypatch.setattr(web_search, "_autorisation_recherche_cache", None)

    class _Contexte:
        async def __aenter__(self):
            raise RuntimeError("database is locked")

        async def __aexit__(self, *_):
            return False

    monkeypatch.setattr("app.models.database.get_session_context", lambda: _Contexte())
    with caplog.at_level(logging.WARNING):
        await web_search.charger_autorisation_depuis_la_base()
    assert web_search.recherche_web_autorisee() is False, "la préférence est illisible : la recherche doit être coupée, pas autorisée par défaut"
    assert any("recherche web" in r.getMessage().lower() for r in caplog.records if r.levelno >= logging.WARNING), "aucun avertissement"


# --- agenda depuis le chat ------------------------------------------------

@pytest.mark.asyncio
async def test_plusieurs_agendas_sans_selection_ne_se_presentent_pas_comme_aucun_calendrier(client, db_session):
    for nom in ("Perso", "Pro"):
        r = await client.post("/api/calendar/calendars", params={"summary": nom, "timezone": "Europe/Paris", "provider_type": "local"})
        assert r.status_code in (200, 201), r.text
    from app.services.workspace_tools import _list_calendar_events

    texte = await _list_calendar_events({}, db_session)
    assert "AUCUN CALENDRIER" not in texte.upper(), texte
    assert "plusieurs agendas" in texte.lower() and "Perso" in texte and "Pro" in texte, texte


# --- synchronisation CRM --------------------------------------------------

@pytest.mark.asyncio
async def test_la_synchronisation_crm_lit_l_onglet_deliverables(client, monkeypatch):
    from app.routers import crm as routeur
    from app.services import crm_sync, sheets_service

    onglets: list[str] = []

    class FauxSheets:
        def __init__(self, access_token=None, api_key=None):
            pass

        async def get_all_data_as_dicts(self, spreadsheet_id, sheet):
            onglets.append(sheet)
            return []

    async def _jeton(session):
        return "jeton"

    monkeypatch.setattr(sheets_service, "GoogleSheetsService", FauxSheets)
    monkeypatch.setattr(crm_sync, "ensure_valid_crm_token", _jeton)
    config = await client.post("/api/crm/sync/config", json={"spreadsheet_id": "feuille-de-test"})
    assert config.status_code in (200, 201), config.text
    reponse = await client.post("/api/crm/sync")
    assert reponse.status_code == 200, reponse.text
    assert "Deliverables" in onglets, f"onglets lus : {onglets}"
    assert routeur is not None


# --- plafonds de jetons ---------------------------------------------------

@pytest.fixture
def singleton_du_compteur_rendu_neutre():
    """Le compteur est un singleton : chaque test le laisse comme il l'a trouvé (défauts, non chargé)."""
    from app.services import token_tracker as module

    suivi = module.TokenTracker()
    yield suivi
    suivi._limits = module.TokenLimits()
    suivi._limites_chargees = False


def test_un_echec_de_lecture_des_plafonds_est_reessaye_au_controle_suivant(monkeypatch, singleton_du_compteur_rendu_neutre):
    from app.services import token_tracker as module

    suivi = singleton_du_compteur_rendu_neutre
    suivi._limites_chargees = False
    suivi._limits = module.TokenLimits()
    appels = {"n": 0}

    class _Connexion:
        def __enter__(self):
            appels["n"] += 1
            if appels["n"] == 1:
                raise RuntimeError("database is locked")
            return self

        def __exit__(self, *_):
            return False

        def execute(self, *_a, **_k):
            class _R:
                @staticmethod
                def fetchone():
                    return ('{"daily_input_limit": 42}',)
            return _R()

    import app.models.database as base

    monkeypatch.setattr(base, "get_sync_connection", lambda: _Connexion())
    suivi._charger_limites_si_besoin()
    assert suivi._limites_chargees is False, "un échec de lecture ne doit pas figer les plafonds par défaut"
    suivi._charger_limites_si_besoin()
    assert appels["n"] == 2 and suivi._limites_chargees is True


# --- compteur de jetons : lecteurs et zéro réel (secondes lectures, Grok D185/D186) --

def test_les_lecteurs_d_usage_chargent_les_plafonds_avant_de_les_lire(monkeypatch, singleton_du_compteur_rendu_neutre):
    suivi = singleton_du_compteur_rendu_neutre
    suivi._limites_chargees = False
    appels = {"n": 0}

    def _charge():
        appels["n"] += 1
        suivi._limites_chargees = True

    monkeypatch.setattr(suivi, "_charger_limites_si_besoin", _charge)
    suivi.get_daily_usage()
    assert appels["n"] >= 1, "get_daily_usage lit self._limits sans les charger"
    suivi._limites_chargees = False  # assignation directe : monkeypatch restaurerait True après la fixture
    suivi.get_monthly_usage()
    assert appels["n"] >= 2, "get_monthly_usage lit self._limits sans les charger"


def test_un_usage_reel_de_zero_jeton_n_est_pas_remplace_par_une_estimation(monkeypatch):
    from types import SimpleNamespace

    from app.services import token_tracker as module

    enregistre = {}

    class FauxSuivi:
        def record_usage(self, **kwargs):
            enregistre.update(kwargs)
            return SimpleNamespace(**kwargs)

    monkeypatch.setattr(module, "get_token_tracker", lambda: FauxSuivi())
    service = SimpleNamespace(config=SimpleNamespace(model="m", provider=SimpleNamespace(value="p")))
    module.enregistrer_usage_llm(service, {"input_tokens": 0, "output_tokens": 0}, "conv", texte_entree="un deux trois", texte_sortie="quatre cinq")
    assert enregistre["input_tokens"] == 0 and enregistre["output_tokens"] == 0, enregistre
    module.enregistrer_usage_llm(service, None, "conv", texte_entree="un deux trois", texte_sortie="quatre cinq")
    assert enregistre["input_tokens"] == 6 and enregistre["output_tokens"] == 4, "sans usage réel, l'estimation reste deux jetons par mot"
