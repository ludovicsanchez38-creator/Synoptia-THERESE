/**
 * Traitements longs (0.46) - le store du panneau.
 *
 * Sondage à deux cadences (design V2.1) : 3 s quand le panneau est ouvert OU
 * qu'un traitement actif est connu ; 12 s sinon quand l'application est
 * visible - jamais d'angle mort au démarrage, jamais de sondage caché.
 */
import { create } from 'zustand';

import * as api from '../services/api';

const CADENCE_ACTIVE_MS = 3_000;
const CADENCE_VEILLE_MS = 12_000;

interface ProcessingTasksStore {
  traitements: api.Traitement[];
  panneauOuvert: boolean;
  erreur: string | null;
  /** ids dont l'arrêt vient d'être demandé (retour visuel immédiat). */
  arretsDemandes: Set<string>;
  ouvrirPanneau: () => void;
  fermerPanneau: () => void;
  charger: () => Promise<void>;
  annuler: (id: string) => Promise<void>;
  demarrerSondage: () => void;
  arreterSondage: () => void;
}

let minuterie: ReturnType<typeof setTimeout> | null = null;

export const useProcessingTasksStore = create<ProcessingTasksStore>((set, get) => ({
  traitements: [],
  panneauOuvert: false,
  erreur: null,
  arretsDemandes: new Set<string>(),

  ouvrirPanneau: () => {
    set({ panneauOuvert: true });
    void get().charger();
  },

  fermerPanneau: () => set({ panneauOuvert: false }),

  charger: async () => {
    try {
      const traitements = await api.listerTraitements({ limit: 30 });
      set({ traitements, erreur: null });
    } catch {
      set({ erreur: 'Traitements indisponibles pour le moment.' });
    }
  },

  annuler: async (id: string) => {
    try {
      await api.annulerTraitement(id);
      const arrets = new Set(get().arretsDemandes);
      arrets.add(id);
      set({ arretsDemandes: arrets });
      await get().charger();
    } catch {
      set({ erreur: "La demande d'arrêt a échoué, réessaie." });
    }
  },

  demarrerSondage: () => {
    const boucle = async () => {
      const { panneauOuvert, traitements } = get();
      const actives = traitements.some((t) =>
        t.state === 'running' || t.state === 'queued' || t.state === 'cancel_requested',
      );
      if (
        typeof document === 'undefined'
        || document.visibilityState === 'visible'
        || panneauOuvert
      ) {
        await get().charger();
      }
      const cadence =
        panneauOuvert || actives ? CADENCE_ACTIVE_MS : CADENCE_VEILLE_MS;
      minuterie = setTimeout(() => void boucle(), cadence);
    };
    if (minuterie === null) void boucle();
  },

  arreterSondage: () => {
    if (minuterie !== null) {
      clearTimeout(minuterie);
      minuterie = null;
    }
  },
}));
