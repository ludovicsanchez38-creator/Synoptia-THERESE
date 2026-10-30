"""Huitième tour : une origine « inconnue » ne se blanchit pas par une écriture.

Reproduction exacte de la relecture 7 (constat 1) : une ancienne conversation
ou une ancienne fiche « inconnue » cite « Maison Ambre » ; avec l'accord
documents, une tâche était créée, puis relue par `list_tasks` après retrait de
l'accord et transmise sous le seul accord « llm ». Transport HTTPX en mémoire,
adaptateur OpenAI réel, aucun envoi réseau.
"""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from app.models.database import get_sync_session
from app.models.entities import Conversation, MemoryCard, Message, Task
from app.services.consentements import enregistrer_accord
from sqlmodel import select

from tests.test_t4_5_chemins_differes import texte_sse
from tests.test_t4_7_rfc import appel_outil, evenements, prefixe, preparer

EXTRAIT = "Maison Ambre"


def _transport(envois):
    async def transport(req):
        corps = json.loads(req.content)
        envois.append(req.content.decode())
        dernier = corps["messages"][-1]
        contenu = dernier.get("content") if isinstance(dernier.get("content"), str) else ""
        if dernier["role"] == "tool":
            texte = texte_sse("Voilà.")
        elif "Crée une tâche" in contenu:
            texte = appel_outil("create_task", {"title": f"Relance {EXTRAIT}"})
        elif "mes tâches" in contenu:
            texte = appel_outil("list_tasks", {})
        else:
            texte = texte_sse("Réponse ordinaire.")
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=texte)
    return transport


def _donnees_anterieures(origine: str) -> str:
    """Données antérieures à la mise à jour : aucune trace de provenance."""
    with get_sync_session() as s:
        conv = Conversation(title="Ancienne conversation")
        s.add(conv)
        s.commit()
        s.refresh(conv)
        if origine == "ancienne_conversation":
            s.add(Message(conversation_id=conv.id, role="user", content="Résume le contrat."))
            s.add(Message(conversation_id=conv.id, role="assistant",
                          content=f"Le contrat de {EXTRAIT} prévoit une relance le 12."))
        else:
            s.add(MemoryCard(kind="preference", subject="relance", title=f"Relances {EXTRAIT}",
                             content=f"Relancer {EXTRAIT} le 12", dedup_key="fiche-ancienne",
                             provenance_documents="inconnue"))
        s.commit()
        return conv.id


@pytest.mark.parametrize("origine", ["ancienne_conversation", "ancienne_fiche"])
async def test_inconnue_ne_se_blanchit_pas_par_une_tache(client, monkeypatch, origine):
    enregistrer_accord("llm", "openai", True, "3", ["memory_cards_r2_v1"])
    enregistrer_accord("documents", "openai", True, "3", ["memory_cards_r2_v1"])
    envois: list[str] = []
    async with httpx.AsyncClient(transport=httpx.MockTransport(_transport(envois))) as http:
        preparer(monkeypatch, http)
        cid = _donnees_anterieures(origine)
        r = await client.post("/api/chat/send", json={"message": "Crée une tâche pour la relance du 12.",
                                                       "conversation_id": cid, "include_memory": True, "stream": True})
        cartes = [e["confirmation"] for e in evenements(r) if e.get("type") == "confirmation_required"]
        assert cartes, r.text[-600:]
        assert cartes[0]["arguments"].get("_provenance_documents") == "inconnue"
        conf = await client.post("/api/chat/confirm-tool", json={"confirmation_id": cartes[0]["confirmation_id"],
                                                                  "approved": True})
        # Rien n'est écrit : la copie survivrait au retrait de l'accord.
        assert conf.json().get("status") == "refused", conf.json()
        resultat = conf.json()["result"]
        assert "origine n’est pas vérifiable" in resultat and "Rien n’a été enregistré" in resultat
        assert "nouvelle conversation" in resultat and "formulaire" in resultat
        with get_sync_session() as s:
            assert s.exec(select(Task)).all() == []
        # L'utilisateur retire ensuite son accord « documents ».
        enregistrer_accord("documents", "openai", False, "3", [])
        avant = len(envois)
        await client.post("/api/chat/send", json={"message": "Quelles sont mes tâches ?", "include_memory": False,
                                                   "stream": True})
        assert len(envois) > avant
        assert not any(EXTRAIT in e for e in envois[avant:])


