"""Septième tour : anciennes fiches, cause nommée et réécriture (réserve 6 de la relecture 6).

Relecture 6 de la branche confidentialité ; transport HTTPX en mémoire,
adaptateur OpenAI réel, aucun envoi réseau.
"""


import httpx
import pytest
from app.models.database import get_sync_session
from app.models.entities import MemoryCard
from app.services.consentements import enregistrer_accord

from tests.test_t4_5_chemins_differes import texte_sse
from tests.test_t4_7_rfc import evenements, preparer

# ---------------------------------------------------------------------------
# Réserve 6 : une ancienne fiche nomme sa cause, et sa réécriture complète la
# rend à l'utilisateur.
# ---------------------------------------------------------------------------


def _fiche_ancienne(reason: str = "") -> str:
    from app.services.memory_cards import normaliser

    with get_sync_session() as s:
        fiche = MemoryCard(kind="preference", subject=normaliser("devis"), title="Maison Ambre",
                           content="Devis Maison Ambre", reason=reason, author="therese",
                           provenance_documents="inconnue", dedup_key="ancienne-fiche")
        s.add(fiche)
        s.commit()
        return fiche.id


@pytest.mark.parametrize("correction, attendue", [
    ({"title": "Devis courts", "content": "Je préfère des devis courts"}, "sans_document"),
    ({"title": "Devis courts"}, "inconnue"),
    ({"title": "Devis courts", "content": "Devis Maison Ambre"}, "inconnue"),
])
async def test_reecriture_manuelle_complete_seulement(client, correction, attendue):
    identifiant = _fiche_ancienne()
    r = await client.patch(f"/api/memory/cards/{identifiant}", json={"version": 1} | correction)
    assert r.status_code == 200, r.text
    with get_sync_session() as s:
        assert s.get(MemoryCard, identifiant).provenance_documents == attendue


async def test_reecriture_garde_une_ancienne_raison(client):
    from app.services import memory_cards

    identifiant = _fiche_ancienne(reason="Vu dans le contrat Maison Ambre")
    await memory_cards.ecrire({"id": identifiant, "version": 1, "title": "Devis courts",
                               "content": "Je préfère des devis courts"})
    with get_sync_session() as s:
        assert s.get(MemoryCard, identifiant).provenance_documents == "inconnue"


async def test_ancienne_fiche_nomme_la_cause_puis_part_apres_reecriture(client, monkeypatch):
    enregistrer_accord("llm", "openai", True, "3", ["memory_cards_r2_v1"])
    identifiant = _fiche_ancienne()
    envois = []

    async def transport(req):
        envois.append(req.content.decode())
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=texte_sse("Réponse ordinaire."))

    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as http:
        preparer(monkeypatch, http)
        ev = evenements(await client.post("/api/chat/send", json={"message": "Bonjour, préparons un devis.",
                                                                   "include_memory": True, "stream": True}))
        assert not envois
        demande = next(e for e in ev if e.get("type") == "memory_consent_required")
        # Le composeur propose l'accord « documents » ou l'envoi sans mémoire.
        assert demande["purpose"] == "documents" and demande["provider"] == "openai"
        assert "fiche mémoire ancienne" in demande["content"] and "Utiliser les fiches mémoire" in demande["content"]
        assert "Maison Ambre" not in demande["content"]
        r = await client.patch(f"/api/memory/cards/{identifiant}", json={
            "version": 1, "title": "Devis courts", "content": "Je préfère des devis courts"})
        assert r.status_code == 200, r.text
        ev = evenements(await client.post("/api/chat/send", json={"message": "Bonjour, préparons un devis.",
                                                                   "include_memory": True, "stream": True}))
        assert any(e.get("type") == "done" for e in ev), ev
        assert len(envois) == 1 and "devis courts" in envois[0]
