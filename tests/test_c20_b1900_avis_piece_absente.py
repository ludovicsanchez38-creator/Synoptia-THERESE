"""Une pièce jointe absente est signalée dans la réponse hors flux."""

from unittest.mock import AsyncMock

import pytest
from app.routers import chat

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
