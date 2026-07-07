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
from app.models.schemas_voice import TranscriptionResponse, TTSRequest
from app.services.http_client import get_http_client
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
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
                return str(decrypt_value(pref.value))
            except Exception:
                logger.warning("Échec déchiffrement clé Groq")
                return None
        return str(pref.value)

    return None


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> TranscriptionResponse:
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
            detail="Clé API Groq non configurée. Ajoute-la dans les paramètres.",
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
                    detail="Limite de requêtes Groq dépassée. Réessaie dans quelques instants.",
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
            detail="Timeout lors de la transcription. Réessaie avec un audio plus court.",
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
        except Exception as e:
            logger.debug("Echec nettoyage fichier temp: %s", e)


# =============================================================================
# Voix LOCALE souveraine (STT + TTS) - OPTIONNELLE (groupe pip voice-local)
# =============================================================================


@router.get("/local/status")
async def voice_local_status_route() -> dict[str, object]:
    """Disponibilité de la voix locale (STT/TTS) + modèles + prérequis RAM.

    Permet à l'UI d'afficher si la voix souveraine est installée, et sinon
    comment l'activer (et la RAM nécessaire).
    """
    from app.services.voice_local import voice_local_status

    status: dict[str, object] = voice_local_status()
    return status


@router.post("/local/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio_local(
    audio: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> TranscriptionResponse:
    """Transcription 100% locale et souveraine (faster-whisper), sans cloud.

    Nécessite le groupe optionnel `voice-local` installé (sinon 503 + indication).
    """
    from app.config import get_settings
    from app.services.voice_local import stt_available, transcribe_local

    if not stt_available():
        from app.services.voice_local import INSTALL_HINT

        raise HTTPException(status_code=503, detail=f"Voix locale non installée. {INSTALL_HINT}")

    audio_data = await audio.read()
    if not audio_data:
        raise HTTPException(status_code=400, detail="Fichier audio vide")

    extension = Path(audio.filename or "recording.webm").suffix or ".webm"
    with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as tmp:
        tmp.write(audio_data)
        tmp_path = tmp.name

    try:
        model = get_settings().voice_local_whisper_model
        text = transcribe_local(tmp_path, model_size=model)
        return TranscriptionResponse(text=text, language="fr")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("Erreur transcription locale")
        raise HTTPException(status_code=500, detail=f"Erreur transcription locale : {e}")
    finally:
        try:
            os.unlink(tmp_path)
        except Exception as e:
            logger.debug("Echec nettoyage fichier temp: %s", e)


@router.post("/tts")
async def text_to_speech_local(payload: TTSRequest) -> FileResponse:
    """Synthèse vocale 100% locale et souveraine (Piper) -> audio WAV.

    Nécessite le groupe optionnel `voice-local` + la voix téléchargée (sinon 503).
    """
    from app.services.voice_local import DEFAULT_PIPER_VOICE, synthesize_local, tts_available

    if not tts_available():
        from app.services.voice_local import INSTALL_HINT

        raise HTTPException(status_code=503, detail=f"Voix locale non installée. {INSTALL_HINT}")

    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Texte vide")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        out_path = tmp.name

    try:
        synthesize_local(text, out_path, voice=payload.voice or DEFAULT_PIPER_VOICE)
        return FileResponse(out_path, media_type="audio/wav", filename="therese-tts.wav")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("Erreur synthèse vocale locale")
        raise HTTPException(status_code=500, detail=f"Erreur synthèse vocale locale : {e}")
