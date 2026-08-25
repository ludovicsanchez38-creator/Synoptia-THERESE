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
