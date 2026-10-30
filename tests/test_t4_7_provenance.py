"""Septième tour : origine inconnue et document avéré (constat 4 de la relecture 6).

Relecture 6 de la branche confidentialité ; transport HTTPX en mémoire,
adaptateur OpenAI réel, aucun envoi réseau.
"""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from app.models.database import get_sync_session
from app.models.entities import Conversation, MemoryCard, Message
from app.services.consentements import enregistrer_accord
from sqlmodel import select

from tests.test_t4_5_chemins_differes import texte_sse
from tests.test_t4_7_rfc import appel_outil, evenements, prefixe, preparer, provenance_en_base

# ---------------------------------------------------------------------------
# Bloquant 4 : une fiche sans document ou une ancienne conversation ne ferment
# pas les créations ; une origine documentaire avérée les ferme toujours.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("meme_conversation", [True, False])
async def test_tache_apres_usage_d_une_fiche_sans_document(client, monkeypatch, meme_conversation):
    enregistrer_accord("llm", "openai", True, "3", ["memory_cards_r2_v1"])
    enregistrer_accord("documents", "openai", True, "3", ["memory_cards_r2_v1"])

    async def transport(req):
        corps = json.loads(req.content)
        dernier = corps["messages"][-1]
        contenu = dernier.get("content") if isinstance(dernier.get("content"), str) else json.dumps(dernier.get("content"))
        if dernier["role"] == "tool":
            texte = texte_sse("C'est noté.")
        elif "retiens" in contenu.lower():
            texte = appel_outil("upsert_memory_card", {"kind": "preference", "subject": "devis", "title": "Devis courts",
                                                      "content": "Je préfère des devis courts"})
        elif "tâche" in contenu:
            texte = appel_outil("create_task", {"title": "Appeler Paul"})
        else:
            texte = texte_sse("Préparons un devis court.")
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=texte)

    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as http:
        preparer(monkeypatch, http)
        await client.post("/api/chat/send", json={"message": "Retiens ma préférence : je préfère des devis courts.",
                                                   "include_memory": True, "stream": True})
        with get_sync_session() as s:
            carte = s.exec(select(MemoryCard)).one()
            assert carte.provenance_documents == "sans_document"
            conv = carte.conversation_id
        r2 = await client.post("/api/chat/send", json={"message": "Bonjour, préparons un devis.", "conversation_id": conv,
                                                        "include_memory": True, "stream": True})
        fin = next(e for e in evenements(r2) if e.get("type") == "done")
        assert fin["memory_used"], "la fiche doit avoir servi"
        assert provenance_en_base(fin["message_id"]) == "sans_document"
        payload = {"message": "Crée une tâche : appeler Paul demain.", "stream": True}
        if meme_conversation:
            payload["conversation_id"] = conv
        ev = evenements(await client.post("/api/chat/send", json=payload))
        carte_conf = next(e["confirmation"] for e in ev if e.get("type") == "confirmation_required")
        conf = await client.post("/api/chat/confirm-tool", json={"confirmation_id": carte_conf["confirmation_id"],
                                                                  "approved": True})
        assert conf.json().get("status") == "executed", conf.json()


async def test_commande_rfc_avec_fiche_sans_document(client, monkeypatch):
    from app.routers import commands_v3

    enregistrer_accord("llm", "openai", True, "3", ["memory_cards_r2_v1"])
    enregistrer_accord("documents", "openai", True, "3", ["memory_cards_r2_v1"])

    async def transport(req):
        corps = json.loads(req.content)
        dernier = corps["messages"][-1]
        contenu = dernier.get("content") if isinstance(dernier.get("content"), str) else ""
        if dernier["role"] != "tool" and contenu.startswith("Retiens"):
            texte = appel_outil("upsert_memory_card", {"kind": "preference", "subject": "devis", "title": "Devis courts",
                                                      "content": "Je préfère des devis courts"})
        else:
            texte = texte_sse("Quelle information variable veux-tu demander ?")
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=texte)

    registre = SimpleNamespace(create_user_command=AsyncMock(return_value=SimpleNamespace()))
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as http:
        preparer(monkeypatch, http)
        await client.post("/api/chat/send", json={"message": "Retiens ma préférence : je préfère des devis courts.",
                                                   "include_memory": True, "stream": True})
        r = await client.post("/api/chat/send", json={"message": prefixe("Je veux une commande pour préparer des devis."),
                                                       "stream": True, "disable_tools": True})
        fin = next(e for e in evenements(r) if e.get("type") == "done")
        assert fin["memory_used"]
        monkeypatch.setattr(commands_v3, "get_command_registry", lambda: registre)
        sauvegarde = await client.post("/api/v3/commands/user", json={
            "name": "devis-relecture", "prompt_template": "Prépare un devis pour {{client}}.",
            "rfc_source_ids": [fin["message_id"]]})
        assert sauvegarde.status_code != 409, sauvegarde.text
        registre.create_user_command.assert_awaited_once()


