import { describe, it, expect, beforeEach, vi } from 'vitest';
import type { Contact } from '../services/api';

vi.mock('../services/api/memory', () => ({
  listContacts: vi.fn(),
  createContact: vi.fn(),
  updateContact: vi.fn(),
  deleteContact: vi.fn(),
  searchMemory: vi.fn(),
}));

import {
  listContacts,
  createContact,
  updateContact,
  deleteContact,
  searchMemory,
} from '../services/api/memory';
import { useContactsStore } from './contactsStore';

const makeContact = (over: Partial<Contact> = {}): Contact =>
  ({ id: 'c1', first_name: 'Jean', last_name: 'Dupont', ...over } as Contact);

describe('contactsStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useContactsStore.setState({
      contacts: [],
      searchResults: null,
      loading: false,
      selectedContactId: null,
    });
  });

  it('fetchContacts peuple contacts et bascule loading', async () => {
    vi.mocked(listContacts).mockResolvedValueOnce([makeContact()]);
    const p = useContactsStore.getState().fetchContacts();
    expect(useContactsStore.getState().loading).toBe(true);
    await p;
    expect(useContactsStore.getState().loading).toBe(false);
    expect(useContactsStore.getState().contacts).toHaveLength(1);
  });

  it("createContact n'ajoute qu'APRÈS confirmation de l'API (anti-faux-succès)", async () => {
    let resolveCreate!: (v: Contact) => void;
    vi.mocked(createContact).mockReturnValueOnce(
      new Promise<Contact>((r) => {
        resolveCreate = r;
      })
    );
    const p = useContactsStore.getState().createContact({ first_name: 'Alice' });
    // Promesse non résolue => la liste ne doit PAS encore contenir le contact
    expect(useContactsStore.getState().contacts).toHaveLength(0);
    resolveCreate(makeContact({ id: 'c2', first_name: 'Alice' }));
    await p;
    expect(useContactsStore.getState().contacts).toHaveLength(1);
    expect(useContactsStore.getState().contacts[0].id).toBe('c2');
  });

  it('createContact en échec ne modifie pas la liste et propage l\'erreur', async () => {
    vi.mocked(createContact).mockRejectedValueOnce(new Error('boom'));
    await expect(
      useContactsStore.getState().createContact({ first_name: 'X' })
    ).rejects.toThrow('boom');
    expect(useContactsStore.getState().contacts).toHaveLength(0);
  });

  it('updateContact patch le bon contact après confirmation', async () => {
    useContactsStore.setState({ contacts: [makeContact({ id: 'c1', company: 'Old' })] });
    vi.mocked(updateContact).mockResolvedValueOnce(makeContact({ id: 'c1', company: 'New' }));
    await useContactsStore.getState().updateContact('c1', { company: 'New' });
    expect(useContactsStore.getState().contacts[0].company).toBe('New');
  });

  it('deleteContact retire le contact et reste idempotent', async () => {
    useContactsStore.setState({ contacts: [makeContact({ id: 'c1' })] });
    vi.mocked(deleteContact).mockResolvedValue(undefined);
    await useContactsStore.getState().deleteContact('c1');
    expect(useContactsStore.getState().contacts).toHaveLength(0);
    await useContactsStore.getState().deleteContact('c1');
    expect(useContactsStore.getState().contacts).toHaveLength(0);
  });

  it('search("q") peuple searchResults via searchMemory (contacts uniquement)', async () => {
    vi.mocked(searchMemory).mockResolvedValueOnce({ contacts: [makeContact({ id: 'c3' })] });
    await useContactsStore.getState().search('jean');
    expect(searchMemory).toHaveBeenCalledWith('jean', ['contacts']);
    expect(useContactsStore.getState().searchResults).toHaveLength(1);
  });

  it('search("") remet searchResults à null sans appeler l\'API (repli liste complète)', async () => {
    useContactsStore.setState({ searchResults: [makeContact()] });
    await useContactsStore.getState().search('   ');
    expect(useContactsStore.getState().searchResults).toBeNull();
    expect(searchMemory).not.toHaveBeenCalled();
  });
});
