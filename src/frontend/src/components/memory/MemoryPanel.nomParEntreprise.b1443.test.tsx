/** B-1443 : dans la liste des Contacts, une fiche sans prénom ni nom
 *  s'appelait « Sans nom ». Elle s'appelle par son entreprise. */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useContactsStore } from '../../stores/contactsStore';
import { MemoryPanel } from './MemoryPanel';

vi.mock('../files/FileBrowser', () => ({ FileBrowser: () => <div data-testid="file-browser" /> }));
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api')>()),
  listProjects: vi.fn().mockResolvedValue([]),
}));

const SOCIETE = {
  id: 'ct-sa', first_name: null, last_name: null, company: 'Sans Nom SA', email: null, phone: null,
  address: null, notes: null, tags: [], stage: 'contact', score: 0, source: null, last_interaction: null,
  created_at: '2026-09-22T10:00:00Z', updated_at: '2026-09-22T10:00:00Z',
};

describe('B-1443 : la liste des Contacts nomme la fiche par son entreprise', () => {
  beforeEach(() => {
    useContactsStore.setState({
      contacts: [SOCIETE], searchResults: null, loading: false, selectedContactId: null, truncated: false,
      loaded: true, fetchContacts: vi.fn().mockResolvedValue(undefined),
    } as never);
  });

  it('la ligne et son bouton de suppression portent « Sans Nom SA »', async () => {
    render(<MemoryPanel standalone onClose={vi.fn()} />);
    expect(await screen.findByRole('button', { name: 'Supprimer Sans Nom SA' })).toBeInTheDocument();
    expect(screen.queryByText('Sans nom')).toBeNull();
  });
});
