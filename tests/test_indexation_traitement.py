"""Phase 2 du chantier 0.47 - Indexation : enrôler les surfaces, jamais le cœur.

Contrats (design V2.1) :
- le cœur (`services/indexation.py`) n'enrôle JAMAIS de ProcessingTask :
  seules les enveloppes de surface `/index` et `/upload` enrôlent ;
- l'abandon n'est plus silencieux : `IndexationAbandonnee` est levée au
  point d'abandon - la route la convertit en `cancelled`, project.sync
  interrompt l'apply SANS marquer l'opération en échec, le fallback du
  chat cesse de la déguiser en erreur de lecture ;
- adaptateur `TravailNonInterruptible` : le panneau peut demander l'arrêt
  d'une indexation en cours (l'extraction déjà lancée va à son terme) ;
- un apply multi-indexations = UN seul ProcessingTask (type project_sync) ;
- les indexations éclair (< 2 s) sont masquées du panneau, jamais les échecs.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from app.models.processing import EtatTache, ProcessingTask
from sqlmodel import select


@pytest.fixture
def fichier_texte(tmp_path: Path) -> Path:
    fichier = tmp_path / "dossier-client.txt"
    fichier.write_text("contenu " * 200, encoding="utf-8")
    return fichier


@pytest.fixture
def qdrant_factice(monkeypatch):
    from app.services import indexation

    faux = AsyncMock()
    monkeypatch.setattr(indexation, "get_qdrant_service", lambda: faux)
    monkeypatch.setattr(indexation, "extract_text", lambda _p: "texte extrait")
    return faux


async def _traitements_indexation() -> list[ProcessingTask]:
    from app.models.database import get_session_context

    async with get_session_context() as session:
        resultat = await session.execute(
            select(ProcessingTask).where(ProcessingTask.type == "indexation")
        )
        return list(resultat.scalars().all())


class TestLeCoeurNEnroleJamais:
    @pytest.mark.asyncio
    async def test_index_payload_direct_ne_cree_aucun_traitement(
        self, client, fichier_texte, qdrant_factice
    ):
        from app.services import indexation

        await indexation.index_payload(str(fichier_texte))

        assert await _traitements_indexation() == [], (
            "le cœur est appelé par project.sync et par le chat : s'il "
            "enrôlait, chaque apply créerait un traitement par fichier"
        )


class TestLesSurfacesEnrolent:
    @pytest.mark.asyncio
    async def test_la_route_index_est_un_traitement(
        self, client, fichier_texte, qdrant_factice
    ):
        reponse = await client.post(
            "/api/files/index", json={"path": str(fichier_texte)}
        )
        assert reponse.status_code == 200

        lignes = await _traitements_indexation()
        assert len(lignes) == 1
        assert lignes[0].state == EtatTache.DONE
        assert lignes[0].label == fichier_texte.name
        assert lignes[0].entity_id == str(fichier_texte)

    @pytest.mark.asyncio
    async def test_l_upload_est_un_traitement(self, client, qdrant_factice):
        import io

        resp = await client.post(
            "/api/memory/projects", json={"name": "Chantier 47"}
        )
        assert resp.status_code in (200, 201), resp.text
        projet_id = resp.json()["id"]

        resp = await client.post(
            "/api/files/upload",
            files={"file": ("piece.txt", io.BytesIO(b"contenu " * 50), "text/plain")},
            data={"project_id": projet_id},
        )
        assert resp.status_code == 200, resp.text

        lignes = await _traitements_indexation()
        assert len(lignes) == 1
        assert lignes[0].state == EtatTache.DONE
        assert lignes[0].label == "piece.txt"
        assert lignes[0].project_id == projet_id

    @pytest.mark.asyncio
    async def test_un_echec_d_indexation_est_visible_en_failed(
        self, client, fichier_texte, qdrant_factice, monkeypatch
    ):
        from app.services import indexation

        async def extraction_en_panne(_p):
            raise RuntimeError("extracteur en panne")

        monkeypatch.setattr(indexation, "extract_text_async", extraction_en_panne)

        reponse = await client.post(
            "/api/files/index", json={"path": str(fichier_texte)}
        )
        assert reponse.status_code >= 400

        lignes = await _traitements_indexation()
        assert len(lignes) == 1
        assert lignes[0].state == EtatTache.FAILED


class TestLAnnulationDepuisLePanneau:
    @pytest.mark.asyncio
    async def test_l_arret_demande_abandonne_avant_toute_ecriture(
        self, client, fichier_texte, qdrant_factice, monkeypatch
    ):
        """Pendant l'extraction, l'utilisateur clique Arrêter au panneau :
        le cœur lève IndexationAbandonnee au point d'abandon, l'enveloppe
        pose cancelled, et RIEN n'a été écrit dans l'index."""
        from app.routers import files as surface
        from app.services import indexation, traitements

        porte = asyncio.Event()

        async def extraction_lente(_p):
            await porte.wait()
            return "texte extrait tardivement"

        monkeypatch.setattr(indexation, "extract_text_async", extraction_lente)

        async def _pas_deconnecte():
            return False

        tache = asyncio.create_task(
            surface.indexer_avec_suivi(
                str(fichier_texte), est_deconnecte=_pas_deconnecte
            )
        )

        traitement = None
        for _ in range(100):
            lignes = await _traitements_indexation()
            if lignes and lignes[0].state == EtatTache.RUNNING:
                traitement = lignes[0]
                break
            await asyncio.sleep(0.05)
        assert traitement is not None, "le traitement doit être running pendant l'extraction"

        arret = await traitements.demander_arret(traitement.id)
        assert arret is not None and arret.transmise

        porte.set()
        with pytest.raises(indexation.IndexationAbandonnee):
            await tache

        lignes = await _traitements_indexation()
        assert lignes[0].state == EtatTache.CANCELLED
        qdrant_factice.async_add_memories.assert_not_called()
        qdrant_factice.async_delete_by_entity.assert_not_called()


class TestLeSeuilDeVisibilite:
    @pytest.mark.asyncio
    async def test_les_indexations_eclair_sont_masquees(self, client):
        from datetime import UTC, datetime, timedelta

        from app.models.database import get_session_context
        from app.services import task_registry, traitements

        async with get_session_context() as session:
            recent = datetime.now(UTC) - timedelta(seconds=1)
            session.add(ProcessingTask(
                type="indexation", label="eclair done", state="done",
                run_instance_id=task_registry.instance_courante(),
                created_at=recent, finished_at=datetime.now(UTC),
            ))
            session.add(ProcessingTask(
                type="indexation", label="eclair failed", state="failed",
                run_instance_id=task_registry.instance_courante(),
                created_at=recent, finished_at=datetime.now(UTC),
            ))
            await session.commit()

        labels = {t["label"] for t in await traitements.lister()}
        assert "eclair done" not in labels, (
            "une indexation de 1 s qui a réussi n'apporte rien au panneau"
        )
        assert "eclair failed" in labels, "un échec est TOUJOURS visible"


class TestProjectSync:
    @pytest.mark.asyncio
    async def test_un_apply_multi_indexations_un_seul_traitement(
        self, client, qdrant_factice, tmp_path
    ):
        from app.services import project_sync_service as svc

        racine = tmp_path / "dossier-sync"
        racine.mkdir()
        (racine / "un.txt").write_text("premier", encoding="utf-8")
        (racine / "deux.txt").write_text("second", encoding="utf-8")
        (racine / "trois.txt").write_text("troisieme", encoding="utf-8")

        resp = await client.post("/api/memory/projects", json={"name": "Chantier"})
        projet = resp.json()["id"]
        await svc.definir_racine(projet, str(racine))
        plan = await svc.preparer_plan(projet)

        await svc.appliquer_plan(projet, plan.id)

        assert await _traitements_indexation() == [], (
            "l'apply est UN traitement project_sync - le cœur d'indexation "
            "ne doit pas en semer un par fichier"
        )

    @pytest.mark.asyncio
    async def test_l_annulation_interrompt_l_operation_en_vol_sans_echec(
        self, client, qdrant_factice, tmp_path, monkeypatch
    ):
        """Annuler l'apply pendant l'indexation d'un gros fichier doit
        interrompre CETTE indexation (pas seulement entre deux opérations),
        et l'opération interrompue reste à_faire - pas un faux échec."""
        from app.models.entities_sync import EtatOperation
        from app.services import indexation, traitements
        from app.services import project_sync_service as svc

        racine = tmp_path / "dossier-sync"
        racine.mkdir()
        (racine / "gros.txt").write_text("premier", encoding="utf-8")
        (racine / "suite.txt").write_text("second", encoding="utf-8")

        resp = await client.post("/api/memory/projects", json={"name": "Chantier"})
        projet = resp.json()["id"]
        await svc.definir_racine(projet, str(racine))
        plan = await svc.preparer_plan(projet)

        porte = asyncio.Event()
        extraction_commencee = asyncio.Event()

        async def extraction_lente(_p):
            extraction_commencee.set()
            await porte.wait()
            return "texte extrait tardivement"

        monkeypatch.setattr(indexation, "extract_text_async", extraction_lente)

        apply_task = asyncio.create_task(svc.appliquer_plan(projet, plan.id))
        await asyncio.wait_for(extraction_commencee.wait(), timeout=5)

        run = await svc.lire_run(plan.id)
        assert run is not None
        arret = await traitements.demander_arret(run.id)
        assert arret is not None and arret.transmise

        porte.set()
        await apply_task

        run_final = await svc.lire_run(plan.id)
        assert run_final.state == EtatTache.CANCELLED
        ops = await svc.lire_operations(plan.id)
        assert all(o.etat != EtatOperation.ECHEC for o in ops), (
            "une opération interrompue par l'utilisateur n'est pas en échec"
        )
        assert any(o.etat == EtatOperation.A_FAIRE for o in ops), (
            "l'opération interrompue doit rester à faire pour le prochain apply"
        )
        qdrant_factice.async_add_memories.assert_not_called()


