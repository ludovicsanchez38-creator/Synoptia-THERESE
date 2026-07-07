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

export function isVoiceLocalPreferred(): boolean {
  return localStorage.getItem(VOICE_LOCAL_PREF_KEY) === 'true';
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

export async function transcribeAudio(audioBlob: Blob): Promise<string> {
  // Voix locale activée : l'audio ne quitte JAMAIS la machine. Pas de repli
  // cloud silencieux en cas d'échec - ce serait trahir le choix de l'utilisateur.
  const endpoint = isVoiceLocalPreferred()
    ? `${API_BASE}/api/voice/local/transcribe`
    : `${API_BASE}/api/voice/transcribe`;

  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.webm');

  const response = await apiFetch(endpoint, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const message = await response.text().catch(() => null);
    throw new ApiError(response.status, response.statusText, message || undefined);
  }

  const data = await response.json() as TranscriptionResponse;
  return data.text;
}
