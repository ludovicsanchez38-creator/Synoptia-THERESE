"""
Contre-vérification Soso du 27/07/2026 (2e passage) - défauts N1 et N2.

N1 : lors d'une RÉINDEXATION, les anciens vecteurs étaient supprimés avant
     l'extraction et avant tout contrôle d'abandon. Une annulation laissait donc
     un fichier sans aucun vecteur, marqué `chunk_count=0` avec un `indexed_at`
     tout neuf : il paraissait indexé alors qu'il ne l'était plus. Une erreur
     d'extraction produisait l'inverse (ancien compteur conservé, vecteurs
     disparus).

N2 : `delete_file` ne prenait pas le verrou de chemin. Il pouvait supprimer la
     ligne pendant l'extraction ; l'indexation ajoutait ensuite ses vecteurs et
     renvoyait un succès, laissant des vecteurs orphelins sans ligne en base.

F1 (resté ouvert) : l'abandon n'était plus consulté après l'attente du
     sémaphore - une déconnexion pendant cette attente n'empêchait rien.
"""
import asyncio
from pathlib import Path

import pytest


@pytest.fixture()
def fichier(tmp_path: Path) -> Path:
    chemin = tmp_path / "rapport.txt"
    chemin.write_text("Contenu de test. " * 200, encoding="utf-8")
    return chemin


class FauxQdrant:
    def __init__(self):
        self.ajouts = []
        self.suppressions = []

    async def async_delete_by_entity(self, entity_id):
        self.suppressions.append(entity_id)
        return 1

    async def async_add_memories(self, items):
        self.ajouts.append(items)
        return None


class TestN1IntegriteDeLaReindexation:
    @pytest.mark.asyncio
    async def test_une_annulation_ne_detruit_pas_l_index_existant(
        self, db_session, fichier, monkeypatch
    ):
        from app.routers import files as files_router
        from app.services import indexation

        faux = FauxQdrant()
        monkeypatch.setattr(indexation, "get_qdrant_service", lambda: faux)
        monkeypatch.setattr(indexation, "extract_text", lambda _p: "texte extrait")

        premiere = await files_router.index_payload(path=str(fichier))
        assert premiere.chunk_count > 0
        indexed_at_initial = premiere.indexed_at
        faux.suppressions.clear()

        async def abandonnee():
            return True

        await files_router.index_payload(path=str(fichier), est_abandonnee=abandonnee)

        assert faux.suppressions == [], (
            "l'index existant a été supprimé alors que la demande était abandonnée"
        )

        from app.models.database import get_session_context
        from app.models.entities import FileMetadata
        from sqlmodel import select

        async with get_session_context() as session:
            ligne = (
                await session.execute(
                    select(FileMetadata).where(FileMetadata.path == str(fichier.resolve()))
                )
            ).scalar_one()
            assert ligne.chunk_count == premiere.chunk_count, (
                "le fichier est présenté comme vide alors que ses vecteurs existent"
            )
            # SQLite rend des dates naïves (gotcha du projet, cf BUG-126) :
            # comparer les instants, pas leur fuseau.
            assert ligne.indexed_at.replace(tzinfo=None) == indexed_at_initial.replace(
                tzinfo=None
            ), "un horodatage neuf laisse croire à une indexation réussie"

    @pytest.mark.asyncio
    async def test_une_extraction_qui_echoue_laisse_l_index_intact(
        self, db_session, fichier, monkeypatch
    ):
        from app.routers import files as files_router
        from app.services import indexation

        faux = FauxQdrant()
        monkeypatch.setattr(indexation, "get_qdrant_service", lambda: faux)
        monkeypatch.setattr(indexation, "extract_text", lambda _p: "texte extrait")

        await files_router.index_payload(path=str(fichier))
        faux.suppressions.clear()

        def extraction_qui_casse(_p):
            raise ValueError("PDF protégé")

        monkeypatch.setattr(indexation, "extract_text", extraction_qui_casse)

        with pytest.raises(ValueError, match="PDF protégé"):
            await files_router.index_payload(path=str(fichier))

        assert faux.suppressions == [], (
            "les anciens vecteurs ont été supprimés avant de savoir si la nouvelle "
            "extraction aboutissait"
        )


class TestEchecDEcritureVectorielle:
    @pytest.mark.asyncio
    async def test_un_echec_apres_suppression_est_consigne_comme_index_vide(
        self, db_session, fichier, monkeypatch
    ):
        """La base ne doit pas annoncer des fragments qui n'existent plus.

        La suppression des anciens vecteurs précède forcément l'écriture des
        nouveaux. Si celle-ci échoue, l'index est vide : le dire, plutôt que de
        laisser l'ancien compteur promettre un contenu introuvable.
        """
        from app.models.database import get_session_context
        from app.models.entities import FileMetadata
        from app.routers import files as files_router
        from app.services import indexation
        from sqlmodel import select

        faux = FauxQdrant()
        monkeypatch.setattr(indexation, "get_qdrant_service", lambda: faux)
        monkeypatch.setattr(indexation, "extract_text", lambda _p: "texte extrait")

        await files_router.index_payload(path=str(fichier))

        class QdrantQuiCasse(FauxQdrant):
            async def async_add_memories(self, items):
                raise RuntimeError("Qdrant injoignable")

        monkeypatch.setattr(indexation, "get_qdrant_service", lambda: QdrantQuiCasse())

        with pytest.raises(RuntimeError, match="Qdrant injoignable"):
            await files_router.index_payload(path=str(fichier))

        async with get_session_context() as session:
            ligne = (
                await session.execute(
                    select(FileMetadata).where(FileMetadata.path == str(fichier.resolve()))
                )
            ).scalar_one()
            assert ligne.chunk_count == 0, (
                "la base promet des fragments alors que l'index vectoriel est vide"
            )


