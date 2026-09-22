/** B-935 : les prompts déjà connus du masque démo ne doivent pas divulguer un client. */
import { act, cleanup, fireEvent, render, renderHook, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useDemoMask } from '../../hooks/useDemoMask';
import { useDemoStore } from '../../stores/demoStore';
import type { ImageResponse } from '../../services/api/images';
import { ImagesWorkspaceCanvas } from './ImagesWorkspaceCanvas';

const api = vi.hoisted(() => ({
  fetchImageObjectUrl: vi.fn(),
  generateImage: vi.fn(),
  getImageStatus: vi.fn(),
  listGeneratedImages: vi.fn(),
  downloadGeneratedImage: vi.fn(),
}));

vi.mock('../../services/api/images', () => ({
  ...api,
  getImageDownloadUrl: (id: string) => `/api/images/download/${id}`,
}));

const PROMPT_REEL = 'Portrait pour le client Victor Ruiz';
const PROMPT_DEMO = 'Portrait pour le client Alexandre Moreau';
const IMAGE: ImageResponse = {
  id: 'image-c10',
  provider: 'gpt-image-2',
  file_name: 'image-c10.png',
  file_size: 1_200,
  mime_type: 'image/png',
  created_at: '2026-09-22T10:00:00Z',
  prompt: PROMPT_REEL,
  download_url: '/api/images/download/image-c10',
};

async function monter(modeDemo: boolean) {
  useDemoStore.setState({
    enabled: modeDemo,
    replacementMap: new Map([['Victor Ruiz', 'Alexandre Moreau']]),
  });
  // Le masque réel est exercé : une erreur dans le jeu de remplacement ne
  // doit jamais être confondue avec un oubli de masquage dans le composant.
  const { result, unmount } = renderHook(() => useDemoMask());
  expect(result.current.maskText(PROMPT_REEL)).toBe(modeDemo ? PROMPT_DEMO : PROMPT_REEL);
  unmount();
  await act(async () => { render(<ImagesWorkspaceCanvas onClose={vi.fn()} />); });
  expect(api.listGeneratedImages).toHaveBeenCalledWith(50);
  expect(screen.getByTestId('selected-generated-image')).toBeInTheDocument();
}

describe('B-935 : prompts du studio Images en mode démo', () => {
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset());
    useDemoStore.setState({ enabled: false, replacementMap: new Map() });
    api.getImageStatus.mockResolvedValue({
      openai_available: true,
      gemini_available: false,
      fal_available: false,
      active_provider: 'gpt-image-2',
    });
    api.listGeneratedImages.mockResolvedValue({ images: [IMAGE], total: 1 });
    api.fetchImageObjectUrl.mockResolvedValue('blob:image-c10');
    api.generateImage.mockResolvedValue({ ...IMAGE, id: 'image-c10-nouvelle' });
    vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined);
  });

  afterEach(() => {
    cleanup();
    useDemoStore.setState({ enabled: false, replacementMap: new Map() });
    vi.restoreAllMocks();
  });

  it('garde les prompts et noms accessibles réels quand le mode démo est désactivé', async () => {
    await monter(false);

    expect(screen.getAllByText(PROMPT_REEL)).toHaveLength(2);
    expect(screen.getAllByRole('img', { name: PROMPT_REEL })).toHaveLength(2);
    expect(screen.getByRole('button', { name: /Victor Ruiz/ })).toBeInTheDocument();
    expect(api.fetchImageObjectUrl).toHaveBeenCalledWith(IMAGE.download_url);
  });

  it('masque le texte du prompt dans l’historique et la sélection', async () => {
    await monter(true);

    expect.soft(screen.queryAllByText(PROMPT_REEL)).toHaveLength(0);
    expect.soft(screen.queryAllByText(PROMPT_DEMO)).toHaveLength(2);
  });

  it('masque aussi le texte alternatif des images et le nom accessible de leur bouton', async () => {
    await monter(true);

    expect.soft(screen.queryAllByRole('img', { name: /Victor Ruiz/ })).toHaveLength(0);
    expect.soft(screen.queryAllByRole('img', { name: PROMPT_DEMO })).toHaveLength(2);
    expect.soft(screen.queryByRole('button', { name: /Victor Ruiz/ })).not.toBeInTheDocument();
    expect.soft(screen.queryByRole('button', { name: /Alexandre Moreau/ })).toBeInTheDocument();
  });

  it('masque le nom accessible de l’aperçu indisponible', async () => {
    api.fetchImageObjectUrl.mockRejectedValue(new Error('Fichier indisponible'));
    await monter(true);

    expect.soft(screen.queryAllByRole('img', { name: /Victor Ruiz/ })).toHaveLength(0);
    expect.soft(screen.queryAllByRole('img', {
      name: `Aperçu indisponible : ${PROMPT_DEMO}`,
    })).toHaveLength(2);
  });

  it('masque le nom accessible pendant le chargement des aperçus', async () => {
    api.fetchImageObjectUrl.mockReturnValue(new Promise(() => {}));
    await monter(true);

    expect.soft(screen.queryAllByRole('status', { name: /Victor Ruiz/ })).toHaveLength(0);
    expect.soft(screen.queryAllByRole('status', {
      name: `Chargement de l’aperçu : ${PROMPT_DEMO}`,
    })).toHaveLength(2);
  });

  it('masque le récapitulatif de confirmation sans changer la demande envoyée', async () => {
    await monter(true);
    fireEvent.change(screen.getByLabelText('Description du visuel'), {
      target: { value: PROMPT_REEL },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Préparer la génération' }));

    const confirmation = screen.getByTestId('image-generation-confirmation');
    expect.soft(confirmation).toHaveTextContent(PROMPT_DEMO);
    expect.soft(confirmation).not.toHaveTextContent(PROMPT_REEL);
    expect(api.generateImage).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer et générer' }));
    await waitFor(() => {
      expect(api.generateImage).toHaveBeenCalledWith(expect.objectContaining({ prompt: PROMPT_REEL }));
    });
  });
});
