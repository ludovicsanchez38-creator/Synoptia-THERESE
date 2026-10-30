"""Dixième tour : réserves 1 et 2 de la relecture 9, avant publication.

Reproductions exactes de la relecture 9 : ancienne préférence « inconnue »
envoyée avec l'accord documents (la suite de la conversation reste fermée,
mais avec la vraie cause), et ancienne préférence « vouvoie-moi » ignorée sans
avis. Transport HTTPX en mémoire, adaptateur OpenAI réel, aucun envoi réseau.
"""

import json

import httpx
import pytest
from app.models.database import get_sync_session
from app.models.entities import MemoryCard, Message, Task
from app.services.consentements import enregistrer_accord
from sqlmodel import select

from tests.test_t4_5_chemins_differes import texte_sse
from tests.test_t4_7_rfc import appel_outil, evenements, preparer


def transport_factory(envois, outil=None):
    async def transport(req):
        corps = json.loads(req.content)
        envois.append(req.content.decode())
        dernier = corps["messages"][-1]
        contenu = dernier.get("content") if isinstance(dernier.get("content"), str) else ""
        if dernier["role"] == "tool":
            texte = texte_sse("Voilà.")
        elif "Crée une tâche" in contenu:
            texte = appel_outil("create_task", {"title": "Relancer Paul"})
        elif outil and "retiens" in contenu.lower():
            texte = appel_outil("upsert_memory_card", outil)
        else:
            texte = texte_sse("Réponse ordinaire.")
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=texte)
    return transport


def fiche(**kw):
    base = dict(kind="preference", subject="devis", title="Devis courts", content="Je préfère des devis courts",
                dedup_key="ancienne", provenance_documents="inconnue")
    base.update(kw)
    with get_sync_session() as s:
        carte = MemoryCard(**base)
        s.add(carte)
        s.commit()
        return carte.id


def textes(r):
    return "".join(e.get("content") or "" for e in evenements(r) if e.get("type") == "text")


async def _tache(client, conv=None):
    payload = {"message": "Crée une tâche : relancer Paul demain.", "stream": True}
    if conv:
        payload["conversation_id"] = conv
    r = await client.post("/api/chat/send", json=payload)
    carte = next(e["confirmation"] for e in evenements(r) if e.get("type") == "confirmation_required")
    conf = await client.post("/api/chat/confirm-tool", json={"confirmation_id": carte["confirmation_id"], "approved": True})
    return carte["arguments"].get("_provenance_documents"), conf.json()


async def test_fiche_inconnue_ferme_la_suite_avec_la_vraie_cause(client, monkeypatch):
    """Reproduction de la relecture 9 (réserve 1), accords llm et documents."""
    enregistrer_accord("llm", "openai", True, "3", ["memory_cards_r2_v1"])
    enregistrer_accord("documents", "openai", True, "3", ["memory_cards_r2_v1"])
    envois: list[str] = []
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport_factory(envois))) as http:
        preparer(monkeypatch, http)
        fid = fiche()
        r1 = await client.post("/api/chat/send", json={"message": "Prépare un devis pour Paul.", "stream": True})
        conv = next(e for e in evenements(r1) if e.get("type") == "done")["conversation_id"]
        assert "devis courts" in envois[0]
        with get_sync_session() as s:
            rep = s.exec(select(Message).where(Message.role == "assistant")).all()[-1]
            # Aucun document : la réponse est d'origine inconnue, pas documentaire.
            assert json.loads(rep.extra_data or "{}").get("provenance_documents") == "inconnue"
        origine, resultat = await _tache(client, conv)
        assert origine == "inconnue" and resultat["status"] == "refused"
        message = resultat["result"]
        assert "document" not in message
        assert "origine n’est pas vérifiable" in message and "Rien n’a été enregistré" in message
        assert "nouvelle conversation" in message and "formulaire" in message and "Mémoire" in message
        assert "ne rouvre pas cette conversation" in message
        # Attester la fiche ne rouvre pas la conversation : sa réponse reste incertaine.
        with get_sync_session() as s:
            version = s.get(MemoryCard, fid).version
        att = await client.patch(f"/api/memory/cards/{fid}", json={"version": version, "atteste_par_utilisateur": True})
        assert att.status_code == 200
        origine, resultat = await _tache(client, conv)
        assert origine == "inconnue" and resultat["status"] == "refused"
        # La sortie annoncée fonctionne : nouvelle conversation, fiche attestée.
        origine, resultat = await _tache(client)
        assert origine == "sans_document" and resultat["status"] == "executed", resultat
        with get_sync_session() as s:
            assert [t.title for t in s.exec(select(Task)).all()] == ["Relancer Paul"]


