/** P-052 (Nadia, c4) : quand ⌘⇧F demande la recherche, le champ « Rechercher un contact » prend le focus, même si la vue est déjà ouverte. */
import { act, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { MemoryPanel } from './MemoryPanel';
import { useContactsStore } from '../../stores/contactsStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { useStatusStore } from '../../stores/statusStore';

vi.mock('../../services/api/memory', async () => {
  const actual = await vi.importActual<typeof import('../../services/api/memory')>('../../services/api/memory');
  return {
    ...actual,
    listContactsWithScope: async () => [],
    listFiles: async () => [],
    getRGPDStats: async () => null,
  };
});
vi.mock('../../hooks', () => ({
  useDemoMask: () => ({ enabled: false, maskContact: (contact: unknown) => contact, populateMap: vi.fn() }),
}));
vi.mock('../files/FileBrowser', () => ({ FileBrowser: () => <div data-testid="file-browser" /> }));

describe('MemoryPanel : focus de la recherche à la demande (P-052)', () => {
  beforeEach(() => {
    useStatusStore.setState({ notifications: [] });
    useContactsStore.setState({ contacts: [], searchResults: null, loading: false, selectedContactId: null, truncated: false });
    useNavigationStore.setState({ activeView: 'memory', history: [], memorySearchFocusRequested: false });
  });

  it('une demande posée avant le montage met le focus dans le champ et se consomme', async () => {
    useNavigationStore.setState({ memorySearchFocusRequested: true });
    render(<MemoryPanel isOpen onClose={vi.fn()} />);
    await waitFor(() => expect(document.activeElement).toBe(screen.getByTestId('memory-search-input')));
    expect(useNavigationStore.getState().memorySearchFocusRequested).toBe(false);
  });

  it('une demande posée après le montage (vue déjà ouverte) met aussi le focus', async () => {
    render(<MemoryPanel isOpen onClose={vi.fn()} />);
    expect(document.activeElement).not.toBe(screen.getByTestId('memory-search-input'));
    await act(async () => { useNavigationStore.getState().requestMemorySearchFocus(); });
    await waitFor(() => expect(document.activeElement).toBe(screen.getByTestId('memory-search-input')));
  });
});
