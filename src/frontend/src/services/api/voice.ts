/**
 * THÉRÈSE v2 - Voice API Module
 *
 * Transcription audio via Groq Whisper, ou 100 % locale (faster-whisper).
 */

import { API_BASE, apiFetch, ApiError } from './core';

export interface TranscriptionResponse {
  text: string;
  duration_seconds?: number;
  language?: string;
}

/** Préférence : le micro utilise la voix locale (aucun audio envoyé au cloud). */
const VOICE_LOCAL_PREF_KEY = 'therese-voice-local';

/**
 * BUG-129 : préférence TRI-ÉTAT. `null` = jamais posée (utilisateur d'avant le
 * fix, réinstallation, localStorage vidé) - dans ce cas le routage de la dictée
 * se réconcilie avec l'état réel du serveur (/local/status) au lieu de retomber
 * silencieusement sur Groq.
 */
export function getVoiceLocalPreference(): boolean | null {
  const raw = localStorage.getItem(VOICE_LOCAL_PREF_KEY);
  if (raw === 'true') return true;
  if (raw === 'false') return false;
  return null;
}

export function isVoiceLocalPreferred(): boolean {
  return getVoiceLocalPreference() === true;
}

export function setVoiceLocalPreferred(value: boolean): void {
  localStorage.setItem(VOICE_LOCAL_PREF_KEY, value ? 'true' : 'false');
}

export interface VoiceLocalSetupState {
  state: 'idle' | 'running' | 'done' | 'error';
  step: string;
  error: string;
}

export interface VoiceLocalStatus {
  stt_available: boolean;
  tts_available: boolean;
  ready: boolean;
  whisper_models: Record<string, { size_mb: number; ram_mb: number; label: string }>;
  default_whisper_model: string;
  active_whisper_model: string | null;
  models_downloaded: Record<string, boolean>;
  tts_voice: string;
  tts_voice_downloaded: boolean;
  setup: VoiceLocalSetupState;
}

export async function getVoiceLocalStatus(): Promise<VoiceLocalStatus> {
  const response = await apiFetch(`${API_BASE}/api/voice/local/status`);
  if (!response.ok) {
    throw new ApiError(response.status, response.statusText);
  }
  return response.json() as Promise<VoiceLocalStatus>;
}

export async function setupVoiceLocal(model?: string): Promise<void> {
  const response = await apiFetch(`${API_BASE}/api/voice/local/setup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(model ? { model } : {}),
  });
  if (!response.ok) {
    const message = await response.text().catch(() => null);
    throw new ApiError(response.status, response.statusText, message || undefined);
  }
}

/**
 * Résout le moteur de transcription à utiliser pour CETTE dictée.
 *
 * - Préférence posée ('true'/'false') : respectée sans exception - jamais de
 *   bascule silencieuse entre deux moteurs explicitement choisis.
 * - Préférence absente (null) : on interroge UNE fois /local/status.
 *   - prête -> migration : persiste 'true' et route local (corrige le cas des
 *     modèles installés avant que la préférence existe, BUG-129 rouvert) ;
 *   - installation en cours -> erreur claire, rien n'est envoyé (ni au cloud
 *     alors que l'utilisateur vient de choisir le local, ni au local pas prêt),
 *     rien n'est persisté ;
 *   - pas prête -> persiste 'false' (comportement cloud historique) ;
 *   - status injoignable -> cloud SANS persister, pour re-tenter la
 *     réconciliation à la prochaine dictée.
 */
async function resolveUseLocalForTranscription(): Promise<boolean> {
  const pref = getVoiceLocalPreference();
  if (pref !== null) return pref;

  let status: VoiceLocalStatus;
  try {
    status = await getVoiceLocalStatus();
  } catch {
    return false;
  }

  if (status.ready) {
    setVoiceLocalPreferred(true);
    return true;
  }
  if (status.setup?.state === 'running') {
    throw new ApiError(
      503,
      'Service Unavailable',
      "Installation de la voix locale en cours. Réessaie dans un instant, ou choisis la transcription cloud dans Paramètres > Confidentialité."
    );
  }
  setVoiceLocalPreferred(false);
  return false;
}

export async function transcribeAudio(
  audioBlob: Blob,
  filename = 'recording.webm',
  signal?: AbortSignal,
): Promise<string> {
  // Voix locale activée : l'audio ne quitte JAMAIS la machine. Pas de repli
  // cloud silencieux en cas d'échec - ce serait trahir le choix de l'utilisateur.
  const useLocal = await resolveUseLocalForTranscription();
  const endpoint = useLocal
    ? `${API_BASE}/api/voice/local/transcribe`
    : `${API_BASE}/api/voice/transcribe`;

  const formData = new FormData();
  formData.append('audio', audioBlob, filename);

  const response = await apiFetch(endpoint, {
    method: 'POST',
    body: formData,
    signal,
  });

  if (!response.ok) {
    // Le backend renvoie { code, message } : on extrait le message lisible au
    // lieu d'afficher le JSON brut à l'utilisateur (ex. « Clé API Groq non
    // configurée » plutôt que {"code":"HTTP_ERROR",...}, finding Codex 16/07).
    const raw = await response.text().catch(() => null);
    let message = raw || undefined;
    if (raw) {
      try {
        const parsed = JSON.parse(raw);
        if (parsed && typeof parsed.message === 'string') message = parsed.message;
      } catch {
        // Corps non-JSON : on garde le texte tel quel.
      }
    }
    throw new ApiError(response.status, response.statusText, message);
  }

  const data = await response.json() as TranscriptionResponse;
  return data.text;
}

/** Génère un WAV avec Piper. Cette route est exclusivement locale. */
export async function synthesizeSpeech(text: string, voice = 'fr'): Promise<Blob> {
  const response = await apiFetch(`${API_BASE}/api/voice/tts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, voice }),
  });
  if (!response.ok) {
    const message = await response.text().catch(() => null);
    throw new ApiError(response.status, response.statusText, message || undefined);
  }
  return response.blob();
}