class TestF1AbandonPendantLAttente:
    @pytest.mark.asyncio
    async def test_l_abandon_est_reconsulte_apres_le_semaphore(self, db_session, fichier, monkeypatch):
        from app.routers import files as files_router
        from app.services import indexation

        faux = FauxQdrant()
        monkeypatch.setattr(indexation, "get_qdrant_service", lambda: faux)
        monkeypatch.setattr(indexation, "extract_text", lambda _p: "texte extrait")

        appels = {"n": 0}

        async def abandonnee_au_dernier_moment():
            # Deux premiers contrôles négatifs (avant découpage, avant sémaphore),
            # puis l'utilisateur retire la pièce jointe.
            appels["n"] += 1
            return appels["n"] > 2

        await files_router.index_payload(
            path=str(fichier), est_abandonnee=abandonnee_au_dernier_moment
        )

        assert faux.ajouts == [], (
            "l'écriture vectorielle a eu lieu alors que la demande venait d'être "
            "abandonnée pendant l'attente du sémaphore"
        )


class TestN2CourseAvecLaSuppression:
    @pytest.mark.asyncio
    async def test_la_vraie_suppression_attend_la_fin_de_l_indexation(
        self, db_session, fichier, monkeypatch
    ):
        """`delete_file` (la vraie route) doit prendre le verrou de chemin."""
        from app.models.database import get_session_context
        from app.routers import files as files_router
        from app.services import indexation

        faux = FauxQdrant()
        monkeypatch.setattr(indexation, "get_qdrant_service", lambda: faux)
        monkeypatch.setattr(indexation, "extract_text", lambda _p: "texte extrait")

        premiere = await files_router.index_payload(path=str(fichier))
        file_id = premiere.id

        ordre: list[str] = []
        indexation_demarree = asyncio.Event()

        def extraction_qui_signale(_p):
            ordre.append("indexation")
            return "nouveau texte"

        monkeypatch.setattr(indexation, "extract_text", extraction_qui_signale)

        async def indexer():
            indexation_demarree.set()
            return await files_router.index_payload(path=str(fichier))

        async def supprimer():
            await indexation_demarree.wait()
            await asyncio.sleep(0)
            async with get_session_context() as session:
                await files_router.delete_file(file_id, session)
            ordre.append("suppression")

        resultats = await asyncio.gather(indexer(), supprimer(), return_exceptions=True)

        assert ordre and ordre[0] == "indexation", (
            "la suppression s'est glissée pendant l'indexation : vecteurs orphelins"
        )
        # L'indexation peut légitimement finir en 409 (sa ligne a disparu), mais
        # jamais laisser un succès silencieux avec des vecteurs orphelins.
        for r in resultats:
            if isinstance(r, Exception):
                from fastapi import HTTPException

                assert isinstance(r, HTTPException) and r.status_code == 409, repr(r)


class TestN5CouvertureUpload:
    @pytest.mark.asyncio
    async def test_l_upload_extrait_hors_du_thread_de_la_route(
        self, client, tmp_path, monkeypatch
    ):
        import threading

        from app.models.database import get_session_context
        from app.models.entities import Project
        from app.services import indexation

        async with get_session_context() as session:
            projet = Project(name="Projet test")
            session.add(projet)
            await session.commit()
            await session.refresh(projet)
            project_id = projet.id

        monkeypatch.setattr(indexation, "get_qdrant_service", lambda: FauxQdrant())

        thread_route: list[int] = []
        thread_extraction: list[int] = []
        vrai_metadata = indexation.get_file_metadata

        def metadata_tracee(path):
            thread_route.append(threading.get_ident())
            return vrai_metadata(path)

        def extraction_tracee(_p):
            thread_extraction.append(threading.get_ident())
            return "texte extrait"

        monkeypatch.setattr(indexation, "get_file_metadata", metadata_tracee)
        monkeypatch.setattr(indexation, "extract_text", extraction_tracee)

        reponse = await client.post(
            "/api/files/upload",
            files={"file": ("note.txt", b"contenu du fichier", "text/plain")},
            data={"project_id": project_id},
        )

        assert reponse.status_code == 200, reponse.text
        assert thread_route and thread_extraction
        assert thread_extraction[0] != thread_route[0], (
            "l'upload extrait dans le thread de la route : la boucle reste bloquée"
        )


class TestN5SemaphoreUtilise:
    @pytest.mark.asyncio
    async def test_le_semaphore_est_reellement_pris(self, db_session, fichier, monkeypatch):
        from app.routers import files as files_router
        from app.services import indexation

        faux = FauxQdrant()
        monkeypatch.setattr(indexation, "get_qdrant_service", lambda: faux)
        monkeypatch.setattr(indexation, "extract_text", lambda _p: "texte extrait")

        libre_avant = indexation.INDEX_SEMAPHORE._value
        vus: list[int] = []

        class QdrantQuiObserve(FauxQdrant):
            async def async_add_memories(self, items):
                vus.append(indexation.INDEX_SEMAPHORE._value)
                return await super().async_add_memories(items)

        monkeypatch.setattr(indexation, "get_qdrant_service", lambda: QdrantQuiObserve())

        await files_router.index_payload(path=str(fichier))

        assert vus and vus[0] == libre_avant - 1, (
            "l'écriture vectorielle ne passe pas par le sémaphore"
        )
        assert indexation.INDEX_SEMAPHORE._value == libre_avant, (
            "le sémaphore n'est pas relâché"
        )
