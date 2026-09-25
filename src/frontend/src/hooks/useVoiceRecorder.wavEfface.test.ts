/**
 * Dictée de l'app packagée (revue adverse de la RFC P-109, 25/09) : le greffon
 * micro écrit chaque enregistrement dans
 * `app_data_dir/tauri-plugin-mic-recorder/{horodatage}.wav`, le hook le lisait
 * puis ne l'effaçait jamais. Les voix dictées s'accumulaient sur le disque,
 * hors de toute purge.
 */
import { act, renderHook, waitFor } from '@testing-library/react';
import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';

const CHEMIN = '/app/tauri-plugin-mic-recorder/20260925170000.wav';
const { remove, readFile, transcribeAudio } = vi.hoisted(() => ({
  remove: vi.fn(),
  readFile: vi.fn(),
  transcribeAudio: vi.fn(),
}));

vi.mock('tauri-plugin-mic-recorder-api', () => ({
  startRecording: vi.fn().mockResolvedValue(undefined),
  stopRecording: vi.fn().mockResolvedValue(CHEMIN),
}));
vi.mock('@tauri-apps/plugin-fs', () => ({ readFile, remove }));
vi.mock('../services/api', () => ({ transcribeAudio }));

type Hook = typeof import('./useVoiceRecorder').useVoiceRecorder;
let useVoiceRecorder: Hook;

beforeAll(async () => {
  (window as unknown as Record<string, unknown>).__TAURI_INTERNALS__ = {};
  vi.resetModules();
  ({ useVoiceRecorder } = await import('./useVoiceRecorder'));
});

afterAll(() => {
  delete (window as unknown as Record<string, unknown>).__TAURI_INTERNALS__;
});

beforeEach(() => {
  remove.mockReset().mockResolvedValue(undefined);
  readFile.mockReset().mockResolvedValue(new Uint8Array([1, 2, 3]));
  transcribeAudio.mockReset();
});

async function dicter() {
  const { result } = renderHook(() => useVoiceRecorder({ onError: vi.fn() }));
  await waitFor(() => expect(result.current.pluginReady).toBe(true));
  await act(async () => { await result.current.startRecording(); });
  await act(async () => { await result.current.stopRecording(); });
  return result;
}

describe('la dictée efface son enregistrement', () => {
  it('après une transcription réussie', async () => {
    transcribeAudio.mockResolvedValue('bonjour');
    await dicter();
    expect(remove).toHaveBeenCalledWith(CHEMIN);
  });

  it('même quand la transcription échoue', async () => {
    transcribeAudio.mockRejectedValue(new Error('panne'));
    await dicter();
    expect(remove).toHaveBeenCalledWith(CHEMIN);
  });

  it('un effacement impossible ne casse pas la dictée', async () => {
    transcribeAudio.mockResolvedValue('bonjour');
    remove.mockRejectedValue(new Error('refusé'));
    const result = await dicter();
    expect(result.current.state).toBe('idle');
    expect(result.current.error).toBeNull();
  });
});
