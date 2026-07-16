import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useVoiceRecorder } from '../../hooks/useVoiceRecorder';
import { VoiceDictationButton } from './VoiceDictationButton';

vi.mock('../../hooks/useVoiceRecorder', () => ({
  useVoiceRecorder: vi.fn(),
}));

const toggleRecording = vi.fn();

function mockVoiceState(overrides: Partial<ReturnType<typeof useVoiceRecorder>> = {}) {
  vi.mocked(useVoiceRecorder).mockReturnValue({
    state: 'idle',
    isRecording: false,
    isProcessing: false,
    pluginReady: true,
    startRecording: vi.fn(),
    stopRecording: vi.fn(),
    toggleRecording,
    error: null,
    ...overrides,
  });
}

describe('VoiceDictationButton', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockVoiceState();
  });

  it('utilise le recorder classique et transmet ses callbacks', () => {
    const onTranscript = vi.fn();
    const onError = vi.fn();

    render(<VoiceDictationButton onTranscript={onTranscript} onError={onError} />);
    fireEvent.click(screen.getByRole('button', { name: 'Message vocal' }));

    expect(useVoiceRecorder).toHaveBeenCalledWith({
      onTranscript,
      onError: expect.any(Function),
    });
    expect(toggleRecording).toHaveBeenCalledTimes(1);
  });

  it('reproduit les états enregistrement et transcription du bouton classique', () => {
    mockVoiceState({ state: 'recording', isRecording: true });
    const { rerender } = render(
      <VoiceDictationButton onTranscript={vi.fn()} onError={vi.fn()} />,
    );

    expect(screen.getByRole('button', { name: "Arrêter l'enregistrement" })).toBeEnabled();

    mockVoiceState({ state: 'processing', isProcessing: true });
    rerender(<VoiceDictationButton onTranscript={vi.fn()} onError={vi.fn()} />);

    expect(screen.getByRole('button', { name: 'Transcription en cours...' })).toBeDisabled();
  });

  it('attend que le plugin et les permissions micro soient prêts', () => {
    mockVoiceState({ pluginReady: false });

    render(<VoiceDictationButton onTranscript={vi.fn()} onError={vi.fn()} />);

    expect(screen.getByRole('button', { name: 'Chargement du micro...' })).toBeDisabled();
  });
});
