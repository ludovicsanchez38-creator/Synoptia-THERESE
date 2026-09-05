/**
 * B-565 (05/09/2026) : `search()` fige un instantané dans `searchResults`,
 * et `upsertLocal()` ne mettait à jour que `contacts`. Pendant une recherche
 * active, la fiche rouverte venait de l'instantané périmé : un « Mettre à
 * jour » sans retouche renvoyait l'ancienne valeur vide et écrasait la vraie.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { Contact } from '../services/api';

vi.mock('../services/api/memory', () => ({
  listContacts: vi.fn(), getContact: vi.fn(), createContact: vi.fn(), updateContact: vi.fn(),
  deleteContact: vi.fn(), searchMemory: vi.fn(),
}));

import { searchMemory, updateContact } from '../services/api/memory';
import { useContactsStore } from './contactsStore';

const claire = {
  id: 'claire-1', first_name: 'Claire', last_name: 'Roux', company: null,
  email: 'claire@roux-conseil.fr', phone: null, address: null,
} as Contact;

describe('contactsStore : mise à jour pendant une recherche active (B-565)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useContactsStore.setState({
      contacts: [claire], searchResults: null, loading: false, loaded: true, error: null,
      selectedContactId: null, truncated: false,
    });
  });

  it('les résultats de recherche reflètent la valeur enregistrée', async () => {
    vi.mocked(searchMemory).mockResolvedValueOnce({ results: [], query: 'Claire', total: 0, search_time_ms: 1 });
    await useContactsStore.getState().search('Claire');
    expect(useContactsStore.getState().searchResults).toEqual([claire]);

    const adresse = '22 rue des Lices, 04100 Manosque';
    vi.mocked(updateContact).mockResolvedValueOnce({ ...claire, address: adresse });
    await useContactsStore.getState().updateContact('claire-1', { address: adresse });

    const etat = useContactsStore.getState();
    expect(etat.contacts[0].address).toBe(adresse);
    expect(etat.searchResults?.[0].address).toBe(adresse);
  });
});
