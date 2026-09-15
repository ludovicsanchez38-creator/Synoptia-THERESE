/**
 * B-780 (cycle 9) : le périmètre était filtré côté client sur une liste déjà
 * tronquée par le serveur (plafond) : un périmètre pouvait paraître vide alors
 * que des fiches existaient au-delà du plafond. Quand la liste est tronquée,
 * le périmètre se demande au serveur.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryPanel } from './MemoryPanel';
import { useStatusStore } from '../../stores/statusStore';
import { PLAFOND_CONTACTS, useContactsStore } from '../../stores/contactsStore';

const mockListContactsWithScope = vi.fn();
vi.mock('../../services/api/memory', async () => {
  const actual = await vi.importActual<typeof import('../../services/api/memory')>('../../services/api/memory');
  return { ...actual, listContacts: vi.fn().mockResolvedValue([]), searchMemory: vi.fn().mockResolvedValue({ contacts: [] }) };
});
vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, listContactsWithScope: (...a: unknown[]) => mockListContactsWithScope(...a), listFiles: vi.fn().mockResolvedValue([]), getRGPDStats: vi.fn().mockResolvedValue(null) };
});
vi.mock('../../hooks', () => ({ useDemoMask: () => ({ enabled: false, maskContact: (c: unknown) => c, populateMap: vi.fn() }) }));
vi.mock('../files/FileBrowser', () => ({ FileBrowser: () => <div data-testid="file-browser" /> }));

const contact = (i: number, scope: string) => ({ id: `c-${i}`, first_name: 'Contact', last_name: String(i), name: `Contact ${i}`, email: `c${i}@example.fr`, company: null, scope, created_at: '2026-09-01T00:00:00Z', updated_at: '2026-09-01T00:00:00Z' });

describe('MemoryPanel - B-780, périmètre demandé au serveur quand la liste est tronquée', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useStatusStore.setState({ notifications: [] });
    useContactsStore.setState({
      contacts: Array.from({ length: PLAFOND_CONTACTS }, (_, i) => contact(i, 'global')) as never,
      searchResults: null, loading: false, selectedContactId: null, truncated: true,
      fetchContacts: vi.fn().mockResolvedValue(undefined),
    } as never);
    mockListContactsWithScope.mockResolvedValue([{ ...contact(9001, 'project'), first_name: 'Zoé', last_name: 'Projet', name: 'Zoé Projet' }, { ...contact(9002, 'project'), first_name: 'Yann', last_name: 'Projet', name: 'Yann Projet' }]);
  });

  it('affiche les fiches « Projet » renvoyées par le serveur, au-delà du plafond', async () => {
    render(<MemoryPanel isOpen onClose={vi.fn()} />);
    await screen.findByText(/Contact 0/);
    fireEvent.click(screen.getByRole('button', { name: 'Projet' }));
    await waitFor(() => expect(mockListContactsWithScope).toHaveBeenCalledWith(0, PLAFOND_CONTACTS, 'project'));
    expect(await screen.findByText(/Zoé Projet/)).toBeInTheDocument();
    expect(screen.queryByText(/Contact 0/)).toBeNull();
  });
});
