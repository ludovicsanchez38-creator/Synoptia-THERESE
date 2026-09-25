/**
 * B-1350 (persona Claire, cycle 13) : chercher un prénom rendait tout le carnet.
 *
 * Trois fiches (Hélène Ménard-Lefèvre, Julien Garnier, Sophie Durand) ; la
 * recherche « helene » rendait les trois, car la moitié sémantique renvoie les
 * voisins au-dessus du seuil (0,568 / 0,536 / 0,518) et le filtre local ne
 * repliait pas les accents. Un nom est une recherche exacte : dès qu'une fiche
 * correspond littéralement, les simples ressemblances sont écartées. La
 * moitié sémantique ne sert que lorsqu'aucune fiche ne correspond.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import type { Contact } from '../services/api';

vi.mock('../services/api/memory', () => ({
  listContacts: vi.fn(),
  getContact: vi.fn(),
  createContact: vi.fn(),
  updateContact: vi.fn(),
  deleteContact: vi.fn(),
  searchMemory: vi.fn(),
}));

import { getContact, searchMemory } from '../services/api/memory';
import { useContactsStore } from './contactsStore';

const fiche = (id: string, first_name: string, last_name: string, notes?: string): Contact =>
  ({ id, first_name, last_name, notes } as Contact);

const hit = (id: string, score: number) => ({
  id, entity_type: 'contact', title: '', content: '', score,
});

const helene = fiche('h', 'Hélène', 'Ménard-Lefèvre');
const julien = fiche('j', 'Julien', 'Garnier');
const sophie = fiche('s', 'Sophie', 'Durand');

const reponseSemantique = (query: string) => ({
  query, total: 3, search_time_ms: 1,
  results: [hit('h', 0.568), hit('j', 0.536), hit('s', 0.518)],
});

const idsAffiches = () =>
  (useContactsStore.getState().searchResults ?? []).map((c) => c.id);

describe('recherche de contacts par nom (B-1350)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useContactsStore.setState({
      contacts: [helene, julien, sophie],
      searchResults: null,
      loading: false,
      loaded: true,
      error: null,
      selectedContactId: null,
      truncated: false,
    });
  });

  it('« helene » sans accent ne rend que Hélène', async () => {
    vi.mocked(searchMemory).mockResolvedValueOnce(reponseSemantique('helene'));
    await useContactsStore.getState().search('helene');
    expect(idsAffiches()).toEqual(['h']);
  });

  it('« Hélène » avec accent ne rend que Hélène', async () => {
    vi.mocked(searchMemory).mockResolvedValueOnce(reponseSemantique('Hélène'));
    await useContactsStore.getState().search('Hélène');
    expect(idsAffiches()).toEqual(['h']);
  });

  it('une fiche du moteur dont les notes contiennent le mot reste affichée', async () => {
    const claire = fiche('c', 'Claire', 'Martin', 'Recommandée par Hélène');
    vi.mocked(searchMemory).mockResolvedValueOnce({
      query: 'helene', total: 3, search_time_ms: 1,
      results: [hit('h', 0.6), hit('c', 0.55), hit('j', 0.52)],
    });
    vi.mocked(getContact).mockResolvedValueOnce(claire);
    await useContactsStore.getState().search('helene');
    expect(idsAffiches()).toEqual(['h', 'c']);
  });

  it('sans correspondance littérale, les ressemblances restent proposées', async () => {
    vi.mocked(searchMemory).mockResolvedValueOnce({
      query: 'reconversion', total: 1, search_time_ms: 1, results: [hit('s', 0.61)],
    });
    await useContactsStore.getState().search('reconversion');
    expect(idsAffiches()).toEqual(['s']);
  });
});
