/**
 * THÉRÈSE v2 - Demo Mode Store
 *
 * Store Zustand pour le mode démo.
 * Masque les données réelles par des personas fictifs pour les vidéos de présentation.
 * Aucune donnée n'est modifiée en base - masquage purement cosmétique.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { buildReplacementMap } from '../lib/demoMask';

interface DemoState {
  /** Mode démo activé */
  enabled: boolean;
  /** Map des remplacements texte (réel → fictif) - non persistée, reconstruite au besoin */
  replacementMap: Map<string, string>;
  /** Toggle on/off */
  toggle: () => void;
  /** Set enabled directement */
  setEnabled: (enabled: boolean) => void;
  /** Construire la map de remplacement depuis les contacts et projets */
  buildMap: (contacts: Array<{ first_name?: string | null; last_name?: string | null; company?: string | null; email?: string | null }>, projects: Array<{ name?: string | null }>) => void;
  /** Vider la map */
  clearMap: () => void;
}

export const useDemoStore = create<DemoState>()(
  persist(
    (set) => ({
      enabled: false,
      replacementMap: new Map(),

      toggle: () => {
        set((state) => ({ enabled: !state.enabled }));
      },

      setEnabled: (enabled) => {
        set({ enabled });
      },

      buildMap: (contacts, projects) => {
        const map = buildReplacementMap(contacts, projects);
        set({ replacementMap: map });
      },

      clearMap: () => {
        set({ replacementMap: new Map() });
      },
    }),
    {
      name: 'therese-demo-mode',
      partialize: (state) => ({
        // On ne persiste que le flag enabled, pas la map
        enabled: state.enabled,
      }),
    }
  )
);
