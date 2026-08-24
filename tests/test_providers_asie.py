"""Quatre fournisseurs ajoutés le 24/08/2026 : GLM, Kimi, Qwen, MiniMax.

Tous exposent une API compatible OpenAI, confirmée dans leur documentation
officielle. Ils héritent donc du fournisseur OpenAI, qui porte déjà la boucle
d'outils complète, le rejeu des tours précédents et la mesure réelle des jetons.

Ce que ces tests protègent, c'est ce qui se perd quand on ajoute un fournisseur
par copier-coller : une URL de base fausse produit une erreur réseau opaque, et
un fournisseur qui n'hérite pas de la boucle d'outils répond en texte sans jamais
créer le contact demandé — c'est exactement le défaut qu'a connu Grok avant qu'il
n'hérite d'OpenAI.

Un cas mérite une attention particulière : Qwen. Son URL contient l'identifiant
d'espace de travail du compte, elle ne peut donc pas être écrite en dur.
"""
import pytest


class TestLesQuatreFournisseursSontDeclares:
    @pytest.mark.parametrize(
        "valeur", ["glm", "kimi", "qwen", "minimax"]
    )
    def test_le_fournisseur_existe_dans_l_enumeration(self, valeur):
        from app.services.providers.base import LLMProvider

        assert valeur in [p.value for p in LLMProvider], (
            f"{valeur} n'est pas déclaré : impossible de le sélectionner"
        )


class TestChacunHeriteDeLaBoucleDOutils:
    """Sans héritage, le modèle répond en texte et n'agit jamais."""

    @pytest.mark.parametrize(
        "chemin,classe",
        [
            ("app.services.providers.glm", "GLMProvider"),
            ("app.services.providers.kimi", "KimiProvider"),
            ("app.services.providers.qwen", "QwenProvider"),
            ("app.services.providers.minimax", "MiniMaxProvider"),
        ],
    )
    def test_le_fournisseur_herite_d_openai(self, chemin, classe):
        import importlib

        from app.services.providers.openai import OpenAIProvider

        module = importlib.import_module(chemin)
        fournisseur = getattr(module, classe)

        assert issubclass(fournisseur, OpenAIProvider), (
            f"{classe} n'hérite pas d'OpenAIProvider : il perdrait la boucle "
            "d'outils, et « crée un contact » répondrait sans rien créer"
        )

    @pytest.mark.parametrize(
        "chemin,classe,fragment",
        [
            ("app.services.providers.glm", "GLMProvider", "api.z.ai"),
            ("app.services.providers.kimi", "KimiProvider", "api.moonshot.ai"),
            ("app.services.providers.minimax", "MiniMaxProvider", "api.minimax.io"),
        ],
    )
    def test_l_adresse_est_celle_de_la_documentation(self, chemin, classe, fragment):
        import importlib

        module = importlib.import_module(chemin)
        fournisseur = getattr(module, classe)

        assert fragment in fournisseur.API_URL, (
            f"{classe} pointe vers {fournisseur.API_URL}, qui ne correspond pas "
            f"à {fragment} relevé dans la documentation officielle"
        )
        assert fournisseur.API_URL.startswith("https://"), "adresse non chiffrée"


class TestQwenGardeSonAdresseParametrable:
    """L'URL de Qwen contient l'identifiant d'espace de travail du compte.

    L'écrire en dur reviendrait à ne fonctionner que pour un seul utilisateur.
    """

    def test_l_adresse_par_defaut_est_surchargeable(self):
        from app.services.providers.qwen import QwenProvider

        assert hasattr(QwenProvider, "API_URL")
        assert "maas.aliyuncs.com" in QwenProvider.API_URL

    def test_une_adresse_personnalisee_est_respectee(self):
        from app.services.providers.base import LLMConfig, LLMProvider
        from app.services.providers.qwen import QwenProvider

        perso = "https://mon-espace.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1/chat/completions"
        config = LLMConfig(
            provider=LLMProvider.QWEN,
            model="qwen3.8-max",
            api_key="essai",
            base_url=perso,
        )
        fournisseur = QwenProvider(config, client=None)

        assert fournisseur.url_effective() == perso, (
            "l'adresse configurée est ignorée : le fournisseur ne marcherait "
            "que pour l'espace de travail écrit en dur"
        )

    def test_sans_adresse_configuree_on_retombe_sur_le_defaut(self):
        from app.services.providers.base import LLMConfig, LLMProvider
        from app.services.providers.qwen import QwenProvider

        config = LLMConfig(
            provider=LLMProvider.QWEN, model="qwen3.8-max", api_key="essai"
        )

        assert QwenProvider(config, client=None).url_effective() == QwenProvider.API_URL


class TestLesModelesSontProposes:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "fournisseur,recommande",
        [
            ("glm", "glm-5.3"),
            ("kimi", "kimi-k3"),
            ("qwen", "qwen3.8-max"),
            ("minimax", "MiniMax-M3"),
        ],
    )
    async def test_le_modele_recommande_arrive_en_premier(
        self, fournisseur, recommande
    ):
        from app.routers.config import _available_models_for

        proposes = await _available_models_for(fournisseur)

        assert proposes, f"aucun modèle proposé pour {fournisseur}"
        assert proposes[0] == recommande, (
            f"{fournisseur} recommande {proposes[0]} au lieu de {recommande}"
        )

    @pytest.mark.asyncio
    async def test_la_casse_de_minimax_est_respectee(self):
        """`MiniMax-M3` : la documentation impose ces majuscules."""
        from app.routers.config import _available_models_for

        proposes = await _available_models_for("minimax")

        assert all(m.startswith("MiniMax-") for m in proposes), (
            f"casse altérée : {proposes}. L'API refuse les minuscules."
        )
