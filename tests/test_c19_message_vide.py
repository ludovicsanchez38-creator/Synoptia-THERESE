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


@pytest.mark.parametrize("message", ["{participants}", "{{action: email-pro}} {participants}", "{{action: email-pro}}"])
@pytest.mark.parametrize("stream", [True, False])
async def test_variable_liste_vide_refusee_avant_fournisseur(client, db_session, monkeypatch, stream, message):
    from app.services.variables_service import create_variable

    await create_variable(db_session, "participants", "list", [])
    fournisseur = Mock(side_effect=RuntimeError("Le fournisseur ne doit pas être appelé"))
    monkeypatch.setattr(chat, "get_llm_service", fournisseur)
    reponse = await client.post("/api/chat/send", json={"message": message, "stream": stream})
    assert reponse.status_code == 400
    assert "Écris un message" in reponse.text
    fournisseur.assert_not_called()


@pytest.mark.parametrize("message", ["", "{{action: email-pro}}", "{{action: email-pro}} {participants}"])
@pytest.mark.parametrize("stream", [True, False])
async def test_message_vide_avec_image_valide_accepte(client, db_session, tmp_path, monkeypatch, stream, message):
    import base64
    from unittest.mock import AsyncMock, MagicMock

    from app.services.variables_service import create_variable

    from tests.test_p159_contexte_transmis import _FauxLLM

    await create_variable(db_session, "participants", "list", [])
    image = tmp_path / "photo.png"
    image.write_bytes(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a4VQAAAAASUVORK5CYII="))
    captures = []
    class Modele(_FauxLLM):
        def prepare_context(self, messages, memory_context=None):
            captures.extend(messages)
            return super().prepare_context(messages, memory_context)
    monkeypatch.setattr(chat, "get_llm_service", Modele)
    monkeypatch.setattr(chat, "_extract_entities_background", AsyncMock())
    mcp = MagicMock()
    mcp.get_tools_for_llm.return_value = []
    monkeypatch.setattr(chat, "get_mcp_service", lambda: mcp)
    reponse = await client.post("/api/chat/send", json={"message": message, "stream": stream,
        "file_paths": [str(image)], "include_memory": False, "disable_tools": True})
    assert reponse.status_code == 200, reponse.text
    assert captures and len(captures[-1].images) == 1
    assert captures[-1].content == ""
