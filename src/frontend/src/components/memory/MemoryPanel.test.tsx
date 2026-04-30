import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryPanel } from './MemoryPanel';
import { useStatusStore } from '../../stores/statusStore';

const mockDownloadVCFFile = vi.fn();
const mockListContactsWithScope = vi.fn();
const mockListFiles = vi.fn();
const mockGetRGPDStats = vi.fn();

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    downloadVCFFile: (...args: unknown[]) => mockDownloadVCFFile(...args),
    listContactsWithScope: (...args: unknown[]) => mockListContactsWithScope(...args),
    listFiles: (...args: unknown[]) => mockListFiles(...args),
    getRGPDStats: (...args: unknown[]) => mockGetRGPDStats(...args),
  };
});

vi.mock('../../hooks', () => ({
  useDemoMask: () => ({
    enabled: false,
    maskContact: (contact: unknown) => contact,
    populateMap: vi.fn(),
  }),
}));

vi.mock('../files/FileBrowser', () => ({
  FileBrowser: () => <div data-testid="file-browser" />,
}));

describe('MemoryPanel export VCF', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(window, 'alert').mockImplementation(() => undefined);
    mockListContactsWithScope.mockResolvedValue([]);
    mockListFiles.mockResolvedValue([]);
    mockGetRGPDStats.mockResolvedValue(null);
    useStatusStore.setState({ notifications: [] });
  });

  it('affiche un succès desktop quand l export est réellement sauvegardé', async () => {
    mockDownloadVCFFile.mockResolvedValue('desktop_saved');

    render(<MemoryPanel isOpen onClose={vi.fn()} />);

    fireEvent.click(await screen.findByTitle('Exporter les contacts (.vcf)'));

    await waitFor(() => {
      expect(useStatusStore.getState().notifications).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            type: 'success',
            title: 'Export VCF',
            message: 'Contacts exportés dans Téléchargements',
          }),
        ])
      );
    });
  });

  it('affiche un succès web quand le téléchargement navigateur démarre', async () => {
    mockDownloadVCFFile.mockResolvedValue('browser_download_started');

    render(<MemoryPanel isOpen onClose={vi.fn()} />);

    fireEvent.click(await screen.findByTitle('Exporter les contacts (.vcf)'));

    await waitFor(() => {
      expect(useStatusStore.getState().notifications).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            type: 'success',
            title: 'Export VCF',
            message: 'Téléchargement du fichier VCF démarré',
          }),
        ])
      );
    });
  });

  it('affiche une erreur visible si l export échoue', async () => {
    mockDownloadVCFFile.mockRejectedValue(new Error('disk full'));

    render(<MemoryPanel isOpen onClose={vi.fn()} />);

    fireEvent.click(await screen.findByTitle('Exporter les contacts (.vcf)'));

    await waitFor(() => {
      expect(useStatusStore.getState().notifications).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            type: 'error',
            title: 'Erreur export VCF',
            message: 'disk full',
          }),
        ])
      );
    });
  });
});
