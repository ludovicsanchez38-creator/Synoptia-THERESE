"""
Remédiation de la revue Soso du 27/07/2026 sur BUG-155 (NO-GO, findings F1 à F4).

F1 : l'annulation côté interface n'arrêtait rien côté serveur (`run_in_threadpool`
     ne peut pas interrompre un traitement synchrone déjà lancé) et deux
     indexations du même chemin pouvaient se croiser malgré `path UNIQUE`.
F2 : la métadonnée était insérée puis `flush()` AVANT l'extraction, gardant le
     verrou d'écriture SQLite (mono-écrivain, busy_timeout 5 s) pendant tout le
     traitement lourd : une écriture concurrente, par exemple l'enregistrement
     d'un message de chat, pouvait échouer.
F3 : `POST /api/files/upload` et `GET /api/files/{id}/content` gardaient le
     même défaut de blocage.
F4 : aucune régulation du nombre d'encodages simultanés.
"""
import asyncio
import threading
import time
from pathlib import Path

import pytest


@pytest.fixture()
def fichier(tmp_path: Path) -> Path:
    chemin = tmp_path / "note.txt"
    chemin.write_text("Contenu de test. " * 200, encoding="utf-8")
    return chemin


class FauxQdrant:
    def __init__(self):
        self.ajouts = []

    async def async_delete_by_entity(self, _entity_id):
        return None

    async def async_add_memories(self, items):
        self.ajouts.append(items)
        return None


class TestF2VerrouEcriture:
    @pytest.mark.asyncio
    async def test_la_metadonnee_est_commitee_avant_le_traitement_lourd(
        self, client, fichier, monkeypatch
    ):
        """Une écriture concurrente ne doit pas attendre la fin de l'indexation."""
        from app.models.database import get_session_context
        from app.models.entities import FileMetadata
        from app.routers import files as files_router
        from sqlmodel import select

        visible_pendant_extraction: list[bool] = []

        def extraction_qui_observe(path):
            async def observer():
                async with get_session_context() as autre_session:
                    resultat = await autre_session.execute(
                        select(FileMetadata).where(FileMetadata.path == str(path))
                    )
                    visible_pendant_extraction.append(resultat.scalar_one_or_none() is not None)

            # L'extraction tourne dans un thread : on y ouvre une boucle dédiée,
            # exactement comme le ferait une autre requête servie en parallèle.
            asyncio.run(observer())
            return "texte extrait"

        monkeypatch.setattr(files_router, "extract_text", extraction_qui_observe)
        monkeypatch.setattr(files_router, "get_qdrant_service", lambda: FauxQdrant())

        reponse = await client.post("/api/files/index", json={"path": str(fichier)})

        assert reponse.status_code == 200, reponse.text
        assert visible_pendant_extraction == [True], (
            "la métadonnée n'était pas encore commitée : la transaction d'écriture "
            "reste ouverte pendant tout le traitement lourd"
        )


class TestF1AnnulationEtConcurrence:
    @pytest.mark.asyncio
    async def test_client_deconnecte_avant_les_embeddings(self, fichier, monkeypatch):
        """Si l'utilisateur a retiré la pièce jointe, on n'encode pas pour rien.

        L'extraction déjà lancée va à son terme (un thread ne s'interrompt pas),
        mais l'étape la plus coûteuse - encodage puis écriture vectorielle - est
        abandonnée dès qu'on constate que personne n'attend plus la réponse.
        """
        from app.routers import files as files_router

        faux_qdrant = FauxQdrant()
        monkeypatch.setattr(files_router, "get_qdrant_service", lambda: faux_qdrant)
        monkeypatch.setattr(files_router, "extract_text", lambda _p: "texte extrait")

        async def toujours_abandonnee():
            return True

        await files_router.index_payload(
            path=str(fichier),
            est_abandonnee=toujours_abandonnee,
        )

        assert faux_qdrant.ajouts == [], (
            "les embeddings ont été calculés alors que la demande était abandonnée"
        )

    @pytest.mark.asyncio
    async def test_sans_abandon_les_embeddings_sont_bien_calcules(self, fichier, monkeypatch):
        from app.routers import files as files_router

        faux_qdrant = FauxQdrant()
        monkeypatch.setattr(files_router, "get_qdrant_service", lambda: faux_qdrant)
        monkeypatch.setattr(files_router, "extract_text", lambda _p: "texte extrait")

        await files_router.index_payload(path=str(fichier))

        assert faux_qdrant.ajouts, "l'indexation normale n'écrit plus les fragments"

    @pytest.mark.asyncio
    async def test_deux_indexations_du_meme_fichier_sont_serialisees(self, fichier, monkeypatch):
        """La contrainte `path UNIQUE` ne doit jamais être atteinte en course."""
        from app.routers import files as files_router

        en_cours = 0
        max_simultane = 0
        verrou = threading.Lock()

        def extraction_lente(_path):
            nonlocal en_cours, max_simultane
            with verrou:
                en_cours += 1
                max_simultane = max(max_simultane, en_cours)
            time.sleep(0.15)
            with verrou:
                en_cours -= 1
            return "texte extrait"

        monkeypatch.setattr(files_router, "extract_text", extraction_lente)
        monkeypatch.setattr(files_router, "get_qdrant_service", lambda: FauxQdrant())

        resultats = await asyncio.gather(
            files_router.index_payload(path=str(fichier)),
            files_router.index_payload(path=str(fichier)),
            return_exceptions=True,
        )

        for r in resultats:
            assert not isinstance(r, Exception), f"course non sérialisée : {r!r}"
        assert max_simultane == 1, (
            f"{max_simultane} indexations simultanées du même chemin (verrou absent)"
        )


class TestF3AutresRoutesBloquantes:
    @pytest.mark.asyncio
    async def test_lecture_de_contenu_hors_thread_de_la_route(self, client, fichier, monkeypatch):
        from app.routers import files as files_router

        monkeypatch.setattr(files_router, "get_qdrant_service", lambda: FauxQdrant())
        monkeypatch.setattr(files_router, "extract_text", lambda _p: "texte extrait")
        creation = await client.post("/api/files/index", json={"path": str(fichier)})
        assert creation.status_code == 200, creation.text
        file_id = creation.json()["id"]

        thread_route: list[int] = []
        thread_extraction: list[int] = []
        vrai_metadata = files_router.get_file_metadata

        def metadata_tracee(path):
            thread_route.append(threading.get_ident())
            return vrai_metadata(path)

        def extraction_tracee(_path):
            thread_extraction.append(threading.get_ident())
            return "contenu du fichier"

        monkeypatch.setattr(files_router, "get_file_metadata", metadata_tracee)
        monkeypatch.setattr(files_router, "extract_text", extraction_tracee)

        reponse = await client.get(f"/api/files/{file_id}/content")

        assert reponse.status_code == 200, reponse.text
        assert thread_extraction, "extract_text n'a pas été appelé"
        assert thread_extraction[0] != threading.get_ident(), (
            "la lecture de contenu bloque la boucle d'événements"
        )


class TestF4Regulation:
    def test_un_semaphore_borne_les_indexations_simultanees(self):
        from app.routers import files as files_router

        assert isinstance(files_router.INDEX_SEMAPHORE, asyncio.Semaphore)
        assert files_router.MAX_INDEXATIONS_SIMULTANEES >= 1
        assert files_router.MAX_INDEXATIONS_SIMULTANEES <= 4, (
            "une limite trop haute laisse plusieurs encodages saturer la machine"
        )
