/**
 * Ronde B4 du cycle 11 : B-1032 (Images et Voix, messages et boutons de
 * confirmation sous le pli de leur section défilante ; le focus visait un
 * bouton radio désactivé) et B-1034 (Voix, focus perdu sur la page quand la
 * confirmation remplace le bouton « Préparer la transcription »).
 */
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ImagesWorkspaceCanvas } from './ImagesWorkspaceCanvas';
import { VoiceWorkspaceCanvas } from './VoiceWorkspaceCanvas';
import { getImageStatus, listGeneratedImages } from '../../services/api/images';
import { transcribeAudio } from '../../services/api/voice';

vi.mock('../../services/api/images', () => ({
  getImageStatus: vi.fn(), listGeneratedImages: vi.fn(), generateImage: vi.fn(),
  getImageDownloadUrl: vi.fn((id: string) => `http://localhost/image/${id}`), downloadGeneratedImage: vi.fn(),
}));
vi.mock('../../services/api/voice', () => ({
  getVoiceLocalPreference: vi.fn(() => true),
  getVoiceLocalStatus: vi.fn().mockResolvedValue({
    stt_available: true, tts_available: true, ready: true, whisper_models: {},
    default_whisper_model: 'base', active_whisper_model: 'base', models_downloaded: { base: true },
    tts_voice: 'fr', tts_voice_downloaded: true, setup: { state: 'done', step: '', error: '' },
  }),
  transcribeAudio: vi.fn(),
  synthesizeSpeech: vi.fn(),
}));

const scrollIntoView = vi.fn();
const original = Element.prototype.scrollIntoView;
const amenesDansLaVue = () => scrollIntoView.mock.contexts as Element[];

describe('cycle 12 : Images et Voix amènent leurs messages dans la vue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    scrollIntoView.mockClear();
    Element.prototype.scrollIntoView = scrollIntoView;
    vi.mocked(getImageStatus).mockResolvedValue({ openai_available: false, gemini_available: false, fal_available: false, active_provider: null } as never);
    vi.mocked(listGeneratedImages).mockResolvedValue({ images: [], total: 0 });
  });
  afterEach(() => { Element.prototype.scrollIntoView = original; });

  it('B-1032 Images : description trop courte, le message est amené dans la vue', async () => {
    render(<ImagesWorkspaceCanvas onClose={vi.fn()} />);
    await waitFor(() => expect(getImageStatus).toHaveBeenCalled());
    fireEvent.change(screen.getByLabelText('Description du visuel'), { target: { value: 'chat' } });
    fireEvent.click(screen.getByRole('button', { name: 'Préparer la génération' }));
    const alerte = await screen.findByRole('alert');
    await waitFor(() => expect(amenesDansLaVue()).toContain(alerte));
  });

  it('B-1032 Images : moteur non configuré, le focus va au geste qui répare, pas au bouton radio désactivé', async () => {
    render(<ImagesWorkspaceCanvas onClose={vi.fn()} />);
    await waitFor(() => expect(getImageStatus).toHaveBeenCalled());
    fireEvent.change(screen.getByLabelText('Description du visuel'), { target: { value: 'Un atelier lumineux au matin' } });
    fireEvent.click(screen.getByRole('button', { name: 'Préparer la génération' }));
    const alerte = await screen.findByRole('alert');
    await waitFor(() => expect(within(alerte).getByRole('button', { name: /Ouvrir les Paramètres/ })).toHaveFocus());
    expect(amenesDansLaVue()).toContain(alerte);
  });

  function preparerLaTranscription() {
    const { container } = render(<VoiceWorkspaceCanvas onClose={vi.fn()} onContinueInChat={vi.fn()} />);
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [new File(['audio'], 'reunion.m4a', { type: 'audio/mp4' })] } });
    const bouton = screen.getByRole('button', { name: 'Préparer la transcription' });
    bouton.focus();
    fireEvent.click(bouton);
  }

  it('B-1034 Voix : la confirmation qui remplace le bouton reçoit le focus et est amenée dans la vue', async () => {
    preparerLaTranscription();
    const confirmation = screen.getByTestId('voice-transcription-confirmation');
    await waitFor(() => expect(within(confirmation).getByRole('button', { name: 'Annuler' })).toHaveFocus());
    expect(amenesDansLaVue()).toContain(confirmation);
  });

  it('B-1032 Voix : « Transcription impossible » est amenée dans la vue', async () => {
    vi.mocked(transcribeAudio).mockRejectedValue(new Error('Whisper indisponible'));
    preparerLaTranscription();
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer et transcrire' }));
    const erreur = (await screen.findByText('Transcription impossible')).closest('[role="alert"]') as Element;
    await waitFor(() => expect(amenesDansLaVue()).toContain(erreur));
  });
});