def _conversation(provenance: str | None) -> str:
    with get_sync_session() as s:
        conv = Conversation(title="Ancienne conversation")
        s.add(conv)
        s.commit()
        s.refresh(conv)
        extra = None if provenance is None else json.dumps({"provenance_documents": provenance})
        s.add(Message(conversation_id=conv.id, role="user", content="Bonjour", extra_data=extra))
        s.add(Message(conversation_id=conv.id, role="assistant", content="Bonjour, que puis-je faire ?", extra_data=extra))
        s.commit()
        return conv.id


async def _creer_tache(client, monkeypatch, http_transport, conversation_id, retirer_avant_confirmation=False):
    async with httpx.AsyncClient(transport=httpx.MockTransport(http_transport)) as http:
        preparer(monkeypatch, http)
        r = await client.post("/api/chat/send", json={"message": "Crée une tâche : appeler Paul demain.",
                                                       "conversation_id": conversation_id, "stream": True})
        carte = next(e["confirmation"] for e in evenements(r) if e.get("type") == "confirmation_required")
        if retirer_avant_confirmation:
            enregistrer_accord("documents", "openai", False, "3", [])
        conf = await client.post("/api/chat/confirm-tool", json={"confirmation_id": carte["confirmation_id"],
                                                                  "approved": True})
        return conf.json()


async def _transport_tache(req):
    corps = json.loads(req.content)
    dernier = corps["messages"][-1]
    contenu = dernier.get("content") if isinstance(dernier.get("content"), str) else ""
    texte = appel_outil("create_task", {"title": "Appeler Paul"}) if dernier["role"] != "tool" and "tâche" in contenu \
        else texte_sse("Je te propose la tâche.")
    return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=texte)


async def test_tache_dans_une_conversation_anterieure(client, monkeypatch):
    """Tour 8 (relecture 7, constat 1) : avec l'accord documents, l'ancien
    historique part ; la carte est « inconnue » et l'écriture reste fermée,
    sinon sa copie survivrait au retrait de l'accord. Le refus dit pourquoi et
    propose les sorties (voir aussi tests/test_t4_8_inconnue.py, où l'écriture
    passe sans accord, l'historique incertain étant alors retiré)."""
    from app.models.entities import Task

    enregistrer_accord("llm", "openai", True, "3", ["memory_cards_r2_v1"])
    enregistrer_accord("documents", "openai", True, "3", ["memory_cards_r2_v1"])
    resultat = await _creer_tache(client, monkeypatch, _transport_tache, _conversation(None))
    assert resultat.get("status") == "refused", resultat
    assert "origine n’est pas vérifiable" in resultat["result"] and "nouvelle conversation" in resultat["result"]
    with get_sync_session() as s:
        assert s.exec(select(Task)).all() == []


async def test_conversation_anterieure_retrait_avant_confirmation(client, monkeypatch):
    enregistrer_accord("llm", "openai", True, "3", ["memory_cards_r2_v1"])
    enregistrer_accord("documents", "openai", True, "3", ["memory_cards_r2_v1"])
    resultat = await _creer_tache(client, monkeypatch, _transport_tache, _conversation(None),
                                  retirer_avant_confirmation=True)
    assert resultat.get("status") == "refused"
    assert "origine" in resultat["result"] and "documents" in resultat["result"]


async def test_conversation_documentaire_averee_reste_fermee(client, monkeypatch):
    enregistrer_accord("llm", "openai", True, "3", ["memory_cards_r2_v1"])
    enregistrer_accord("documents", "openai", True, "3", ["memory_cards_r2_v1"])
    resultat = await _creer_tache(client, monkeypatch, _transport_tache, _conversation("documents"))
    assert resultat.get("status") == "refused"
    assert "document" in resultat["result"]
