"""B-1105 : ne pas recopier le décalage actuel sur une autre saison."""
import os
import sys
import time
from datetime import datetime

import pytest
from app.services import llm, workspace_tools

from tests.test_b1500_outil_agenda_heure_de_paris import _creer, _stocke


@pytest.fixture
def horloge(monkeypatch):
    ancien = os.environ.get("TZ")
    def poser(maintenant, fuseau="Europe/Paris"):
        monkeypatch.setenv("TZ", fuseau)
        time.tzset()
        class Horloge(datetime):
            @classmethod
            def now(cls, tz=None):
                instant = datetime.fromisoformat(maintenant)
                return instant.astimezone(tz) if tz else instant.astimezone().replace(tzinfo=None)
        monkeypatch.setattr(workspace_tools, "datetime", Horloge)
        monkeypatch.setattr(llm, "datetime", Horloge)
    yield poser
    if ancien is None:
        os.environ.pop("TZ", None)
    else:
        os.environ["TZ"] = ancien
    if hasattr(time, "tzset"):
        time.tzset()


@pytest.mark.skipif(sys.platform == "win32", reason="time.tzset absent sous Windows")
def test_invite_et_outil_demandent_heure_murale_a_la_date(horloge):
    horloge("2026-10-23T11:40:00+02:00")
    service = llm.LLMService(llm.LLMConfig(provider=llm.LLMProvider.OLLAMA, model="factice", api_key=None))
    prompt = service._get_system_prompt_with_identity()
    assert "23 octobre 2026, 11:40" in prompt and "UTC+02:00" in prompt
    assert "heure murale du poste à la date du rendez-vous" in prompt
    assert "sans décalage ni Z" in prompt
    outil = workspace_tools.CREATE_CALENDAR_EVENT_TOOL["function"]
    for description in [outil["description"], *(outil["parameters"]["properties"][c]["description"] for c in ("start", "end"))]:
        assert "heure murale du poste à la date du rendez-vous" in description
        assert "sans décalage ni Z" in description


@pytest.mark.skipif(sys.platform == "win32", reason="time.tzset absent sous Windows")
@pytest.mark.parametrize("maintenant,debut,fin,attendu", [
    ("2026-10-23T12:00:00+02:00", "2026-10-30T14:30:00+02:00", "2026-10-30T15:30:00+02:00", "2026-10-30T14:30:00"),
    ("2026-10-30T12:00:00+01:00", "2026-10-23T14:30:00+01:00", "2026-10-23T15:30:00+01:00", "2026-10-23T14:30:00"),
    ("2026-03-20T12:00:00+01:00", "2026-03-30T14:30:00+01:00", "2026-03-30T15:30:00+01:00", "2026-03-30T14:30:00"),
    ("2026-03-30T12:00:00+02:00", "2026-03-20T14:30:00+02:00", "2026-03-20T15:30:00+02:00", "2026-03-20T14:30:00"),
    ("2026-10-23T12:00:00+02:00", "2026-10-30T14:30:00Z", "2026-10-30T15:30:00Z", "2026-10-30T15:30:00"),
    ("2026-10-23T12:00:00+02:00", "2026-10-30T14:30:00", "2026-10-30T15:30:00", "2026-10-30T14:30:00"),
    ("2026-10-23T12:00:00+02:00", "2026-10-30T14:30:00-05:00", "2026-10-30T15:30:00-05:00", "2026-10-30T20:30:00"),
])
async def test_rendez_vous_stocke_a_la_bonne_heure(client, db_session, horloge, maintenant, debut, fin, attendu):
    horloge(maintenant)
    resultat = await _creer(db_session, debut, fin)
    assert not resultat.startswith("Erreur"), resultat
    evenement = await _stocke(db_session)
    assert evenement.start_datetime == datetime.fromisoformat(attendu)
    assert (evenement.end_datetime - evenement.start_datetime).total_seconds() == 3600


@pytest.mark.skipif(sys.platform == "win32", reason="time.tzset absent sous Windows")
async def test_z_reste_absolu_si_le_decalage_courant_est_zero(client, db_session, horloge):
    horloge("2026-03-20T12:00:00+00:00", "Europe/London")
    resultat = await _creer(db_session, "2026-03-30T14:30:00Z", "2026-03-30T15:30:00Z")
    assert not resultat.startswith("Erreur"), resultat
    assert (await _stocke(db_session)).start_datetime == datetime(2026, 3, 30, 16, 30)


