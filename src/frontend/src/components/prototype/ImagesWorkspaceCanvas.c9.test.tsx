/**
 * B-766 (cycle 9) : « Actualiser l’historique » reposait le moteur depuis le
 * statut serveur et écrasait le moteur choisi à la main.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ImagesWorkspaceCanvas } from './ImagesWorkspaceCanvas';
import { getImageStatus, listGeneratedImages } from '../../services/api/images';

vi.mock('../../services/api/images', () => ({
  getImageStatus: vi.fn(),
  listGeneratedImages: vi.fn(),
  generateImage: vi.fn(),
  getImageDownloadUrl: vi.fn((id: string) => `http://localhost/image/${id}`),
  downloadGeneratedImage: vi.fn(),
}));

describe('ImagesWorkspaceCanvas - B-766, actualiser ne change pas le moteur choisi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getImageStatus).mockResolvedValue({
      openai_available: true, gemini_available: true, fal_available: false, active_provider: 'gpt-image-2',
    });
    vi.mocked(listGeneratedImages).mockResolvedValue({ images: [], total: 0 });
  });

  it('conserve le moteur sélectionné à la main après « Actualiser l’historique »', async () => {
    render(<ImagesWorkspaceCanvas onClose={vi.fn()} />);
    await waitFor(() => expect(getImageStatus).toHaveBeenCalledTimes(1));

    const gemini = screen.getByRole('radio', { name: /Nano Banana/ });
    fireEvent.click(gemini);
    expect(gemini).toBeChecked();

    fireEvent.click(screen.getByRole('button', { name: 'Actualiser l’historique' }));
    await waitFor(() => expect(getImageStatus).toHaveBeenCalledTimes(2));

    expect(screen.getByRole('radio', { name: /Nano Banana/ })).toBeChecked();
  });
});
