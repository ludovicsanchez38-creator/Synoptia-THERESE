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
  searchQuery: string;
  setFilterStatus: (status: string | null) => void;
  setFilterPriority: (priority: string | null) => void;
  setFilterProjectId: (projectId: string | null) => void;
  setSearchQuery: (query: string) => void;
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
      searchQuery: '',
      setFilterStatus: (status) => set({ filterStatus: status }),
      setFilterPriority: (priority) => set({ filterPriority: priority }),
      setFilterProjectId: (projectId) => set({ filterProjectId: projectId }),
      setSearchQuery: (query) => set({ searchQuery: query }),
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
