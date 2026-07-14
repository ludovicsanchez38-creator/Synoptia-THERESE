import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ImagesWorkspaceCanvas } from './ImagesWorkspaceCanvas';
import {
  generateImage,
  getImageStatus,
  listGeneratedImages,
  type ImageResponse,
} from '../../services/api/images';

vi.mock('../../services/api/images', () => ({
  getImageStatus: vi.fn(),
  listGeneratedImages: vi.fn(),
  generateImage: vi.fn(),
  getImageDownloadUrl: vi.fn((id: string) => `http://localhost/image/${id}`),
  downloadGeneratedImage: vi.fn(),
}));

const historicalImage: ImageResponse = {
  id: 'image-old',
  provider: 'gpt-image-2',
  file_name: 'old.png',
  file_size: 1200,
  mime_type: 'image/png',
  created_at: '2026-07-13T10:00:00Z',
  prompt: 'Un atelier lumineux',
  download_url: '/api/images/download/image-old',
};

describe('ImagesWorkspaceCanvas', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getImageStatus).mockResolvedValue({
      openai_available: true,
      gemini_available: false,
      fal_available: false,
      active_provider: 'gpt-image-2',
    });
    vi.mocked(listGeneratedImages).mockResolvedValue({ images: [historicalImage], total: 1 });
    vi.mocked(generateImage).mockResolvedValue({
      ...historicalImage,
      id: 'image-new',
      prompt: 'Portrait éditorial de Thérèse',
      created_at: '2026-07-14T10:00:00Z',
    });
  });

  it('affiche l’historique réellement renvoyé par le backend', async () => {
    render(<ImagesWorkspaceCanvas onClose={vi.fn()} />);

    expect((await screen.findAllByText('Un atelier lumineux')).length).toBeGreaterThan(0);
    expect(getImageStatus).toHaveBeenCalledTimes(1);
    expect(listGeneratedImages).toHaveBeenCalledWith(50);
  });

  it('ne génère rien avant la confirmation explicite puis verrouille la requête', async () => {
    render(<ImagesWorkspaceCanvas onClose={vi.fn()} />);
    await screen.findAllByText('Un atelier lumineux');

    fireEvent.change(screen.getByLabelText('Description du visuel'), {
      target: { value: 'Portrait éditorial de Thérèse' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Préparer la génération' }));

    expect(screen.getByTestId('image-generation-confirmation')).toBeInTheDocument();
    expect(generateImage).not.toHaveBeenCalled();

    const confirmButton = screen.getByRole('button', { name: 'Confirmer et générer' });
    fireEvent.click(confirmButton);
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(generateImage).toHaveBeenCalledTimes(1);
      expect(generateImage).toHaveBeenCalledWith(expect.objectContaining({
        prompt: 'Portrait éditorial de Thérèse',
        provider: 'gpt-image-2',
      }));
    });
    expect((await screen.findAllByText('Portrait éditorial de Thérèse')).length).toBeGreaterThan(0);
  });
});
