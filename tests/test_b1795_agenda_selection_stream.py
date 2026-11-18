"""La sélection du panneau doit accompagner le flux jusqu'à l'outil d'agenda."""

import json
from datetime import datetime, timedelta

import httpx
import pytest
from app.models.entities import Calendar, CalendarEvent
from app.services import llm, user_profile
from app.services.civil_time import PARIS
from app.services.providers.base import LLMConfig, LLMProvider
from app.services.providers.ollama import OllamaProvider

from tests.test_r2_3_outil import fournisseur  # noqa: F401


@pytest.mark.asyncio
async def test_le_chat_lit_l_agenda_choisi_parmi_plusieurs(
    client, db_session, fournisseur, monkeypatch  # noqa: F811
):
    monkeypatch.setattr(user_profile, "get_cached_profile", lambda: None)
    monkeypatch.setattr(llm, "load_therese_md", lambda: None)
    db_session.add_all([
        Calendar(id="agenda-a", summary="Personnel", provider="local"),
        Calendar(id="agenda-b", summary="Professionnel", provider="local"),
    ])
    debut = (datetime.now(PARIS) + timedelta(days=1)).replace(tzinfo=None)
    db_session.add(CalendarEvent(
        id="rdv-b", calendar_id="agenda-b", summary="Rendez-vous professionnel fictif",
        start_datetime=debut, end_datetime=debut + timedelta(hours=1), status="confirmed",
    ))
    await db_session.commit()

    charges = []

    def recevoir(requete: httpx.Request) -> httpx.Response:
        charges.append(json.loads(requete.content))
        message = (
            {"content": "", "tool_calls": [{"function": {
                "name": "list_calendar_events", "arguments": {"days": 30},
            }}]}
            if len(charges) == 1 else {"content": "Lecture terminée."}
        )
        return httpx.Response(200, text=json.dumps({"message": message, "done": True}) + "\n")

    service = fournisseur[0]
    service.config = LLMConfig(
        LLMProvider.OLLAMA, "modele-fictif", context_window=32768, max_tokens=1024,
    )
    service.config.ollama_show_lu = True
    async with httpx.AsyncClient(transport=httpx.MockTransport(recevoir)) as transport:
        service._provider = OllamaProvider(service.config, transport)
        reponse = await client.post("/api/chat/send", json={
            "message": "Quels sont mes rendez-vous à venir ?", "calendar_id": "agenda-b",
            "include_memory": False, "stream": True,
        })

    assert reponse.status_code == 200
    assert len(charges) == 2, reponse.text
    resultat = next(m["content"] for m in charges[1]["messages"] if m["role"] == "tool")
    assert "Rendez-vous professionnel fictif" in resultat
    assert "Plusieurs agendas" not in resultat
