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
import contextlib
from unittest.mock import MagicMock

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
            # 0.46 : le premier événement peut annoncer le generation_id -
            # c'est du suivi, pas du contenu.
            if '"generation"' not in morceau
        ]

        assert len(morceaux) == 3
        assert not any("cancelled" in m for m in morceaux)

    @pytest.mark.asyncio
    async def test_une_deconnexion_du_client_ferme_proprement_le_producteur(
        self, monkeypatch
    ):
        """Finding BLOQUANT n°1 de la revue Soso, reproduit.

        L'utilisateur n'appelle pas toujours `/cancel` : il ferme la fenêtre,
        change de page, ou perd le réseau. Le consommateur du générateur
        disparaît alors et Starlette ferme `_stream_response`.

        Le `finally` appelait `producteur.aclose()` alors que la tâche
        `producteur.__anext__()` tournait encore, ce qui lève
        `RuntimeError: aclose(): asynchronous generator is already running`.
        Cette exception empêchait `_unregister_generation` de s'exécuter :
        l'entrée restait dans le registre pour toujours, et le producteur
        continuait de consommer des tokens dans le vide.
        """
        from app.routers import chat as chat_router

        producteur_interrompu = asyncio.Event()
        producteur_demarre = asyncio.Event()

        async def flux_bloque(*_args, **_kwargs):
            producteur_demarre.set()
            try:
                await asyncio.Event().wait()
                yield "jamais"
            except (asyncio.CancelledError, GeneratorExit):
                producteur_interrompu.set()
                raise

        monkeypatch.setattr(chat_router, "_do_stream_response", flux_bloque)

        conversation_id = "conv-deconnexion"
        chat_router._register_generation(conversation_id)

        flux = chat_router._stream_response(conversation_id, "question", None, None)
        # Amorcer le générateur sans attendre de morceau : il se met en attente
        # sur un fournisseur qui ne répond pas. 0.46 : le premier événement
        # peut être le suivi de génération - on le consomme et on ré-amorce.
        tache = asyncio.create_task(flux.__anext__())
        fini, _ = await asyncio.wait({tache}, timeout=2)
        if tache in fini and '"generation"' in tache.result():
            tache = asyncio.create_task(flux.__anext__())
        await asyncio.wait_for(producteur_demarre.wait(), timeout=2)

        # Le client s'en va : le consommateur est annulé, puis le générateur
        # est refermé — exactement ce que fait Starlette.
        tache.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await tache
        await asyncio.wait_for(flux.aclose(), timeout=3)

        assert producteur_interrompu.is_set(), (
            "le producteur tourne encore après le départ du client"
        )
        assert conversation_id not in chat_router._active_generations, (
            "l'entrée reste dans le registre : elle fuit et fausse les "
            "annulations suivantes portant le même identifiant"
        )

    @pytest.mark.asyncio
    async def test_aucun_outil_ne_s_execute_apres_la_demande_d_arret(self, monkeypatch):
        """Finding 3, troisième passe : la boucle d'OUTILS ignorait l'annulation.

        Les gardes posées jusque-là protégeaient l'enregistrement du message et
        l'auto-exécution finale du skill. Mais `_execute_tools_and_continue`
        émet d'abord un statut « Exécution des outils », puis exécute les outils
        SANS consulter l'annulation.

        Ces outils ne sont pas anodins : ils créent des contacts et des projets
        (commit SQLite et Qdrant), écrivent des documents sur le disque, ou
        appellent un outil MCP arbitraire.

        Conséquence : l'utilisateur clique sur Arrêter, reçoit bien l'événement
        `cancelled`, et retrouve quand même un fichier ou un contact créé après
        coup, sans rien à l'écran pour l'expliquer.
        """
        from app.routers import chat as chat_router
        from app.services.llm import ToolCall

        executes: list[str] = []

        async def faux_search_emails(nom, arguments, session, **kwargs):
            executes.append("search_emails")
            return "résultat"

        monkeypatch.setattr(chat_router, "execute_workspace_tool", faux_search_emails)

        conversation_id = "conv-outils"
        chat_router._register_generation(conversation_id)

        appels = [ToolCall(id="1", name="search_emails", arguments={"query": "test"})]

        def lancer():
            return chat_router._execute_tools_and_continue(
                llm_service=None,
                mcp_service=None,
                context=[],
                assistant_content="",
                tool_calls=appels,
                tools=[],
                conversation_id=conversation_id,
                remaining_iterations=3,
                session=MagicMock(),
                usage_totals={"input_tokens": 0, "output_tokens": 0, "estimated": True},
                tool_outcomes=[],
            )

        flux = lancer()
        # 1. On consomme le statut « Exécution des outils ».
        premier = await flux.__anext__()
        assert "status" in premier

        # 2. L'utilisateur clique sur Arrêter pendant ce temps.
        chat_router._cancel_generation(conversation_id)

        # 3. Le flux reprend. Les services LLM sont à None : la continuation
        # lèvera. Peu importe — ce qu'on mesure, c'est si les OUTILS ont tourné.
        with contextlib.suppress(StopAsyncIteration, Exception):
            async for _ in flux:
                pass

        assert executes == [], (
            f"outils exécutés APRÈS la demande d'arrêt : {executes}. "
            "L'utilisateur retrouve un fichier ou une entité créés alors qu'il "
            "avait annulé, sans rien à l'écran pour l'expliquer"
        )

        # Garde-fou du test lui-même : SANS annulation, l'outil DOIT tourner.
        # Sans cette vérification, un `executes` vide pour une autre raison
        # (mauvais nom monkeypatché, chemin non emprunté) rendrait le test creux
        # — piège rencontré en écrivant cette série.
        chat_router._active_generations.pop(conversation_id, None)
        chat_router._register_generation(conversation_id)
        flux_temoin = lancer()
        with contextlib.suppress(StopAsyncIteration, Exception):
            async for _ in flux_temoin:
                pass
        assert executes == ["search_emails"], (
            "le test ne prouve rien : l'outil ne s'exécute pas non plus dans le "
            f"cas nominal (executes={executes})"
        )

    @pytest.mark.asyncio
    async def test_les_metriques_sont_finalisees_meme_sur_annulation(self, monkeypatch):
        """Finding MAJEUR n°4 de la revue Soso.

        `start_stream()` est appelé avant la génération, `finish_stream()`
        seulement au bout du chemin nominal. Une annulation - ou une simple
        déconnexion - saute donc la finalisation : `CancelledError` n'hérite pas
        d'`Exception` et ne passe dans aucun `except`.

        Pour l'utilisateur : Réglages > Performances affiche des flux actifs
        qui ne finiront jamais, et les statistiques ignorent les flux arrêtés.
        Le compteur ne redescend qu'au redémarrage.
        """
        from app.routers import chat as chat_router
        from app.services.performance import get_performance_monitor

        moniteur = get_performance_monitor()
        conversation_id = "conv-metriques"
        moniteur.start_stream(conversation_id, provider="ollama", model="x")
        assert conversation_id in moniteur._active_streams

        async def flux_bloque(*_args, **_kwargs):
            await asyncio.Event().wait()
            yield "jamais"

        monkeypatch.setattr(chat_router, "_do_stream_response", flux_bloque)
        chat_router._register_generation(conversation_id)

        async def consommer():
            async for _ in chat_router._stream_response(conversation_id, "q", None, None):
                pass

        tache = asyncio.create_task(consommer())
        await asyncio.sleep(0.05)
        chat_router._cancel_generation(conversation_id)
        await asyncio.wait_for(tache, timeout=3)

        assert conversation_id not in moniteur._active_streams, (
            "le flux reste compté comme actif après son annulation : le compteur "
            "de Réglages > Performances ne redescend plus jusqu'au redémarrage"
        )

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
