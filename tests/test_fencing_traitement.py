"""Phase 4 du chantier 0.47 - Fencing : un contexte d'exécution, pas un
drapeau partagé.

Promesse écrite du design V2.1 : « aucun nouvel effet MÉTIER local après
observation de l'annulation » - la consignation du traitement et le message
partiel sont explicitement exclus.

Contrats :
- `ContexteExecution` (generation_id + token) est l'AUTORITÉ : un unique
  token par génération alimente le flux, l'adaptateur canonique, le
  fallback d'indexation et les outils ; `_active_generations` n'est plus
  qu'une table conversation→contexte courant (compat lecture) ;
- registre déclaratif : chaque outil du dispatcher est classé
  read_only | local_mutation | external_mutation - un outil non classé
  est un test rouge ;
- les trois mutateurs locaux immédiats (create_contact, create_project,
  generate_document) consultent le fence JUSTE AVANT leur premier effet
  durable : annulation observée = « interrompu avant écriture », zéro
  effet SQLite, zéro effet Qdrant, zéro fichier ;
- le fallback d'indexation du chat est raccordé au même cœur
  (`index_payload`) et au même signal (le token de SA génération).
"""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from sqlmodel import select


@pytest.fixture
def fichier_texte(tmp_path: Path) -> Path:
    fichier = tmp_path / "note-client.txt"
    fichier.write_text("contenu " * 100, encoding="utf-8")
    return fichier


class TestLeRegistreDeclaratif:
    def test_chaque_outil_du_dispatcher_est_classe(self):
        from app.services.contexte_execution import CLASSIFICATION_DES_OUTILS
        from app.services.memory_tools import MEMORY_TOOLS
        from app.services.workspace_tools import WORKSPACE_TOOLS

        integres = {"web_search", "browser_navigate"}
        noms = (
            {t["function"]["name"] for t in MEMORY_TOOLS}
            | {t["function"]["name"] for t in WORKSPACE_TOOLS}
            | integres
        )

        non_classes = sorted(noms - set(CLASSIFICATION_DES_OUTILS))
        assert non_classes == [], (
            f"outils sans classe d'effet : {non_classes} - un outil non "
            "classé échappe au raisonnement d'annulation"
        )

    def test_les_classes_encodent_les_decisions_du_design(self):
        from app.services.contexte_execution import (
            CLASSIFICATION_DES_OUTILS,
            LECTURE_SEULE,
            MUTATION_EXTERNE,
            MUTATION_LOCALE,
            classe_de,
        )

        assert CLASSIFICATION_DES_OUTILS["create_contact"] == MUTATION_LOCALE
        assert CLASSIFICATION_DES_OUTILS["create_project"] == MUTATION_LOCALE
        assert CLASSIFICATION_DES_OUTILS["generate_document"] == MUTATION_LOCALE
        assert CLASSIFICATION_DES_OUTILS["read_contact"] == LECTURE_SEULE
        assert CLASSIFICATION_DES_OUTILS["send_email"] == MUTATION_EXTERNE
        # Un outil MCP inconnu est externe par nature : dans le doute, la
        # classe la plus prudente.
        assert classe_de("mcp__inconnu__outil") == MUTATION_EXTERNE


class TestLeTokenEstLAutorite:
    def test_deux_generations_chevauchees_ne_se_fencent_pas(self):
        """Le drapeau historique était indexé par conversation : annuler
        pouvait fencer la MAUVAISE génération. Le token est par génération."""
        from app.routers import chat as chat_router

        conversation = "conv-chevauchement"
        try:
            ctx1 = chat_router._register_generation(conversation, "gen-1")
            ctx2 = chat_router._register_generation(conversation, "gen-2")

            assert chat_router._cancel_generation(conversation) is True

            assert ctx2.annulation_observee() is True
            assert ctx1.annulation_observee() is False, (
                "la génération remplacée garde SON token : l'annulation vise "
                "la génération courante, jamais l'ancienne"
            )
            # Compat lecture : le drapeau par conversation lit le token courant.
            assert chat_router._is_cancelled(conversation) is True
        finally:
            chat_router._active_generations.pop(conversation, None)


