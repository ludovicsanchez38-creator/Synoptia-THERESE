import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { VoiceWorkspaceCanvas } from './VoiceWorkspaceCanvas';
import { synthesizeSpeech, transcribeAudio } from '../../services/api/voice';

vi.mock('../../services/api/voice', () => ({
  getVoiceLocalPreference: vi.fn(() => true),
  getVoiceLocalStatus: vi.fn().mockResolvedValue({
    stt_available: true,
    tts_available: true,
    ready: true,
    whisper_models: {},
    default_whisper_model: 'base',
    active_whisper_model: 'base',
    models_downloaded: { base: true },
    tts_voice: 'fr',
    tts_voice_downloaded: true,
    setup: { state: 'done', step: '', error: '' },
  }),
  transcribeAudio: vi.fn(),
  synthesizeSpeech: vi.fn(),
}));

describe('VoiceWorkspaceCanvas', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(transcribeAudio).mockResolvedValue('Décision : lancer la bêta lundi.');
    vi.mocked(synthesizeSpeech).mockResolvedValue(new Blob(['wav'], { type: 'audio/wav' }));
    vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:voice');
    vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined);
  });

  it('importe le vrai fichier, confirme la transcription locale et transmet le texte au chat', async () => {
    const onContinueInChat = vi.fn();
    const { container } = render(<VoiceWorkspaceCanvas onClose={vi.fn()} onContinueInChat={onContinueInChat} />);
    const file = new File(['audio'], 'reunion.m4a', { type: 'audio/mp4' });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });

    fireEvent.click(screen.getByRole('button', { name: 'Préparer la transcription' }));
    expect(screen.getByTestId('voice-transcription-confirmation')).toHaveTextContent('Whisper local');
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer et transcrire' }));

    expect(await screen.findByDisplayValue('Décision : lancer la bêta lundi.')).toBeInTheDocument();
    expect(transcribeAudio).toHaveBeenCalledWith(file, 'reunion.m4a');
    fireEvent.click(screen.getByRole('button', { name: 'Analyser dans le chat' }));
    expect(onContinueInChat).toHaveBeenCalledWith(expect.stringContaining('lancer la bêta lundi'));
  });

  it('expose la synthèse Piper locale', async () => {
    render(<VoiceWorkspaceCanvas onClose={vi.fn()} onContinueInChat={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('Texte à lire'), { target: { value: 'Bonjour Ludo' } });
    await waitFor(() => expect(screen.getByRole('button', { name: 'Générer l’audio local' })).toBeEnabled());
    fireEvent.click(screen.getByRole('button', { name: 'Générer l’audio local' }));
    await waitFor(() => expect(synthesizeSpeech).toHaveBeenCalledWith('Bonjour Ludo'));
    expect(await screen.findByText('Audio généré localement')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Texte à lire'), { target: { value: 'Texte modifié' } });
    expect(screen.queryByText('Audio généré localement')).not.toBeInTheDocument();
  });

  it('affiche une erreur de synthèse dans le panneau concerné avec Réessayer', async () => {
    vi.mocked(synthesizeSpeech).mockRejectedValueOnce(new Error('Piper indisponible'));
    render(<VoiceWorkspaceCanvas onClose={vi.fn()} onContinueInChat={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('Texte à lire'), { target: { value: 'Bonjour Ludo' } });
    fireEvent.click(await screen.findByRole('button', { name: 'Générer l’audio local' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Piper indisponible');
    expect(screen.getByRole('button', { name: 'Réessayer' })).toBeInTheDocument();
  });
});