class TestLeFallbackChat:
    @pytest.mark.asyncio
    async def test_l_abandon_n_est_pas_deguise_en_erreur_de_lecture(
        self, client, fichier_texte, monkeypatch
    ):
        """`_get_file_context` absorbait tout dans « Erreur lors de la
        lecture » : un abandon d'indexation doit se propager, pas mentir."""
        from app.models.database import get_session_context
        from app.routers import chat as module
        from app.services.indexation import IndexationAbandonnee

        async def abandon(*_a, **_k):
            raise IndexationAbandonnee("arrêt demandé")

        # 0.47 : le fallback délègue au cœur - c'est LUI qui lève.
        from app.services import indexation

        monkeypatch.setattr(indexation, "index_payload", abandon)
        monkeypatch.setattr(
            module, "extract_text", lambda _p: "du texte", raising=False
        )

        async with get_session_context() as session:
            with pytest.raises(IndexationAbandonnee):
                await module._get_file_context(str(fichier_texte), session)


class TestLesFenetresDeLaRevue:
    @pytest.mark.asyncio
    async def test_f4_le_depot_n_a_pas_lieu_si_l_arret_est_deja_pose(
        self, client, fichier_texte, qdrant_factice
    ):
        """F4 : `remplacer_puis_indexer` remplaçait le fichier sur disque
        AVANT de consulter l'abandon - la version précédente était perdue
        alors que son index restait servi."""
        from app.services import indexation

        await indexation.index_payload(str(fichier_texte))
        contenu_initial = fichier_texte.read_bytes()

        depots = {"n": 0}

        async def deposer():
            depots["n"] += 1
            fichier_texte.write_text("NOUVELLE VERSION", encoding="utf-8")

        async def toujours_abandonnee() -> bool:
            return True

        with pytest.raises(indexation.IndexationAbandonnee):
            await indexation.remplacer_puis_indexer(
                str(fichier_texte), deposer,
                est_abandonnee=toujours_abandonnee,
            )

        assert depots["n"] == 0, (
            "le dépôt a eu lieu alors que l'arrêt était déjà posé"
        )
        assert fichier_texte.read_bytes() == contenu_initial

    @pytest.mark.asyncio
    async def test_f5_l_upload_ecoute_la_deconnexion_du_client(
        self, client, qdrant_factice, monkeypatch
    ):
        """F5 : contrairement à /index, /upload ne recevait pas la requête
        et ne pouvait jamais constater la déconnexion du client."""
        import io

        from app.routers import files as surface
        from fastapi import HTTPException

        capture: dict = {}

        async def espionne(**kwargs):
            capture.update(kwargs)
            raise HTTPException(status_code=418, detail="spy")

        monkeypatch.setattr(surface, "_executer_avec_suivi", espionne)

        resp = await client.post(
            "/api/memory/projects", json={"name": "Chantier deco"}
        )
        projet_id = resp.json()["id"]
        await client.post(
            "/api/files/upload",
            files={"file": ("gros.txt", io.BytesIO(b"x" * 100), "text/plain")},
            data={"project_id": projet_id},
        )

        assert capture, "l'enveloppe n'a pas été invoquée"
        assert capture.get("est_deconnecte") is not None, (
            "/upload ignore la déconnexion : copie, extraction et indexation "
            "continuent pour un client parti"
        )