async def test_ancienne_conversation_sans_accord_documents_cree_la_tache(client, monkeypatch):
    """Témoin : sans accord, l'historique incertain est retiré ; la demande seule suffit."""
    enregistrer_accord("llm", "openai", True, "3", ["memory_cards_r2_v1"])
    envois: list[str] = []
    async with httpx.AsyncClient(transport=httpx.MockTransport(_transport(envois))) as http:
        preparer(monkeypatch, http)
        cid = _donnees_anterieures("ancienne_conversation")
        r = await client.post("/api/chat/send", json={"message": "Crée une tâche pour la relance du 12.",
                                                       "conversation_id": cid, "include_memory": False, "stream": True})
        # Le premier envoi ne porte que la demande : l'ancien échange est retiré.
        # (Le faux modèle écrit lui-même « Maison Ambre » dans son appel d'outil.)
        assert EXTRAIT not in envois[0] and "Résume le contrat" not in envois[0]
        carte = next(e["confirmation"] for e in evenements(r) if e.get("type") == "confirmation_required")
        assert carte["arguments"].get("_provenance_documents") == "sans_document"
        conf = await client.post("/api/chat/confirm-tool", json={"confirmation_id": carte["confirmation_id"],
                                                                  "approved": True})
        assert conf.json().get("status") == "executed", conf.json()


async def test_commande_rfc_d_origine_inconnue_refusee_meme_avec_accord(client, monkeypatch):
    from app.routers import commands_v3

    enregistrer_accord("llm", "openai", True, "3", ["memory_cards_r2_v1"])
    enregistrer_accord("documents", "openai", True, "3", ["memory_cards_r2_v1"])
    with get_sync_session() as s:
        conv = Conversation(title="RFC fictif")
        s.add(conv)
        s.commit()
        s.refresh(conv)
        s.add(Message(conversation_id=conv.id, role="user", content=prefixe("Une commande de relance."),
                      extra_data=json.dumps({"provenance_documents": "sans_document"})))
        reponse = Message(conversation_id=conv.id, role="assistant", content=f"Relancer {EXTRAIT}.",
                          extra_data=json.dumps({"provenance_documents": "inconnue"}))
        s.add(reponse)
        s.commit()
        source = reponse.id
    registre = SimpleNamespace(create_user_command=AsyncMock(return_value=SimpleNamespace()))
    monkeypatch.setattr(commands_v3, "get_command_registry", lambda: registre)
    async with httpx.AsyncClient(transport=httpx.MockTransport(_transport([]))) as http:
        preparer(monkeypatch, http)  # fournisseur configuré : l'accord documents est lisible
        r = await client.post("/api/v3/commands/user", json={"name": "relance", "prompt_template": f"Relancer {EXTRAIT}.",
                                                              "rfc_source_ids": [source]})
    # Rien n'est enregistré, même avec l'accord documents.
    registre.create_user_command.assert_not_called()
    assert r.status_code == 409, r.text
    assert "origine n’est pas vérifiable" in r.text
    assert "Cette commande reprend un document" not in r.text


@pytest.mark.parametrize("flux", [False, True])
async def test_reponse_issue_d_une_fiche_documentaire_reste_filtree(client, monkeypatch, flux):
    """Témoin de la relecture 7 : `memory_used` ne prouve plus rien seul, la fiche « documents » si."""
    enregistrer_accord("llm", "openai", True, "3", ["memory_cards_r2_v1"])
    enregistrer_accord("documents", "openai", True, "3", ["memory_cards_r2_v1"])
    envois: list[str] = []

    async def transport(req):
        envois.append(req.content.decode())
        texte = f"Pour {EXTRAIT}, je propose un devis court." if len(envois) == 1 else "Réponse ordinaire."
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=texte_sse(texte))

    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as http:
        preparer(monkeypatch, http)
        with get_sync_session() as s:
            s.add(MemoryCard(kind="preference", subject="devis", title=f"Devis pour {EXTRAIT}",
                             content="Je préfère des devis courts", dedup_key="fiche-doc",
                             provenance_documents="documents"))
            s.commit()
        await client.post("/api/chat/send", json={"message": "Bonjour, préparons un devis.", "include_memory": True,
                                                   "stream": flux})
        assert EXTRAIT in envois[0]
        with get_sync_session() as s:
            rep = s.exec(select(Message).where(Message.role == "assistant")).all()[-1]
            assert json.loads(rep.extra_data or "{}").get("provenance_documents") == "documents"
            conv = rep.conversation_id
        enregistrer_accord("documents", "openai", False, "3", [])
        avant = len(envois)
        await client.post("/api/chat/send", json={"message": "Continue.", "conversation_id": conv,
                                                   "include_memory": False, "stream": flux})
        assert not any(EXTRAIT in e for e in envois[avant:])
