"""Onzième tour : les avis système ne sont jamais dans le contenu de la réponse.

Reproduction exacte de la relecture 10 (constat 1) avec un vrai .docx : l'avis
des anciennes préférences entrait dans le texte transmis à la génération de
fichier. Les avis (anciennes préférences, fiche retirée, historique retiré,
anciennes pièces jointes, fenêtre locale, pièces non transmises, commandes non
rejouées) partent dans un événement `notice` distinct, conservé à part dans
`extra_data`, jamais dans le texte, un document, un mail ou un post généré.
"""

import json

import httpx
import pytest
from app.models.database import get_sync_session
from app.models.entities import Conversation, MemoryCard, Message
from app.services.consentements import enregistrer_accord
from sqlmodel import select

from tests.test_t4_5_chemins_differes import texte_sse
from tests.test_t4_7_rfc import evenements, preparer

NOTE = "# Horaires d’été\n\nLe bureau ouvre de 8 h à 16 h."


def fiche(**kw):
    base = dict(kind="preference", subject="ton", title="Vouvoiement", content="Je préfère que tu me vouvoies",
                dedup_key="ancienne", provenance_documents="inconnue")
    base.update(kw)
    with get_sync_session() as s:
        s.add(MemoryCard(**base))
        s.commit()


def transport_texte(texte, envois=None):
    async def transport(req):
        if envois is not None:
            envois.append(req.content.decode())
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=texte_sse(texte))
    return transport


def derniere_reponse():
    with get_sync_session() as s:
        rep = s.exec(select(Message).where(Message.role == "assistant")).all()[-1]
        return rep.content, json.loads(rep.extra_data or "{}")


async def _docx(client, monkeypatch, message, **payload):
    from app.services.skills.registry import get_skills_registry, init_skills
    from docx import Document as Docx

    await init_skills()
    r = await client.post("/api/chat/send", json={"message": message, "skill_id": "docx-pro", "stream": True} | payload)
    ev = evenements(r)
    fichier = next((e.get("skill_file") for e in ev if e.get("type") == "skill_file"), None)
    assert fichier, [e.get("type") for e in ev]
    res = get_skills_registry()._file_cache.get(fichier["file_id"])
    return ev, "\n".join(p.text for p in Docx(str(res.file_path)).paragraphs)


@pytest.mark.parametrize("ancienne", [False, True])
async def test_docx_reel_sans_avis_des_anciennes_preferences(client, monkeypatch, ancienne):
    """Reproduction exacte de la relecture 10 (voie Markdown, vrai générateur Word)."""
    enregistrer_accord("llm", "openai", True, "3", ["memory_cards_r2_v1"])
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport_texte(NOTE))) as http:
        preparer(monkeypatch, http)
        if ancienne:
            fiche()
        ev, texte = await _docx(client, monkeypatch, "Rédige une note sur les horaires d’été.")
        assert "Mémoire" not in texte and "ancienne préférence" not in texte
        assert texte.startswith("Horaires d’été")
        textes = "".join(e.get("content") or "" for e in ev if e.get("type") == "text")
        assert textes == NOTE
        avis = [e["content"] for e in ev if e.get("type") == "notice"]
        contenu, extra = derniere_reponse()
        assert contenu == NOTE
        if ancienne:
            assert len(avis) == 1 and "1 ancienne préférence" in avis[0]
            assert extra.get("avis") == avis
        else:
            assert avis == [] and "avis" not in extra


async def test_docx_reel_sans_avis_de_fiche_retiree(client, monkeypatch):
    enregistrer_accord("llm", "openai", True, "3", ["memory_cards_r2_v1"])
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport_texte(NOTE))) as http:
        preparer(monkeypatch, http)
        fiche(kind="fait", subject="horaires", title="Horaires Maison Ambre",
              content="Horaires d’été de Maison Ambre", provenance_documents="documents")
        ev, texte = await _docx(client, monkeypatch, "Rédige une note sur les horaires d’été.")
        assert "transmise" not in texte and "Maison Ambre" not in texte
        avis = [e["content"] for e in ev if e.get("type") == "notice"]
        assert any("n’a pas été transmise" in a for a in avis)
        assert derniere_reponse()[0] == NOTE


async def test_docx_reel_sans_confirmation_de_directive(client, monkeypatch):
    """Une directive en ligne reste confirmée dans le message, jamais dans le fichier."""
    enregistrer_accord("llm", "openai", True, "3", [])
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport_texte(NOTE))) as http:
        preparer(monkeypatch, http)
        ev, texte = await _docx(client, monkeypatch, "[contact: Paul Ambre] Rédige une note sur les horaires d’été.")
        assert "Paul" not in texte and texte.startswith("Horaires d’été")
        assert "Paul Ambre" in "".join(e.get("content") or "" for e in ev if e.get("type") == "text")


@pytest.mark.parametrize("flux", [True, False])
async def test_avis_d_historique_retire_hors_du_contenu(client, monkeypatch, flux):
    enregistrer_accord("llm", "openai", True, "3", ["memory_cards_r2_v1"])
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport_texte("Réponse ordinaire."))) as http:
        preparer(monkeypatch, http)
        with get_sync_session() as s:
            conv = Conversation(title="Ancienne conversation")
            s.add(conv)
            s.commit()
            s.refresh(conv)
            s.add(Message(conversation_id=conv.id, role="user", content="Résume le contrat."))
            s.add(Message(conversation_id=conv.id, role="assistant", content="Le contrat prévoit une relance."))
            s.commit()
            cid = conv.id
        r = await client.post("/api/chat/send", json={"message": "Bonjour.", "conversation_id": cid,
                                                       "include_memory": False, "stream": flux})
        if flux:
            ev = evenements(r)
            assert "".join(e.get("content") or "" for e in ev if e.get("type") == "text") == "Réponse ordinaire."
            avis = [e["content"] for e in ev if e.get("type") == "notice"]
        else:
            assert r.json()["content"] == "Réponse ordinaire."
            avis = r.json()["avis"]
        assert any("historique" in a for a in avis)
        contenu, extra = derniere_reponse()
        assert contenu == "Réponse ordinaire." and extra.get("avis") == avis


async def test_aucun_avis_dans_une_reponse_texte(client, monkeypatch):
    """Compétence texte (mail, post) : la réponse copiée ne contient que le texte du modèle."""
    enregistrer_accord("llm", "openai", True, "3", ["memory_cards_r2_v1"])
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport_texte("Bonjour Paul,\n\nMerci."))) as http:
        preparer(monkeypatch, http)
        fiche()
        r = await client.post("/api/chat/send", json={"message": "Écris un mail à Paul.", "stream": False})
        assert r.json()["content"] == "Bonjour Paul,\n\nMerci."
        assert any("1 ancienne préférence" in a for a in r.json()["avis"])


async def test_docx_reel_sans_annonce_de_coupe(client, monkeypatch):
    """L'annonce d'une réponse coupée reste dans le message (C18), jamais dans le fichier."""
    from app.routers import chat

    from tests.test_c18_arrets_visibles import _Service

    monkeypatch.setattr(chat, "get_llm_service", lambda: _Service("max_tokens", NOTE))
    ev, texte = await _docx(client, monkeypatch, "Rédige une note sur les horaires d’été.", include_memory=False)
    assert "coupée" not in texte and texte.startswith("Horaires d’été")
    assert "Réponse coupée" in "".join(e.get("content") or "" for e in ev if e.get("type") == "text")
