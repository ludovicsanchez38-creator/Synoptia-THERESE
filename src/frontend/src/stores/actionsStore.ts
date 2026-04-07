/**
 * THERESE v2 - Actions Store (Zustand)
 *
 * Gere l'etat des agents actionnables et des taches en cours.
 */

import { create } from 'zustand';
import type { ActionAgent, TaskState } from '../services/api/actions';
import {
  fetchActions,
  runAction,
  fetchTask,
  cancelTask,
} from '../services/api/actions';

interface ActionsState {
  /** Liste des agents disponibles */
  agents: ActionAgent[];
  /** Taches en cours / terminees */
  tasks: TaskState[];
  /** Agent actuellement selectionne */
  selectedAgent: ActionAgent | null;
  /** Tache actuellement affichee */
  activeTask: TaskState | null;
  /** Chargement en cours */
  isLoading: boolean;
  /** Panneau d'actions visible */
  isPanelOpen: boolean;
  /** Erreur */
  error: string | null;

  /** Charge les agents depuis le backend */
  loadAgents: () => Promise<void>;

  /** Selectionne un agent */
  selectAgent: (agent: ActionAgent | null) => void;

  /** Lance un agent */
  launchAction: (agentId: string, params?: Record<string, string>) => Promise<TaskState>;

  /** Met a jour le statut d'une tache (polling) */
  refreshTask: (taskId: string) => Promise<void>;

  /** Annule une tache */
  cancelTask: (taskId: string) => Promise<void>;

  /** Ouvre / ferme le panneau */
  togglePanel: () => void;
  openPanel: () => void;
  closePanel: () => void;

  /** Definit la tache active */
  setActiveTask: (task: TaskState | null) => void;
}

export const useActionsStore = create<ActionsState>((set, get) => ({
  agents: [],
  tasks: [],
  selectedAgent: null,
  activeTask: null,
  isLoading: false,
  isPanelOpen: false,
  error: null,

  loadAgents: async () => {
    set({ isLoading: true, error: null });
    try {
      const agents = await fetchActions();
      set({ agents, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Erreur de chargement',
        isLoading: false,
      });
    }
  },

  selectAgent: (agent) => {
    set({ selectedAgent: agent });
  },

  launchAction: async (agentId, params = {}) => {
    set({ isLoading: true, error: null });
    try {
      const task = await runAction(agentId, params);
      set((state) => ({
        tasks: [task, ...state.tasks],
        activeTask: task,
        isLoading: false,
        selectedAgent: null,
      }));

      // Demarrer le polling
      get()._startPolling(task.task_id);

      return task;
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Erreur de lancement',
        isLoading: false,
      });
      throw err;
    }
  },

  refreshTask: async (taskId) => {
    try {
      const updated = await fetchTask(taskId);
      set((state) => ({
        tasks: state.tasks.map((t) => (t.task_id === taskId ? updated : t)),
        activeTask:
          state.activeTask?.task_id === taskId ? updated : state.activeTask,
      }));
    } catch {
      // Silencieux en cas d'erreur de polling
    }
  },

  cancelTask: async (taskId) => {
    try {
      await cancelTask(taskId);
      // Rafraichir immediatement
      await get().refreshTask(taskId);
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Erreur d\'annulation',
      });
    }
  },

  togglePanel: () => set((s) => ({ isPanelOpen: !s.isPanelOpen })),
  openPanel: () => set({ isPanelOpen: true }),
  closePanel: () => set({ isPanelOpen: false, selectedAgent: null }),

  setActiveTask: (task) => set({ activeTask: task }),

  // Polling interne (non expose dans le type public)
  _startPolling: (taskId: string) => {
    const poll = async () => {
      const state = get();
      const task = state.tasks.find((t) => t.task_id === taskId);
      if (!task) return;
      if (task.status === 'completed' || task.status === 'cancelled' || task.status === 'error') {
        return;
      }

      await state.refreshTask(taskId);

      // Re-verifier apres refresh
      const updated = get().tasks.find((t) => t.task_id === taskId);
      if (
        updated &&
        updated.status !== 'completed' &&
        updated.status !== 'cancelled' &&
        updated.status !== 'error'
      ) {
        setTimeout(poll, 1500);
      }
    };

    // Premier polling apres 1s
    setTimeout(poll, 1000);
  },
}));
