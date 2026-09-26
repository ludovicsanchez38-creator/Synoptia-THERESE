"""B-1495 : `include_memory` était déclaré par l'API du chat et lu nulle
part. La mémoire partait avec chaque message, même quand l'appelant
demandait de l'exclure, et le test qui devait le prouver n'affirmait rien.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True])
@pytest.mark.parametrize("include_memory", [False, True])
async def test_la_memoire_ne_part_que_si_elle_est_demandee(
    client: AsyncClient, monkeypatch, stream: bool, include_memory: bool
):
    from app.routers import chat

    appels: list[str] = []

    async def espion(message, *args, **kwargs):
        appels.append(message)
        return ""

    monkeypatch.setattr(chat, "_get_memory_context", espion)
    reponse = await client.post("/api/chat/send", json={
        "message": "Où en est le devis de Julien ?",
        "conversation_id": None,
        "include_memory": include_memory,
        "stream": stream,
    })
    assert reponse.status_code == 200, reponse.text[:200]
    assert bool(appels) is include_memory
