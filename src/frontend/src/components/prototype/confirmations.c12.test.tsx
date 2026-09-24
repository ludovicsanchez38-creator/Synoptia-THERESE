/**
 * Lecteur D de la carte c12 : B-1059 (la confirmation d'Images ne reçoit pas
 * le focus), B-1061 (« Annuler » laisse tomber le focus sur la page) et B-1062
 * (« Synthèse vocale impossible » n'est pas amenée dans la vue).
 */
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const images = vi.hoisted(() => ({
  fetchImageObjectUrl: vi.fn(), generateImage: vi.fn(), getImageStatus: vi.fn(),
  listGeneratedImages: vi.fn(), downloadGeneratedImage: vi.fn(),
}));
vi.mock('../../services/api/images', () => ({ ...images, getImageDownloadUrl: (id: string) => `/api/images/download/${id}` }));
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

import { ImagesWorkspaceCanvas } from './ImagesWorkspaceCanvas';
import { VoiceWorkspaceCanvas } from './VoiceWorkspaceCanvas';
import { synthesizeSpeech } from '../../services/api/voice';

const scrollIntoView = vi.fn();
const original = Element.prototype.scrollIntoView;

describe('cycle 12 : confirmations en ligne d’Images et de Voix', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Element.prototype.scrollIntoView = scrollIntoView;
    images.getImageStatus.mockResolvedValue({ openai_available: true, gemini_available: false, fal_available: false, active_provider: 'gpt-image-2' });
    images.listGeneratedImages.mockResolvedValue({ images: [], total: 0 });
  });
  afterEach(() => { Element.prototype.scrollIntoView = original; });

  async function preparerLaGeneration() {
    await act(async () => { render(<ImagesWorkspaceCanvas onClose={vi.fn()} />); });
    fireEvent.change(screen.getByLabelText('Description du visuel'), { target: { value: 'Un atelier lumineux au matin' } });
    const preparer = screen.getByRole('button', { name: 'Préparer la génération' });
    preparer.focus();
    fireEvent.click(preparer);
    return screen.getByTestId('image-generation-confirmation');
  }

  it('B-1059 : la confirmation d’Images reçoit le focus à son apparition', async () => {
    const confirmation = await preparerLaGeneration();
    await waitFor(() => expect(within(confirmation).getByRole('button', { name: 'Annuler' })).toHaveFocus());
  });

  it('B-1061 : « Annuler » dans Images rend le focus à « Préparer la génération »', async () => {
    const confirmation = await preparerLaGeneration();
    const annuler = within(confirmation).getByRole('button', { name: 'Annuler' });
    annuler.focus();
    fireEvent.click(annuler);
    await waitFor(() => expect(screen.getByRole('button', { name: 'Préparer la génération' })).toHaveFocus());
  });

  it('B-1061 : « Annuler » dans Voix rend le focus à « Préparer la transcription »', async () => {
    const { container } = render(<VoiceWorkspaceCanvas onClose={vi.fn()} onContinueInChat={vi.fn()} />);
    fireEvent.change(container.querySelector('input[type="file"]') as HTMLInputElement, { target: { files: [new File(['a'], 'r.m4a', { type: 'audio/mp4' })] } });
    fireEvent.click(screen.getByRole('button', { name: 'Préparer la transcription' }));
    const annuler = within(screen.getByTestId('voice-transcription-confirmation')).getByRole('button', { name: 'Annuler' });
    annuler.focus();
    fireEvent.click(annuler);
    await waitFor(() => expect(screen.getByRole('button', { name: 'Préparer la transcription' })).toHaveFocus());
  });

  it('B-1062 : « Synthèse vocale impossible » est amenée dans la vue', async () => {
    vi.mocked(synthesizeSpeech).mockRejectedValueOnce(new Error('Piper indisponible'));
    render(<VoiceWorkspaceCanvas onClose={vi.fn()} onContinueInChat={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('Texte à lire'), { target: { value: 'Bonjour Ludo' } });
    fireEvent.click(await screen.findByRole('button', { name: 'Générer l’audio local' }));
    const alerte = (await screen.findByText('Synthèse vocale impossible')).closest('[role="alert"]') as Element;
    await waitFor(() => expect(scrollIntoView.mock.contexts).toContain(alerte));
  });
});
