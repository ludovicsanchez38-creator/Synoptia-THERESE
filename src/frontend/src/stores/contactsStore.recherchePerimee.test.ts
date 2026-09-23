/**
 * B-977 (cycle 11, 23/09/2026, ronde B du ZERO_CHECK) : une réponse de
 * recherche arrivée en retard remplaçait la liste de la requête en cours.
 * « Zéphyrin » (réponse lente) puis « qwxv » (réponse immédiate, vide) :
 * quand la réponse de « Zéphyrin » arrivait, la liste l'affichait sous la
 * requête « qwxv ». `search()` n'avait ni numéro de requête ni annulation.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { Contact } from '../services/api';

vi.mock('../services/api/memory', () => ({
  listContacts: vi.fn(), getContact: vi.fn(), createContact: vi.fn(), updateContact: vi.fn(),
  deleteContact: vi.fn(), searchMemory: vi.fn(),
}));

import { searchMemory } from '../services/api/memory';
import { useContactsStore } from './contactsStore';

const zephyrin = {
  id: 'zeph-1', first_name: 'Zéphyrin', last_name: 'Aubry', company: null,
  email: 'z@exemple.invalid', phone: null, address: null,
} as Contact;

const reponse = (ids: string[]) => ({
  results: ids.map((id) => ({ id, entity_type: 'contact' })), query: '', total: ids.length, search_time_ms: 1,
}) as never;

describe('contactsStore : une réponse périmée ne remplace pas la recherche en cours (B-977)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useContactsStore.setState({
      contacts: [zephyrin], searchResults: null, loading: false, loaded: true, error: null,
      selectedContactId: null, truncated: false,
    });
  });

  it('la réponse lente de la première requête arrive après celle de la seconde', async () => {
    let libererLaPremiere: (valeur: unknown) => void = () => {};
    vi.mocked(searchMemory)
      .mockImplementationOnce(() => new Promise((ok) => { libererLaPremiere = ok; }) as never)
      .mockResolvedValueOnce(reponse([]));

    const premiere = useContactsStore.getState().search('Zéphyrin');
    await useContactsStore.getState().search('qwxv');
    expect(useContactsStore.getState().searchResults).toEqual([]);

    libererLaPremiere(reponse(['zeph-1']));
    await premiere;

    expect(useContactsStore.getState().searchResults).toEqual([]);
    expect(useContactsStore.getState().loading).toBe(false);
  });

  it('effacer la recherche pendant une réponse lente ne la fait pas revenir', async () => {
    let liberer: (valeur: unknown) => void = () => {};
    vi.mocked(searchMemory).mockImplementationOnce(() => new Promise((ok) => { liberer = ok; }) as never);

    const enCours = useContactsStore.getState().search('Zéphyrin');
    await useContactsStore.getState().search('');
    liberer(reponse(['zeph-1']));
    await enCours;

    expect(useContactsStore.getState().searchResults).toBeNull();
  });
});
