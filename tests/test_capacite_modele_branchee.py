"""La capacité d'un modèle doit voyager jusqu'à l'écran.

Écrit après un constat gênant : `motif_d_exclusion` avait été rédigé avec soin,
commenté, testé — et appelé nulle part. Le code et son commentaire promettaient
une explication que l'utilisateur n'aurait jamais vue.

Le même défaut est apparu trois fois dans la même journée. Ces tests vérifient
le CHEMIN, pas la fonction : ce qui compte est qu'un modèle incapable d'agir
arrive marqué jusqu'à l'interface, avec son motif.
"""
import pytest


class TestLaCapaciteVoyageJusquALInterface:
    @pytest.mark.asyncio
    async def test_le_statut_ollama_porte_la_capacite_de_chaque_modele(
        self, monkeypatch
    ):
        """Sans ces champs dans la réponse, l'écran ne peut rien afficher."""
        from app.routers import config as config_router

        class FausseReponse:
            status_code = 200

            @staticmethod
            def json():
                return {
                    "models": [
                        {"name": "gemma3:1b", "size": 815319791},
                        {"name": "qwen3.5:9b", "size": 6600000000},
                    ]
                }

        class FauxClient:
            async def get(self, *args, **kwargs):
                return FausseReponse()

        async def faux_client():
            return FauxClient()

        monkeypatch.setattr(config_router, "get_http_client", faux_client)

        statut = await config_router.get_ollama_status()
        par_nom = {m.name: m for m in statut.models}

        assert par_nom["gemma3:1b"].gere_les_outils is False, (
            "le statut ne signale pas que ce modèle est incapable d'agir : "
            "l'interface ne peut donc ni le griser, ni dire pourquoi"
        )
        assert par_nom["qwen3.5:9b"].gere_les_outils is True

    @pytest.mark.asyncio
    async def test_le_motif_accompagne_le_marquage(self, monkeypatch):
        """Marquer sans expliquer serait la moitié du travail."""
        from app.routers import config as config_router

        class FausseReponse:
            status_code = 200

            @staticmethod
            def json():
                return {"models": [{"name": "gemma3:1b"}]}

        class FauxClient:
            async def get(self, *args, **kwargs):
                return FausseReponse()

        monkeypatch.setattr(
            config_router, "get_http_client", lambda: _resoudre(FauxClient())
        )

        statut = await config_router.get_ollama_status()
        motif = statut.models[0].motif_indisponible

        assert motif, "aucun motif : le modèle serait grisé sans raison visible"
        # Un motif utile nomme une porte de sortie, pas seulement le problème.
        assert "qwen3.5" in motif or "ministral" in motif


async def _resoudre(valeur):
    return valeur