class TestLaFenceDesMutateursLocaux:
    @pytest.mark.asyncio
    async def test_create_contact_interrompu_avant_toute_ecriture(
        self, client, monkeypatch
    ):
        """Barrière : l'annulation arrive PENDANT l'outil (dedup en cours),
        avant le premier effet durable - zéro ligne, zéro vecteur."""
        from app.models.database import get_session_context
        from app.models.entities import Contact
        from app.services import memory_tools
        from app.services.contexte_execution import ContexteExecution

        contexte = ContexteExecution(generation_id="gen-fence")
        qdrant = AsyncMock()
        monkeypatch.setattr(memory_tools, "get_qdrant_service", lambda: qdrant)

        async def dedup_pendant_laquelle_on_annule(*_a, **_k):
            contexte.demander_arret()
            return None

        monkeypatch.setattr(
            memory_tools, "_find_existing_contact",
            dedup_pendant_laquelle_on_annule,
        )

        async with get_session_context() as session:
            resultat = json.loads(await memory_tools.execute_create_contact(
                {"first_name": "Ada", "last_name": "Fence"},
                session,
                contexte=contexte,
            ))

        assert resultat.get("interrupted") is True
        assert not resultat.get("contact_id")

        async with get_session_context() as session:
            lignes = (await session.execute(select(Contact))).scalars().all()
        assert lignes == [], "aucun contact ne doit naître après l'annulation"
        qdrant.async_add_memory.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_contact_sans_annulation_ecrit_vraiment(
        self, client, monkeypatch
    ):
        """Garde-fou du harnais : sans annulation, le MÊME chemin écrit."""
        from app.models.database import get_session_context
        from app.models.entities import Contact
        from app.services import memory_tools
        from app.services.contexte_execution import ContexteExecution

        monkeypatch.setattr(
            memory_tools, "get_qdrant_service", lambda: AsyncMock()
        )

        async with get_session_context() as session:
            resultat = json.loads(await memory_tools.execute_create_contact(
                {"first_name": "Ada", "last_name": "Temoin"},
                session,
                contexte=ContexteExecution(generation_id="gen-temoin"),
            ))

        assert resultat.get("success") is True
        async with get_session_context() as session:
            lignes = (await session.execute(select(Contact))).scalars().all()
        assert len(lignes) == 1

    @pytest.mark.asyncio
    async def test_create_project_interrompu_avant_toute_ecriture(
        self, client, monkeypatch
    ):
        from app.models.database import get_session_context
        from app.models.entities import Project
        from app.services import memory_tools
        from app.services.contexte_execution import ContexteExecution

        contexte = ContexteExecution(generation_id="gen-fence")
        qdrant = AsyncMock()
        monkeypatch.setattr(memory_tools, "get_qdrant_service", lambda: qdrant)

        async def dedup_pendant_laquelle_on_annule(*_a, **_k):
            contexte.demander_arret()
            return None

        monkeypatch.setattr(
            memory_tools, "_find_existing_project",
            dedup_pendant_laquelle_on_annule,
        )

        async with get_session_context() as session:
            resultat = json.loads(await memory_tools.execute_create_project(
                {"name": "Chantier Fence"},
                session,
                contexte=contexte,
            ))

        assert resultat.get("interrupted") is True
        async with get_session_context() as session:
            lignes = (await session.execute(select(Project))).scalars().all()
        assert lignes == []
        qdrant.async_add_memory.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_document_interrompu_avant_le_disque(
        self, client, monkeypatch
    ):
        """`generate_document` écrit via le registre de skills : annulation
        observée = le registre n'est JAMAIS invoqué, aucun fichier."""
        from app.models.database import get_session_context
        from app.services.contexte_execution import ContexteExecution
        from app.services.workspace_tools import execute_workspace_tool

        registre = AsyncMock()
        monkeypatch.setattr(
            "app.services.skills.get_skills_registry", lambda: registre
        )

        contexte = ContexteExecution(generation_id="gen-fence")
        contexte.demander_arret()

        async with get_session_context() as session:
            resultat = await execute_workspace_tool(
                "generate_document",
                {"format": "docx", "content": "Rapport", "title": "Essai"},
                session,
                contexte=contexte,
            )

        assert "interromp" in resultat.lower()
        registre.execute.assert_not_called()


