/**
 * THÉRÈSE v2 - Voice API Module
 *
 * Transcription audio via Groq Whisper.
 */

import { API_BASE, apiFetch, ApiError } from './core';

export interface TranscriptionResponse {
  text: string;
  duration_seconds?: number;
  language?: string;
}

export async function transcribeAudio(audioBlob: Blob): Promise<string> {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.webm');

  const response = await apiFetch(`${API_BASE}/api/voice/transcribe`, {
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
