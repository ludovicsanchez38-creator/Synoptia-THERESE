"""B-1107 : rejet explicite pour l'écran, l'historique et le modèle."""
import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.routers import chat
from app.services.file_parser import MAX_FILE_SIZE_BYTES

from tests.test_p159_contexte_transmis import _FauxLLM


@pytest.mark.parametrize("stream", [True, False])
async def test_piece_trop_grosse_signalee(client, tmp_path, monkeypatch, stream, nom="inventaire-complet.txt"):
    fichier = tmp_path / nom
    with fichier.open("wb") as flux:
        flux.truncate(MAX_FILE_SIZE_BYTES + 1)
    captures = []

    class Modele(_FauxLLM):
        def prepare_context(self, messages, memory_context=None):
            captures.append(memory_context or "")
            return super().prepare_context(messages, memory_context)

    monkeypatch.setattr(chat, "get_llm_service", Modele)
    monkeypatch.setattr(chat, "_extract_entities_background", AsyncMock())
    mcp = MagicMock()
    mcp.get_tools_for_llm.return_value = []
    monkeypatch.setattr(chat, "get_mcp_service", lambda: mcp)
    reponse = await client.post("/api/chat/send", json={
        "message": "Combien de lignes dans mon document ?", "stream": stream,
        "file_paths": [str(fichier)], "include_memory": False, "disable_tools": True,
    })
    assert reponse.status_code == 200
    texte = "".join(json.loads(ligne[6:]).get("content", "") for ligne in reponse.text.splitlines()
                    if ligne.startswith("data: ")) if stream else reponse.json()["content"]
    assert nom in texte and "50 Mo" in texte
    assert captures and nom in captures[-1] and "50 Mo" in captures[-1]
    assert str(tmp_path) not in captures[-1]
    conversations = (await client.get("/api/chat/conversations")).json()
    messages = (await client.get(f"/api/chat/conversations/{conversations[0]['id']}/messages")).json()
    assert any(nom in m["content"] and "50 Mo" in m["content"] for m in messages if m["role"] == "assistant")


@pytest.mark.parametrize("nom", ["stock.txt", "achats.md", "résumé.csv", "devis.docx", "plans.pdf",
                                  "commandes.xlsx", "ventes.txt", "chantier.md", "tarif.csv", "matériaux.pdf"])
async def test_rejeu_pieces(client, tmp_path, monkeypatch, nom):
    await test_piece_trop_grosse_signalee(client, tmp_path, monkeypatch, True, nom)
