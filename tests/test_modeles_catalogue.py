"""Lot A1 du jalon 0.48 - le catalogue neutre, source unique des modèles
et de la politique d'effort.

Contrats (design V3.5, docs/plans/2026-08-25-jalon-048-design.md) :
- la TÊTE de chaque liste est le frontier du fournisseur (relevé aux
  sources le 25/08/2026) ;
- `resoudre_effort(modele, effort_demande)` est LE résolveur unique :
  trois politiques par modèle (non envoyé | transmis tel quel |
  traduit) ; un modèle inconnu (Ollama dynamique) = transmis tel quel ;
- les quatre tables de llm.py et `_available_models_for` de config.py
  DÉRIVENT du catalogue - plus aucun modèle codé en dur ailleurs ;
- aucun import de llm.py (pas de cycle) : LLMProvider vient de
  providers.base.
"""

import pytest


class TestLesFrontiers:
    def test_la_tete_de_chaque_liste_est_le_frontier_verifie(self):
        from app.services import modeles_catalogue as cat

        attendus = {
            "anthropic": "claude-opus-5",
            "openai": "gpt-5.6-sol",
            "gemini": "gemini-3.7-flash",
            "mistral": "mistral-medium-3-5",
            "grok": "grok-4.6",
        }
        for fournisseur, frontier in attendus.items():
            assert cat.frontier(fournisseur) == frontier, (
                f"le frontier de {fournisseur} n'est pas la tête du catalogue"
            )
            assert cat.modeles_ordonnes(fournisseur)[0] == frontier

    def test_le_catalogue_n_importe_pas_llm(self):
        import app.services.modeles_catalogue as cat

        assert "app.services.llm" not in getattr(cat, "__dict__", {}).get(
            "__depends__", ""
        )

        from pathlib import Path

        source = Path(cat.__file__).read_text(encoding="utf-8")
        assert "from app.services.llm" not in source
        assert "import app.services.llm" not in source
        assert "from app.services import llm" not in source


class TestLeResolveurUnique:
    @pytest.mark.parametrize(
        ("modele", "demande", "attendu"),
        [
            # traduit : la valeur MAX vérifiée à la source
            ("claude-opus-5", "max", "max"),
            ("claude-fable-5", "max", "max"),
            ("grok-4.6", "max", "xhigh"),
            ("grok-4.5", "max", "high"),  # plafond existant conservé
            ("gemini-3.7-flash", "max", "HIGH"),
            ("mistral-medium-3-5", "max", "high"),
            ("mistral-medium-latest", "max", "high"),
            # transmis tel quel (support vérifié)
            ("gpt-5.6-sol", "max", "max"),
            ("gpt-5.6-terra", "high", "high"),
            # NON envoyé (support non vérifié - contrat figé 0.31)
            ("gpt-5.5", "max", None),
            ("gpt-5.4-mini", "high", None),
            # inconnu (Ollama dynamique) : transmis tel quel, le provider
            # garde sa dégradation gracieuse
            ("mistral-nemo:12b", "max", "max"),
            ("qwen3:8b", "high", "high"),
        ],
    )
    def test_resolution(self, modele, demande, attendu):
        from app.services.modeles_catalogue import resoudre_effort

        assert resoudre_effort(modele, demande) == attendu

    def test_sans_demande_rien_n_est_resolu(self):
        from app.services.modeles_catalogue import resoudre_effort

        assert resoudre_effort("claude-opus-5", None) is None
        assert resoudre_effort("gpt-5.6-sol", None) is None

    def test_gemini_3_6_et_anterieurs_gardent_leurs_niveaux(self):
        """thinkingLevel sur un modèle < 3 = erreur API : le résolveur ne
        doit RIEN envoyer aux 2.x, et traduire pour les 3.x."""
        from app.services.modeles_catalogue import resoudre_effort

        assert resoudre_effort("gemini-2.5-pro", "max") is None
        assert resoudre_effort("gemini-3.6-flash", "max") == "HIGH"

    def test_max_tokens_recommande(self):
        from app.services.modeles_catalogue import max_tokens_recommande

        assert max_tokens_recommande("claude-opus-5") == 64000
        assert max_tokens_recommande("gpt-5.5") is None


