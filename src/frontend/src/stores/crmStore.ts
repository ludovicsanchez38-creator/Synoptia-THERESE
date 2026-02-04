/**
 * THÉRÈSE v2 - CRM Store
 *
 * Zustand store pour la gestion du CRM.
 * Persistance des contacts et projets pour affichage instantané.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ContactResponse, Project } from '../services/api';

type Tab = 'pipeline' | 'activities' | 'dashboard';

interface CRMStore {
  // Contacts
  contacts: ContactResponse[];
  selectedContactId: string | null;
  setContacts: (contacts: ContactResponse[]) => void;
  setSelectedContact: (contactId: string | null) => void;
  updateContact: (contactId: string, updates: Partial<ContactResponse>) => void;
  addContact: (contact: ContactResponse) => void;

  // Projects
  projects: Project[];
  setProjects: (projects: Project[]) => void;

  // UI State
  isCRMPanelOpen: boolean;
  activeTab: Tab;
  toggleCRMPanel: () => void;
  setIsCRMPanelOpen: (open: boolean) => void;
  setActiveTab: (tab: Tab) => void;
}

export const useCRMStore = create<CRMStore>()(
  persist(
    (set) => ({
      // Contacts
      contacts: [],
      selectedContactId: null,
      setContacts: (contacts) => set({ contacts }),
      setSelectedContact: (contactId) => set({ selectedContactId: contactId }),
      updateContact: (contactId, updates) =>
        set((state) => ({
          contacts: state.contacts.map((c) =>
            c.id === contactId ? { ...c, ...updates } : c
          ),
        })),
      addContact: (contact) =>
        set((state) => ({
          contacts: [contact, ...state.contacts],
        })),

      // Projects
      projects: [],
      setProjects: (projects) => set({ projects }),

      // UI State
      isCRMPanelOpen: false,
      activeTab: 'pipeline',
      toggleCRMPanel: () =>
        set((state) => ({ isCRMPanelOpen: !state.isCRMPanelOpen })),
      setIsCRMPanelOpen: (open) => set({ isCRMPanelOpen: open }),
      setActiveTab: (tab) => set({ activeTab: tab }),
    }),
    {
      name: 'crm-storage',
      partialize: (state) => ({
        contacts: state.contacts,
        projects: state.projects,
        activeTab: state.activeTab,
      }),
    }
  )
);
