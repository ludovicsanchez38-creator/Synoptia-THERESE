# Voix locale souveraine (STT + TTS) — option

THÉRÈSE peut fonctionner avec une voix **100 % locale et souveraine**, sans envoyer
l'audio à un service cloud. C'est une **option** : elle n'est pas incluse par défaut
pour garder le paquet léger. Tu l'installes seulement si tu en as besoin.

- **STT** (reconnaissance vocale) : [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (Whisper via CTranslate2, CPU, quantization int8).
- **TTS** (synthèse vocale) : [Piper](https://github.com/rhasspy/piper) (modèles ONNX légers, CPU).

Les deux sont open source et tournent entièrement sur ta machine. C'est l'alternative
souveraine à la transcription via Groq Whisper (cloud) déjà présente.

## Installation (option)

```bash
pip install 'therese-backend[voice-local]'
```

Les **modèles se téléchargent au premier usage** (ils ne sont pas dans le paquet).
Ensuite, active la voix locale dans les réglages (`voice_local_enabled`).

## Prérequis RAM

### STT — modèles Whisper (faster-whisper, CPU int8)

| Modèle | Taille disque | RAM nécessaire | Qualité |
|--------|---------------|----------------|---------|
| `tiny` | ~75 Mo | ~1 Go | Basique, très rapide |
| `base` (recommandé) | ~145 Mo | ~1 Go | Bon compromis FR |
| `small` | ~480 Mo | ~2 Go | Meilleure, plus lourde |

Le modèle par défaut est `base`. Choix via le réglage `voice_local_whisper_model`
(`tiny` | `base` | `small`).

### TTS — Piper

| Composant | Taille disque | RAM nécessaire |
|-----------|---------------|----------------|
| 1 voix Piper (ex. `fr_FR-siwis-medium`) | ~60–110 Mo | ~0,5 Go |

> Repère pratique : prévoir **~2 Go de RAM libre** pour un confort STT `base` + TTS
> en parallèle. Sur une machine avec peu de RAM, rester sur `tiny`.

## Voix Piper (TTS)

Les voix Piper se placent dans `~/.therese/voices/` (fichiers `.onnx` + `.onnx.json`).
Voix française conseillée : `fr_FR-siwis-medium`. Téléchargement des voix :
https://github.com/rhasspy/piper/blob/master/VOICES.md

## API

- `GET /api/voice/local/status` — disponibilité (STT/TTS), modèles et prérequis RAM.
- `POST /api/voice/local/transcribe` — transcription locale (multipart audio).
- `POST /api/voice/tts` — synthèse vocale locale (`{ "text": "...", "voice": "..." }`) → WAV.

Si le groupe `voice-local` n'est pas installé, ces endpoints renvoient un `503`
avec l'indication d'installation (jamais de plantage).

## Souveraineté

Avec cette option activée, l'audio (entrée et sortie) ne quitte jamais la machine :
ni la transcription, ni la synthèse n'appellent un service externe. C'est cohérent
avec la promesse « assistant IA desktop souverain, données 100 % locales ».