class TestLeSecondPanel:
    @pytest.mark.asyncio
    async def test_une_panne_du_suivi_apres_succes_ne_ment_pas_au_client(
        self, client, fichier_texte, qdrant_factice, monkeypatch
    ):
        """Une indexation RÉUSSIE (Qdrant écrit, résultat consigné) doit
        répondre 200 même si la clôture du suivi tombe en panne - pas un
        500 qui fait croire à un échec."""
        from app.services import traitements

        async def progresser_en_panne(self, **_k):
            raise RuntimeError("database is locked")

        monkeypatch.setattr(
            traitements.TraitementHandle, "progresser", progresser_en_panne
        )

        reponse = await client.post(
            "/api/files/index", json={"path": str(fichier_texte)}
        )
        assert reponse.status_code == 200, (
            "le fichier EST indexé et cherchable : répondre 500 fait "
            "recommencer l'utilisateur pour rien"
        )
        qdrant_factice.async_add_memories.assert_called()
        # Passe 2 de revue (P2-1) : progresser et terminer ne partagent pas
        # leur sort - la ligne doit finir done, pas running fantôme.
        lignes = await _traitements_indexation()
        assert lignes and lignes[0].state == EtatTache.DONE

    @pytest.mark.asyncio
    async def test_une_panne_du_demarrage_du_suivi_n_empeche_pas_d_indexer(
        self, client, fichier_texte, qdrant_factice, monkeypatch
    ):
        """Fail-open promis : une panne de demarrer()/lier_adaptateur() ne
        doit pas transformer l'indexation en échec jamais tenté."""
        from app.services import traitements

        async def demarrer_en_panne(self):
            raise RuntimeError("database is locked")

        monkeypatch.setattr(
            traitements.TraitementHandle, "demarrer", demarrer_en_panne
        )

        reponse = await client.post(
            "/api/files/index", json={"path": str(fichier_texte)}
        )
        assert reponse.status_code == 200
        qdrant_factice.async_add_memories.assert_called()
        # Passe 2 de revue (P2-2) : le suivi qui a raté son départ ne doit
        # pas afficher « échec » pour une indexation réussie - la clôture
        # normale pose done depuis queued.
        lignes = await _traitements_indexation()
        assert lignes and lignes[0].state == EtatTache.DONE, (
            f"la ligne dit « {lignes[0].state if lignes else '?'} » pour "
            "une indexation qui a réussi"
        )

    @pytest.mark.asyncio
    async def test_une_panne_de_la_cloture_cancelled_garde_le_409(
        self, client, fichier_texte, qdrant_factice, monkeypatch
    ):
        from app.routers import files as surface
        from app.services import indexation, traitements

        async def toujours_abandonnee() -> bool:
            return True

        async def terminer_en_panne(self, *_a, **_k):
            raise RuntimeError("database is locked")

        monkeypatch.setattr(
            traitements.TraitementHandle, "terminer", terminer_en_panne
        )

        with pytest.raises(indexation.IndexationAbandonnee):
            await surface.indexer_avec_suivi(
                str(fichier_texte), est_deconnecte=toujours_abandonnee
            )

    @pytest.mark.asyncio
    async def test_apres_le_depot_l_indexation_va_au_bout(
        self, client, fichier_texte, qdrant_factice
    ):
        """Second panel : un abandon constaté APRÈS os.replace laissait
        trois vérités (disque v2, fiche v2, index v1). Le dépôt est le
        point de non-retour : ensuite, l'indexation va au bout."""
        from app.services import indexation

        await indexation.index_payload(str(fichier_texte))
        qdrant_factice.async_add_memories.reset_mock()

        drapeau = {"pose": False}

        async def deposer():
            fichier_texte.write_text("NOUVELLE VERSION", encoding="utf-8")
            drapeau["pose"] = True  # l'arrêt arrive juste après le dépôt

        async def abandonnee_apres_depot() -> bool:
            return drapeau["pose"]

        reponse = await indexation.remplacer_puis_indexer(
            str(fichier_texte), deposer,
            est_abandonnee=abandonnee_apres_depot,
        )

        assert reponse.chunk_count > 0
        qdrant_factice.async_add_memories.assert_called(), (
            "après le point de non-retour, l'index doit suivre le disque"
        )


    @pytest.mark.asyncio
    async def test_p28_l_arret_pendant_la_copie_empeche_le_remplacement(
        self, client, qdrant_factice, monkeypatch
    ):
        """Passe 2 (P2-8) : le vrai point de non-retour est os.replace, pas
        l'entrée dans le dépôt. Un arrêt posé pendant la copie (longue sur
        un gros fichier) doit préserver la version en place."""
        import io
        import shutil as shutil_module

        from app.routers import files as surface

        resp = await client.post(
            "/api/memory/projects", json={"name": "Chantier copie"}
        )
        projet_id = resp.json()["id"]
        resp = await client.post(
            "/api/files/upload",
            files={"file": ("piece.txt", io.BytesIO(b"VERSION UN"), "text/plain")},
            data={"project_id": projet_id},
        )
        assert resp.status_code == 200
        chemin = Path(resp.json()["path"])
        assert chemin.read_bytes() == b"VERSION UN"

        copie_originale = shutil_module.copyfileobj

        def copie_pendant_laquelle_on_annule(src, dst, *a, **k):
            copie_originale(src, dst, *a, **k)
            # l'utilisateur clique Arrêter pendant la (longue) copie :
            # l'évènement du panneau est posé par l'adaptateur
            surface._arrets_de_test_p28.set()

        monkeypatch.setattr(
            surface.shutil, "copyfileobj", copie_pendant_laquelle_on_annule
        )

        # brancher l'évènement de l'enveloppe pour ce test : on passe par
        # la route réelle, l'arrêt vient du traitement durable
        import asyncio as asyncio_module

        surface._arrets_de_test_p28 = asyncio_module.Event()
        vrai_executer = surface._executer_avec_suivi

        async def executer_espionne(**kwargs):
            vraie_cb = kwargs["est_deconnecte"]

            async def deconnecte_ou_arret_test() -> bool:
                if surface._arrets_de_test_p28.is_set():
                    return True
                return bool(vraie_cb and await vraie_cb())

            kwargs["est_deconnecte"] = deconnecte_ou_arret_test
            return await vrai_executer(**kwargs)

        monkeypatch.setattr(surface, "_executer_avec_suivi", executer_espionne)

        resp = await client.post(
            "/api/files/upload",
            files={"file": ("piece.txt", io.BytesIO(b"VERSION DEUX"), "text/plain")},
            data={"project_id": projet_id},
        )
        assert resp.status_code == 409, resp.text
        assert chemin.read_bytes() == b"VERSION UN", (
            "os.replace a eu lieu alors que l'arrêt était posé pendant la copie"
        )


