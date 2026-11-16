/**
 * B-1928 : la fermeture du tiroir Contacts n'a qu'une icône X.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { useContactsStore } from '../../stores/contactsStore';
import { MemoryPanel } from './MemoryPanel';

vi.mock('../../services/api/memory', async () => {
  const reel = await vi.importActual<typeof import('../../services/api/memory')>('../../services/api/memory');
  return { ...reel, listContacts: vi.fn().mockResolvedValue([]), searchMemory: vi.fn().mockResolvedValue({ contacts: [] }) };
});
vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    listContactsWithScope: vi.fn().mockResolvedValue([]),
    listFiles: vi.fn().mockResolvedValue([]),
    getRGPDStats: vi.fn().mockResolvedValue(null),
  };
});
vi.mock('../../hooks', () => ({
  useDemoMask: () => ({ enabled: false, maskContact: (contact: unknown) => contact, populateMap: vi.fn() }),
}));
vi.mock('../files/FileBrowser', () => ({ FileBrowser: () => null }));

beforeEach(() => {
  useContactsStore.setState({ contacts: [], searchResults: null, loading: false, selectedContactId: null, truncated: false });
});

it('B-1928 : le tiroir nomme sa fermeture', () => {
  const fermer = vi.fn();
  render(<MemoryPanel isOpen onClose={fermer} />);
  fireEvent.click(screen.getByRole('button', { name: 'Fermer les contacts' }));
  expect(fermer).toHaveBeenCalledTimes(1);
});
