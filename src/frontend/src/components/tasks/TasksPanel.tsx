/**
 * THÉRÈSE v2 - Tasks Panel
 *
 * Panel principal pour gérer les tâches.
 * Phase 3 - Tasks/Todos
 */

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Plus, ListTodo, LayoutGrid, RefreshCw, Filter } from 'lucide-react';
import { useTaskStore } from '../../stores/taskStore';
import { TaskKanban } from './TaskKanban';
import { TaskList } from './TaskList';
import { TaskForm } from './TaskForm';
import { Button } from '../ui/Button';
import { useDemoMask } from '../../hooks';
import * as api from '../../services/api';

interface TasksPanelProps {
  isOpen?: boolean;
  onClose?: () => void;
  standalone?: boolean;
}

export function TasksPanel({ isOpen, onClose, standalone = false }: TasksPanelProps) {
  const {
    tasks,
    viewMode,
    filterStatus,
    filterPriority,
    filterProjectId,
    isTaskFormOpen,
    setTasks,
    setCurrentTask,
    setIsTaskFormOpen,
    setViewMode,
    setFilterStatus,
    setFilterPriority,
    setFilterProjectId,
  } = useTaskStore();

  const { enabled: demoEnabled, populateMap } = useDemoMask();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  const effectiveOpen = standalone || isOpen;

  // Load tasks on mount
  useEffect(() => {
    if (effectiveOpen) {
      loadTasks();
    }
  }, [effectiveOpen, filterStatus, filterPriority, filterProjectId]);

  // Populate demo replacement map when demo mode is enabled
  useEffect(() => {
    if (!effectiveOpen || !demoEnabled) return;

    Promise.all([api.listContacts(), api.listProjects()])
      .then(([contacts, projects]) => {
        populateMap(contacts, projects);
      })
      .catch((err) => {
        console.error('Failed to load contacts/projects for demo mask:', err);
      });
  }, [effectiveOpen, demoEnabled, populateMap]);

  async function loadTasks() {
    setLoading(true);
    setError(null);

    try {
      const params: any = {};
      if (filterStatus) params.status = filterStatus;
      if (filterPriority) params.priority = filterPriority;
      if (filterProjectId) params.project_id = filterProjectId;

      const result = await api.listTasks(params);
      setTasks(result);
    } catch (err) {
      console.error('Failed to load tasks:', err);
      setError('Impossible de charger les tâches');
    } finally {
      setLoading(false);
    }
  }

  function handleNewTask() {
    setCurrentTask(null);
    setIsTaskFormOpen(true);
  }

  if (!effectiveOpen) return null;

  const tasksHeader = (
    <div className="px-6 py-4 border-b border-border/30 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center">
          <ListTodo className="w-5 h-5 text-accent-cyan" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-text">Taches</h2>
          <p className="text-sm text-text-muted">{tasks.length} tache{tasks.length > 1 ? 's' : ''}</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {/* View Mode Toggle */}
        <div className="flex items-center gap-1 bg-background/60 rounded-lg p-1">
          <button
            onClick={() => setViewMode('kanban')}
            className={`p-2 rounded transition-colors ${
              viewMode === 'kanban'
                ? 'bg-accent-cyan/20 text-accent-cyan'
                : 'text-text-muted hover:text-text'
            }`}
            title="Kanban"
          >
            <LayoutGrid className="w-4 h-4" />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`p-2 rounded transition-colors ${
              viewMode === 'list'
                ? 'bg-accent-cyan/20 text-accent-cyan'
                : 'text-text-muted hover:text-text'
            }`}
            title="Liste"
          >
            <ListTodo className="w-4 h-4" />
          </button>
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowFilters(!showFilters)}
          className={showFilters ? 'bg-accent-cyan/20 text-accent-cyan' : ''}
        >
          <Filter className="w-4 h-4" />
        </Button>

        <Button variant="ghost" size="sm" onClick={loadTasks}>
          <RefreshCw className="w-4 h-4" />
        </Button>

        <Button variant="primary" size="sm" onClick={handleNewTask}>
          <Plus className="w-4 h-4 mr-2" />
          Nouvelle tache
        </Button>

        {!standalone && (
          <button
            onClick={onClose}
            className="p-2 hover:bg-border/30 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-text-muted" />
          </button>
        )}
      </div>
    </div>
  );

  const tasksFilters = showFilters ? (
    <div className="px-6 py-3 border-b border-border/30 flex items-center gap-4">
      <select
        value={filterStatus || ''}
        onChange={(e) => setFilterStatus(e.target.value || null)}
        className="px-3 py-1.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
      >
        <option value="">Tous les statuts</option>
        <option value="todo">A faire</option>
        <option value="in_progress">En cours</option>
        <option value="done">Terminé</option>
        <option value="cancelled">Annulé</option>
      </select>

      <select
        value={filterPriority || ''}
        onChange={(e) => setFilterPriority(e.target.value || null)}
        className="px-3 py-1.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
      >
        <option value="">Toutes les priorités</option>
        <option value="urgent">Urgent</option>
        <option value="high">Haute</option>
        <option value="medium">Moyenne</option>
        <option value="low">Basse</option>
      </select>

      {(filterStatus || filterPriority || filterProjectId) && (
        <button
          onClick={() => {
            setFilterStatus(null);
            setFilterPriority(null);
            setFilterProjectId(null);
          }}
          className="text-sm text-accent-cyan hover:underline"
        >
          Réinitialiser
        </button>
      )}
    </div>
  ) : null;

  const tasksContent = (
    <>
      {error && (
        <div className="mx-6 mt-4 px-3 py-2 bg-red-500/10 border border-red-500/20 rounded-lg">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      <div className="flex-1 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <RefreshCw className="w-8 h-8 animate-spin text-accent-cyan" />
          </div>
        ) : isTaskFormOpen ? (
          <TaskForm />
        ) : viewMode === 'kanban' ? (
          <TaskKanban />
        ) : (
          <TaskList />
        )}
      </div>
    </>
  );

  // Mode standalone : pleine page
  if (standalone) {
    return (
      <div className="h-full flex flex-col bg-bg">
        {tasksHeader}
        {tasksFilters}
        {tasksContent}
      </div>
    );
  }

  // Mode modal
  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/60 backdrop-blur-md"
          onClick={onClose}
        />

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="relative w-full h-full max-w-7xl max-h-[90vh] mx-4 bg-surface/95 backdrop-blur-xl border border-border/50 rounded-xl shadow-2xl overflow-hidden flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {tasksHeader}
          {tasksFilters}
          {tasksContent}
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
