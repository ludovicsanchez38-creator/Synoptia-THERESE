"""
THERESE v2 - Voice Router Tests

Tests for US-VOICE-01 to US-VOICE-05.
"""

from unittest.mock import patch

import pytest
from httpx import AsyncClient


class TestVoiceTranscription:
    """Tests for US-VOICE-02: Groq Whisper transcription."""

    @pytest.mark.asyncio
    async def test_transcribe_without_audio(self, client: AsyncClient):
        """Test transcription without audio data."""
        response = await client.post("/api/voice/transcribe")

        # Should fail without audio
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_transcribe_empty_audio(self, client: AsyncClient):
        """Test transcription with empty audio."""
        # Create empty audio file
        files = {"audio": ("test.webm", b"", "audio/webm")}
        response = await client.post("/api/voice/transcribe", files=files)

        assert response.status_code in [400, 422]


class TestVoiceConfig:
    """Tests for US-VOICE-05: Groq API key configuration."""

    @pytest.mark.asyncio
    async def test_transcribe_without_groq_key(self, client: AsyncClient):
        """US-VOICE-05: Transcription fails without Groq key."""
        # Create minimal audio data
        audio_data = b"RIFF" + b"\x00" * 100  # Fake WAV header
        files = {"audio": ("test.wav", audio_data, "audio/wav")}

        response = await client.post("/api/voice/transcribe", files=files)

        # Should fail gracefully without API key
        assert response.status_code in [400, 401, 422, 503]


class TestVoiceErrors:
    """Tests for US-VOICE-04: Error handling."""

    @pytest.mark.asyncio
    async def test_transcribe_invalid_format(self, client: AsyncClient):
        """US-VOICE-04: Clear error for invalid format."""
        files = {"audio": ("test.txt", b"not audio", "text/plain")}

        response = await client.post("/api/voice/transcribe", files=files)

        assert response.status_code in [400, 415, 422]

        if response.status_code in [400, 422]:
            error = response.json()
            # Should have error message
            assert "detail" in error or "message" in error

    @pytest.mark.asyncio
    async def test_transcribe_too_large(self, client: AsyncClient):
        """Test transcription with file too large."""
        # Create large fake audio (over 25MB limit)
        large_audio = b"RIFF" + b"\x00" * (26 * 1024 * 1024)
        files = {"audio": ("test.wav", large_audio, "audio/wav")}

        response = await client.post("/api/voice/transcribe", files=files)

        # Should either reject or chunk (413 or handle gracefully)
        assert response.status_code in [200, 400, 413, 422, 503]


class TestVoiceLanguage:
    """Tests for voice transcription language support."""

    @pytest.mark.asyncio
    async def test_transcribe_french(self, client: AsyncClient):
        """Test transcription with French language hint."""
        audio_data = b"RIFF" + b"\x00" * 100
        files = {"audio": ("test.wav", audio_data, "audio/wav")}

        response = await client.post(
            "/api/voice/transcribe?language=fr",
            files=files,
        )

        # Request should be accepted (may fail for other reasons)
        assert response.status_code in [200, 400, 401, 422, 503]


class TestVoiceFormats:
    """Tests for supported audio formats."""

    @pytest.mark.asyncio
    async def test_webm_format(self, client: AsyncClient):
        """Test WebM audio format."""
        files = {"audio": ("test.webm", b"\x1a\x45\xdf\xa3" + b"\x00" * 100, "audio/webm")}

        response = await client.post("/api/voice/transcribe", files=files)

        # Format should be accepted
        assert response.status_code in [200, 400, 401, 422, 503]

    @pytest.mark.asyncio
    async def test_mp3_format(self, client: AsyncClient):
        """Test MP3 audio format."""
        # ID3 header for MP3
        files = {"audio": ("test.mp3", b"ID3" + b"\x00" * 100, "audio/mpeg")}

        response = await client.post("/api/voice/transcribe", files=files)

        assert response.status_code in [200, 400, 401, 422, 503]

    @pytest.mark.asyncio
    async def test_ogg_format(self, client: AsyncClient):
        """Test OGG audio format."""
        files = {"audio": ("test.ogg", b"OggS" + b"\x00" * 100, "audio/ogg")}

        response = await client.post("/api/voice/transcribe", files=files)

        assert response.status_code in [200, 400, 401, 422, 503]


# =============================================================================
# Voix locale « un clic » (0.27) - status enrichi + setup + garde-fous
# =============================================================================


