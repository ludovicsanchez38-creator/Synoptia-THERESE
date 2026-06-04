/**
 * THÉRÈSE v2 - CRM Store
 *
 * Zustand store recentré sur les PROJETS et l'UI du CRM (pipeline).
 * Les CONTACTS sont désormais détenus par `contactsStore` (source de vérité unique,
 * P4 - Chantier B revue produit). Le CRM est une VUE filtrée (contacts avec source).
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Project } from '../services/api';

type Tab = 'pipeline' | 'activities';

interface CRMStore {
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
        projects: state.projects,
        activeTab: state.activeTab,
      }),
    }
  )
);
