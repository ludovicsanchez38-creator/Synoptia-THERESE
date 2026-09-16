/**
 * B-814 (cycle 9) : une validation de champ (« Décris le visuel en au moins 8
 * caractères ») était annoncée sous le titre « Studio Images indisponible »,
 * comme une panne de service.
 */
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ImagesWorkspaceCanvas } from './ImagesWorkspaceCanvas';
import { getImageStatus, listGeneratedImages } from '../../services/api/images';

vi.mock('../../services/api/images', () => ({
  getImageStatus: vi.fn(), listGeneratedImages: vi.fn(), generateImage: vi.fn(),
  getImageDownloadUrl: vi.fn((id: string) => `http://localhost/image/${id}`), downloadGeneratedImage: vi.fn(),
}));

describe('ImagesWorkspaceCanvas - B-814, le titre de l’alerte nomme ce qui manque', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getImageStatus).mockResolvedValue({ openai_available: false, gemini_available: false, fal_available: false, active_provider: null } as never);
    vi.mocked(listGeneratedImages).mockResolvedValue({ images: [], total: 0 });
  });

  it('description vide : « Description à compléter », pas « indisponible »', async () => {
    render(<ImagesWorkspaceCanvas onClose={vi.fn()} />);
    await waitFor(() => expect(getImageStatus).toHaveBeenCalled());
    fireEvent.click(screen.getByRole('button', { name: 'Préparer la génération' }));
    const alerte = await screen.findByRole('alert');
    expect(alerte).toHaveTextContent(/Description à compléter/);
    expect(alerte).not.toHaveTextContent(/indisponible/);
  });

  it('aucun moteur configuré : « Moteur à configurer »', async () => {
    render(<ImagesWorkspaceCanvas onClose={vi.fn()} />);
    await waitFor(() => expect(getImageStatus).toHaveBeenCalled());
    fireEvent.change(screen.getByLabelText('Description du visuel'), { target: { value: 'Un atelier lumineux au matin' } });
    fireEvent.click(screen.getByRole('button', { name: 'Préparer la génération' }));
    const alerte = await screen.findByRole('alert');
    expect(alerte).toHaveTextContent(/Moteur à configurer/);
    expect(alerte).not.toHaveTextContent(/indisponible/);
  });
});

describe('P-062 : le refus sans moteur dit où configurer', () => {
  it('l’alerte « Moteur à configurer » porte un bouton vers Paramètres > Services et connecteurs', async () => {
    const { usePanelStore } = await import('../../stores/panelStore');
    usePanelStore.setState({ showSettings: false, requestedSettingsTab: null } as never);
    render(<ImagesWorkspaceCanvas onClose={vi.fn()} />);
    await waitFor(() => expect(getImageStatus).toHaveBeenCalled());
    fireEvent.change(screen.getByLabelText('Description du visuel'), { target: { value: 'Un atelier lumineux au matin' } });
    fireEvent.click(screen.getByRole('button', { name: 'Préparer la génération' }));
    const alerte = await screen.findByRole('alert');
    fireEvent.click(within(alerte).getByRole('button', { name: /Ouvrir les Paramètres/ }));
    expect(usePanelStore.getState().showSettings).toBe(true);
    expect(usePanelStore.getState().requestedSettingsTab).toBe('services');
  });
});
