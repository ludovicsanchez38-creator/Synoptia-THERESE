"""Voix locale souveraine (STT + TTS) - OPTIONNELLE.

STT : faster-whisper (Whisper via CTranslate2, CPU, int8, léger).
TTS : Piper (rhasspy, ONNX, CPU, léger).

Ces dépendances sont dans le groupe pip OPTIONNEL `voice-local` (cf pyproject) :
elles NE SONT PAS incluses dans le build par défaut, pour garder le paquet léger
et le 100% souverain en option. Les modèles se téléchargent au premier usage.

Prérequis RAM : voir docs/VOICE-LOCAL.md (et WHISPER_MODELS ci-dessous).
"""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Modèles Whisper supportés (faster-whisper, quantization int8 CPU).
# ram_mb = RAM approximative nécessaire au modèle chargé (hors OS/app).
WHISPER_MODELS: dict[str, dict] = {
    "tiny": {"size_mb": 75, "ram_mb": 1024, "label": "Tiny - le plus léger, qualité basique"},
    "base": {"size_mb": 145, "ram_mb": 1024, "label": "Base - recommandé, bon compromis"},
    "small": {"size_mb": 480, "ram_mb": 2048, "label": "Small - meilleure qualité, plus lourd"},
}
DEFAULT_WHISPER_MODEL = "base"

# Piper TTS : très léger, ~1 voix ONNX (60-110 Mo), faible RAM.
DEFAULT_PIPER_VOICE = "fr_FR-siwis-medium"
PIPER_TTS_RAM_MB = 512

INSTALL_HINT = (
    "Installe la voix locale en option : `pip install 'therese-backend[voice-local]'`. "
    "Les modèles se téléchargent au premier usage."
)


def stt_available() -> bool:
    """faster-whisper est-il installé (groupe optionnel voice-local) ?"""
    return importlib.util.find_spec("faster_whisper") is not None


def tts_available() -> bool:
    """Piper est-il installé (groupe optionnel voice-local) ? (piper-tts -> module `piper`)."""
    return importlib.util.find_spec("piper") is not None


def voices_dir() -> Path:
    """Dossier où sont rangées les voix Piper téléchargées."""
    from app.config import get_settings

    return Path(get_settings().data_dir) / "voices"


def voice_local_status() -> dict:
    """État de la voix locale : disponibilité + modèles + prérequis RAM."""
    from app.config import get_settings

    settings = get_settings()
    return {
        "enabled": bool(getattr(settings, "voice_local_enabled", False)),
        "stt_available": stt_available(),
        "tts_available": tts_available(),
        "whisper_models": WHISPER_MODELS,
        "default_whisper_model": getattr(settings, "voice_local_whisper_model", DEFAULT_WHISPER_MODEL),
        "tts_voice": DEFAULT_PIPER_VOICE,
        "tts_ram_mb": PIPER_TTS_RAM_MB,
        "install_hint": INSTALL_HINT,
    }


_whisper_cache: dict[str, object] = {}


def transcribe_local(audio_path: str, model_size: str | None = None, language: str = "fr") -> str:
    """Transcrit un fichier audio en texte, 100% local (faster-whisper).

    Lève RuntimeError si la dépendance optionnelle n'est pas installée.
    """
    if not stt_available():
        raise RuntimeError(
            "STT local indisponible : faster-whisper non installé. " + INSTALL_HINT
        )

    from faster_whisper import WhisperModel  # import paresseux (dépendance optionnelle)

    size = model_size if model_size in WHISPER_MODELS else DEFAULT_WHISPER_MODEL
    model = _whisper_cache.get(size)
    if model is None:
        logger.info("Chargement du modèle Whisper local '%s' (CPU, int8)", size)
        model = WhisperModel(size, device="cpu", compute_type="int8")
        _whisper_cache[size] = model

    segments, _info = model.transcribe(audio_path, language=language)
    return " ".join(seg.text.strip() for seg in segments).strip()


def synthesize_local(text: str, out_path: str, voice: str = DEFAULT_PIPER_VOICE) -> str:
    """Synthétise du texte en audio WAV, 100% local (Piper).

    Lève RuntimeError si la dépendance ou la voix n'est pas disponible.
    """
    if not tts_available():
        raise RuntimeError("TTS local indisponible : Piper non installé. " + INSTALL_HINT)

    import wave

    from piper import PiperVoice  # import paresseux (dépendance optionnelle)

    onnx = voices_dir() / f"{voice}.onnx"
    if not onnx.exists():
        raise RuntimeError(
            f"Voix Piper '{voice}' absente ({onnx}). "
            "Télécharge-la (voir docs/VOICE-LOCAL.md) puis réessaie."
        )

    loaded = PiperVoice.load(str(onnx))
    with wave.open(out_path, "wb") as wav:
        loaded.synthesize(text, wav)
    return out_path
