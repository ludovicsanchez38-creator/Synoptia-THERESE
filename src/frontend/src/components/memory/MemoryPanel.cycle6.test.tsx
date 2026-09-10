/**
 * Cycle 6, lecteurs #149 et #150 (MemoryPanel.tsx).
 * - #149 : `loadData` avalait l'échec de `fetchContacts` ; le store posait
 *   pourtant `error`, mais le panneau ne le lisait pas : un carnet en panne
 *   s'affichait comme un carnet vide.
 * - #150 : un échec d'export VCF envoyait deux notifications, la première
 *   avec le message brut de l'exception.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useContactsStore } from '../../stores/contactsStore';
import { useStatusStore } from '../../stores/statusStore';

const { mockListContacts, mockDownloadVCF } = vi.hoisted(() => ({
  mockListContacts: vi.fn(),
  mockDownloadVCF: vi.fn(),
}));

vi.mock('../../services/api/memory', async () => {
  const actual = await vi.importActual<typeof import('../../services/api/memory')>('../../services/api/memory');
  return {
    ...actual,
    listContacts: (...args: unknown[]) => mockListContacts(...args),
    searchMemory: vi.fn().mockResolvedValue({ contacts: [] }),
  };
});
vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    listContactsWithScope: vi.fn().mockResolvedValue([]),
    listFiles: vi.fn().mockResolvedValue([]),
    getRGPDStats: vi.fn().mockResolvedValue(null),
    downloadVCFFile: (...args: unknown[]) => mockDownloadVCF(...args),
  };
});
vi.mock('../../hooks', () => ({
  useDemoMask: () => ({ enabled: false, maskContact: (c: unknown) => c, populateMap: vi.fn() }),
}));

import { MemoryPanel } from './MemoryPanel';

beforeEach(() => {
  vi.clearAllMocks();
  useContactsStore.setState({
    contacts: [], searchResults: null, loading: false, loaded: false, error: null, selectedContactId: null, truncated: false,
  });
  useStatusStore.setState({ notifications: [] });
});

describe('#149 : une panne de lecture des contacts est visible dans Contacts', () => {
  it('affiche une alerte avec reprise quand la lecture échoue, et la reprise relit', async () => {
    mockListContacts.mockRejectedValueOnce(new Error('boom')).mockResolvedValue([]);
    render(<MemoryPanel standalone />);
    expect(await screen.findByRole('alert')).toHaveTextContent(/Impossible de charger les contacts/);
    fireEvent.click(screen.getByRole('button', { name: 'Réessayer' }));
    await waitFor(() => expect(screen.queryByRole('alert')).toBeNull());
    expect(mockListContacts).toHaveBeenCalledTimes(2);
  });
});

describe('#150 : un export VCF en panne produit une seule notification', () => {
  it('une seule notification d’erreur, sans le message brut de l’exception', async () => {
    mockListContacts.mockResolvedValue([]);
    mockDownloadVCF.mockRejectedValue(new Error('TypeError: Failed to fetch'));
    render(<MemoryPanel standalone />);
    fireEvent.click((await screen.findAllByTitle('Exporter les contacts (.vcf)'))[0]);
    await waitFor(() => expect(useStatusStore.getState().notifications.length).toBeGreaterThan(0));
    const erreurs = useStatusStore.getState().notifications.filter((n) => n.type === 'error');
    expect(erreurs).toHaveLength(1);
    expect(erreurs[0].message).not.toMatch(/Failed to fetch/);
  });
});