class TestLeFallbackChatEstRaccorde:
    @pytest.mark.asyncio
    async def test_le_fallback_passe_par_le_coeur(
        self, client, fichier_texte, monkeypatch
    ):
        """Le corps historique 500/50 dupliquait le cœur : un fichier neuf
        joint au chat doit passer par `index_payload` (verrou, invariant N1,
        périmètre) avec un signal d'abandon branché."""
        from app.models.database import get_session_context
        from app.routers import chat as module
        from app.services import indexation

        appels: list[dict] = []

        async def coeur_espionne(path, est_abandonnee=None, **kwargs):
            appels.append({"path": path, "signal": est_abandonnee})
            from datetime import UTC, datetime

            from app.models.schemas import FileResponse

            return FileResponse(
                id="f-1", path=path, name=Path(path).name, extension=".txt",
                size=1, mime_type="text/plain", chunk_count=1,
                indexed_at=datetime.now(UTC), created_at=datetime.now(UTC),
                scope="global", scope_id=None,
            )

        monkeypatch.setattr(indexation, "index_payload", coeur_espionne)
        monkeypatch.setattr(
            module, "extract_text", lambda _p: "du texte", raising=False
        )

        async with get_session_context() as session:
            contexte_txt, erreur = await module._get_file_context(
                str(fichier_texte), session
            )

        assert erreur is None
        assert len(appels) == 1, "le fallback doit déléguer au cœur"
        assert appels[0]["signal"] is not None, (
            "le cœur doit recevoir le signal d'abandon de la génération"
        )

    @pytest.mark.asyncio
    async def test_le_signal_de_generation_interrompt_le_fallback(
        self, client, fichier_texte, monkeypatch
    ):
        """Token posé pendant l'extraction : IndexationAbandonnee se propage
        (phase 2) et RIEN n'est écrit - ni métadonnée, ni vecteur."""
        from app.models.database import get_session_context
        from app.routers import chat as module
        from app.services import indexation
        from app.services.contexte_execution import ContexteExecution

        contexte = ContexteExecution(generation_id="gen-fallback")
        qdrant = AsyncMock()
        monkeypatch.setattr(indexation, "get_qdrant_service", lambda: qdrant)

        def extraction_pendant_laquelle_on_annule(_p):
            contexte.demander_arret()
            return "texte extrait"

        monkeypatch.setattr(
            indexation, "extract_text", extraction_pendant_laquelle_on_annule
        )
        monkeypatch.setattr(
            module, "extract_text",
            extraction_pendant_laquelle_on_annule, raising=False,
        )

        async with get_session_context() as session:
            with pytest.raises(indexation.IndexationAbandonnee):
                await module._get_file_context(
                    str(fichier_texte), session, contexte=contexte
                )

        qdrant.async_add_memories.assert_not_called()


