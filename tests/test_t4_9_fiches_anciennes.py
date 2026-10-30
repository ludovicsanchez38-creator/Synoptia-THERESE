"""Neuvième tour : les anciennes fiches ne bloquent plus l'usage ordinaire.

Reproduction exacte de la relecture 8 (constat 1) : conversation neuve,
mémoire active par défaut, une ancienne préférence migrée « inconnue ».
L'invariant ne bouge pas : rien d'origine documentaire ou inconnue ne part
sans accord ni après retrait. Transport HTTPX en mémoire, adaptateur OpenAI
réel, aucun envoi réseau.
"""

import json

import httpx
import pytest
from app.models.database import get_sync_session
from app.models.entities import MemoryCard, Task
from app.services.consentements import enregistrer_accord
from app.services.memory_cards import normaliser
from sqlmodel import select

from tests.test_t4_5_chemins_differes import texte_sse
from tests.test_t4_7_rfc import appel_outil, evenements, preparer


def transport_factory(envois):
    async def transport(req):
        corps = json.loads(req.content)
        envois.append(req.content.decode())
        dernier = corps["messages"][-1]
        contenu = dernier.get("content") if isinstance(dernier.get("content"), str) else ""
        if dernier["role"] == "tool":
            texte = texte_sse("Voilà.")
        elif "Crée une tâche" in contenu:
            texte = appel_outil("create_task", {"title": "Appeler Paul"})
        else:
            texte = texte_sse("Réponse ordinaire.")
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=texte)
    return transport


def ancienne_fiche(kind="preference", provenance="inconnue", title="Devis courts",
                   content="Je préfère des devis courts"):
    with get_sync_session() as s:
        fiche = MemoryCard(kind=kind, subject=normaliser("devis"), title=title, content=content,
                           dedup_key=f"ancienne-{kind}-{provenance}-{title}", provenance_documents=provenance,
                           search_text=normaliser(f"{title} {content}"))
        s.add(fiche)
        s.commit()
        return fiche.id


@pytest.mark.parametrize("fiche", ["aucune", "preference_inconnue", "fait_inconnue", "preference_sans_document",
                                   "correction_inconnue"])
async def test_tache_dans_une_conversation_neuve(client, monkeypatch, fiche):
    """Reproduction de la relecture 8 : accords llm et documents, demande sans rapport avec la fiche."""
    enregistrer_accord("llm", "openai", True, "3", ["memory_cards_r2_v1"])
    enregistrer_accord("documents", "openai", True, "3", ["memory_cards_r2_v1"])
    envois: list[str] = []
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport_factory(envois))) as http:
        preparer(monkeypatch, http)
        if fiche != "aucune":
            kind, prov = fiche.split("_", 1)
            ancienne_fiche(kind, prov)
        r = await client.post("/api/chat/send", json={"message": "Crée une tâche : appeler Paul demain.", "stream": True})
        cartes = [e["confirmation"] for e in evenements(r) if e.get("type") == "confirmation_required"]
        assert cartes, r.text[-500:]
        conf = await client.post("/api/chat/confirm-tool", json={"confirmation_id": cartes[0]["confirmation_id"],
                                                                  "approved": True})
        assert conf.json().get("status") == "executed", conf.json()


@pytest.mark.parametrize("fiche", ["preference", "fait", "correction"])
async def test_message_ordinaire_avec_le_seul_accord_llm(client, monkeypatch, fiche):
    """Reproduction de la relecture 8 : l'accord de l'accueil suffit pour une question sans rapport."""
    enregistrer_accord("llm", "openai", True, "3", ["memory_cards_r2_v1"])
    envois: list[str] = []
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport_factory(envois))) as http:
        preparer(monkeypatch, http)
        ancienne_fiche(fiche)
        r = await client.post("/api/chat/send", json={"message": "Quelle est la capitale de l’Italie ?", "stream": True})
        assert any(e.get("type") == "done" for e in evenements(r)), r.text[-400:]
        assert len(envois) == 1
        assert "devis courts" not in envois[0].lower()


