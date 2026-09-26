/**
 * THÉRÈSE v2 - Task Store
 *
 * Zustand store pour la gestion des tâches.
 * Phase 3 - Tasks/Todos
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Task } from '../services/api';

interface TaskStore {
  // Tasks
  tasks: Task[];
  currentTaskId: string | null;
  setTasks: (tasks: Task[]) => void;
  setCurrentTask: (taskId: string | null) => void;
  addTask: (task: Task) => void;
  updateTask: (taskId: string, updates: Partial<Task>) => void;
  removeTask: (taskId: string) => void;

  // UI State
  isTasksPanelOpen: boolean;
  isTaskFormOpen: boolean;
  viewMode: 'list' | 'kanban';
  toggleTasksPanel: () => void;
  setIsTasksPanelOpen: (open: boolean) => void;
  setIsTaskFormOpen: (open: boolean) => void;
  setViewMode: (mode: 'list' | 'kanban') => void;

  // Draft Task
  draftTask: Partial<Task>;
  setDraftTitle: (title: string) => void;
  setDraftDescription: (description: string) => void;
  setDraftStatus: (status: string) => void;
  setDraftPriority: (priority: string) => void;
  setDraftDueDate: (dueDate: string) => void;
  setDraftProjectId: (projectId: string | null) => void;
  setDraftTags: (tags: string[]) => void;
  clearDraft: () => void;

  // Filters
  filterStatus: string | null;
  filterPriority: string | null;
  filterProjectId: string | null;
  /** BUG-118 : filtre par étiquette, appliqué côté client. Non persisté. */
  filterTag: string | null;
  searchQuery: string;
  setFilterStatus: (status: string | null) => void;
  setFilterPriority: (priority: string | null) => void;
  setFilterProjectId: (projectId: string | null) => void;
  setFilterTag: (tag: string | null) => void;
  setSearchQuery: (query: string) => void;
  /**
   * Revue P-148, constat 8 : les filtres qu'un geste venu d'ailleurs a
   * retirés, pour que la vue le dise. Effacé au premier changement de filtre.
   */
  filtresRetires: FiltresRetires | null;
  /**
   * « Voir les tâches » d'un projet : filtre sur ce projet et retire tout ce
   * qui montrerait moins de tâches qu'annoncé (statut, priorité, étiquette,
   * recherche), en retenant ce qui a été retiré.
   */
  ouvrirSurLeProjet: (projetId: string) => void;
}

/** Valeurs brutes des filtres retirés (la vue les nomme). */
export interface FiltresRetires {
  statut: string | null;
  priorite: string | null;
  etiquette: string | null;
  recherche: string | null;
}

export const useTaskStore = create<TaskStore>()(
  persist(
    (set) => ({
      // Tasks
      tasks: [],
      currentTaskId: null,
      setTasks: (tasks) => set({ tasks }),
      setCurrentTask: (taskId) => set({ currentTaskId: taskId }),
      addTask: (task) =>
        set((state) => ({
          tasks: [...state.tasks, task],
        })),
      updateTask: (taskId, updates) =>
        set((state) => ({
          tasks: state.tasks.map((t) =>
            t.id === taskId ? { ...t, ...updates } : t
          ),
        })),
      removeTask: (taskId) =>
        set((state) => ({
          tasks: state.tasks.filter((t) => t.id !== taskId),
          currentTaskId: state.currentTaskId === taskId ? null : state.currentTaskId,
        })),

      // UI State
      isTasksPanelOpen: false,
      isTaskFormOpen: false,
      viewMode: 'kanban',
      toggleTasksPanel: () =>
        set((state) => ({ isTasksPanelOpen: !state.isTasksPanelOpen })),
      setIsTasksPanelOpen: (open) => set({ isTasksPanelOpen: open }),
      setIsTaskFormOpen: (open) => set({ isTaskFormOpen: open }),
      setViewMode: (mode) => set({ viewMode: mode }),

      // Draft Task
      draftTask: {},
      setDraftTitle: (title) =>
        set((state) => ({
          draftTask: { ...state.draftTask, title },
        })),
      setDraftDescription: (description) =>
        set((state) => ({
          draftTask: { ...state.draftTask, description },
        })),
      setDraftStatus: (status) =>
        set((state) => ({
          draftTask: { ...state.draftTask, status: status as any },
        })),
      setDraftPriority: (priority) =>
        set((state) => ({
          draftTask: { ...state.draftTask, priority: priority as any },
        })),
      setDraftDueDate: (dueDate) =>
        set((state) => ({
          draftTask: { ...state.draftTask, due_date: dueDate },
        })),
      setDraftProjectId: (projectId) =>
        set((state) => ({
          draftTask: { ...state.draftTask, project_id: projectId },
        })),
      setDraftTags: (tags) =>
        set((state) => ({
          draftTask: { ...state.draftTask, tags },
        })),
      clearDraft: () => set({ draftTask: {} }),

      // Filters
      filterStatus: null,
      filterPriority: null,
      filterProjectId: null,
      filterTag: null,
      searchQuery: '',
      filtresRetires: null,
      setFilterStatus: (status) => set({ filterStatus: status, filtresRetires: null }),
      setFilterPriority: (priority) => set({ filterPriority: priority, filtresRetires: null }),
      setFilterProjectId: (projectId) => set({ filterProjectId: projectId, filtresRetires: null }),
      setFilterTag: (tag) => set({ filterTag: tag, filtresRetires: null }),
      setSearchQuery: (query) => set({ searchQuery: query }),
      ouvrirSurLeProjet: (projetId) =>
        set((etat) => {
          const retires: FiltresRetires = {
            statut: etat.filterStatus,
            priorite: etat.filterPriority,
            etiquette: etat.filterTag,
            recherche: etat.searchQuery.trim() || null,
          };
          const aucun = !retires.statut && !retires.priorite && !retires.etiquette && !retires.recherche;
          return {
            filterProjectId: projetId,
            filterStatus: null,
            filterPriority: null,
            filterTag: null,
            searchQuery: '',
            filtresRetires: aucun ? null : retires,
          };
        }),
    }),
    {
      name: 'task-storage',
      partialize: (state) => ({
        tasks: state.tasks,
        viewMode: state.viewMode,
        filterStatus: state.filterStatus,
        filterPriority: state.filterPriority,
      }),
    }
  )
);
