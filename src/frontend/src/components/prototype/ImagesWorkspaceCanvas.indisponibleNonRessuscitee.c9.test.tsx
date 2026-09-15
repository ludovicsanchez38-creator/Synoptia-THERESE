/**
 * B-895 (cycle 9, relecteur V3) : une vignette marquée indisponible (l'image
 * ne se décode pas) révoquait son URL objet mais restait dans la table des
 * vignettes chargées : à la génération suivante, la table la ressuscitait avec
 * l'URL révoquée, sans re-téléchargement, et l'image restait cassée.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ImagesWorkspaceCanvas } from './ImagesWorkspaceCanvas';

const api = vi.hoisted(() => ({
  fetchImageObjectUrl: vi.fn(),
  generateImage: vi.fn(),
  getImageStatus: vi.fn(),
  listGeneratedImages: vi.fn(),
}));

vi.mock('../../services/api/images', () => ({
  downloadGeneratedImage: vi.fn(),
  fetchImageObjectUrl: api.fetchImageObjectUrl,
  generateImage: api.generateImage,
  getImageDownloadUrl: vi.fn((id: string) => `http://localhost/image/${id}`),
  getImageStatus: api.getImageStatus,
  listGeneratedImages: api.listGeneratedImages,
}));

function image(id: string, prompt: string) {
  return {
    id, provider: 'gpt-image-2', file_name: `${id}.png`, file_size: 1_200, mime_type: 'image/png',
    created_at: '2026-07-13T10:00:00Z', prompt, download_url: `/api/images/download/${id}`,
  };
}

describe('ImagesWorkspaceCanvas - B-895, une vignette illisible n’est pas ressuscitée avec une URL révoquée', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.getImageStatus.mockResolvedValue({ openai_available: true, gemini_available: false, fal_available: false, active_provider: 'gpt-image-2' });
    api.listGeneratedImages.mockResolvedValue({ images: [image('img-a', 'Un atelier lumineux')], total: 1 });
    api.fetchImageObjectUrl.mockImplementation(async (url: string) => `blob:${url}`);
    api.generateImage.mockResolvedValue(image('img-c', 'Portrait éditorial de Thérèse'));
    vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined);
  });
  afterEach(() => vi.restoreAllMocks());

  it('après un aperçu illisible, la génération suivante retente le téléchargement au lieu de remettre l’URL révoquée', async () => {
    render(<ImagesWorkspaceCanvas onClose={vi.fn()} />);
    const apercus = await screen.findAllByRole('img', { name: 'Un atelier lumineux' });
    await waitFor(() => expect(api.fetchImageObjectUrl).toHaveBeenCalledTimes(1));

    fireEvent.error(apercus[0]);
    expect(await screen.findAllByRole('img', { name: 'Aperçu indisponible : Un atelier lumineux' })).not.toHaveLength(0);

    fireEvent.change(screen.getByLabelText('Description du visuel'), { target: { value: 'Portrait éditorial de Thérèse' } });
    fireEvent.click(screen.getByRole('button', { name: 'Préparer la génération' }));
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer et générer' }));
    await screen.findAllByText('Portrait éditorial de Thérèse');

    await waitFor(() => expect(api.fetchImageObjectUrl).toHaveBeenCalledWith('http://localhost/image/img-c'));
    await waitFor(() => expect(api.fetchImageObjectUrl.mock.calls.filter(([u]) => u === 'http://localhost/image/img-a')).toHaveLength(2));
  });
});