async def test_fiche_ecrite_dans_un_tour_incertain_reste_attestable(client, monkeypatch):
    """Même cause : une fiche écrite pendant un tour d'origine inconnue n'est pas « documents »."""
    enregistrer_accord("llm", "openai", True, "3", ["memory_cards_r2_v1"])
    enregistrer_accord("documents", "openai", True, "3", ["memory_cards_r2_v1"])
    envois: list[str] = []
    outil = {"kind": "preference", "subject": "relance", "title": "Relances le lundi",
             "content": "Retiens que je relance le lundi"}
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport_factory(envois, outil))) as http:
        preparer(monkeypatch, http)
        fiche(title="Relances courtes", content="Je préfère des relances courtes")
        await client.post("/api/chat/send", json={"message": "Retiens que je relance le lundi, relances courtes.",
                                                   "stream": True})
        with get_sync_session() as s:
            nouvelle = s.exec(select(MemoryCard).where(MemoryCard.title == "Relances le lundi")).one()
            assert nouvelle.provenance_documents == "inconnue"


@pytest.mark.parametrize("accord_documents", [False, True])
async def test_preference_ancienne_annoncee_une_fois_par_conversation(client, monkeypatch, accord_documents):
    """Reproduction de la relecture 9 (réserve 2) : « vouvoie-moi » ne s'applique plus sans rien dire."""
    enregistrer_accord("llm", "openai", True, "3", ["memory_cards_r2_v1"])
    enregistrer_accord("documents", "openai", accord_documents, "3", ["memory_cards_r2_v1"])
    envois: list[str] = []
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport_factory(envois))) as http:
        preparer(monkeypatch, http)
        fiche(subject="ton", title="Vouvoiement", content="Je préfère que tu me vouvoies", dedup_key="ton")
        r = await client.post("/api/chat/send", json={"message": "Bonjour, quoi de neuf ?", "stream": True})
        avis = textes(r)
        assert "vouvoies" not in envois[-1] and "Vouvoiement" not in envois[-1]
        assert "1 ancienne préférence" in avis and "Mémoire" in avis
        assert "Vouvoiement" not in avis and "vouvoies" not in avis
        conv = next(e for e in evenements(r) if e.get("type") == "done")["conversation_id"]
        r2 = await client.post("/api/chat/send", json={"message": "Et sinon ?", "conversation_id": conv, "stream": True})
        assert "Mémoire" not in textes(r2)
        r3 = await client.post("/api/chat/send", json={"message": "Bonjour à nouveau.", "stream": False})
        assert "1 ancienne préférence" in r3.json()["content"]


async def test_sans_ancienne_fiche_aucun_avis_et_attestee_elle_s_applique(client, monkeypatch):
    enregistrer_accord("llm", "openai", True, "3", ["memory_cards_r2_v1"])
    envois: list[str] = []
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport_factory(envois))) as http:
        preparer(monkeypatch, http)
        r = await client.post("/api/chat/send", json={"message": "Bonjour, quoi de neuf ?", "stream": True})
        assert "Mémoire" not in textes(r)
        fid = fiche(subject="ton", title="Vouvoiement", content="Je préfère que tu me vouvoies", dedup_key="ton")
        await client.patch(f"/api/memory/cards/{fid}", json={"version": 1, "atteste_par_utilisateur": True})
        r = await client.post("/api/chat/send", json={"message": "Bonjour, quoi de neuf ?", "stream": True})
        assert "Mémoire" not in textes(r)
        assert "vouvoies" in envois[-1]
