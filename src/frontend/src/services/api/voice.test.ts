/**
 * BUG-129 (rouvert) - routage de la dictée micro : tri-état.
 *
 * L'ancien routage reposait sur un booléen localStorage posé UNIQUEMENT au
 * clic « Activer la voix locale » : quiconque avait les modèles déjà installés
 * (activation antérieure au fix 598d53a, réinstallation, localStorage vidé)
 * gardait la préférence à faux et la dictée partait sur Groq -> « Clé API
 * Groq non configurée ».
 *
 * Nouvelle spec : préférence tri-état.
 * - 'true'  -> transcription locale, sans exception ;
 * - 'false' -> Groq (choix cloud explicite), sans exception ;
 * - absente -> interroger UNE fois /local/status : prête -> migrer et
 *   persister 'true' ; installation en cours -> erreur claire (rien envoyé
 *   au cloud, rien persisté) ; sinon persister 'false' (cloud historique).
 * Jamais de bascule silencieuse entre deux moteurs explicitement choisis.
 */

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiFetch } from './core';
import {
  getVoiceLocalPreference,
  setVoiceLocalPreferred,
  synthesizeSpeech,
  transcribeAudio,
} from './voice';

vi.mock('./core', async () => {
  const actual = await vi.importActual<typeof import('./core')>('./core');
  return { ...actual, apiFetch: vi.fn() };
});

const mockedFetch = vi.mocked(apiFetch);

function okJson(data: unknown): Response {
  return { ok: true, json: async () => data } as Response;
}

function localStatus(overrides: Record<string, unknown> = {}): Response {
  return okJson({
    stt_available: true,
    tts_available: true,
    ready: false,
    whisper_models: {},
    default_whisper_model: 'base',
    active_whisper_model: null,
    models_downloaded: {},
    tts_voice: 'fr',
    tts_voice_downloaded: false,
    setup: { state: 'idle', step: '', error: '' },
    ...overrides,
  });
}

const AUDIO = new Blob(['audio'], { type: 'audio/webm' });

function calledUrls(): string[] {
  return mockedFetch.mock.calls.map((c) => String(c[0]));
}

// Le setup global (src/test/setup.ts) mocke localStorage en no-op : on donne
// ici une vraie sémantique de stockage aux vi.fn(), indispensable pour tester
// le tri-état (posé / absent) et la persistance de la migration.
const store = new Map<string, string>();

beforeEach(() => {
  store.clear();
  vi.mocked(localStorage.getItem).mockImplementation((k: string) => store.get(k) ?? null);
  vi.mocked(localStorage.setItem).mockImplementation(
    (k: string, v: string) => void store.set(k, String(v))
  );
  vi.mocked(localStorage.removeItem).mockImplementation((k: string) => void store.delete(k));
  vi.mocked(localStorage.clear).mockImplementation(() => store.clear());
  mockedFetch.mockReset();
});

describe('getVoiceLocalPreference - tri-état', () => {
  it("retourne null quand rien n'est posé", () => {
    expect(getVoiceLocalPreference()).toBeNull();
  });

  it("retourne true/false quand posé explicitement", () => {
    setVoiceLocalPreferred(true);
    expect(getVoiceLocalPreference()).toBe(true);
    setVoiceLocalPreferred(false);
    expect(getVoiceLocalPreference()).toBe(false);
  });
});

describe('BUG-129 - transcribeAudio route selon le tri-état', () => {
  it("préférence 'true' -> endpoint local direct, sans appel status", async () => {
    setVoiceLocalPreferred(true);
    mockedFetch.mockResolvedValueOnce(okJson({ text: 'bonjour' }));

    const text = await transcribeAudio(AUDIO);

    expect(text).toBe('bonjour');
    expect(calledUrls()).toHaveLength(1);
    expect(calledUrls()[0]).toContain('/api/voice/local/transcribe');
  });

  it('conserve le nom et le format du fichier audio importé', async () => {
    setVoiceLocalPreferred(true);
    mockedFetch.mockResolvedValueOnce(okJson({ text: 'réunion' }));
    const imported = new Blob(['audio'], { type: 'audio/mp4' });

    await transcribeAudio(imported, 'réunion.m4a');

    const options = mockedFetch.mock.calls[0][1] as RequestInit;
    const formData = options.body as FormData;
    const audio = formData.get('audio') as File;
    expect(audio.name).toBe('réunion.m4a');
  });

  it("préférence 'false' explicite -> Groq, jamais le local ni le status", async () => {
    setVoiceLocalPreferred(false);
    mockedFetch.mockResolvedValueOnce(okJson({ text: 'cloud' }));

    await transcribeAudio(AUDIO);

    expect(calledUrls()).toHaveLength(1);
    expect(calledUrls()[0]).toContain('/api/voice/transcribe');
    expect(calledUrls()[0]).not.toContain('/local/');
  });

  it('préférence absente + voix locale prête -> migre à true et route local', async () => {
    mockedFetch
      .mockResolvedValueOnce(localStatus({ ready: true, active_whisper_model: 'base' }))
      .mockResolvedValueOnce(okJson({ text: 'local' }));

    const text = await transcribeAudio(AUDIO);

    expect(text).toBe('local');
    expect(calledUrls()[0]).toContain('/api/voice/local/status');
    expect(calledUrls()[1]).toContain('/api/voice/local/transcribe');
    expect(getVoiceLocalPreference()).toBe(true);
  });

  it('préférence absente + voix locale pas prête -> persiste false et route Groq', async () => {
    mockedFetch
      .mockResolvedValueOnce(localStatus({ ready: false }))
      .mockResolvedValueOnce(okJson({ text: 'cloud' }));

    await transcribeAudio(AUDIO);

    expect(calledUrls()[0]).toContain('/api/voice/local/status');
    expect(calledUrls()[1]).toContain('/api/voice/transcribe');
    expect(getVoiceLocalPreference()).toBe(false);
  });

  it('préférence absente + installation en cours -> erreur claire, rien persisté, aucun audio envoyé', async () => {
    mockedFetch.mockResolvedValueOnce(
      localStatus({ ready: false, setup: { state: 'running', step: 'Téléchargement', error: '' } })
    );

    await expect(transcribeAudio(AUDIO)).rejects.toThrow(/installation.*en cours/i);
    // Un seul appel réseau : le status. Aucun audio n'est parti (ni local ni cloud).
    expect(calledUrls()).toHaveLength(1);
    expect(getVoiceLocalPreference()).toBeNull();
  });

  it('préférence absente + status injoignable -> Groq sans persister (on retentera)', async () => {
    mockedFetch
      .mockRejectedValueOnce(new Error('backend down'))
      .mockResolvedValueOnce(okJson({ text: 'cloud' }));

    await transcribeAudio(AUDIO);

    expect(calledUrls()[1]).toContain('/api/voice/transcribe');
    expect(getVoiceLocalPreference()).toBeNull();
  });
});

describe('synthesizeSpeech', () => {
  it('appelle uniquement la synthèse vocale locale', async () => {
    const wav = new Blob(['wav'], { type: 'audio/wav' });
    mockedFetch.mockResolvedValueOnce({ ok: true, blob: async () => wav } as Response);

    await expect(synthesizeSpeech('Bonjour')).resolves.toBe(wav);
    expect(calledUrls()[0]).toContain('/api/voice/tts');
  });
});
