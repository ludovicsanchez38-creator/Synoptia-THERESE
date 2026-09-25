"""B-1368 (persona Hugo, cycle 13) : une conversation rattachée à un projet
AVANT d'écrire gardait « Nouvelle conversation » en base, et sa date ne
bougeait plus.

Le sélecteur de projet crée la conversation (0 message, titre provisoire) ; le
moteur ne posait le titre que lorsqu'il créait lui-même la conversation au
premier message. Et `updated_at` n'était jamais avancé par un envoi : le tiroir
rangeait la conversation à sa date de création. Le lendemain, Hugo ne la
retrouvait ni par son sujet ni à sa place.
"""

import pytest


class _FauxService:
    config = type("C", (), {"provider": type("P", (), {"value": "ollama"})(), "model": "test"})()

    def prepare_context(self, messages, system_prompt=None, memory_context=None):
        return type("Ctx", (), {"messages": messages, "system_prompt": system_prompt})()

    async def stream_response(self, *args, **kwargs):
        for morceau in ("C'est ", "noté."):
            yield morceau


async def _envoyer(client, monkeypatch, conversation_id: str, message: str):
    from app.routers import chat as chat_router

    monkeypatch.setattr(chat_router, "get_llm_service", lambda: _FauxService())
    reponse = await client.post("/api/chat/send", json={
        "message": message, "conversation_id": conversation_id,
        "include_memory": False, "stream": False,
    })
    assert reponse.status_code == 200, reponse.text


@pytest.mark.asyncio
async def test_le_premier_message_titre_une_conversation_creee_vide(client, monkeypatch):
    creee = (await client.post("/api/chat/conversations", json={"title": "Nouvelle conversation"})).json()

    message = "Orion : on a retenu la variante B pour l'API client, note-le."
    await _envoyer(client, monkeypatch, creee["id"], message)

    relue = (await client.get(f"/api/chat/conversations/{creee['id']}")).json()
    assert relue["title"] == message[:50], "même règle qu'une conversation créée par son premier message"
    assert relue["updated_at"] > creee["updated_at"], "un envoi avance la date de la conversation"


@pytest.mark.asyncio
async def test_un_titre_choisi_n_est_jamais_remplace(client, monkeypatch):
    creee = (await client.post("/api/chat/conversations", json={"title": "Suivi Orion"})).json()

    await _envoyer(client, monkeypatch, creee["id"], "Premier message sur un autre sujet")

    assert (await client.get(f"/api/chat/conversations/{creee['id']}")).json()["title"] == "Suivi Orion"


@pytest.mark.asyncio
async def test_le_second_message_ne_retitre_pas(client, monkeypatch):
    creee = (await client.post("/api/chat/conversations", json={"title": "Nouvelle conversation"})).json()
    await _envoyer(client, monkeypatch, creee["id"], "Veille : comparer Qwen3 et Gemma")
    await _envoyer(client, monkeypatch, creee["id"], "Et ajoute Mistral")

    assert (await client.get(f"/api/chat/conversations/{creee['id']}")).json()["title"] == "Veille : comparer Qwen3 et Gemma"
