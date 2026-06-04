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

/** Vrai si le contact matche la requête sur nom/email/entreprise (filtre local). */
export function contactMatchesQuery(contact: Contact, query: string): boolean {
  const q = query.toLowerCase();
  return (
    (contact.first_name?.toLowerCase().includes(q) ?? false) ||
    (contact.last_name?.toLowerCase().includes(q) ?? false) ||
    (contact.company?.toLowerCase().includes(q) ?? false) ||
    (contact.email?.toLowerCase().includes(q) ?? false)
  );
}

/** Fusionne deux listes de contacts en dédupliquant par id (la première prime). */
function mergeContactsById(primary: Contact[], extra: Contact[]): Contact[] {
  const seen = new Set(primary.map((c) => c.id));
  return [...primary, ...extra.filter((c) => !seen.has(c.id))];
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
    // Filtre local immédiat (nom/email/entreprise) : garantit qu'on retrouve TOUJOURS
    // par le nom (régression P5 trouvée par Syn : la recherche sémantique pure cachait
    // les contacts au lieu de les trouver).
    const local = get().contacts.filter((c) => contactMatchesQuery(c, q));
    try {
      const res = await apiSearchMemory(q, ['contacts']);
      // Hybride : matches locaux d'abord, puis résultats sémantiques non déjà présents.
      set({ searchResults: mergeContactsById(local, res.contacts ?? []), loading: false });
    } catch {
      // Sémantique indisponible : la recherche reste utilisable via le filtre local.
      set({ searchResults: local, loading: false });
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
