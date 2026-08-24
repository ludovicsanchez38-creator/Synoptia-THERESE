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

// Revue jalon (F9) : propriétaire + refcount. Sans eux, un démontage
// pendant le premier chargement laissait une boucle orpheline, et deux
// montages rapprochés (StrictMode) créaient deux boucles dont une
// impossible à arrêter.
let minuterie: ReturnType<typeof setTimeout> | null = null;
let abonnes = 0;
let boucleEnVol = false;

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
      // Purge des arrêts demandés arrivés à terme (F9) : sans elle, un
      // traitement fini trop tard affichait « Arrêt demandé » pour toujours.
      const arrets = new Set(
        [...get().arretsDemandes].filter((id) => {
          const t = traitements.find((x) => x.id === id);
          return t !== undefined && (
            t.state === 'running' || t.state === 'queued'
            || t.state === 'cancel_requested'
          );
        }),
      );
      set({ traitements, erreur: null, arretsDemandes: arrets });
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
    abonnes += 1;
    const boucle = async () => {
      if (abonnes === 0) {
        boucleEnVol = false;
        return;
      }
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
      // Garde APRÈS chaque await (F9) : le dernier abonné a pu partir
      // pendant le chargement - ne jamais reprogrammer dans le vide.
      if (abonnes === 0) {
        boucleEnVol = false;
        return;
      }
      const cadence =
        panneauOuvert || actives ? CADENCE_ACTIVE_MS : CADENCE_VEILLE_MS;
      minuterie = setTimeout(() => void boucle(), cadence);
    };
    if (!boucleEnVol) {
      boucleEnVol = true;
      void boucle();
    }
  },

  arreterSondage: () => {
    abonnes = Math.max(0, abonnes - 1);
    if (abonnes === 0 && minuterie !== null) {
      clearTimeout(minuterie);
      minuterie = null;
      boucleEnVol = false;
    }
  },
}));
