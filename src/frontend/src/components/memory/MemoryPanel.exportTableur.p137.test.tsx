/**
 * P-137 : « Exporter » ne disait pas son format et ne sortait qu'un vCard,
 * sans les étapes. L'écran Contacts propose aussi l'export en tableur.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryPanel } from './MemoryPanel';
import { useStatusStore } from '../../stores/statusStore';
import { useContactsStore } from '../../stores/contactsStore';

const mockDownloadContactsTableur = vi.fn();
vi.mock('../../services/api/memory', async () => {
  const actual = await vi.importActual<typeof import('../../services/api/memory')>('../../services/api/memory');
  return { ...actual, listContacts: vi.fn().mockResolvedValue([]), searchMemory: vi.fn().mockResolvedValue({ contacts: [] }) };
});
vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    downloadContactsTableur: (...args: unknown[]) => mockDownloadContactsTableur(...args),
    listContactsWithScope: vi.fn().mockResolvedValue([]),
    listFiles: vi.fn().mockResolvedValue([]),
    getRGPDStats: vi.fn().mockResolvedValue(null),
  };
});
vi.mock('../../hooks', () => ({ useDemoMask: () => ({ enabled: false, maskContact: (c: unknown) => c, populateMap: vi.fn() }) }));
vi.mock('../files/FileBrowser', () => ({ FileBrowser: () => <div data-testid="file-browser" /> }));

describe('P-137 : exporter les contacts en tableur depuis l’écran', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useStatusStore.setState({ notifications: [] });
    useContactsStore.setState({ contacts: [], searchResults: null, loading: false, selectedContactId: null, truncated: false });
  });

  it.each([
    ['vue plein écran', { standalone: true }],
    ['panneau', { isOpen: true }],
  ])('%s : le bouton dit son format et exporte, succès annoncé', async (_nom, props) => {
    mockDownloadContactsTableur.mockResolvedValue('desktop_saved');
    render(<MemoryPanel onClose={vi.fn()} {...props} />);
    fireEvent.click(await screen.findByRole('button', { name: /Exporter en tableur \(\.xlsx\)/ }));
    await waitFor(() => expect(mockDownloadContactsTableur).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(useStatusStore.getState().notifications).toEqual(expect.arrayContaining([
      expect.objectContaining({ type: 'success', message: 'Contacts exportés en tableur dans Téléchargements' }),
    ])));
    expect(screen.getByRole('button', { name: /Exporter \(\.vcf\)|Exporter VCF/ })).toBeInTheDocument();
  });
});
