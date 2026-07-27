"""
Troisième chemin d'indexation, trouvé en contre-vérifiant le finding F3.

`chat.py::_get_file_context` (fichier joint à un message) refaisait
l'extraction et le découpage en synchrone dans une coroutine, et gardait la
session de la requête ouverte pendant l'écriture vectorielle. C'est le chemin
emprunté quand on discute d'un document : le même gel que BUG-155.
"""
import threading

import pytest


@pytest.fixture()
def document(tmp_path):
    chemin = tmp_path / "rapport.txt"
    chemin.write_text("Contenu de test. " * 300, encoding="utf-8")
    return chemin


class TestContexteFichierNonBloquant:
    @pytest.mark.asyncio
    async def test_extraction_et_decoupage_hors_thread_de_la_coroutine(
        self, db_session, document, monkeypatch
    ):
        from app.routers import chat as chat_router

        thread_appelant = threading.get_ident()
        threads_extraction: list[int] = []
        threads_decoupage: list[int] = []

        def extraction_tracee(_path):
            threads_extraction.append(threading.get_ident())
            return "texte extrait du rapport"

        def decoupage_trace(_texte, chunk_size=1000, overlap=200):
            threads_decoupage.append(threading.get_ident())
            return iter(["fragment 1", "fragment 2"])

        class FauxQdrant:
            def __init__(self):
                self.ajouts = []

            async def async_add_memories(self, items):
                self.ajouts.append(items)
                return None

        faux = FauxQdrant()
        monkeypatch.setattr(chat_router, "extract_text", extraction_tracee)
        monkeypatch.setattr(chat_router, "chunk_text", decoupage_trace)
        monkeypatch.setattr(chat_router, "get_qdrant_service", lambda: faux)

        contexte, erreur = await chat_router._get_file_context(str(document), db_session)

        assert erreur is None, erreur
        assert contexte
        assert threads_extraction and threads_decoupage
        assert threads_extraction[0] != thread_appelant, (
            "l'extraction bloque la boucle d'événements quand on joint un fichier au chat"
        )
        assert threads_decoupage[0] != thread_appelant, (
            "le découpage bloque la boucle d'événements quand on joint un fichier au chat"
        )
        assert faux.ajouts, "les fragments n'ont pas été envoyés à la mémoire vectorielle"
