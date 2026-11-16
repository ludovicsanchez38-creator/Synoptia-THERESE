"""Une pièce jointe absente est signalée dans la réponse hors flux."""

from unittest.mock import AsyncMock

import pytest
from app.models.entities import FileMetadata
from app.routers import chat
from app.services import memory_card_context

from tests.test_p159_contexte_transmis import _evenements, _FauxLLM


@pytest.mark.asyncio
async def test_piece_absente_signalee_dans_les_avis(client, monkeypatch, tmp_path):
    monkeypatch.setattr(chat, "get_llm_service", _FauxLLM)
    monkeypatch.setattr(chat, "_extract_entities_background", AsyncMock())
    fichier_absent = tmp_path / "piece-introuvable.txt"

    reponse = await client.post("/api/chat/send", json={
        "message": "Que contient le document ?", "stream": False,
        "file_paths": [str(fichier_absent)], "include_memory": False, "disable_tools": True,
    })
    assert reponse.status_code == 200
    avis = reponse.json().get("avis") or []
    assert avis, "le document non chargé doit être signalé à l'écran"


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True])
async def test_piece_absente_ne_divulgue_que_son_nom(client, monkeypatch, tmp_path, stream):
    contextes = []

    class FauxLLMAvecTrace(_FauxLLM):
        def prepare_context(self, messages, memory_context=None):
            contextes.append(memory_context or "")
            return super().prepare_context(messages, memory_context=memory_context)

    monkeypatch.setattr(chat, "get_llm_service", FauxLLMAvecTrace)
    monkeypatch.setattr(chat, "_extract_entities_background", AsyncMock())
    fichier_absent = tmp_path / "dossier-personnel-fictif" / "piece-introuvable.txt"
    reponse = await client.post("/api/chat/send", json={
        "message": "Que contient le document ?", "stream": stream,
        "file_paths": [str(fichier_absent)], "include_memory": False, "disable_tools": True,
    })
    assert reponse.status_code == 200
    avis = (
        [event["content"] for event in _evenements(reponse.text) if event.get("type") == "notice"]
        if stream else reponse.json().get("avis") or []
    )
    assert avis
    dossier = str(fichier_absent.parent.resolve())
    assert not any(dossier in texte for texte in avis), "Le chemin du dossier est exposé à l'écran"
    assert any(fichier_absent.name in texte for texte in avis)
    assert contextes and any(fichier_absent.name in texte for texte in contextes)
    assert not any(dossier in texte for texte in contextes), "Le chemin du dossier est transmis au modèle"


@pytest.mark.asyncio
async def test_avis_de_lecture_ne_divulgue_pas_erreur_technique(client, monkeypatch, tmp_path):
    monkeypatch.setattr(chat, "get_llm_service", _FauxLLM)
    monkeypatch.setattr(chat, "_extract_entities_background", AsyncMock())
    fichier = tmp_path / "piece.txt"
    fichier.write_text("contenu fictif", encoding="utf-8")
    temoin = "identifiant-technique-confidentiel-fictif"

    def lecture_impossible(_fichier):
        raise RuntimeError(temoin)

    monkeypatch.setattr(chat, "extract_text", lecture_impossible)
    reponse = await client.post("/api/chat/send", json={
        "message": "Que contient le document ?", "stream": False,
        "file_paths": [str(fichier)], "include_memory": False, "disable_tools": True,
    })
    assert reponse.status_code == 200
    assert reponse.json().get("avis")
    assert temoin not in reponse.text


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True])
@pytest.mark.parametrize("cas", [
    "fichier", "lien_fichier", "absent", "dossier", "lien", "lien_absent", "lien_boucle",
    "acces", "validation_os", "test_fichier", "lecture", "taille", "vide",
])
async def test_avis_de_fichier_ne_contient_aucun_chemin_absolu(
    client, db_session, monkeypatch, tmp_path, stream, cas,
):
    contextes = []

    class FauxLLMAvecTrace(_FauxLLM):
        def prepare_context(self, messages, memory_context=None):
            contextes.append(memory_context or "")
            return super().prepare_context(messages, memory_context=memory_context)

    monkeypatch.setattr(chat, "get_llm_service", FauxLLMAvecTrace)
    monkeypatch.setattr(chat, "_extract_entities_background", AsyncMock())
    monkeypatch.setattr(memory_card_context, "documents_autorises", lambda *_args: True)
    dossier = tmp_path / "dossier-personnel-fictif"
    dossier.mkdir()
    chemin = dossier / "piece.txt"
    if cas == "dossier":
        chemin.mkdir()
    elif cas == "lien":
        cible = dossier / "cible"
        cible.mkdir()
        chemin.symlink_to(cible, target_is_directory=True)
    elif cas == "lien_absent":
        chemin.symlink_to(dossier / "cible-absente")
    elif cas == "lien_boucle":
        chemin.symlink_to(chemin)
    elif cas == "lien_fichier":
        cible = dossier / "cible.txt"
        cible.write_text("contenu fictif", encoding="utf-8")
        chemin.symlink_to(cible)
    elif cas != "absent":
        chemin.write_text("contenu fictif", encoding="utf-8")

    if cas in ("acces", "validation_os"):
        def acces_refuse(_chemin):
            erreur = PermissionError if cas == "acces" else OSError
            raise erreur(str(chemin))
        monkeypatch.setattr(chat, "validate_file_path", acces_refuse)
    elif cas == "test_fichier":
        class CheminIllisible:
            def is_file(self):
                raise PermissionError(str(chemin))
        monkeypatch.setattr(chat, "validate_file_path", lambda _chemin: CheminIllisible())
    elif cas in ("lecture", "taille"):
        def lecture_impossible(_chemin):
            erreur = chat.ErreurTailleFichier if cas == "taille" else OSError
            raise erreur(str(chemin))
        monkeypatch.setattr(chat, "extract_text", lecture_impossible)
    elif cas == "vide":
        monkeypatch.setattr(chat, "extract_text", lambda _chemin: "")

    if cas in ("fichier", "lien_fichier"):
        cible = chemin.resolve()
        db_session.add(FileMetadata(path=str(cible), name=cible.name, extension=".txt", size=16))
        await db_session.commit()

    contexte, erreur = await chat._get_file_context(str(chemin), db_session)
    if cas in ("fichier", "lien_fichier"):
        assert contexte and not erreur
    else:
        assert erreur
    for message in (contexte, erreur):
        assert not message or str(tmp_path) not in message

    reponse = await client.post("/api/chat/send", json={
        "message": "Que contient le document ?", "stream": stream,
        "file_paths": [str(chemin)], "include_memory": False, "disable_tools": True,
    })
    assert reponse.status_code == 200
    avis = (
        [event["content"] for event in _evenements(reponse.text) if event.get("type") == "notice"]
        if stream else reponse.json().get("avis") or []
    )
    assert contextes
    if cas not in ("fichier", "lien_fichier"):
        assert avis
    assert all(str(tmp_path) not in message for message in [*avis, *contextes])
