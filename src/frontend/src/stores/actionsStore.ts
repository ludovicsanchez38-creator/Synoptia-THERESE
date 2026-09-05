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
import { useChatStore } from './chatStore';
import { useNavigationStore } from './navigationStore';

/**
 * Set d'idempotence : empeche d'inserer plusieurs fois le resultat
 * d'une meme tache (defense en profondeur contre les re-poll concurrents
 * ou un futur re-fetch de taches historiques).
 */
const insertedTaskIds = new Set<string>();

/**
 * B-304 : echecs consecutifs du SUIVI d'une tache, par identifiant.
 *
 * Le sondage avalait l'erreur et se reprogrammait toutes les 1,5 s tant que le
 * statut n'etait pas final ; comme l'echec ne changeait pas le statut, la
 * condition restait vraie pour toujours et l'utilisateur voyait une tache
 * tourner sans fin. On borne desormais la serie, et le compteur est remis a
 * zero au premier succes pour qu'une coupure passagere ne tue pas un suivi qui
 * allait aboutir.
 */
const ECHECS_DE_SUIVI_AVANT_ABANDON = 3;
const echecsDeSuivi = new Map<string, number>();

/** Message d'ecran : c'est le SUIVI qui a lache, pas forcement la tache. */
const MESSAGE_SUIVI_PERDU =
  'Suivi interrompu : le service ne répond plus. La tâche a peut-être continué de son côté.';

/**
 * Insere le resultat d'une action terminee dans le chat actif.
 * BUG-097 (Smileshoot) : l'UI annoncait "Resultat insere dans le chat"
 * mais aucun code ne realisait l'insertion.
 *
 * Pour status `completed` : insere le resultat avec header agent.
 * Pour status `error` : insere un message d'erreur clair (resultat
 * partiel inclus s'il existe).
 */
export function insertResultInChat(task: TaskState): void {
  if (insertedTaskIds.has(task.task_id)) return;

  const header = task.agent_name ? `**${task.agent_name}**\n\n` : '';
  let content: string | null = null;

  if (task.status === 'completed' && task.result?.trim()) {
    content = `${header}${task.result}`;
  } else if (task.status === 'error') {
    const partial = task.result?.trim() ? `\n\n${task.result}` : '';
    const errMsg = task.error?.trim() || 'tâche échouée';
    content = `${header}Erreur : ${errMsg}${partial}`;
  }

  if (!content) return;
  insertedTaskIds.add(task.task_id);
  useChatStore.getState().addMessage({ role: 'assistant', content });
  // BUG-107 : le résultat d'une action lancée depuis l'Accueil partait dans une
  // conversation invisible. On ramène la vue sur le chat pour le rendre visible.
  useNavigationStore.getState().setView('chat');
}

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

  /** Polling interne */
  _startPolling: (taskId: string) => void;
  _stopPolling: (taskId: string) => void;
}

// B-492 : une seule minuterie de sondage par tâche, annulable.
const minuteriesDeSondage = new Map<string, ReturnType<typeof setTimeout>>();

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
      const previous = get().tasks.find((t) => t.task_id === taskId);

      set((state) => ({
        tasks: state.tasks.map((t) => (t.task_id === taskId ? updated : t)),
        activeTask:
          state.activeTask?.task_id === taskId ? updated : state.activeTask,
      }));

      // BUG-097 : transition vers completed ou error -> injecter dans le chat
      // Le Set insertedTaskIds garantit l'idempotence (pas de doublon)
      const becameFinal =
        previous?.status !== updated.status &&
        (updated.status === 'completed' || updated.status === 'error');
      if (becameFinal) {
        insertResultInChat(updated);
      }
      // B-304 : une lecture reussie efface la serie d'echecs en cours.
      echecsDeSuivi.delete(taskId);
    } catch {
      // Toujours pas d'erreur a l'ecran ici (un echec isole ne dit rien), mais
      // la serie est comptee : c'est le sondage qui decide d'abandonner.
      echecsDeSuivi.set(taskId, (echecsDeSuivi.get(taskId) ?? 0) + 1);
    }
  },

  cancelTask: async (taskId) => {
    get()._stopPolling(taskId);
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
    const programmer = (delai: number) => {
      get()._stopPolling(taskId);
      minuteriesDeSondage.set(
        taskId,
        setTimeout(() => {
          minuteriesDeSondage.delete(taskId);
          void poll();
        }, delai),
      );
    };
    const poll = async () => {
      const state = get();
      const task = state.tasks.find((t) => t.task_id === taskId);
      if (!task) return;
      if (task.status === 'completed' || task.status === 'cancelled' || task.status === 'error') {
        return;
      }

      await state.refreshTask(taskId);

      // B-304 : au-dela de la serie toleree, on arrete le sondage et on le
      // DIT - sinon la tache reste affichee « en cours » indefiniment.
      if ((echecsDeSuivi.get(taskId) ?? 0) >= ECHECS_DE_SUIVI_AVANT_ABANDON) {
        echecsDeSuivi.delete(taskId);
        set((s) => ({
          error: MESSAGE_SUIVI_PERDU,
          tasks: s.tasks.map((t) =>
            t.task_id === taskId
              ? { ...t, status: 'error' as const, error: MESSAGE_SUIVI_PERDU }
              : t,
          ),
          activeTask:
            s.activeTask?.task_id === taskId
              ? { ...s.activeTask, status: 'error' as const, error: MESSAGE_SUIVI_PERDU }
              : s.activeTask,
        }));
        return;
      }

      // Re-verifier apres refresh
      const updated = get().tasks.find((t) => t.task_id === taskId);
      if (
        updated &&
        updated.status !== 'completed' &&
        updated.status !== 'cancelled' &&
        updated.status !== 'error'
      ) {
        programmer(1500);
      }
    };

    // Premier polling apres 1s - un second démarrage pour la même tâche
    // REMPLACE la minuterie au lieu d'en empiler une deuxième (B-492).
    programmer(1000);
  },
  _stopPolling: (taskId: string) => {
    const minuterie = minuteriesDeSondage.get(taskId);
    if (minuterie) clearTimeout(minuterie);
    minuteriesDeSondage.delete(taskId);
  },
}));
