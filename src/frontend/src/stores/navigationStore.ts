/**
 * THÉRÈSE v2 - Navigation Store (Phase 1 revue produit)
 *
 * Modèle "content-swap par vues" : la zone principale rend la VUE active.
 * Les surfaces de productivité (CRM, Email, Agenda, Tâches, Factures, Mémoire)
 * deviennent des vues, au lieu de fenêtres Tauri séparées.
 */

import { create } from 'zustand';

export type AppView =
  | 'chat'
  | 'memory'
  | 'crm'
  | 'email'
  | 'calendar'
  | 'tasks'
  | 'invoices'
  | 'files' // Indexation de fichiers (sortie de la Mémoire, arbitrage A/B 2026-06-05)
  | 'projects'; // Vue Projets dédiée (BUG-104 : surface perdue à la refonte 0.20)

interface NavigationStore {
  activeView: AppView;
  /** Pile des vues précédentes (pour le retour / Échap). */
  history: AppView[];
  setView: (view: AppView) => void;
  goBack: () => void;
  resetToChat: () => void;
}

export const useNavigationStore = create<NavigationStore>((set) => ({
  activeView: 'chat',
  history: [],

  setView: (view) =>
    set((state) => {
      if (view === state.activeView) return state; // no-op : pas de doublon
      return {
        activeView: view,
        history: [...state.history, state.activeView],
      };
    }),

  goBack: () =>
    set((state) => {
      if (state.history.length === 0) {
        return { activeView: 'chat', history: [] };
      }
      const history = [...state.history];
      const previous = history.pop() as AppView;
      return { activeView: previous, history };
    }),

  resetToChat: () => set({ activeView: 'chat', history: [] }),
}));
