"""
J1b (31/07/2026) - L'annulation du chat doit couper le producteur.

Relevé par la revue du plan : `POST /api/chat/cancel` existe
(`chat.py:454`) mais n'est appelé par AUCUN code frontend, et surtout son
drapeau n'est consulté qu'APRÈS qu'un chunk a été produit (`chat.py:1156`).

Conséquence : si le fournisseur est lent ou bloqué - exactement le moment où
l'utilisateur veut arrêter - la boucle `async for` attend le prochain chunk et
l'annulation n'a aucun effet. Le producteur continue de consommer des tokens.

Le test exigé par la revue : fournisseur bloqué, annulation demandée, le
producteur DOIT recevoir l'interruption.
"""
import asyncio

import pytest


class TestAnnulationCoupeLeProducteur:
    @pytest.mark.asyncio
    async def test_un_fournisseur_bloque_est_bien_interrompu(self, monkeypatch):
        from app.routers import chat as chat_router

        producteur_interrompu = asyncio.Event()
        producteur_demarre = asyncio.Event()

        async def flux_bloque(*_args, **_kwargs):
            """Un fournisseur qui ne rend jamais la main."""
            producteur_demarre.set()
            try:
                await asyncio.Event().wait()  # ne se résout jamais
                yield "jamais"
            except (asyncio.CancelledError, GeneratorExit):
                producteur_interrompu.set()
                raise

        monkeypatch.setattr(chat_router, "_do_stream_response", flux_bloque)

        conversation_id = "conv-bloquee"
        chat_router._register_generation(conversation_id)

        async def consommer():
            morceaux = []
            async for morceau in chat_router._stream_response(
                conversation_id, "question", None, None
            ):
                morceaux.append(morceau)
            return morceaux

        tache = asyncio.create_task(consommer())
        await asyncio.wait_for(producteur_demarre.wait(), timeout=2)

        # L'utilisateur clique sur Arrêter.
        chat_router._cancel_generation(conversation_id)

        morceaux = await asyncio.wait_for(tache, timeout=3)

        assert producteur_interrompu.is_set(), (
            "le producteur tourne toujours après l'annulation : les tokens "
            "continuent d'être consommés alors que l'utilisateur a demandé l'arrêt"
        )
        assert any("cancelled" in m for m in morceaux), (
            "l'interface doit recevoir l'événement d'annulation"
        )

    @pytest.mark.asyncio
    async def test_un_flux_normal_n_est_pas_interrompu(self, monkeypatch):
        """Garde-fou : l'annulation ne doit pas casser le cas nominal."""
        from app.routers import chat as chat_router

        async def flux_normal(*_args, **_kwargs):
            for i in range(3):
                yield f"data: chunk-{i}\n\n"
                await asyncio.sleep(0)

        monkeypatch.setattr(chat_router, "_do_stream_response", flux_normal)

        conversation_id = "conv-normale"
        chat_router._register_generation(conversation_id)

        morceaux = [
            morceau
            async for morceau in chat_router._stream_response(
                conversation_id, "question", None, None
            )
        ]

        assert len(morceaux) == 3
        assert not any("cancelled" in m for m in morceaux)

    @pytest.mark.asyncio
    async def test_le_registre_est_nettoye_apres_annulation(self, monkeypatch):
        from app.routers import chat as chat_router

        async def flux_bloque(*_args, **_kwargs):
            await asyncio.Event().wait()
            yield "jamais"

        monkeypatch.setattr(chat_router, "_do_stream_response", flux_bloque)

        conversation_id = "conv-nettoyage"
        chat_router._register_generation(conversation_id)

        async def consommer():
            async for _ in chat_router._stream_response(conversation_id, "q", None, None):
                pass

        tache = asyncio.create_task(consommer())
        await asyncio.sleep(0.05)
        chat_router._cancel_generation(conversation_id)
        await asyncio.wait_for(tache, timeout=3)

        assert conversation_id not in chat_router._active_generations, (
            "une entrée laissée dans le registre fuit et fausse les annulations suivantes"
        )
