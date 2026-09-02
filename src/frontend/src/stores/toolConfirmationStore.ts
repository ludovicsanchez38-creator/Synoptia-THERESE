/**
 * THÉRÈSE v2 - Tool Confirmation Store (US-002)
 *
 * Actions sensibles (ex. send_email) mises en attente par le backend : elles
 * ne s'exécutent qu'après validation explicite de l'utilisateur via une carte
 * de confirmation affichée dans le chat.
 */
import { create } from 'zustand';

/**
 * B-248 : ancrage du calque de confirmation, `bottom-24` soit 96 px du bas de
 * la fenêtre. Vit ici avec la hauteur mesurée : le calque le pose, le fil s'en
 * sert pour dimensionner sa réserve.
 */
export const ANCRE_CALQUE_CONFIRMATION_PX = 96;

export interface PendingConfirmation {
  confirmation_id: string;
  tool_name: string;
  arguments: Record<string, unknown>;
}

interface ToolConfirmationStore {
  pending: PendingConfirmation[];
  /**
   * B-248 : hauteur en pixels réellement occupée par la pile de cartes, mesurée
   * par la couche qui les rend. Le fil de conversation s'en sert pour réserver
   * la bande que le calque recouvre. Le calque étant en position fixe à la
   * racine de l'application (il doit survivre au remplacement du contenu
   * principal), il n'existe pas d'autre voie pour que le fil connaisse son
   * encombrement.
   */
  hauteurCalque: number;
  add: (confirmation: PendingConfirmation) => void;
  remove: (confirmationId: string) => void;
  clear: () => void;
  setHauteurCalque: (hauteur: number) => void;
}

export const useToolConfirmationStore = create<ToolConfirmationStore>((set) => ({
  pending: [],
  hauteurCalque: 0,
  add: (confirmation) =>
    set((state) =>
      state.pending.some((p) => p.confirmation_id === confirmation.confirmation_id)
        ? state
        : { pending: [...state.pending, confirmation] }
    ),
  remove: (confirmationId) =>
    set((state) => ({
      pending: state.pending.filter((p) => p.confirmation_id !== confirmationId),
    })),
  clear: () => set({ pending: [] }),
  // Une mesure identique ne doit pas réveiller les abonnés : le fil se
  // réabonnerait à chaque passage du ResizeObserver.
  setHauteurCalque: (hauteur) =>
    set((state) => (state.hauteurCalque === hauteur ? state : { hauteurCalque: hauteur })),
}));
