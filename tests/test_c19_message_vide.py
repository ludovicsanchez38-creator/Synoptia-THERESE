"""B-1106 : aucun accès au modèle pour un message blanc."""
from unittest.mock import Mock

import pytest
from app.routers import chat


@pytest.mark.parametrize("message", ["", "   \n  "])
@pytest.mark.parametrize("stream", [True, False])
async def test_message_vide_refuse_avant_fournisseur(client, monkeypatch, message, stream):
    fournisseur = Mock(side_effect=RuntimeError("Le fournisseur ne doit pas être appelé"))
    monkeypatch.setattr(chat, "get_llm_service", fournisseur)
    reponse = await client.post("/api/chat/send", json={"message": message, "stream": stream})
    assert reponse.status_code == 400
    assert "Écris un message" in reponse.text
    fournisseur.assert_not_called()
    assert (await client.get("/api/chat/conversations")).json() == []


@pytest.mark.parametrize("message", ["\t", "\r\n", "\u00a0", "\u2003", " \t ", "\n\n",
                                      "\u202f", "\u3000", "\v\f", " \r\n\t\u00a0 "])
async def test_rejeu_blancs(client, monkeypatch, message):
    await test_message_vide_refuse_avant_fournisseur(client, monkeypatch, message, True)
