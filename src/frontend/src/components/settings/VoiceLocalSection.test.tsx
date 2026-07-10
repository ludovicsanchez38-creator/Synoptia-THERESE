/**
 * BUG-129 (revue Codex 10/07) - l'INTENTION d'activation doit être mémorisée.
 *
 * Trou de séquence relevé en revue : première dictée sans voix locale ->
 * préférence auto-persistée à 'false' ; l'utilisateur clique ensuite
 * « Activer la voix locale » ; la réconciliation ne rebasculait que si la
 * préférence était null -> le micro restait routé vers Groq après le
 * téléchargement. Le clic « Activer » est un choix EXPLICITE : il doit poser
 * la préférence à true immédiatement.
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { VoiceLocalSection } from './VoiceLocalSection';
import {
  getVoiceLocalPreference,
  getVoiceLocalStatus,
  setVoiceLocalPreferred,
  setupVoiceLocal,
  type VoiceLocalStatus,
} from '../../services/api/voice';
import { installLocalStorageStub } from '../../test/localStorage-stub';

vi.mock('../../services/api/voice', async () => {
  const actual = await vi.importActual<typeof import('../../services/api/voice')>(
    '../../services/api/voice'
  );
  return { ...actual, getVoiceLocalStatus: vi.fn(), setupVoiceLocal: vi.fn() };
});

const mockedStatus = vi.mocked(getVoiceLocalStatus);
const mockedSetup = vi.mocked(setupVoiceLocal);

function notReadyStatus(): VoiceLocalStatus {
  return {
    stt_available: true,
    tts_available: true,
    ready: false,
    whisper_models: { base: { size_mb: 145, ram_mb: 500, label: 'Base' } },
    default_whisper_model: 'base',
    active_whisper_model: null,
    models_downloaded: {},
    tts_voice: 'fr',
    tts_voice_downloaded: false,
    setup: { state: 'idle', step: '', error: '' },
  };
}

describe('BUG-129 - activation = intention explicite', () => {
  beforeEach(() => {
    installLocalStorageStub();
    mockedStatus.mockReset();
    mockedSetup.mockReset();
  });

  it("cliquer « Activer » pose la préférence locale à true, même si une dictée cloud l'avait posée à false", async () => {
    // Séquence du testeur : une dictée sans voix locale a persisté 'false'.
    setVoiceLocalPreferred(false);
    mockedStatus.mockResolvedValue(notReadyStatus());
    mockedSetup.mockResolvedValue(undefined);

    render(<VoiceLocalSection />);
    const button = await screen.findByRole('button', { name: /activer la voix locale/i });
    fireEvent.click(button);

    await waitFor(() => expect(mockedSetup).toHaveBeenCalled());
    expect(getVoiceLocalPreference()).toBe(true);
  });

  it("si l'activation échoue, la préférence n'est pas posée", async () => {
    mockedStatus.mockResolvedValue(notReadyStatus());
    mockedSetup.mockRejectedValue(new Error('réseau'));

    render(<VoiceLocalSection />);
    const button = await screen.findByRole('button', { name: /activer la voix locale/i });
    fireEvent.click(button);

    await waitFor(() => expect(mockedSetup).toHaveBeenCalled());
    expect(getVoiceLocalPreference()).toBeNull();
  });
});
