"""B-1448 (recette P-146, lot 3, KO-7) : après la carte de confirmation d'un
document, le chat affichait le retour de l'outil destiné au MODÈLE :
« Document PPTX genere : … L'utilisateur peut l'enregistrer via la carte
affichee sous ce message - ne fournis aucun lien. » La route de confirmation
rend désormais une phrase pour l'utilisatrice, accentuée, sans consigne."""

import app.routers.chat as chat_mod
import pytest
from app.services.tool_confirmations import register_pending
from app.services.workspace_tools import _texte_de_retour_document


@pytest.mark.asyncio
@pytest.mark.parametrize("collecte", [True, False])
async def test_le_document_confirme_s_annonce_a_l_utilisatrice(client, monkeypatch, collecte):
    async def _outil_reel(tool_name, arguments, session, conversation_id=None):
        # Le texte exact que rend generate_document au modèle.
        return _texte_de_retour_document("Offre Atelier Ménard.pptx", "pptx", collecte=collecte)

    monkeypatch.setattr(chat_mod, "execute_workspace_tool", _outil_reel)
    cid = register_pending("generate_document", {"format": "pptx", "content": "Offre"})
    reponse = await client.post("/api/chat/confirm-tool", json={"confirmation_id": cid, "approved": True})
    assert reponse.status_code == 200, reponse.text
    texte = reponse.json()["result"]
    assert texte == "Document PPTX créé : Offre Atelier Ménard.pptx.", texte
