import { render, screen, waitFor } from '@testing-library/react';
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

describe('B-756 - aperçu authentifié du studio Images', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.getImageStatus.mockResolvedValue({
      openai_available: true,
      gemini_available: false,
      fal_available: false,
      active_provider: 'gpt-image-2',
    });
    api.listGeneratedImages.mockResolvedValue({
      images: [{
        id: 'image-protegee',
        provider: 'gpt-image-2',
        file_name: 'image-protegee.png',
        file_size: 1_200,
        mime_type: 'image/png',
        created_at: '2026-07-13T10:00:00Z',
        prompt: 'Un atelier lumineux',
        download_url: '/api/images/download/image-protegee',
      }],
      total: 1,
    });
    api.fetchImageObjectUrl.mockResolvedValue('blob:image-protegee');
    vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('charge la grille et le grand aperçu via un blob authentifié puis le révoque', async () => {
    const { unmount } = render(<ImagesWorkspaceCanvas onClose={vi.fn()} />);

    const images = await screen.findAllByRole('img', { name: 'Un atelier lumineux' });
    expect(images).toHaveLength(2);

    await vi.waitFor(() => {
      expect(api.fetchImageObjectUrl).toHaveBeenCalledWith(
        'http://localhost/image/image-protegee',
      );
    });

    await waitFor(() => {
      expect(images.every((image) => image.getAttribute('src') === 'blob:image-protegee')).toBe(true);
    });

    unmount();

    await waitFor(() => {
      expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:image-protegee');
    });
  });
});