class TestLesFenetresDeLaRevue:
    """Passe 1 de la revue de jalon : les fenêtres que la matrice ne
    couvrait pas. Chaque test reproduit le scénario du finding."""

    @pytest.mark.asyncio
    async def test_f1_le_wrapper_lit_le_token_de_sa_generation(
        self, client, monkeypatch
    ):
        """F1 : annuler G2 ne doit JAMAIS déclarer G1 annulée - le wrapper
        de G1 doit relire SON token, pas le drapeau partagé par
        conversation."""
        import json as json_module

        from app.models.processing import EtatTache
        from app.routers import chat as chat_router

        capture: dict = {}
        intruse: dict = {}

        class FauxService:
            class config:
                model = "test"

                class provider:
                    value = "ollama"

            def prepare_context(self, messages, system_prompt=None, memory_context=None):
                return type("Ctx", (), {"messages": messages, "system_prompt": ""})()

            async def stream_response_with_tools(self, _context, _tools=None):
                from app.services.providers import StreamEvent

                yield StreamEvent(type="text", content="Début ")
                # Une seconde génération démarre et est annulée PENDANT G1.
                intruse["ctx"] = chat_router._register_generation(
                    capture["conversation"], "gen-intruse"
                )
                chat_router._cancel_generation(capture["conversation"])
                yield StreamEvent(type="text", content="suite et fin.")
                yield StreamEvent(type="done", stop_reason="stop")

        monkeypatch.setattr(chat_router, "get_llm_service", lambda: FauxService())

        creation = await client.post(
            "/api/chat/conversations", json={"title": "Chevauchement"}
        )
        capture["conversation"] = creation.json()["id"]

        try:
            reponse = await client.post(
                "/api/chat/send",
                json={"message": "Salut", "stream": True,
                      "conversation_id": capture["conversation"]},
            )
            assert reponse.status_code == 200
            assert '"cancelled"' not in reponse.text, (
                "G1 a été déclarée annulée alors que c'est G2 (l'intruse) "
                "qui l'était - le wrapper lit encore le drapeau partagé"
            )
            evenement = next(
                (json_module.loads(ligne.removeprefix("data: "))
                 for ligne in reponse.text.splitlines()
                 if ligne.startswith("data: ") and '"generation"' in ligne),
                None,
            )
            assert evenement is not None

            from app.services import traitements

            ligne = await traitements.lire(evenement["generation_id"])
            assert ligne.state == EtatTache.DONE
        finally:
            chat_router._active_generations.pop(capture["conversation"], None)

    def test_f2_le_nettoyage_d_une_vieille_generation_epargne_la_neuve(self):
        """F2 : G2 s'enregistre AVANT que son generation_id soit connu
        (fenêtre creer_traitement). La fin de G1 ne doit pas retirer
        l'entrée de G2 - sinon la façade /cancel ne trouve plus rien."""
        from app.routers import chat as chat_router

        conversation = "conv-fenetre-none"
        try:
            ctx2 = chat_router._register_generation(conversation)
            assert ctx2.generation_id is None  # la fenêtre du finding

            chat_router._unregister_generation(conversation, "gen-1-finie")

            assert chat_router._active_generations.get(conversation) is ctx2, (
                "la fin de G1 a supprimé le contexte de G2 : dans cette "
                "fenêtre, la façade /cancel ne peut plus rien arrêter"
            )
        finally:
            chat_router._active_generations.pop(conversation, None)

    @pytest.mark.asyncio
    async def test_f6_annulation_entre_flush_et_qdrant_zero_effet(
        self, client, monkeypatch
    ):
        """F6 : le fence unique laissait un contact ENTIER se créer (SQLite
        + Qdrant) quand l'annulation tombait après le flush. Re-check avant
        l'écriture vectorielle : rollback, zéro ligne, zéro vecteur."""
        from app.models.database import get_session_context
        from app.models.entities import Contact
        from app.services import memory_tools
        from app.services.contexte_execution import ContexteExecution

        contexte = ContexteExecution(generation_id="gen-flush")
        qdrant = AsyncMock()
        monkeypatch.setattr(memory_tools, "get_qdrant_service", lambda: qdrant)

        async with get_session_context() as session:
            flush_originale = session.flush

            async def flush_puis_annulation():
                await flush_originale()
                contexte.demander_arret()

            session.flush = flush_puis_annulation
            resultat = json.loads(await memory_tools.execute_create_contact(
                {"first_name": "Zoe", "last_name": "Flush"},
                session,
                contexte=contexte,
            ))

        assert resultat.get("interrupted") is True
        qdrant.async_add_memory.assert_not_called()
        async with get_session_context() as session:
            lignes = (await session.execute(select(Contact))).scalars().all()
        assert lignes == []

    @pytest.mark.asyncio
    async def test_f6_projet_annule_entre_flush_et_qdrant_zero_effet(
        self, client, monkeypatch
    ):
        from app.models.database import get_session_context
        from app.models.entities import Project
        from app.services import memory_tools
        from app.services.contexte_execution import ContexteExecution

        contexte = ContexteExecution(generation_id="gen-flush")
        qdrant = AsyncMock()
        monkeypatch.setattr(memory_tools, "get_qdrant_service", lambda: qdrant)

        async with get_session_context() as session:
            flush_originale = session.flush

            async def flush_puis_annulation():
                await flush_originale()
                contexte.demander_arret()

            session.flush = flush_puis_annulation
            resultat = json.loads(await memory_tools.execute_create_project(
                {"name": "Chantier Flush"},
                session,
                contexte=contexte,
            ))

        assert resultat.get("interrupted") is True
        qdrant.async_add_memory.assert_not_called()
        async with get_session_context() as session:
            lignes = (await session.execute(select(Project))).scalars().all()
        assert lignes == []

    @pytest.mark.asyncio
    async def test_f7_les_pieces_jointes_recoivent_le_token(
        self, client, fichier_texte, monkeypatch
    ):
        """F7 : le token n'était transmis qu'aux commandes /fichier - les
        pièces jointes (file_paths) et leur rejeu doivent le recevoir
        aussi."""
        from app.routers import chat as chat_router

        contextes_recus: list = []

        async def espionne(
            file_path, session, command="fichier",
            scope="global", scope_id=None, contexte=None,
        ):
            contextes_recus.append(contexte)
            return None, None

        monkeypatch.setattr(chat_router, "_get_file_context", espionne)

        class FauxService:
            class config:
                model = "test"

                class provider:
                    value = "ollama"

            def prepare_context(self, messages, system_prompt=None, memory_context=None):
                return type("Ctx", (), {"messages": messages, "system_prompt": ""})()

            async def stream_response_with_tools(self, _context, _tools=None):
                from app.services.providers import StreamEvent

                yield StreamEvent(type="text", content="ok")
                yield StreamEvent(type="done", stop_reason="stop")

        monkeypatch.setattr(chat_router, "get_llm_service", lambda: FauxService())

        reponse = await client.post(
            "/api/chat/send",
            json={"message": "regarde ce document", "stream": True,
                  "file_paths": [str(fichier_texte)]},
        )
        assert reponse.status_code == 200
        assert contextes_recus, "la pièce jointe n'a pas été traitée"
        assert all(c is not None for c in contextes_recus), (
            "une pièce jointe traitée sans token : son indexation et son "
            "rattrapage de périmètre échappent à l'annulation"
        )

    @pytest.mark.asyncio
    async def test_f7_le_rattrapage_de_perimetre_est_fence(
        self, client, fichier_texte, monkeypatch
    ):
        """F7 (suite) : le rattrapage BUG-165 mute Qdrant + SQLite pour un
        fichier DÉJÀ indexé - annulation observée = aucun rattrapage."""
        from app.models.database import get_session_context
        from app.models.entities import FileMetadata
        from app.routers import chat as module
        from app.services.contexte_execution import ContexteExecution

        qdrant = AsyncMock()
        monkeypatch.setattr(module, "get_qdrant_service", lambda: qdrant)
        monkeypatch.setattr(
            module, "extract_text", lambda _p: "du texte", raising=False
        )

        async with get_session_context() as session:
            session.add(FileMetadata(
                path=str(fichier_texte.resolve()),
                name=fichier_texte.name,
                extension=".txt", size=10, mime_type="text/plain",
                scope="global", scope_id=None, scope_provisoire=True,
            ))
            await session.commit()

        contexte = ContexteExecution(generation_id="gen-rattrapage")
        contexte.demander_arret()

        async with get_session_context() as session:
            await module._get_file_context(
                str(fichier_texte), session,
                scope="project", scope_id="projet-x",
                contexte=contexte,
            )

        qdrant.definir_perimetre_entite.assert_not_called()
        async with get_session_context() as session:
            ligne = (await session.execute(
                select(FileMetadata).where(
                    FileMetadata.path == str(fichier_texte.resolve())
                )
            )).scalar_one()
        assert ligne.scope == "global", (
            "le périmètre a été rattrapé après l'annulation observée"
        )