@pytest.mark.parametrize("flux", [True, False])
async def test_fiche_concernee_sans_accord_retiree_avec_un_avis(client, monkeypatch, flux):
    """La fiche ne part pas, le reste du message part, et la réponse le dit."""
    enregistrer_accord("llm", "openai", True, "3", ["memory_cards_r2_v1"])
    envois: list[str] = []
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport_factory(envois))) as http:
        preparer(monkeypatch, http)
        ancienne_fiche(title="Devis Maison Ambre", content="Devis courts pour Maison Ambre")
        r = await client.post("/api/chat/send", json={"message": "Prépare un devis.", "stream": flux})
        assert len(envois) == 1
        assert "Maison Ambre" not in envois[0]
        texte = "".join(e.get("content") or "" for e in evenements(r) if e.get("type") == "text") if flux \
            else r.json()["content"]
        assert "n’a pas été transmise" in texte and "Mémoire" in texte
        assert "Maison Ambre" not in texte


async def test_fiche_concernee_avec_accord_part_et_ferme_les_ecritures(client, monkeypatch):
    """Témoin de l'invariant : avec l'accord, la fiche part ; la création du même tour reste fermée."""
    enregistrer_accord("llm", "openai", True, "3", ["memory_cards_r2_v1"])
    enregistrer_accord("documents", "openai", True, "3", ["memory_cards_r2_v1"])
    envois: list[str] = []
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport_factory(envois))) as http:
        preparer(monkeypatch, http)
        ancienne_fiche(title="Relances Paul", content="Appeler Paul avant chaque devis")
        r = await client.post("/api/chat/send", json={"message": "Crée une tâche : appeler Paul demain.", "stream": True})
        assert "Appeler Paul avant chaque devis" in envois[0]
        carte = next(e["confirmation"] for e in evenements(r) if e.get("type") == "confirmation_required")
        assert carte["arguments"]["_provenance_documents"] == "inconnue"
        conf = await client.post("/api/chat/confirm-tool", json={"confirmation_id": carte["confirmation_id"],
                                                                  "approved": True})
        assert conf.json()["status"] == "refused"
        assert "Mémoire" in conf.json()["result"]
        with get_sync_session() as s:
            assert s.exec(select(Task)).all() == []


async def test_attestation_rend_une_ancienne_fiche_a_l_utilisateur(client, monkeypatch):
    enregistrer_accord("llm", "openai", True, "3", ["memory_cards_r2_v1"])
    identifiant = ancienne_fiche()
    # L'écran Mémoire montre l'origine et sait filtrer les fiches à confirmer.
    page = (await client.get("/api/memory/cards", params={"provenance": "inconnue"})).json()
    assert [f["id"] for f in page["items"]] == [identifiant]
    assert page["items"][0]["provenance_documents"] == "inconnue"
    assert (await client.get("/api/memory/cards", params={"provenance": "sans_document"})).json()["items"] == []
    r = await client.patch(f"/api/memory/cards/{identifiant}", json={"version": 1, "atteste_par_utilisateur": True})
    assert r.status_code == 200, r.text
    assert r.json()["provenance_documents"] == "sans_document"
    assert r.json()["title"] == "Devis courts" and r.json()["content"] == "Je préfère des devis courts"
    envois: list[str] = []
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport_factory(envois))) as http:
        preparer(monkeypatch, http)
        # Préférence attestée : de nouveau retenue à chaque message, sous l'accord « llm ».
        await client.post("/api/chat/send", json={"message": "Quelle est la capitale de l’Italie ?", "stream": True})
        assert "Je préfère des devis courts" in envois[0]


async def test_attestation_refusee_pour_une_fiche_issue_d_un_document(client):
    identifiant = ancienne_fiche(provenance="documents")
    r = await client.patch(f"/api/memory/cards/{identifiant}", json={"version": 1, "atteste_par_utilisateur": True})
    assert r.status_code == 409, r.text
    assert "réécris" in r.text
    with get_sync_session() as s:
        assert s.get(MemoryCard, identifiant).provenance_documents == "documents"


async def test_attestation_reservee_a_l_ecran(client, monkeypatch):
    """Le modèle ne peut pas attester à la place de l'utilisateur."""
    from app.services import memory_card_tools

    identifiant = ancienne_fiche()
    resultat = await memory_card_tools.executer_outil(
        {"id": identifiant, "version": 1, "kind": "preference", "subject": "devis", "title": "Devis courts",
         "content": "Je préfère des devis courts", "atteste_par_utilisateur": True},
        scope="global", scope_id=None, conversation_id="inexistante", contient_documents=False)
    assert resultat["success"] is False
    with get_sync_session() as s:
        assert s.get(MemoryCard, identifiant).provenance_documents == "inconnue"
