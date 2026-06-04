/**
 * THÉRÈSE v2 - Contacts Store
 *
 * Source de vérité UNIQUE des contacts (P4 - Chantier B revue produit).
 * Mémoire et CRM consomment ce store ; aucun autre store ne duplique les contacts.
 * Règle : aucune mutation locale avant confirmation de l'API (anti-faux-succès).
 */

import { create } from 'zustand';
import type { Contact } from '../services/api';
import {
  listContacts as apiListContacts,
  createContact as apiCreateContact,
  updateContact as apiUpdateContact,
  deleteContact as apiDeleteContact,
  searchMemory as apiSearchMemory,
} from '../services/api/memory';

interface ContactsStore {
  contacts: Contact[];
  /** Résultats de recherche sémantique ; null = pas de recherche active (on affiche `contacts`). */
  searchResults: Contact[] | null;
  loading: boolean;
  selectedContactId: string | null;

  fetchContacts: () => Promise<void>;
  createContact: (data: Partial<Contact>) => Promise<Contact>;
  updateContact: (id: string, patch: Partial<Contact>) => Promise<void>;
  deleteContact: (id: string) => Promise<void>;
  search: (query: string) => Promise<void>;
  setSelectedContact: (id: string | null) => void;
  upsertLocal: (contact: Contact) => void;
  removeLocal: (id: string) => void;
}

export const useContactsStore = create<ContactsStore>((set, get) => ({
  contacts: [],
  searchResults: null,
  loading: false,
  selectedContactId: null,

  fetchContacts: async () => {
    set({ loading: true });
    try {
      const contacts = await apiListContacts(0, 200);
      set({ contacts, loading: false });
    } catch (e) {
      set({ loading: false });
      throw e;
    }
  },

  createContact: async (data) => {
    // Confirmation API AVANT toute mutation locale (pas de faux succès).
    const created = await apiCreateContact(data);
    get().upsertLocal(created);
    return created;
  },

  updateContact: async (id, patch) => {
    const updated = await apiUpdateContact(id, patch);
    get().upsertLocal(updated);
  },

  deleteContact: async (id) => {
    await apiDeleteContact(id);
    get().removeLocal(id);
  },

  search: async (query) => {
    const q = query.trim();
    if (!q) {
      set({ searchResults: null });
      return;
    }
    set({ loading: true });
    try {
      const res = await apiSearchMemory(q, ['contacts']);
      set({ searchResults: res.contacts ?? [], loading: false });
    } catch (e) {
      set({ loading: false });
      throw e;
    }
  },

  setSelectedContact: (id) => set({ selectedContactId: id }),

  upsertLocal: (contact) =>
    set((state) => {
      const exists = state.contacts.some((c) => c.id === contact.id);
      return {
        contacts: exists
          ? state.contacts.map((c) => (c.id === contact.id ? contact : c))
          : [contact, ...state.contacts],
      };
    }),

  removeLocal: (id) =>
    set((state) => ({
      contacts: state.contacts.filter((c) => c.id !== id),
      searchResults: state.searchResults
        ? state.searchResults.filter((c) => c.id !== id)
        : state.searchResults,
    })),
}));