class TestLeSecondPanel:
    """Second panel de revue (vérification interne multi-agents) : les
    chemins que ni la matrice ni la première passe ne couvraient."""

    @pytest.mark.asyncio
    async def test_annulation_en_vol_pendant_qdrant_rollback_avant_le_teardown(
        self, client, monkeypatch
    ):
        """Le wrapper J1b annule la coroutine de l'outil par CancelledError.
        Tombée entre flush et commit (attente Qdrant), elle sautait le
        rollback (except Exception) - et le teardown de `get_session`
        committait l'écriture « annulée » à la fin de la requête."""
        import asyncio
        import contextlib

        from app.models.database import get_session_context
        from app.models.entities import Contact
        from app.services import memory_tools
        from app.services.contexte_execution import ContexteExecution

        qdrant_commence = asyncio.Event()

        class QdrantBloquant:
            async def async_add_memory(self, **_k):
                qdrant_commence.set()
                await asyncio.sleep(3600)

        monkeypatch.setattr(
            memory_tools, "get_qdrant_service", lambda: QdrantBloquant()
        )

        async with get_session_context() as session:
            tache = asyncio.create_task(memory_tools.execute_create_contact(
                {"first_name": "Jean", "last_name": "EnVol"},
                session,
                contexte=ContexteExecution(generation_id="gen-vol"),
            ))
            await asyncio.wait_for(qdrant_commence.wait(), timeout=5)
            tache.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await tache
            # le teardown de la dépendance get_session commit sur sortie
            # propre : rejouer exactement ce geste
            await session.commit()

        async with get_session_context() as session:
            lignes = (await session.execute(select(Contact))).scalars().all()
        assert lignes == [], (
            "l'écriture flushée a été commitée par le teardown alors que "
            "l'outil venait d'être annulé en vol"
        )

    @pytest.mark.asyncio
    async def test_p23_le_vecteur_orphelin_est_compense_apres_annulation_en_vol(
        self, client, monkeypatch
    ):
        """Passe 2 (P2-3) : l'upsert Qdrant tourne dans un thread - annuler
        l'await ne l'arrête pas. Après le rollback SQLite, le vecteur du
        contact fantôme peut exister : une compensation détachée doit le
        purger."""
        import asyncio
        import contextlib

        from app.models.database import get_session_context
        from app.services import memory_tools
        from app.services.contexte_execution import ContexteExecution

        qdrant = AsyncMock()
        qdrant.async_add_memory.side_effect = asyncio.CancelledError()
        monkeypatch.setattr(memory_tools, "get_qdrant_service", lambda: qdrant)
        # pas d'attente réelle dans la compensation de test
        monkeypatch.setattr(memory_tools, "_DELAI_COMPENSATION_S", 0.0, raising=False)

        async with get_session_context() as session:
            with pytest.raises(asyncio.CancelledError):
                await memory_tools.execute_create_contact(
                    {"first_name": "Ada", "last_name": "Orpheline"},
                    session,
                    contexte=ContexteExecution(generation_id="gen-orphelin"),
                )

        for _ in range(100):
            if qdrant.async_delete_by_entity.called:
                break
            await asyncio.sleep(0.05)
        qdrant.async_delete_by_entity.assert_called(), (
            "aucune compensation : le vecteur du contact annulé reste dans "
            "l'index et le RAG peut servir un fantôme"
        )
        with contextlib.suppress(Exception):
            pass

    @pytest.mark.asyncio
    async def test_p29_l_abandon_du_fallback_finit_en_chunk_cancelled(
        self, client, fichier_texte, monkeypatch
    ):
        """Passe 2 (P2-9) : IndexationAbandonnee levée par le fallback
        traversait le wrapper comme une panne de stream - le client doit
        recevoir un chunk `cancelled` propre."""
        import json as json_module

        from app.models.processing import EtatTache
        from app.routers import chat as chat_router
        from app.services import indexation
        from app.services.indexation import IndexationAbandonnee

        async def coeur_abandonne(*_a, **_k):
            raise IndexationAbandonnee("arrêt demandé")

        monkeypatch.setattr(indexation, "index_payload", coeur_abandonne)
        monkeypatch.setattr(
            chat_router, "extract_text", lambda _p: "du texte", raising=False
        )

        class FauxService:
            class config:
                model = "test"

                class provider:
                    value = "ollama"

            def prepare_context(self, messages, system_prompt=None, memory_context=None):
                return type("Ctx", (), {"messages": messages, "system_prompt": ""})()

            async def stream_response_with_tools(self, _context, _tools=None):
                from app.services.providers import StreamEvent

                yield StreamEvent(type="text", content="jamais atteint")
                yield StreamEvent(type="done", stop_reason="stop")

        monkeypatch.setattr(chat_router, "get_llm_service", lambda: FauxService())

        reponse = await client.post(
            "/api/chat/send",
            json={"message": "regarde", "stream": True,
                  "file_paths": [str(fichier_texte)]},
        )
        assert reponse.status_code == 200
        assert '"cancelled"' in reponse.text, (
            "l'abandon d'indexation doit se présenter comme une annulation "
            "propre, pas comme un stream qui meurt"
        )
        evenement = next(
            (json_module.loads(ligne.removeprefix("data: "))
             for ligne in reponse.text.splitlines()
             if ligne.startswith("data: ") and '"generation"' in ligne),
            None,
        )
        if evenement is not None:
            from app.services import traitements

            ligne = await traitements.lire(evenement["generation_id"])
            assert ligne.state == EtatTache.CANCELLED

    @pytest.mark.asyncio
    async def test_p26_le_rattrapage_survit_a_l_annulation_en_vol(
        self, client, fichier_texte, monkeypatch
    ):
        """Passe 2 (P2-6) : annulé pendant l'appel Qdrant (thread), le
        rattrapage laissait les vecteurs re-périmétrés et SQLite global -
        divergence durable. Le geste détaché doit finir les DEUX côtés."""
        import threading

        from app.models.database import get_session_context
        from app.models.entities import FileMetadata
        from app.routers import chat as module

        porte_thread = threading.Event()
        appels: list = []

        class QdrantLent:
            def definir_perimetre_entite(self, entity_id, scope, scope_id):
                appels.append((entity_id, scope, scope_id))
                porte_thread.wait(10)

        monkeypatch.setattr(module, "get_qdrant_service", lambda: QdrantLent())
        monkeypatch.setattr(
            module, "extract_text", lambda _p: "du texte", raising=False
        )

        async with get_session_context() as session:
            session.add(FileMetadata(
                path=str(fichier_texte.resolve()),
                name=fichier_texte.name,
                extension=".txt", size=10, mime_type="text/plain",
                scope="global", scope_id=None, scope_provisoire=True,
            ))
            await session.commit()

        async def rattraper():
            async with get_session_context() as session:
                await module._get_file_context(
                    str(fichier_texte), session,
                    scope="project", scope_id="projet-y",
                )

        tache = asyncio.create_task(rattraper())
        for _ in range(100):
            if appels:
                break
            await asyncio.sleep(0.05)
        assert appels, "le rattrapage n'a pas démarré"

        tache.cancel()  # l'annulation frappe pendant le thread Qdrant
        import contextlib as _ctx

        with _ctx.suppress(asyncio.CancelledError):
            await tache
        porte_thread.set()  # le thread Qdrant finit son travail

        for _ in range(100):
            async with get_session_context() as session:
                ligne = (await session.execute(
                    select(FileMetadata).where(
                        FileMetadata.path == str(fichier_texte.resolve())
                    )
                )).scalar_one()
            if ligne.scope == "project":
                break
            await asyncio.sleep(0.05)
        assert ligne.scope == "project", (
            "les vecteurs sont re-périmétrés mais SQLite est resté global : "
            "divergence durable après l'annulation en vol"
        )

    @pytest.mark.asyncio
    async def test_p211_la_surveillance_rafraichit_le_timestamp(self, client):
        """Passe 2 (P2-11) : une génération vivante mais silencieuse (outil
        long) restait purgeable après 5 min - la surveillance (50 ms) doit
        rafraîchir son timestamp, pas seulement les chunks."""
        import contextlib as _ctx
        import time

        from app.routers import chat as chat_router

        conversation = "conv-silencieuse"
        try:
            contexte = chat_router._register_generation(conversation, "gen-s")
            chat_router._generation_timestamps[conversation] = (
                time.monotonic() - 400
            )

            tache = asyncio.create_task(
                chat_router._attendre_annulation(contexte, conversation)
            )
            await asyncio.sleep(0.2)
            tache.cancel()
            with _ctx.suppress(asyncio.CancelledError):
                await tache

            age = time.monotonic() - chat_router._generation_timestamps[conversation]
            assert age < 5, (
                f"timestamp vieux de {age:.0f}s : une génération vivante "
                "mais silencieuse reste purgeable par le cleanup"
            )
        finally:
            chat_router._active_generations.pop(conversation, None)
            chat_router._generation_timestamps.pop(conversation, None)

    @pytest.mark.asyncio
    async def test_p25_le_document_produit_pendant_l_annulation_est_retire(
        self, client, tmp_path, monkeypatch
    ):
        """Passe 2 (P2-5) : le skill écrit via thread/sous-processus -
        l'annulation en vol laissait un fichier orphelin sans carte. Le
        geste détaché compense : fichier retiré, jamais enregistré."""
        import contextlib as _ctx

        from app.services import workspace_tools
        from app.services.contexte_execution import ContexteExecution

        contexte = ContexteExecution(generation_id="gen-doc")
        porte = asyncio.Event()
        execution_commencee = asyncio.Event()
        fichier_produit = tmp_path / "rapport.docx"

        class FauxRegistry:
            output_dir = tmp_path
            travail = None

            async def execute(self, _skill_id, _req, _content):
                # Comme le vrai code (thread + sous-processus) : le travail
                # SURVIT à l'annulation de la coroutine qui l'attend.
                execution_commencee.set()

                async def _travail():
                    await porte.wait()
                    fichier_produit.write_bytes(b"contenu")
                    from app.services.skills.base import SkillExecuteResponse

                    return SkillExecuteResponse(
                        success=True, file_id="f-1", file_name="rapport.docx",
                        file_size=7, download_url="/api/files/generated/f-1",
                    )

                FauxRegistry.travail = asyncio.create_task(_travail())
                return await asyncio.shield(FauxRegistry.travail)

        monkeypatch.setattr(
            "app.services.skills.get_skills_registry", lambda: FauxRegistry()
        )
        cartes: list = []
        monkeypatch.setattr(
            workspace_tools, "record_generated_file",
            lambda d: cartes.append(d),
        )

        from app.models.database import get_session_context

        async with get_session_context() as session:
            tache = asyncio.create_task(workspace_tools.execute_workspace_tool(
                "generate_document",
                {"format": "docx", "content": "Rapport", "title": "Essai"},
                session,
                contexte=contexte,
            ))
            await asyncio.wait_for(execution_commencee.wait(), timeout=5)
            contexte.demander_arret()
            tache.cancel()
            with _ctx.suppress(asyncio.CancelledError):
                await tache
            porte.set()

            for _ in range(100):
                if not fichier_produit.exists() and not cartes:
                    break
                if not fichier_produit.exists():
                    break
                await asyncio.sleep(0.05)

        assert not fichier_produit.exists(), (
            "un fichier orphelin est apparu après l'annulation, sans carte "
            "pour l'expliquer ni le retrouver"
        )
        assert cartes == [], "aucune carte ne doit être enregistrée"

    @pytest.mark.asyncio
    async def test_p27_l_ecriture_du_coeur_annulee_en_vol_reste_coherente(
        self, client, tmp_path, monkeypatch
    ):
        """Passe 2 (P2-7) : annulé pendant l'écriture Qdrant, le cœur
        laissait la fiche et l'index diverger (delete fait, add ou
        consignation sautés). Le geste détaché finit tout ou consigne
        l'échec."""
        import contextlib as _ctx

        from app.models.database import get_session_context
        from app.models.entities import FileMetadata
        from app.services import indexation

        fichier = tmp_path / "gros-document.txt"
        fichier.write_text("contenu " * 100, encoding="utf-8")

        porte = asyncio.Event()
        ecriture_commencee = asyncio.Event()

        class QdrantGate:
            async def async_delete_by_entity(self, _eid):
                return None

            async def async_add_memories(self, items):
                ecriture_commencee.set()
                await porte.wait()
                return None

        monkeypatch.setattr(
            indexation, "get_qdrant_service", lambda: QdrantGate()
        )
        monkeypatch.setattr(indexation, "extract_text", lambda _p: "texte")

        tache = asyncio.create_task(indexation.index_payload(str(fichier)))
        await asyncio.wait_for(ecriture_commencee.wait(), timeout=5)
        tache.cancel()
        with _ctx.suppress(asyncio.CancelledError):
            await tache
        porte.set()  # le thread d'écriture finit son travail

        ligne = None
        for _ in range(100):
            async with get_session_context() as session:
                ligne = (await session.execute(
                    select(FileMetadata).where(
                        FileMetadata.path == str(fichier.resolve())
                    )
                )).scalar_one_or_none()
            if ligne is not None and ligne.chunk_count:
                break
            await asyncio.sleep(0.05)
        assert ligne is not None
        assert ligne.chunk_count and ligne.chunk_count > 0, (
            "l'écriture vectorielle a eu lieu mais la consignation a été "
            "coupée par l'annulation : la fiche ment sur l'index"
        )