class TestLaPasse3:
    @pytest.mark.asyncio
    async def test_p31_le_verrou_est_tenu_jusqu_au_bout_du_geste(
        self, client, fichier_texte, monkeypatch
    ):
        """Passe 3 (P3-1) : le porteur annulé libérait le verrou de chemin
        pendant que le geste détaché écrivait encore - une demande B
        pouvait entrelacer ses écritures avec celles de A (index mélangé).
        Le geste doit POSSÉDER le verrou jusqu'à sa fin."""
        import contextlib as _ctx

        from app.services import indexation

        porte = asyncio.Event()
        ecriture_commencee = asyncio.Event()
        journal: list[str] = []

        class QdrantJournal:
            async def async_delete_by_entity(self, _eid):
                journal.append("delete")

            async def async_add_memories(self, items):
                if not ecriture_commencee.is_set():
                    ecriture_commencee.set()
                    journal.append("A:debut")
                    await porte.wait()
                    journal.append("A:fin")
                else:
                    journal.append("B")

        monkeypatch.setattr(
            indexation, "get_qdrant_service", lambda: QdrantJournal()
        )
        monkeypatch.setattr(indexation, "extract_text", lambda _p: "texte")

        tache_a = asyncio.create_task(indexation.index_payload(str(fichier_texte)))
        await asyncio.wait_for(ecriture_commencee.wait(), timeout=5)
        tache_a.cancel()
        with _ctx.suppress(asyncio.CancelledError):
            await tache_a

        # B se présente sur le MÊME chemin pendant que le geste A écrit encore
        tache_b = asyncio.create_task(indexation.index_payload(str(fichier_texte)))
        await asyncio.sleep(0.3)
        assert not tache_b.done(), (
            "B est entré dans la section critique pendant que le geste A "
            "écrivait encore : le verrou a été libéré avec le porteur"
        )

        porte.set()
        await asyncio.wait_for(tache_b, timeout=10)
        assert journal.index("A:fin") < journal.index("B"), (
            "les écritures de B se sont intercalées dans le geste A"
        )

    @pytest.mark.asyncio
    async def test_p36_l_annulation_apres_le_depot_n_ampute_pas_l_indexation(
        self, client, qdrant_factice, tmp_path, monkeypatch
    ):
        """Passe 3 (P3-6) : après os.replace, l'extraction restait dans le
        porteur annulable - un cancel dur laissait disque v2 / index v1.
        Toute la section post-dépôt doit survivre au porteur."""
        import contextlib as _ctx

        from app.models.database import get_session_context
        from app.models.entities import FileMetadata
        from app.services import indexation

        fichier = tmp_path / "piece.txt"
        fichier.write_text("VERSION UN", encoding="utf-8")
        await indexation.index_payload(str(fichier))

        extraction_commencee = asyncio.Event()
        porte = asyncio.Event()

        def extraction_lente(_p):
            # sync, appelée via extract_text_async/threadpool
            return "VERSION DEUX EXTRAITE"

        async def extraction_async_lente(_p):
            extraction_commencee.set()
            await porte.wait()
            return "VERSION DEUX EXTRAITE"

        monkeypatch.setattr(
            indexation, "extract_text_async", extraction_async_lente
        )

        async def deposer():
            fichier.write_text("VERSION DEUX", encoding="utf-8")

        porteur = asyncio.create_task(indexation.remplacer_puis_indexer(
            str(fichier), deposer,
        ))
        await asyncio.wait_for(extraction_commencee.wait(), timeout=5)
        porteur.cancel()  # annulation DURE après le point de non-retour
        with _ctx.suppress(asyncio.CancelledError):
            await porteur
        porte.set()

        # l'index doit suivre le disque (v2), pas rester amputé sur v1
        ligne = None
        for _ in range(100):
            async with get_session_context() as session:
                ligne = (await session.execute(
                    select(FileMetadata).where(
                        FileMetadata.path == str(fichier.resolve())
                    )
                )).scalar_one_or_none()
            if ligne is not None and ligne.chunk_count:
                derniers = qdrant_factice.async_add_memories.call_args
                if derniers and "VERSION DEUX" in str(derniers):
                    break
            await asyncio.sleep(0.05)
        derniers = qdrant_factice.async_add_memories.call_args
        assert derniers and "VERSION DEUX" in str(derniers), (
            "le disque porte v2 mais l'index sert toujours v1 : le geste "
            "post-dépôt est mort avec le porteur"
        )

    @pytest.mark.asyncio
    async def test_p31b_l_enveloppe_cloture_meme_si_son_porteur_meurt(
        self, client, fichier_texte, monkeypatch
    ):
        """Passe 3 (P3-1b) : le porteur de /index annulé (déconnexion dure)
        pendant le geste - le geste réussit mais la ligne restait running.
        Une clôture détachée doit poser l'état final."""
        import contextlib as _ctx

        from app.routers import files as surface
        from app.services import indexation

        porte = asyncio.Event()
        ecriture_commencee = asyncio.Event()

        class QdrantGate:
            async def async_delete_by_entity(self, _eid):
                return None

            async def async_add_memories(self, items):
                ecriture_commencee.set()
                await porte.wait()

        monkeypatch.setattr(
            indexation, "get_qdrant_service", lambda: QdrantGate()
        )
        monkeypatch.setattr(indexation, "extract_text", lambda _p: "texte")

        porteur = asyncio.create_task(
            surface.indexer_avec_suivi(str(fichier_texte))
        )
        await asyncio.wait_for(ecriture_commencee.wait(), timeout=5)
        porteur.cancel()
        with _ctx.suppress(asyncio.CancelledError):
            await porteur
        porte.set()

        ligne = None
        for _ in range(100):
            lignes = await _traitements_indexation()
            if lignes and lignes[0].state == EtatTache.DONE:
                ligne = lignes[0]
                break
            await asyncio.sleep(0.05)
        assert ligne is not None and ligne.state == EtatTache.DONE, (
            "le geste a réussi mais la ligne reste "
            f"« {lignes[0].state if lignes else '?'} » : porteur mort = "
            "plus personne pour clore"
        )


