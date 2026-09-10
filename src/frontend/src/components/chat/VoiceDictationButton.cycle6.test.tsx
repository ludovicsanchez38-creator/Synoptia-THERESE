/**
 * Cycle 6, lecteur D67 (VoiceDictationButton.tsx) : pendant l'enregistrement,
 * l'écran annonçait un « Aperçu audio en direct » fait de cinq barres aux
 * hauteurs écrites en dur : rien ne lisait le micro. L'annonce ne promet plus
 * ce que le code ne mesure pas.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { useVoiceRecorder } from '../../hooks/useVoiceRecorder';
import { VoiceDictationButton } from './VoiceDictationButton';

vi.mock('../../hooks/useVoiceRecorder', () => ({ useVoiceRecorder: vi.fn() }));
vi.mock('../../services/api/voice', () => ({ needsVoiceCloudConsent: vi.fn().mockResolvedValue(false), VOICE_CLOUD_PROVIDER: 'Groq' }));

describe('D67 : l’état d’enregistrement ne promet pas un aperçu du micro', () => {
  it('aucune mention d’aperçu en direct ; les barres sont décoratives', () => {
    vi.mocked(useVoiceRecorder).mockReturnValue({
      state: 'recording', isRecording: true, isProcessing: false, pluginReady: true, startRecording: vi.fn(),
      stopRecording: vi.fn(), toggleRecording: vi.fn(), cancelProcessing: vi.fn(), elapsedSeconds: 3, error: null,
    } as never);
    render(<VoiceDictationButton onTranscript={vi.fn()} onError={vi.fn()} />);
    const statut = screen.getByRole('status');
    expect(statut).toHaveTextContent(/Enregistrement en cours/);
    expect(statut.textContent).not.toMatch(/Aperçu|en direct|live/i);
    expect(screen.queryByLabelText(/Aperçu/)).toBeNull();
    expect(statut.querySelector('[aria-hidden="true"][data-decoratif]')).not.toBeNull();
  });
});
