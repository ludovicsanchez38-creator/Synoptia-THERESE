"""Huitième tour : mini-chat RFC sans mémoire et références disparues.

Réserves 2 et 3 de la relecture 7. Transport HTTPX en mémoire, adaptateur
OpenAI réel, aucun envoi réseau.
"""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
from app.services.consentements import enregistrer_accord

from tests.test_t4_5_chemins_differes import texte_sse
from tests.test_t4_7_rfc import evenements, prefixe, preparer


async def _echanges(client, envois, n=2):
    """Deux tours RFC réussis ; rend les identifiants des réponses et des conversations."""
    reponses, conversations = [], []
    for tour in range(n):
        payload = {"message": prefixe(f"Précision {tour}."), "stream": True, "disable_tools": True}
        if reponses:
            payload["rfc_source_ids"] = list(reponses)
        fin = next(e for e in evenements(await client.post("/api/chat/send", json=payload)) if e.get("type") == "done")
        reponses.append(fin["message_id"])
        conversations.append(fin["conversation_id"])
    return reponses, conversations


def _transport(envois):
    async def transport(req):
        envois.append(req.content.decode())
        corps = req.content.decode()
        texte = (json.dumps({"name": "relance", "prompt_template": "Relance {{client}}."})
                 if "format JSON" in corps else f"Réponse numéro {len(envois)}.")
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=texte_sse(texte))
    return transport


async def test_reference_supprimee_ne_bloque_plus_le_mini_chat(client, monkeypatch):
    enregistrer_accord("llm", "openai", True, "3", [])
    envois: list[str] = []
    async with httpx.AsyncClient(transport=httpx.MockTransport(_transport(envois))) as http:
        preparer(monkeypatch, http)
        reponses, conversations = await _echanges(client, envois)
        # L'utilisateur supprime la première conversation RFC depuis l'historique.
        assert (await client.delete(f"/api/chat/conversations/{conversations[0]}")).status_code == 200
        avant = len(envois)
        r = await client.post("/api/chat/send", json={"message": prefixe("Suite."), "stream": True,
                                                       "disable_tools": True, "rfc_source_ids": reponses})
        ev = evenements(r)
        fin = next((e for e in ev if e.get("type") == "done"), None)
        assert fin and fin.get("message_id"), r.text[-400:]
        # La référence disparue est signalée pour que l'interface la retire ; rien n'en part.
        assert fin.get("rfc_sources_absentes") == [reponses[0]]
        assert "Précision 0" not in envois[avant] and "Précision 1" in envois[avant]


async def test_capture_ignore_une_reference_supprimee_et_la_signale(client, monkeypatch):
    enregistrer_accord("llm", "openai", True, "3", [])
    envois: list[str] = []
    async with httpx.AsyncClient(transport=httpx.MockTransport(_transport(envois))) as http:
        preparer(monkeypatch, http)
        reponses, conversations = await _echanges(client, envois)
        await client.delete(f"/api/chat/conversations/{conversations[0]}")
        r = await client.post("/api/v3/commands/generate-template",
                              json={"brief": "Crée une commande.", "rfc_source_ids": reponses})
        assert r.status_code == 200, r.text
        assert r.json()["rfc_sources_absentes"] == [reponses[0]]
        assert "Précision 0" not in envois[-1]
        await client.delete(f"/api/chat/conversations/{conversations[1]}")
        r = await client.post("/api/v3/commands/generate-template",
                              json={"brief": "Crée une commande.", "rfc_source_ids": reponses})
        assert r.status_code == 409 and "à la main" in r.text


async def test_sauvegarde_avec_reference_supprimee_dit_comment_repartir(client, monkeypatch):
    from app.routers import commands_v3

    enregistrer_accord("llm", "openai", True, "3", [])
    envois: list[str] = []
    registre = SimpleNamespace(create_user_command=AsyncMock(return_value=SimpleNamespace()))
    async with httpx.AsyncClient(transport=httpx.MockTransport(_transport(envois))) as http:
        preparer(monkeypatch, http)
        reponses, conversations = await _echanges(client, envois)
        await client.delete(f"/api/chat/conversations/{conversations[1]}")
        monkeypatch.setattr(commands_v3, "get_command_registry", lambda: registre)
        r = await client.post("/api/v3/commands/user", json={"name": "relance", "prompt_template": "Relance {{client}}.",
                                                              "rfc_source_ids": reponses})
        registre.create_user_command.assert_not_called()
        assert r.status_code == 409
        assert "supprimé" in r.text and "Capturer" in r.text