class TestLaPasse4:
    @pytest.mark.asyncio
    async def test_p41_le_verrou_ne_se_contourne_pas_par_alias(
        self, client, tmp_path, monkeypatch
    ):
        """Passe 4 (P4-1) : index_payload verrouillait le chemin RÉSOLU,
        remplacer_puis_indexer la chaîne BRUTE - un alias (relatif vs
        absolu, symlink) contournait la sérialisation par chemin."""
        import contextlib as _ctx
        import os

        from app.services import indexation

        reel = tmp_path / "dossier"
        reel.mkdir()
        fichier = reel / "piece.txt"
        fichier.write_text("contenu", encoding="utf-8")
        lien = tmp_path / "alias"
        os.symlink(reel, lien)
        chemin_alias = str(lien / "piece.txt")

        porte = asyncio.Event()
        en_section = asyncio.Event()
        entrees: list[str] = []

        class QdrantGate:
            async def async_delete_by_entity(self, _eid):
                return None

            async def async_add_memories(self, items):
                entrees.append("ecriture")
                if len(entrees) == 1:
                    en_section.set()
                    await porte.wait()

        monkeypatch.setattr(
            indexation, "get_qdrant_service", lambda: QdrantGate()
        )
        monkeypatch.setattr(indexation, "extract_text", lambda _p: "texte")
        # neutraliser le sémaphore d'encodage : c'est le VERROU DE CHEMIN
        # qui doit sérialiser, pas la borne d'encodages simultanés
        monkeypatch.setattr(indexation, "INDEX_SEMAPHORE", asyncio.Semaphore(10))

        tache_a = asyncio.create_task(
            indexation.index_payload(str(fichier))
        )
        await asyncio.wait_for(en_section.wait(), timeout=5)

        async def deposer():
            (lien / "piece.txt").write_text("v2", encoding="utf-8")

        tache_b = asyncio.create_task(indexation.remplacer_puis_indexer(
            chemin_alias, deposer,
        ))
        await asyncio.sleep(0.3)
        assert len(entrees) == 1, (
            "B est entré en ÉCRITURE par l'ALIAS pendant que A tenait le "
            "verrou du chemin réel : la sérialisation par chemin est "
            "contournée"
        )
        porte.set()
        with _ctx.suppress(Exception):
            await asyncio.wait_for(tache_a, timeout=10)
        with _ctx.suppress(Exception):
            await asyncio.wait_for(tache_b, timeout=10)

    @pytest.mark.asyncio
    async def test_p42_annulation_pendant_la_cloture_pose_quand_meme_l_etat(
        self, client, fichier_texte, qdrant_factice, monkeypatch
    ):
        """Passe 4 (P4-2) : le porteur annulé PENDANT _clore_succes (travail
        déjà fini) échappait à la continuation - zéro terminaison, ligne
        running. Le superviseur travail+clôture doit être détaché en bloc."""
        import contextlib as _ctx

        from app.routers import files as surface
        from app.services import traitements

        porte = asyncio.Event()
        cloture_commencee = asyncio.Event()
        progresser_originale = traitements.TraitementHandle.progresser

        async def progresser_gated(self, **kwargs):
            if kwargs.get("progress") == 1.0:
                cloture_commencee.set()
                await porte.wait()
            await progresser_originale(self, **kwargs)

        monkeypatch.setattr(
            traitements.TraitementHandle, "progresser", progresser_gated
        )

        porteur = asyncio.create_task(
            surface.indexer_avec_suivi(str(fichier_texte))
        )
        await asyncio.wait_for(cloture_commencee.wait(), timeout=5)
        porteur.cancel()  # l'annulation frappe PENDANT la clôture vivante
        with _ctx.suppress(asyncio.CancelledError):
            await porteur
        porte.set()

        ligne = None
        for _ in range(100):
            lignes = await _traitements_indexation()
            if lignes and lignes[0].state == EtatTache.DONE:
                ligne = lignes[0]
                break
            await asyncio.sleep(0.05)
        assert ligne is not None and ligne.state == EtatTache.DONE, (
            f"ligne « {lignes[0].state if lignes else '?'} » : l'annulation "
            "pendant la clôture a laissé zéro terminaison"
        )
