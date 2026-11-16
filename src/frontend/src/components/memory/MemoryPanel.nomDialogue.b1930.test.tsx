/**
 * B-1930 : les dialogues d'export et de renouvellement nomment la fiche
 * par le prénom et le nom. La liste, elle, passe par l'entreprise puis l'e-mail.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { useContactsStore } from '../../stores/contactsStore';
import { MemoryPanel } from './MemoryPanel';

vi.mock('../files/FileBrowser', () => ({ FileBrowser: () => null }));
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api')>()),
  listProjects: vi.fn().mockResolvedValue([]),
  getRGPDStats: vi.fn().mockResolvedValue(null),
}));

function fiche(over: Record<string, unknown>) {
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
}

beforeEach(() => fiche({ company: 'Sans Nom SA' }));

async function ouvrir(action: string, dialogue: string) {
  render(<MemoryPanel standalone />);
  fireEvent.click(await screen.findByRole('button', { name: 'Actions RGPD' }));
  fireEvent.click(screen.getByRole('button', { name: action }));
  return screen.findByRole('dialog', { name: dialogue });
}

it('B-1930 : l’export nomme la fiche comme la liste', async () => {
  const dialogue = await ouvrir('Exporter (Art. 20)', 'Export RGPD');
  expect(dialogue).toHaveTextContent('Sans Nom SA');
});

it('B-1930 : le renouvellement nomme la fiche comme la liste', async () => {
  const dialogue = await ouvrir('Renouveler consentement', 'Renouveler le consentement');
  expect(dialogue).toHaveTextContent('Sans Nom SA');
});

it('B-1930 : sans entreprise, le dialogue retombe sur l’e-mail', async () => {
  fiche({ email: 'ada@example.fr' });
  const dialogue = await ouvrir('Exporter (Art. 20)', 'Export RGPD');
  expect(dialogue).toHaveTextContent('ada@example.fr');
});
