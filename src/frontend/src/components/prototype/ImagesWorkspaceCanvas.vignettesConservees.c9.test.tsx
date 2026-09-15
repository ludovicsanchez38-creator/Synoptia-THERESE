/**
 * B-862 (cycle 9) : chaque génération remplaçait le tableau des images, ce
 * qui relançait l'effet de chargement des aperçus : toutes les vignettes déjà
 * chargées étaient révoquées puis re-téléchargées une par une par appel
 * authentifié, jusqu'à cinquante, à chaque nouvelle image.
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

describe('ImagesWorkspaceCanvas - B-862, une génération ne recharge pas les vignettes existantes', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.getImageStatus.mockResolvedValue({ openai_available: true, gemini_available: false, fal_available: false, active_provider: 'gpt-image-2' });
    api.listGeneratedImages.mockResolvedValue({ images: [image('img-a', 'Un atelier lumineux'), image('img-b', 'Une vitrine')], total: 2 });
    api.fetchImageObjectUrl.mockImplementation(async (url: string) => `blob:${url}`);
    api.generateImage.mockResolvedValue(image('img-c', 'Portrait éditorial de Thérèse'));
    vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('ne télécharge que la nouvelle image et ne révoque aucune vignette encore affichée', async () => {
    render(<ImagesWorkspaceCanvas onClose={vi.fn()} />);
    await screen.findAllByText('Une vitrine');
    await waitFor(() => expect(api.fetchImageObjectUrl).toHaveBeenCalledTimes(2));

    fireEvent.change(screen.getByLabelText('Description du visuel'), { target: { value: 'Portrait éditorial de Thérèse' } });
    fireEvent.click(screen.getByRole('button', { name: 'Préparer la génération' }));
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer et générer' }));
    await screen.findAllByText('Portrait éditorial de Thérèse');
    await waitFor(() => expect(api.fetchImageObjectUrl).toHaveBeenCalledWith('http://localhost/image/img-c'));

    expect(api.fetchImageObjectUrl).toHaveBeenCalledTimes(3);
    expect(URL.revokeObjectURL).not.toHaveBeenCalledWith('blob:http://localhost/image/img-a');
    expect(URL.revokeObjectURL).not.toHaveBeenCalledWith('blob:http://localhost/image/img-b');
  });
});
