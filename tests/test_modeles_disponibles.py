"""Les modèles proposés à l'utilisateur doivent exister (24/08/2026).

Deux défauts distincts motivent ces tests.

Le premier est un décalage : la liste s'était arrêtée à Claude Opus 4.8 et
Grok 4.3, alors que plusieurs générations sont sorties depuis. Proposer un
modèle périmé n'est pas grave ; proposer un modèle RETIRÉ produit une erreur
d'API incompréhensible pour l'utilisateur, qui croit à une panne du logiciel.

Le second touche les modèles locaux, et il est plus vicieux. Un testeur a
utilisé `gemma3:1b` : THÉRÈSE lui a envoyé douze outils, Ollama a répondu
« does not support tools », et il a attendu trois minutes pour une réponse
dégradée. La famille gemma3 ne porte pas le badge « tools » d'Ollama. Un modèle
sans outils ne peut ni créer un contact, ni poser un rendez-vous, ni produire un
document : ce n'est pas un modèle au rabais, c'est un modèle qui ne fait pas le
travail. Il ne doit donc plus être proposé comme choix valide.

Les identifiants ci-dessous ont tous été relevés dans la documentation officielle
de leur fournisseur le 24/08/2026, et contre-vérifiés une seconde fois.
"""
import pytest


class TestLesModelesRetiresNeSontPlusProposes:
    """Un identifiant retiré fait échouer chaque requête, sans recours."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "fournisseur,retires",
        [
            # Retirés par Anthropic : la requête échoue avec un 404.
            ("anthropic", ["claude-3-opus-20240229", "claude-opus-4-1-20250805"]),
            # Disparus de l'API DeepSeek au profit de la génération v4.
            ("deepseek", ["deepseek-chat", "deepseek-reasoner"]),
        ],
    )
    async def test_aucun_modele_retire_dans_la_liste(self, fournisseur, retires):
        from app.routers.config import _available_models_for

        proposes = await _available_models_for(fournisseur)

        survivants = [m for m in retires if m in proposes]
        assert survivants == [], (
            f"{survivants} n'existent plus chez {fournisseur} : chaque requête "
            "échouera sans que l'utilisateur comprenne pourquoi"
        )


class TestLesGenerationsCourantesSontProposees:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "fournisseur,attendu",
        [
            ("anthropic", "claude-opus-5"),
            ("openai", "gpt-5.6-sol"),
            ("grok", "grok-4.6"),
            ("gemini", "gemini-3.7-flash"),
            ("mistral", "mistral-medium-latest"),
            ("deepseek", "deepseek-v4-pro"),
        ],
    )
    async def test_la_generation_courante_est_offerte(self, fournisseur, attendu):
        from app.routers.config import _available_models_for

        proposes = await _available_models_for(fournisseur)

        assert attendu in proposes, (
            f"{attendu} est la génération courante de {fournisseur} et n'est pas "
            f"proposée. L'utilisateur reste sur un modèle dépassé sans le savoir."
        )

    @pytest.mark.asyncio
    async def test_le_premier_propose_est_celui_a_recommander(self):
        """L'ordre fait la recommandation : le premier est pré-sélectionné."""
        from app.routers.config import _available_models_for

        for fournisseur, attendu in [
            ("anthropic", "claude-opus-5"),
            ("openai", "gpt-5.6-sol"),
            ("grok", "grok-4.6"),
        ]:
            proposes = await _available_models_for(fournisseur)
            assert proposes[0] == attendu, (
                f"{fournisseur} recommande {proposes[0]} au lieu de {attendu}"
            )


class TestUnModeleLocalSansOutilsNEstPasProposeCommeValide:
    """BUG-169 : douze outils envoyés à un modèle qui n'en gère aucun.

    Le testeur a attendu 3 min 26 s le premier mot, pour une réponse dégradée
    après une erreur HTTP 400. La cause n'est pas Ollama : c'est THÉRÈSE qui
    propose un modèle incapable de faire ce qu'elle promet.
    """

    @pytest.mark.parametrize(
        "modele",
        ["gemma3:1b", "gemma3:4b", "gemma3:12b", "gemma3:27b", "gemma3", "phi4:14b"],
    )
    def test_les_modeles_sans_outils_sont_reconnus(self, modele):
        from app.services.ollama_capabilites import gere_les_outils

        assert gere_les_outils(modele) is False, (
            f"{modele} ne porte pas le badge « tools » d'Ollama : le proposer "
            "revient à promettre des actions qu'il ne peut pas exécuter"
        )

    @pytest.mark.parametrize(
        "modele",
        ["qwen3.5:9b", "ministral-3:8b", "llama3.1:8b", "gpt-oss:20b", "gemma4:12b"],
    )
    def test_les_modeles_avec_outils_restent_proposes(self, modele):
        """Le verrou inverse : ne pas devenir si strict qu'on ne propose rien."""
        from app.services.ollama_capabilites import gere_les_outils

        assert gere_les_outils(modele) is True

    def test_un_modele_inconnu_est_presume_capable(self):
        """Moindre surprise : on n'écarte que ce qu'on sait incapable.

        Ollama accepte n'importe quel modèle, y compris local ou renommé. Un
        inconnu écarté d'office priverait l'utilisateur de son propre modèle.
        """
        from app.services.ollama_capabilites import gere_les_outils

        assert gere_les_outils("mon-modele-perso:latest") is True

    def test_la_variante_est_reconnue_comme_sa_famille(self):
        """`gemma3:1b-instruct-q4_0` reste un gemma3."""
        from app.services.ollama_capabilites import gere_les_outils

        assert gere_les_outils("gemma3:1b-instruct-q4_0") is False


class TestLeSelecteurEcarteReellementLesModelesSansOutils:
    """Le service de capacités ne sert à rien s'il n'est pas branché."""

    @pytest.mark.asyncio
    async def test_gemma3_installe_n_est_pas_propose(self, monkeypatch):
        """Le cas exact du testeur : gemma3:1b installé, donc proposé."""
        from app.routers import config as config_router

        class FausseReponse:
            status_code = 200

            @staticmethod
            def json():
                return {
                    "models": [
                        {"name": "gemma3:1b"},      # sans outils : à écarter
                        {"name": "qwen3.5:9b"},     # outillé : à garder
                    ]
                }

        class FauxClient:
            async def get(self, *args, **kwargs):
                return FausseReponse()

        async def faux_client():
            return FauxClient()

        monkeypatch.setattr(config_router, "get_http_client", faux_client)

        proposes = await config_router._available_models_for("ollama")

        assert "gemma3:1b" not in proposes, (
            "gemma3:1b reste proposé alors qu'il ne gère aucun outil : "
            "l'utilisateur le choisira et attendra des minutes pour rien"
        )
        assert "qwen3.5:9b" in proposes, "le modèle capable a disparu aussi"

    def test_le_motif_d_exclusion_est_dit_a_l_utilisateur(self):
        """Écarter en silence recrée le défaut qu'on corrige ailleurs."""
        from app.services.ollama_capabilites import motif_d_exclusion

        motif = motif_d_exclusion("gemma3:1b")

        assert motif is not None
        assert "gemma3" in motif
        # Un motif utile nomme une porte de sortie, pas seulement le problème.
        assert "qwen3.5" in motif or "ministral" in motif
        assert motif_d_exclusion("qwen3.5:9b") is None
