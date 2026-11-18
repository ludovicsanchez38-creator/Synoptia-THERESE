"""Une lecture distante en échec ne valide pas la transaction de l'appelant."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.models.entities import Calendar, Preference
from app.services import workspace_tools
from sqlmodel import select


@pytest.mark.asyncio
async def test_echec_lecture_distante_ne_valide_pas_les_modifications_en_attente(
    db_session, monkeypatch
):
    calendrier = Calendar(
        id="agenda-distant", summary="Agenda fictif", provider="caldav",
        sync_status="idle", synced_at=datetime.now(UTC),
    )
    db_session.add(calendrier)
    await db_session.commit()
    db_session.add(Preference(key="modification-en-attente", value="fictive", category="test"))
    fournisseur = SimpleNamespace(list_events=AsyncMock(side_effect=RuntimeError("Panne fictive")))
    monkeypatch.setattr(
        workspace_tools, "_provider_depuis_calendrier",
        AsyncMock(return_value=(fournisseur, "distant-fictif", None)),
    )

    resultat = await workspace_tools.execute_workspace_tool(
        "list_calendar_events", {"calendar_id": "agenda-distant"}, db_session,
    )
    await db_session.rollback()
    preference = (await db_session.execute(
        select(Preference).where(Preference.key == "modification-en-attente")
    )).scalar_one_or_none()
    calendrier_relu = await db_session.get(Calendar, "agenda-distant")

    assert preference is None
    assert calendrier_relu.sync_status == "idle"
    assert calendrier_relu.last_sync_error is None
    assert "lecture" in resultat.lower()
    assert "synchronisation a échoué" not in resultat.lower()
