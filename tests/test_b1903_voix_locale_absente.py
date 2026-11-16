"""B-1903 : une dépendance vocale absente donne la même indication."""

import sys

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


@pytest.mark.asyncio
@pytest.mark.parametrize("application_installee", [False, True])
async def test_absence_partagee_selon_le_mode_d_installation(client, monkeypatch, application_installee):
    monkeypatch.setattr(sys, "frozen", application_installee, raising=False)
    monkeypatch.setattr(voice_local, "stt_available", lambda: False)
    monkeypatch.setattr(voice_local, "tts_available", lambda: False)
    monkeypatch.setattr(voice_local, "stt_model_downloaded", lambda *_: False)
    monkeypatch.setattr(voice_local, "active_whisper_model", lambda: None)
    monkeypatch.setattr(voice_local, "tts_voice_downloaded", lambda: False)
    monkeypatch.setattr(voice_local, "get_setup_state", lambda: {"state": "idle"})

    statut = await client.get("/api/voice/local/status")
    setup = await client.post("/api/voice/local/setup", json={})
    dictee = await client.post(
        "/api/voice/local/transcribe",
        files={"audio": ("essai.wav", b"audio factice", "audio/wav")},
    )
    tts = await client.post("/api/voice/tts", json={"text": "Bonjour"})

    assert setup.status_code == dictee.status_code == tts.status_code == 503
    message = setup.json()["message"]
    assert statut.json()["install_hint"] == message == dictee.json()["message"] == tts.json()["message"]
    if application_installee:
        assert "application installée" in message.lower()
        assert "pip install" not in message
    else:
        assert "pip install 'therese-backend[voice-local]'" in message
