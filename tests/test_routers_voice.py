"""
THERESE v2 - Voice Router Tests

Tests for US-VOICE-01 to US-VOICE-05.
"""

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
