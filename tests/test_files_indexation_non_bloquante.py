"""
BUG-155 (27/07/2026) - L'indexation d'une pièce jointe volumineuse gelait
toute l'application.

`POST /api/files/index` est une route `async` mais appelait `extract_text` et
`chunk_text` de façon synchrone : pendant l'extraction d'un gros document, la
boucle d'événements du backend était bloquée et AUCUNE autre requête n'était
servie (chat, emails, agenda). Le testeur a dû fermer THÉRÈSE.

Le test mesure ce que l'utilisateur ressent : pendant que l'indexation tourne,
une autre coroutine doit continuer à progresser.
"""
import asyncio
import threading
import time
from pathlib import Path

import pytest


@pytest.fixture()
def gros_fichier(tmp_path: Path) -> Path:
    chemin = tmp_path / "rapport.txt"
    chemin.write_text("Contenu de test. " * 500, encoding="utf-8")
    return chemin


class TestIndexationNonBloquante:
    @pytest.mark.asyncio
    async def test_extraction_lente_ne_gele_pas_la_boucle(self, gros_fichier, monkeypatch):
        """Une extraction lente laisse les autres coroutines progresser."""
        from app.services import indexation

        duree_extraction = 0.4

        def extraction_lente(_path):
            time.sleep(duree_extraction)  # simule un PDF de plusieurs centaines de pages
            return "texte extrait"

        monkeypatch.setattr(indexation, "extract_text", extraction_lente)

        battements = 0

        async def horloge():
            nonlocal battements
            while True:
                await asyncio.sleep(0.02)
                battements += 1

        tache_horloge = asyncio.create_task(horloge())
        try:
            await indexation.extract_text_async(gros_fichier)
        finally:
            tache_horloge.cancel()

        # Sans blocage : ~20 battements. Boucle gelée : 0 ou 1.
        assert battements >= 5, (
            f"la boucle d'événements est restée bloquée ({battements} battements "
            f"pendant {duree_extraction}s d'extraction)"
        )

    @pytest.mark.asyncio
    async def test_decoupage_lent_ne_gele_pas_la_boucle(self, gros_fichier, monkeypatch):
        """Le découpage en fragments passe lui aussi hors de la boucle."""
        from app.services import indexation

        def decoupage_lent(_texte, chunk_size=1000, overlap=200):
            time.sleep(0.4)
            return iter(["fragment 1", "fragment 2"])

        monkeypatch.setattr(indexation, "chunk_text", decoupage_lent)

        battements = 0

        async def horloge():
            nonlocal battements
            while True:
                await asyncio.sleep(0.02)
                battements += 1

        tache_horloge = asyncio.create_task(horloge())
        try:
            fragments = await indexation.chunk_text_async("texte extrait")
        finally:
            tache_horloge.cancel()

        assert fragments == ["fragment 1", "fragment 2"]
        assert battements >= 5, (
            f"la boucle d'événements est restée bloquée ({battements} battements)"
        )

    @pytest.mark.asyncio
    async def test_la_route_extrait_hors_du_thread_de_la_boucle(
        self, client, gros_fichier, monkeypatch
    ):
        """Bout en bout : la route indexe sans exécuter l'extraction dans son propre thread.

        Le client de test est synchrone (portal anyio) : mesurer la latence d'une
        requête concurrente ne prouverait rien. On observe donc le fait
        structurel dont découle le non-blocage : `extract_text` et `chunk_text`
        s'exécutent dans un thread distinct de celui qui porte la route.
        """
        from app.services import indexation

        thread_route: list[int] = []
        thread_extraction: list[int] = []
        thread_decoupage: list[int] = []

        vrai_get_metadata = indexation.get_file_metadata

        def metadata_tracee(path):
            thread_route.append(threading.get_ident())
            return vrai_get_metadata(path)

        def extraction_tracee(_path):
            thread_extraction.append(threading.get_ident())
            return "texte extrait du rapport"

        def decoupage_trace(_texte, chunk_size=1000, overlap=200):
            thread_decoupage.append(threading.get_ident())
            return iter(["fragment 1", "fragment 2"])

        monkeypatch.setattr(indexation, "get_file_metadata", metadata_tracee)
        monkeypatch.setattr(indexation, "extract_text", extraction_tracee)
        monkeypatch.setattr(indexation, "chunk_text", decoupage_trace)

        appels_qdrant = []

        class FauxQdrant:
            async def async_delete_by_entity(self, _entity_id):
                return None

            async def async_add_memories(self, items):
                appels_qdrant.append(items)
                return None

        monkeypatch.setattr(indexation, "get_qdrant_service", lambda: FauxQdrant())

        reponse = await client.post("/api/files/index", json={"path": str(gros_fichier)})

        assert reponse.status_code == 200, reponse.text
        assert thread_route and thread_extraction and thread_decoupage
        assert thread_extraction[0] != thread_route[0], (
            "l'extraction tourne dans le thread de la route : la boucle reste bloquée"
        )
        assert thread_decoupage[0] != thread_route[0], (
            "le découpage tourne dans le thread de la route : la boucle reste bloquée"
        )
        assert appels_qdrant, "les fragments n'ont pas été envoyés à la mémoire vectorielle"