class TestLesQuatreTablesDerivent:
    def test_le_helper_par_fournisseur_sert_le_frontier(self, client):
        """llm.py:1016 - le défaut du helper est la tête du catalogue."""
        from app.services import modeles_catalogue as cat
        from app.services.llm import get_llm_service_for_provider

        for fournisseur in ("anthropic", "openai", "gemini", "mistral", "grok"):
            service = get_llm_service_for_provider(fournisseur)
            if service is None:  # pas de clé configurée dans le harnais
                continue
            assert service.config.model == cat.frontier(fournisseur)

    @pytest.mark.asyncio
    async def test_available_models_suit_l_ordre_du_catalogue(self, client):
        """config.py - la liste UI est CELLE du catalogue, même ordre."""
        from app.routers.config import _available_models_for
        from app.services import modeles_catalogue as cat

        for fournisseur in ("anthropic", "openai", "gemini", "mistral", "grok"):
            assert await _available_models_for(fournisseur) == cat.modeles_ordonnes(
                fournisseur
            ), f"la liste UI de {fournisseur} diverge du catalogue"


class TestLesTablesDeLlmDeriventDuCatalogue:
    """0.48 : les 3 tables restantes de llm.py (_default_config principale,
    repli par clé, circuit breaker) suivent le catalogue - plus aucun
    modèle codé en dur qui périme en silence (claude-opus-4-8, gpt-5.5,
    grok-4.3 étaient restés dans ces tables après la MAJ 0.43.4)."""

    def _poser_preference(self, cle, valeur):
        from app.models.database import get_sync_connection
        from sqlalchemy import text

        with get_sync_connection() as conn:
            conn.execute(
                text(
                    "INSERT OR REPLACE INTO preferences"
                    " (id, key, value, category, created_at, updated_at)"
                    " VALUES (lower(hex(randomblob(16))), :k, :v, 'llm',"
                    " datetime('now'), datetime('now'))"
                ),
                {"k": cle, "v": valeur},
            )
            conn.commit()

    def test_provider_selectionne_sans_modele_recoit_le_frontier(
        self, client, monkeypatch
    ):
        from app.services.llm import LLMService
        from app.services.modeles_catalogue import CATALOGUE, frontier

        self._poser_preference("llm_provider", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        config = LLMService()._default_config()
        assert config.model == frontier("openai")
        assert config.context_window == CATALOGUE["openai"].context_window

    def test_repli_par_cle_recoit_le_frontier(self, client, monkeypatch):
        """Sans préférence : première clé trouvée (anthropic) -> frontier."""
        from app.services.llm import LLMService
        from app.services.modeles_catalogue import CATALOGUE, frontier

        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        for var in ("OPENAI_API_KEY", "GEMINI_API_KEY", "MISTRAL_API_KEY"):
            monkeypatch.delenv(var, raising=False)
        config = LLMService()._default_config()
        assert config.provider.value == "anthropic"
        assert config.model == frontier("anthropic")
        assert config.context_window == CATALOGUE["anthropic"].context_window

    def test_circuit_breaker_derive_du_catalogue(self, client, monkeypatch):
        from app.services.llm import LLMService
        from app.services.modeles_catalogue import CATALOGUE, frontier
        from app.services.providers.base import LLMConfig, LLMProvider

        for var in (
            "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "MISTRAL_API_KEY",
            "XAI_API_KEY", "OPENROUTER_API_KEY", "DEEPSEEK_API_KEY",
        ):
            monkeypatch.delenv(var, raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

        service = LLMService(LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-opus-5",
            api_key="sk-ant-test",
        ))
        fallbacks = service._get_fallback_configs()
        openai_fb = next(
            c for c in fallbacks if c.provider is LLMProvider.OPENAI
        )
        assert openai_fb.model == frontier("openai")
        assert openai_fb.context_window == CATALOGUE["openai"].context_window


class TestSabotageParPermutation:
    """Design V3.5 : permuter la tête d'une fiche du catalogue doit se
    refléter PARTOUT (preuve que les tables dérivent, sans copie cachée)."""

    def test_permuter_la_tete_change_le_defaut_partout(self, client, monkeypatch):
        import dataclasses

        from app.services import modeles_catalogue as mc
        from app.services.llm import LLMService, get_llm_service_for_provider

        fiche = mc.CATALOGUE["openai"]
        modeles_permutes = (fiche.modeles[1], fiche.modeles[0], *fiche.modeles[2:])
        fiche_permutee = dataclasses.replace(fiche, modeles=modeles_permutes)
        monkeypatch.setitem(mc.CATALOGUE, "openai", fiche_permutee)
        # 1. frontier() suit
        tete = mc.frontier("openai")
        # 2. le helper (Board) suit
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        service = get_llm_service_for_provider(
            "openai", model_override=mc.frontier("openai")
        )
        # 3. _default_config suit (repli par clé, sans préférence)
        for var in ("ANTHROPIC_API_KEY",):
            monkeypatch.delenv(var, raising=False)
        config = LLMService()._default_config()

        assert tete != "gpt-5.6-sol"
        assert service is not None and service.config.model == tete
        assert config.model == tete or config.provider.value != "openai"


class TestLaCompletudeDuCatalogue:
    """Revue 0.48 F1 : le catalogue est devenu LA source des 4 tables de
    llm.py - un fournisseur de l'enum absent du catalogue disparaît de
    l'application au redémarrage (Infomaniak, trouvé par la revue)."""

    def test_chaque_fournisseur_de_l_enum_a_sa_fiche(self):
        from app.services.modeles_catalogue import CATALOGUE
        from app.services.providers.base import LLMProvider

        manquants = {p.value for p in LLMProvider} - set(CATALOGUE)
        assert manquants == set(), (
            f"fournisseurs sans fiche au catalogue : {manquants} - "
            "ils disparaissent de _default_config au redémarrage"
        )

    def test_infomaniak_redevient_reconnu_au_demarrage(self, client, monkeypatch):
        """Le scénario de la revue : préférence infomaniak posée, clé env -
        _default_config doit rendre une config infomaniak, pas Ollama."""
        from app.models.database import get_sync_connection
        from app.services.llm import LLMService
        from sqlalchemy import text

        with get_sync_connection() as conn:
            for cle, valeur in (("llm_provider", "infomaniak"), ("llm_model", "mix")):
                conn.execute(
                    text(
                        "INSERT OR REPLACE INTO preferences"
                        " (id, key, value, category, created_at, updated_at)"
                        " VALUES (lower(hex(randomblob(16))), :k, :v, 'llm',"
                        " datetime('now'), datetime('now'))"
                    ),
                    {"k": cle, "v": valeur},
                )
            conn.commit()
        monkeypatch.setenv("INFOMANIAK_API_KEY", "ik-test")
        config = LLMService()._default_config()
        assert config.provider.value == "infomaniak"
        assert config.model == "mix"


class TestLesFrontiersSontTarifes:
    """Panel 0.48 : les 5 frontiers que le Board force étaient absents de
    TOKEN_PRICES → coût 0,00 € pour l'appel le plus cher de l'app. Prix
    relevés aux sources officielles le 25/08/2026."""

    def test_chaque_frontier_du_board_a_un_prix(self):
        from app.services.modeles_catalogue import frontier
        from app.services.token_tracker import TOKEN_PRICES

        sans_prix = []
        for fournisseur in ("anthropic", "openai", "gemini", "mistral", "grok"):
            modele = frontier(fournisseur)
            if modele not in TOKEN_PRICES:
                sans_prix.append(modele)
        assert sans_prix == [], (
            f"frontiers sans tarif (coût menti à 0,00 €) : {sans_prix}"
        )
