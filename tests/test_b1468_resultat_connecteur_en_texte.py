"""B-1468 (recette P-146, lot 5, KO-2) : confirmer un outil de connecteur
(MCP) rendait à l'écran l'objet brut du résultat
(`{"content": [{"type": "text", ...}], "structuredContent": {...}}`) ;
l'écran le traitait comme du texte et plantait, puis le tiroir des
conversations plantait à chaque ouverture (message empoisonné en cache).
La route rend le texte de l'outil."""

from types import SimpleNamespace

import app.routers.chat as chat_mod
import pytest
from app.services.tool_confirmations import register_pending


@pytest.mark.asyncio
@pytest.mark.parametrize(("brut", "attendu"), [
    ({"content": [{"type": "text", "text": "Il est 22:41 à Paris."}], "structuredContent": {"heure": "22:41"}},
     "Il est 22:41 à Paris."),
    ({"content": [{"type": "text", "text": "Ligne 1"}, {"type": "image", "data": "..."}, {"type": "text", "text": "Ligne 2"}]},
     "Ligne 1\nLigne 2"),
    ({"heure": "22:41"}, '{"heure": "22:41"}'),
    ("Déjà du texte", "Déjà du texte"),
])
async def test_le_resultat_d_un_connecteur_revient_en_texte(client, monkeypatch, brut, attendu):
    class FauxMCP:
        async def execute_tool_call(self, _nom, _arguments):
            return SimpleNamespace(success=True, result=brut, error=None)

    monkeypatch.setattr(chat_mod, "get_mcp_service", lambda: FauxMCP())
    cid = register_pending("time__get_current_time", {"timezone": "Europe/Paris"})
    reponse = await client.post("/api/chat/confirm-tool", json={"confirmation_id": cid, "approved": True})
    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["result"] == attendu
