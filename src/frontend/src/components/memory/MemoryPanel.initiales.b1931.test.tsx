/**
 * B-1931 : la puce d'initiales retombe sur « ? » sans prénom ni nom,
 * même quand le titre de ligne affiche l'entreprise ou l'e-mail.
 */
import { render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { useContactsStore } from '../../stores/contactsStore';
import { MemoryPanel } from './MemoryPanel';

vi.mock('../files/FileBrowser', () => ({ FileBrowser: () => null }));
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api')>()),
  listProjects: vi.fn().mockResolvedValue([]),
  getRGPDStats: vi.fn().mockResolvedValue(null),
}));

function afficher(over: Record<string, unknown>) {
  useContactsStore.setState({
    contacts: [{
      id: 'ct-sa', first_name: null, last_name: null, company: null, email: null,
      phone: null, address: null, notes: null, tags: [], stage: 'contact', score: 0,
      source: null, last_interaction: null, created_at: '2026-09-22T10:00:00Z',
      updated_at: '2026-09-22T10:00:00Z', ...over,
    }],
    searchResults: null, loading: false, selectedContactId: null, truncated: false,
    loaded: true, fetchContacts: vi.fn().mockResolvedValue(undefined),
  } as never);
  render(<MemoryPanel standalone />);
}

it('B-1931 : la puce reprend l’entreprise', async () => {
  afficher({ company: 'Sans Nom SA' });
  expect(await screen.findAllByText('Sans Nom SA')).not.toHaveLength(0);
  expect(screen.getByText('SA')).toBeInTheDocument();
  expect(screen.queryByText('?')).not.toBeInTheDocument();
});

it('B-1931 : sans entreprise, la puce reprend l’e-mail', async () => {
  afficher({ email: 'ada@example.fr' });
  expect(await screen.findAllByText('ada@example.fr')).not.toHaveLength(0);
  expect(screen.getByText('AD')).toBeInTheDocument();
});
