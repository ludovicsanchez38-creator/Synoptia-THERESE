import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useVoiceRecorder } from '../../hooks/useVoiceRecorder';
import { needsVoiceCloudConsent } from '../../services/api/voice';
import { hasCloudConsent } from '../../lib/consent';
import { VoiceDictationButton } from './VoiceDictationButton';

vi.mock('../../hooks/useVoiceRecorder', () => ({
  useVoiceRecorder: vi.fn(),
}));

// Revue 0.40 : le bouton pré-vérifie le consentement Groq avant une dictée
// cloud. Mock du service pour ne jamais toucher le réseau dans ces tests.
vi.mock('../../services/api/voice', () => ({
  needsVoiceCloudConsent: vi.fn().mockResolvedValue(false),
  VOICE_CLOUD_PROVIDER: 'Groq',
}));

const toggleRecording = vi.fn();
const cancelProcessing = vi.fn();

function mockVoiceState(overrides: Partial<ReturnType<typeof useVoiceRecorder>> = {}) {
  vi.mocked(useVoiceRecorder).mockReturnValue({
    state: 'idle',
    isRecording: false,
    isProcessing: false,
    pluginReady: true,
    startRecording: vi.fn(),
    stopRecording: vi.fn(),
    toggleRecording,
    cancelProcessing,
    elapsedSeconds: 0,
    error: null,
    ...overrides,
  });
}

describe('VoiceDictationButton', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockVoiceState();
  });

  it('utilise le recorder classique et transmet ses callbacks', async () => {
    const onTranscript = vi.fn();
    const onError = vi.fn();

    render(<VoiceDictationButton onTranscript={onTranscript} onError={onError} />);
    fireEvent.click(screen.getByRole('button', { name: 'Message vocal' }));

    expect(useVoiceRecorder).toHaveBeenCalledWith({
      onTranscript,
      onError: expect.any(Function),
    });
    await waitFor(() => expect(toggleRecording).toHaveBeenCalledTimes(1));
  });

  it('reproduit les états enregistrement et transcription du bouton classique', () => {
    mockVoiceState({ state: 'recording', isRecording: true, elapsedSeconds: 12 });
    const { rerender } = render(
      <VoiceDictationButton onTranscript={vi.fn()} onError={vi.fn()} />,
    );

    expect(screen.getByRole('button', { name: "Arrêter l'enregistrement" })).toBeEnabled();
    expect(screen.getByRole('status')).toHaveTextContent('Écoute 00:12');
    expect(screen.getByLabelText('Aperçu live de la dictée')).toBeInTheDocument();

    mockVoiceState({ state: 'processing', isProcessing: true });
    rerender(<VoiceDictationButton onTranscript={vi.fn()} onError={vi.fn()} />);

    expect(screen.getByRole('button', { name: 'Transcription en cours...' })).toBeDisabled();
    expect(screen.getByRole('status')).toHaveTextContent('Transcription en cours');
    fireEvent.click(screen.getByRole('button', { name: 'Annuler' }));
    expect(cancelProcessing).toHaveBeenCalledTimes(1);
  });

  it('attend que le plugin et les permissions micro soient prêts', () => {
    mockVoiceState({ pluginReady: false });

    render(<VoiceDictationButton onTranscript={vi.fn()} onError={vi.fn()} />);

    expect(screen.getByRole('button', { name: 'Chargement du micro...' })).toBeDisabled();
  });
});

describe('VoiceDictationButton - consentement dictée cloud (revue 0.40)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockVoiceState();
    // localStorage à mémoire réelle pour que le grant se relise.
    const store: Record<string, string> = {};
    vi.stubGlobal('localStorage', {
      getItem: (k: string) => store[k] ?? null,
      setItem: (k: string, v: string) => {
        store[k] = v;
      },
      removeItem: (k: string) => {
        delete store[k];
      },
      clear: () => {
        for (const k of Object.keys(store)) delete store[k];
      },
    });
  });

  afterEach(() => vi.unstubAllGlobals());

  it('demande l’accord Groq au premier usage cloud, puis démarre la dictée', async () => {
    vi.mocked(needsVoiceCloudConsent).mockResolvedValue(true);
    render(<VoiceDictationButton onTranscript={vi.fn()} onError={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: 'Message vocal' }));

    expect(await screen.findByText(/envoie ton audio à Groq/)).toBeInTheDocument();
    expect(toggleRecording).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Autoriser et dicter' }));

    expect(hasCloudConsent('voice', 'Groq')).toBe(true);
    await waitFor(() => expect(toggleRecording).toHaveBeenCalledTimes(1));
  });

  it('refuser ferme la demande sans consentir ni dicter', async () => {
    vi.mocked(needsVoiceCloudConsent).mockResolvedValue(true);
    render(<VoiceDictationButton onTranscript={vi.fn()} onError={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: 'Message vocal' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Pas maintenant' }));

    expect(hasCloudConsent('voice', 'Groq')).toBe(false);
    expect(toggleRecording).not.toHaveBeenCalled();
    expect(screen.queryByText(/envoie ton audio à Groq/)).not.toBeInTheDocument();
  });

  it('voix locale active ou accord déjà donné : dictée directe, sans demande', async () => {
    vi.mocked(needsVoiceCloudConsent).mockResolvedValue(false);
    render(<VoiceDictationButton onTranscript={vi.fn()} onError={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: 'Message vocal' }));

    await waitFor(() => expect(toggleRecording).toHaveBeenCalledTimes(1));
    expect(screen.queryByText(/envoie ton audio à Groq/)).not.toBeInTheDocument();
  });
});