class TestVoiceLocalStatus:
    """GET /api/voice/local/status - contrat de l'UI réglages."""

    @pytest.mark.asyncio
    async def test_status_expose_le_contrat_ui(self, client: AsyncClient):
        response = await client.get("/api/voice/local/status")
        assert response.status_code == 200
        data = response.json()
        # Le contrat que l'écran de réglages consomme
        for key in ("stt_available", "tts_available", "ready", "models_downloaded",
                    "tts_voice_downloaded", "setup", "whisper_models", "default_whisper_model"):
            assert key in data, f"clé manquante : {key}"
        assert data["setup"]["state"] in ("idle", "running", "done", "error")
        # models_downloaded couvre chaque modèle proposé
        assert set(data["models_downloaded"].keys()) == set(data["whisper_models"].keys())

    @pytest.mark.asyncio
    async def test_models_whisper_isoles_dans_le_data_dir(self, client: AsyncClient):
        """Les modèles doivent vivre dans ~/.therese (backup/RGPD), pas ~/.cache."""
        from app.config import get_settings
        from app.services.voice_local import whisper_models_dir

        assert str(get_settings().data_dir) in str(whisper_models_dir())


class TestVoiceLocalSetup:
    """POST /api/voice/local/setup - activation en un clic."""

    @pytest.mark.asyncio
    async def test_setup_refuse_si_libs_absentes(self, client: AsyncClient):
        with patch("app.services.voice_local.stt_available", return_value=False):
            response = await client.post("/api/voice/local/setup", json={})
        assert response.status_code == 503
        assert "à jour" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_setup_refuse_double_lancement(self, client: AsyncClient):
        from app.services import voice_local

        with patch("app.services.voice_local.stt_available", return_value=True), \
             patch.dict(voice_local._setup_state, {"state": "running"}):
            response = await client.post("/api/voice/local/setup", json={})
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_setup_pose_running_avant_de_rendre_la_main(self, client: AsyncClient):
        """Revue 10/07 : l'état `running` n'était posé QUE dans le thread du
        téléchargement -> le refresh immédiat de l'UI pouvait lire `idle` (donc
        jamais de polling) et un 2e POST passait le garde 409 pendant la
        fenêtre (double téléchargement concurrent)."""
        import threading

        from app.services import voice_local

        release = threading.Event()

        def slow_setup(model_size):
            release.wait(timeout=5)

        try:
            with patch("app.services.voice_local.stt_available", return_value=True), \
                 patch("app.services.voice_local.run_voice_setup", side_effect=slow_setup), \
                 patch.dict(voice_local._setup_state):
                response = await client.post("/api/voice/local/setup", json={})
                assert response.status_code == 200
                # SANS attendre le thread : l'état doit déjà être running.
                assert voice_local.get_setup_state()["state"] == "running"
                # Et le garde anti-double lancement doit tenir pendant la fenêtre.
                second = await client.post("/api/voice/local/setup", json={})
                assert second.status_code == 409
        finally:
            release.set()

    @pytest.mark.asyncio
    async def test_transcribe_local_message_clair_pendant_le_telechargement(
        self, client: AsyncClient
    ):
        """Revue 10/07 : une dictée pendant le téléchargement des modèles
        recevait « Aucun modèle vocal téléchargé. Active la voix locale... »
        alors que l'installation TOURNAIT déjà - message dédié attendu."""
        from app.services import voice_local

        with patch("app.services.voice_local.stt_available", return_value=True), \
             patch("app.services.voice_local.active_whisper_model", return_value=None), \
             patch.dict(
                 voice_local._setup_state,
                 {"state": "running", "step": "Téléchargement du modèle"},
             ):
            files = {"audio": ("test.webm", b"fake-audio", "audio/webm")}
            response = await client.post("/api/voice/local/transcribe", files=files)

        assert response.status_code == 503
        assert "en cours" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_setup_lance_le_telechargement_en_fond(self, client: AsyncClient):
        calls = {}

        def fake_setup(model_size):
            calls["model"] = model_size

        with patch("app.services.voice_local.stt_available", return_value=True), \
             patch("app.services.voice_local.run_voice_setup", side_effect=fake_setup):
            response = await client.post("/api/voice/local/setup", json={"model": "small"})
            assert response.status_code == 200
            assert response.json() == {"started": True, "model": "small"}
            # L'executor est fire-and-forget : laisser un tick au thread
            import asyncio
            await asyncio.sleep(0.2)
        assert calls.get("model") == "small"


class TestPiperVoiceDownload:
    """download_piper_voice - écriture atomique, pas de voix corrompue."""

    def test_voix_inconnue_refusee(self):
        from app.services.voice_local import download_piper_voice

        with pytest.raises(RuntimeError, match="inconnue"):
            download_piper_voice("xx_XX-fantome-large")

    def test_telechargement_atomique(self, tmp_path):
        """Un flux interrompu ne doit jamais laisser un .onnx partiel visible."""
        from app.services import voice_local

        class _BoomStream:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def raise_for_status(self):
                pass

            def iter_bytes(self, chunk_size):
                yield b"debut"
                raise OSError("connexion coupee")

        with patch.object(voice_local, "voices_dir", return_value=tmp_path), \
             patch("httpx.stream", return_value=_BoomStream()), pytest.raises(OSError):
            voice_local.download_piper_voice()

        assert not list(tmp_path.glob("*.onnx")), "un .onnx partiel est visible"
        assert list(tmp_path.glob("*.part")), "le fichier temporaire devrait rester en .part"
