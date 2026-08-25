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
