/**
 * B-1929 : le badge RGPD affiche une abréviation. Le libellé complet
 * n'est porté que par le title.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { useContactsStore } from '../../stores/contactsStore';
import { MemoryPanel } from './MemoryPanel';

vi.mock('../files/FileBrowser', () => ({ FileBrowser: () => null }));
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api')>()),
  listProjects: vi.fn().mockResolvedValue([]),
  getRGPDStats: vi.fn().mockResolvedValue(null),
}));

const BASES = [
  ['consentement', 'Consentement'],
  ['contrat', 'Contrat'],
  ['interet_legitime', 'Intérêt légitime'],
  ['obligation_legale', 'Obligation légale'],
] as const;

beforeEach(() => {
  useContactsStore.setState({
    contacts: [], searchResults: null, loading: false, selectedContactId: null,
    truncated: false, loaded: true, fetchContacts: vi.fn().mockResolvedValue(undefined),
  } as never);
});

it.each(BASES)('B-1929 : la base %s s’écrit « %s »', async (base, complet) => {
  useContactsStore.setState({
    contacts: [{
      id: 'ct-sa', first_name: 'Ada', last_name: 'Lovelace', company: null, email: null,
      phone: null, address: null, notes: null, tags: [], stage: 'contact', score: 0,
      source: null, last_interaction: null, created_at: '2026-09-22T10:00:00Z',
      updated_at: '2026-09-22T10:00:00Z', rgpd_base_legale: base,
    }],
  } as never);
  render(<MemoryPanel standalone />);
  expect(await screen.findByText('Ada Lovelace')).toBeInTheDocument();
  expect(screen.getByText(complet)).toBeInTheDocument();
});
