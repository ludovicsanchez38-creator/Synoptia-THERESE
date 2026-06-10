/**
 * THÉRÈSE v2 - Tool Confirmation Store (US-002)
 *
 * Actions sensibles (ex. send_email) mises en attente par le backend : elles
 * ne s'exécutent qu'après validation explicite de l'utilisateur via une carte
 * de confirmation affichée dans le chat.
 */
import { create } from 'zustand';

export interface PendingConfirmation {
  confirmation_id: string;
  tool_name: string;
  arguments: Record<string, unknown>;
}

interface ToolConfirmationStore {
  pending: PendingConfirmation[];
  add: (confirmation: PendingConfirmation) => void;
  remove: (confirmationId: string) => void;
  clear: () => void;
}

export const useToolConfirmationStore = create<ToolConfirmationStore>((set) => ({
  pending: [],
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
}));
