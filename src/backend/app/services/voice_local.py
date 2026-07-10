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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

# Modèles Whisper supportés (faster-whisper, quantization int8 CPU).
# ram_mb = RAM approximative nécessaire au modèle chargé (hors OS/app).
WHISPER_MODELS: dict[str, dict[str, int | str]] = {
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


def whisper_models_dir() -> Path:
    """Dossier des modèles Whisper (dans ~/.therese, pas ~/.cache/huggingface).

    Sans download_root explicite, faster-whisper télécharge dans le cache
    HuggingFace global - hors du périmètre de données de THÉRÈSE (backup,
    RGPD, désinstallation propre).
    """
    from app.config import get_settings

    return Path(get_settings().data_dir) / "models" / "whisper"


def stt_model_downloaded(size: str) -> bool:
    """Le modèle Whisper est-il déjà téléchargé localement ?"""
    # Convention de cache HuggingFace Hub : models--{org}--{repo}
    model_dir = whisper_models_dir() / f"models--Systran--faster-whisper-{size}"
    return model_dir.exists() and any(model_dir.rglob("model.bin"))


def tts_voice_downloaded(voice: str = "") -> bool:
    """La voix Piper est-elle déjà téléchargée ?"""
    name = voice or DEFAULT_PIPER_VOICE
    return (voices_dir() / f"{name}.onnx").exists()


# Voix Piper officielles (repo HuggingFace rhasspy/piper-voices)
_PIPER_VOICE_URLS = {
    "fr_FR-siwis-medium": (
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/"
    ),
}


def download_piper_voice(voice: str = DEFAULT_PIPER_VOICE) -> Path:
    """Télécharge une voix Piper (.onnx + .onnx.json) dans voices_dir().

    Écriture atomique (fichier temporaire puis rename) : un téléchargement
    interrompu ne laisse jamais une voix corrompue considérée comme présente.
    """
    import httpx

    base_url = _PIPER_VOICE_URLS.get(voice)
    if not base_url:
        raise RuntimeError(f"Voix Piper inconnue : {voice}")

    target_dir = voices_dir()
    target_dir.mkdir(parents=True, exist_ok=True)

    for suffix in (f"{voice}.onnx", f"{voice}.onnx.json"):
        target = target_dir / suffix
        if target.exists():
            continue
        tmp = target.with_suffix(target.suffix + ".part")
        logger.info("Téléchargement de la voix Piper : %s", suffix)
        with httpx.stream("GET", base_url + suffix, follow_redirects=True, timeout=120) as resp:
            resp.raise_for_status()
            with open(tmp, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=1 << 20):
                    f.write(chunk)
        tmp.rename(target)
    return target_dir / f"{voice}.onnx"


# État du setup en cours (téléchargement des modèles) - module-level, un seul
# setup à la fois (protégé par le router).
_setup_state: dict[str, object] = {"state": "idle", "step": "", "error": ""}


def get_setup_state() -> dict[str, object]:
    return dict(_setup_state)


def mark_setup_starting() -> None:
    """Pose l'état `running` de façon SYNCHRONE, avant le thread de setup.

    Revue 10/07 : `running` n'était posé que dans run_voice_setup (thread
    executor) - entre le POST /local/setup et le premier tour du thread, un
    status lisait encore `idle` (l'UI ne démarrait pas son polling) et un 2e
    POST passait le garde 409 (double téléchargement concurrent).
    """
    _setup_state.update(state="running", step="Préparation du téléchargement", error="")


def run_voice_setup(model_size: str) -> None:
    """Télécharge le modèle Whisper + la voix Piper (SYNCHRONE, à lancer en executor).

    Met à jour _setup_state au fil des étapes pour l'UI (polling /local/status).
    """
    size = model_size if model_size in WHISPER_MODELS else DEFAULT_WHISPER_MODEL
    try:
        _setup_state.update(state="running", step=f"Téléchargement du modèle Whisper « {size} »", error="")
        if stt_available():
            from faster_whisper import WhisperModel

            # Instancier = télécharger (si absent) + valider le chargement
            model = WhisperModel(
                size, device="cpu", compute_type="int8",
                download_root=str(whisper_models_dir()),
            )
            _whisper_cache[size] = model

        _setup_state.update(step="Téléchargement de la voix française")
        if tts_available():
            download_piper_voice(DEFAULT_PIPER_VOICE)

        _setup_state.update(state="done", step="Voix locale prête")
    except Exception as e:  # noqa: BLE001 - l'état d'erreur EST le contrat de l'UI
        logger.exception("Échec du setup voix locale")
        _setup_state.update(state="error", error=str(e))


def active_whisper_model() -> str | None:
    """Le modèle Whisper réellement utilisable : le défaut s'il est téléchargé,
    sinon le premier modèle présent sur disque (l'utilisateur a pu choisir
    tiny ou small au setup), sinon None."""
    from app.config import get_settings

    default = getattr(get_settings(), "voice_local_whisper_model", DEFAULT_WHISPER_MODEL)
    if stt_model_downloaded(default):
        return default
    for size in WHISPER_MODELS:
        if stt_model_downloaded(size):
            return size
    return None


def voice_local_status() -> dict[str, object]:
    """État de la voix locale : disponibilité + modèles + prérequis RAM."""
    from app.config import get_settings

    settings = get_settings()
    default_model = getattr(settings, "voice_local_whisper_model", DEFAULT_WHISPER_MODEL)
    stt_ok = stt_available()
    tts_ok = tts_available()
    models_downloaded = {size: stt_model_downloaded(size) for size in WHISPER_MODELS}
    active = active_whisper_model()
    voice_ok = tts_voice_downloaded()
    return {
        "enabled": bool(getattr(settings, "voice_local_enabled", False)),
        "stt_available": stt_ok,
        "tts_available": tts_ok,
        "whisper_models": WHISPER_MODELS,
        "default_whisper_model": default_model,
        "active_whisper_model": active,
        "models_downloaded": models_downloaded,
        "tts_voice": DEFAULT_PIPER_VOICE,
        "tts_voice_downloaded": voice_ok,
        "tts_ram_mb": PIPER_TTS_RAM_MB,
        # Prêt à l'emploi = libs embarquées ET au moins un modèle sur disque
        "ready": stt_ok and active is not None,
        "setup": get_setup_state(),
        "install_hint": INSTALL_HINT,
    }


_whisper_cache: dict[str, WhisperModel] = {}


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
        model = WhisperModel(
            size, device="cpu", compute_type="int8",
            download_root=str(whisper_models_dir()),
        )
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
    # piper-tts >= 1.3 : synthesize() renvoie un flux d'AudioChunk ; l'écriture
    # WAV passe par synthesize_wav (l'ancien synthesize(text, wav) de la 1.2
    # laissait un WAV vide - jamais exécuté en réel avant le 07/07/2026).
    with wave.open(out_path, "wb") as wav:
        loaded.synthesize_wav(text, wav)
    return out_path
