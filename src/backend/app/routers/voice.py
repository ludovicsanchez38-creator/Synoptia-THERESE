"""
THÉRÈSE v2 - Voice Router

Endpoints for voice transcription using Groq Whisper API.
"""

import logging
import os
import tempfile
from pathlib import Path

from app.models.database import get_session
from app.models.entities import Preference
from app.models.schemas_voice import TranscriptionResponse
from app.services.http_client import get_http_client
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

logger = logging.getLogger(__name__)

router = APIRouter()


async def _get_groq_api_key(session: AsyncSession) -> str | None:
    """Get Groq API key from environment or database."""
    # Check environment first
    api_key = os.environ.get("GROQ_API_KEY")
    if api_key:
        return api_key

    # Check database (valeur chiffrée Fernet)
    result = await session.execute(
        select(Preference).where(Preference.key == "groq_api_key")
    )
    pref = result.scalar_one_or_none()
    if pref and pref.value:
        from app.services.encryption import decrypt_value, is_value_encrypted

        if is_value_encrypted(pref.value):
            try:
                return decrypt_value(pref.value)
            except Exception:
                logger.warning("Échec déchiffrement clé Groq")
                return None
        return pref.value

    return None


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    """
    Transcribe audio to text using Groq Whisper API.

    Accepts audio files in various formats (webm, wav, mp3, m4a, etc.)
    and returns the transcribed text.
    """
    import httpx

    # Get API key
    api_key = await _get_groq_api_key(session)
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Clé API Groq non configurée. Ajoutez-la dans les paramètres.",
        )

    # Read audio data
    audio_data = await audio.read()

    if not audio_data:
        raise HTTPException(status_code=400, detail="Fichier audio vide")

    # Determine file extension
    filename = audio.filename or "recording.webm"
    extension = Path(filename).suffix or ".webm"

    # Save to temp file (Groq API requires file upload)
    with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as tmp:
        tmp.write(audio_data)
        tmp_path = tmp.name

    try:
        # Call Groq Whisper API
        client = await get_http_client()
        with open(tmp_path, "rb") as f:
            response = await client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                },
                files={
                    "file": (filename, f, audio.content_type or "audio/webm"),
                },
                data={
                    "model": "whisper-large-v3-turbo",
                    "language": "fr",  # Default to French
                    "response_format": "verbose_json",
                },
                timeout=60.0,
            )

        if response.status_code != 200:
            error_msg = response.text
            logger.error(f"Groq API error: {response.status_code} - {error_msg}")

            if response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Clé API Groq invalide",
                )
            elif response.status_code == 429:
                raise HTTPException(
                    status_code=429,
                    detail="Limite de requêtes Groq dépassée. Réessayez dans quelques instants.",
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Erreur transcription: {error_msg}",
                )

        result = response.json()

        return TranscriptionResponse(
            text=result.get("text", "").strip(),
            duration_seconds=result.get("duration"),
            language=result.get("language"),
        )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Timeout lors de la transcription. Réessayez avec un audio plus court.",
        )
    except httpx.RequestError as e:
        logger.error(f"Network error during transcription: {e}")
        raise HTTPException(
            status_code=502,
            detail="Erreur réseau lors de la transcription",
        )
    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
