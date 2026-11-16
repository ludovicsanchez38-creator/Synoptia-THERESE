"""B-1903 : une dépendance vocale absente donne la même indication."""

import pytest
from app.services import voice_local


@pytest.mark.asyncio
async def test_setup_et_dictee_expliquent_la_meme_absence(client, monkeypatch):
    monkeypatch.setattr(voice_local, "stt_available", lambda: False)
    monkeypatch.setattr(voice_local, "get_setup_state", lambda: {"state": "idle"})

    setup = await client.post("/api/voice/local/setup", json={})
    dictee = await client.post(
        "/api/voice/local/transcribe",
        files={"audio": ("essai.wav", b"audio factice", "audio/wav")},
    )

    assert setup.status_code == dictee.status_code == 503
    assert setup.json()["message"] == dictee.json()["message"]
    assert "Voix locale non installée" in setup.json()["message"]
