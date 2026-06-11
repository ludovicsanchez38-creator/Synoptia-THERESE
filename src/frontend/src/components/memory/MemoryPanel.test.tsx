import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryPanel } from './MemoryPanel';
import { useStatusStore } from '../../stores/statusStore';
import { useContactsStore } from '../../stores/contactsStore';

const mockDownloadVCFFile = vi.fn();
const mockListContactsWithScope = vi.fn();
const mockListFiles = vi.fn();
const mockGetRGPDStats = vi.fn();

// contactsStore importe directement depuis services/api/memory : on le mocke ici
// pour éviter un fetch réel en jsdom et garder le test déterministe.
vi.mock('../../services/api/memory', async () => {
  const actual = await vi.importActual<typeof import('../../services/api/memory')>(
    '../../services/api/memory'
  );
  return {
    ...actual,
    listContacts: vi.fn().mockResolvedValue([]),
    searchMemory: vi.fn().mockResolvedValue({ contacts: [] }),
  };
});

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
    useContactsStore.setState({ contacts: [], searchResults: null, loading: false, selectedContactId: null });
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

// L6 (revue produit) : la Mémoire devient une VUE plein écran (content-swap),
// au même titre que CRM/Email/Agenda/Tâches/Factures. En mode `standalone`,
// pas de tiroir `fixed w-[420px]` ni de backdrop qui masque le chat.
describe('MemoryPanel mode standalone (vue L6)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockListFiles.mockResolvedValue([]);
    mockGetRGPDStats.mockResolvedValue(null);
    useContactsStore.setState({ contacts: [], searchResults: null, loading: false, selectedContactId: null });
  });

  it('rend une vue pleine hauteur, sans tiroir fixe 420px', async () => {
    render(<MemoryPanel standalone />);
    const panel = await screen.findByTestId('memory-panel');
    // flex-1 min-h-0 (et plus h-full) : pleine hauteur DANS le conteneur de
    // vue ; h-full débordait de la hauteur de la back-bar (bug 11/06/2026).
    expect(panel.className).toContain('flex-1');
    expect(panel.className).toContain('min-h-0');
    expect(panel.className).not.toContain('h-full');
    expect(panel.className).not.toContain('w-[420px]');
    expect(panel.className).not.toContain('fixed');
  });

  it('ne pose aucun backdrop qui masque le chat', async () => {
    const { container } = render(<MemoryPanel standalone />);
    await screen.findByTestId('memory-panel');
    // Le tiroir posait un backdrop `fixed inset-0 bg-black/40` par-dessus le chat.
    expect(container.querySelector('.bg-black\\/40')).toBeNull();
  });

  it('charge ses données sans dépendre de isOpen (standalone est toujours ouvert)', async () => {
    render(<MemoryPanel standalone />);
    // Le footer "Nouveau contact" n'existe que quand le contenu contacts est monté.
    expect(await screen.findByTestId('memory-add-contact-btn')).toBeInTheDocument();
  });
});