@pytest.mark.skipif(sys.platform == "win32", reason="time.tzset absent sous Windows")
@pytest.mark.parametrize("maintenant,debut,fin,attendu,fuseau", [
    ("2026-10-23T12:00:00+02:00", "2026-10-30T14:30:00+02:00", "2026-10-30T15:30:00+02:00", "2026-10-30T14:30:00", "Europe/Paris"),
    ("2026-03-20T12:00:00+01:00", "2026-03-30T14:30:00+01:00", "2026-03-30T15:30:00+01:00", "2026-03-30T14:30:00", "Europe/Paris"),
    ("2026-10-23T12:00:00+02:00", "2026-10-30T14:30:00Z", "2026-10-30T15:30:00Z", "2026-10-30T15:30:00", "Europe/Paris"),
    ("2026-10-23T12:00:00+02:00", "2026-10-30T14:30:00", "2026-10-30T15:30:00", "2026-10-30T14:30:00", "Europe/Paris"),
    ("2026-10-23T12:00:00+02:00", "2026-10-30T14:30:00-05:00", "2026-10-30T15:30:00-05:00", "2026-10-30T20:30:00", "Europe/Paris"),
    ("2026-10-23T12:00:00-04:00", "2026-10-30T10:30:00", "2026-10-30T11:30:00", "2026-10-30T15:30:00", "America/Martinique"),
    ("2026-10-23T12:00:00+01:00", "2026-10-30T14:30:00", "2026-10-30T15:30:00", "2026-10-30T15:30:00", "Europe/London"),
])
async def test_carte_confirmation_et_heure_enregistree_identiques(
    client, db_session, monkeypatch, horloge, maintenant, debut, fin, attendu, fuseau,
):
    import json
    from zoneinfo import ZoneInfo

    from app.models.entities import CalendarEvent, Conversation
    from app.routers import chat
    from app.services.providers.base import ToolCall
    from sqlmodel import select

    from tests.test_chat_tool_confirmation import _FakeLLM

    horloge(maintenant, fuseau)
    conv = Conversation(title="Confirmation agenda")
    db_session.add(conv)
    await db_session.commit()
    appel = ToolCall(id="agenda-c19", name="create_calendar_event", arguments={
        "summary": "Point chantier", "start": debut, "end": fin,
    })
    chunks = [json.loads(c.removeprefix("data: ")) async for c in chat._execute_tools_and_continue(
        _FakeLLM(), None, None, "", [appel], [workspace_tools.CREATE_CALENDAR_EVENT_TOOL],
        conv.id, 3, session=db_session,
    )]
    carte, = [c["confirmation"] for c in chunks if c["type"] == "confirmation_required"]
    assert not (await db_session.execute(select(CalendarEvent))).scalars().all()
    affiches = carte["arguments"]
    # L'interface affiche un ISO daté dans ce fuseau, une heure sans fuseau telle quelle.
    def heure_affichee(valeur):
        heure = datetime.fromisoformat(valeur)
        return heure.astimezone(ZoneInfo(affiches.get("timezone", "Europe/Paris"))).replace(tzinfo=None) if heure.tzinfo else heure
    attendu_dt = datetime.fromisoformat(attendu)
    assert heure_affichee(affiches["start"]) == attendu_dt
    assert (heure_affichee(affiches["end"]) - attendu_dt).total_seconds() == 3600
    executes = []
    executer = chat.execute_workspace_tool
    async def capturer(nom, arguments, *args, **kwargs):
        executes.append(dict(arguments))
        return await executer(nom, arguments, *args, **kwargs)
    monkeypatch.setattr(chat, "execute_workspace_tool", capturer)
    # L'heure courante peut changer entre préparation et accord humain.
    horloge("2026-11-01T12:00:00+01:00", fuseau)
    reponse = await client.post("/api/chat/confirm-tool", json={
        "confirmation_id": carte["confirmation_id"], "approved": True,
    })
    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["status"] == "executed"
    assert executes == [affiches]
    evenement = await _stocke(db_session)
    assert evenement.start_datetime == attendu_dt
    assert (evenement.end_datetime - evenement.start_datetime).total_seconds() == 3600
